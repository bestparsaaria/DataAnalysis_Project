"""Text, deduplication sensitivity and evidence-based EDA reporting helpers."""
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
import hashlib
from importlib.metadata import version as package_version
import html
import math
import re
import sqlite3
import tempfile
import unicodedata
import numpy as np
import regex
from audit_shared import (fingerprint, finite_number, usable_text, media_available,
                          text_list_available, pct, markdown_table)

SCRIPTS = ('Latin','Cyrillic','Arabic','Han','Hiragana','Katakana','Hangul','Greek','Hebrew',
           'Devanagari','Thai','Bengali','Tamil','Telugu','Armenian','Georgian','Common','Inherited')
SCRIPT_PATTERN = regex.compile('|'.join(f'(?P<{s}>\\p{{Script={s}}})' for s in SCRIPTS))
UNUSUAL = ['replacement', 'control_excluding_tab_lf_cr', 'format', 'surrogate', 'private_use', 'unassigned']
LID_SOURCE = 'https://fasttext.cc/docs/en/language-identification.html'


@lru_cache(maxsize=65536)
def character_class(char):
    cat = unicodedata.category(char)
    m = SCRIPT_PATTERN.fullmatch(char)
    script = m.lastgroup if m else 'Other_script'
    unusual = []
    if char == '\ufffd': unusual.append('replacement')
    if cat == 'Cc' and char not in '\t\n\r': unusual.append('control_excluding_tab_lf_cr')
    for code, name in [('Cf','format'),('Cs','surrogate'),('Co','private_use'),('Cn','unassigned')]:
        if cat == code: unusual.append(name)
    return script, tuple(unusual), cat.startswith('L')


class LanguageDetector:
    def __init__(self, path, confidence=.8, margin=.2, min_letters=20, max_characters=5000):
        import fasttext
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f'Language model missing: {self.path}. See UNIVARIATE_EDA_GUIDE_EN.md; supply --language-model.')
        self.model = fasttext.load_model(str(self.path))
        self.confidence, self.margin = confidence, margin
        self.min_letters, self.max_characters = min_letters, max_characters
        self.manifest = dict(engine='fasttext-wheel', engine_version=package_version('fasttext-wheel'), model='lid.176.ftz', path=str(self.path.resolve()),
                             sha256=hashlib.sha256(self.path.read_bytes()).hexdigest(), source=LID_SOURCE,
                             license='CC BY-SA 3.0', minimum_score=confidence, minimum_top2_margin=margin,
                             minimum_letters=min_letters, max_input_characters=max_characters,
                             interpretation='Model scores are not validated accuracy estimates; abstain on low score/margin or short text. Mixed-language text receives at most one dominant label.')

    def predict(self, texts):
        # Batch API avoids the single-string NumPy 2 copy=False incompatibility.
        labels, scores = self.model.predict(texts, k=2)
        output = []
        for labs, ps in zip(labels, scores):
            if len(ps)<2 or ps[0] < self.confidence or ps[0]-ps[1] < self.margin:
                output.append(('unknown','low_confidence_or_margin'))
            else: output.append((labs[0].removeprefix('__label__'), None))
        return output


class TextAudit:
    def __init__(self, detector=None, short_max_words=5, long_min_words=500):
        self.detector = detector
        self.short, self.long = short_max_words, long_min_words
        self.counts = Counter(); self.languages = Counter(); self.unknown = Counter()
        self.script_chars = Counter(); self.script_rows = Counter()
        self.unusual_chars = Counter(); self.unusual_rows = Counter()
        self.by_rating = {r:dict(rows=0, string_rows=0, blank=0, unavailable=0, chars=Counter(), words=Counter()) for r in range(1,6)}
        self.pending = []

    def add(self, record):
        self.counts['all_review_objects'] += 1
        text = record.get('text'); rating = record.get('rating')
        bucket = self.by_rating[int(rating)] if finite_number(rating) and 1<=rating<=5 and rating%1==0 else None
        if bucket is not None:
            bucket['rows'] += 1; bucket['unavailable'] += not usable_text(text)
        if not isinstance(text,str):
            self.languages['unknown'] += 1; self.unknown['absent_null_or_wrong_type'] += 1
            return
        self.counts['string_texts'] += 1
        words = len(text.split()); blank = not text.strip()
        if bucket is not None:
            bucket['string_rows'] += 1; bucket['blank'] += blank
            bucket['chars'][len(text)] += 1; bucket['words'][words] += 1
        self.counts['blank_texts'] += blank
        if not blank:
            self.counts['nonblank_string_texts'] += 1
            self.counts['very_short'] += words <= self.short
            self.counts['very_long'] += words >= self.long
        scripts, anomalies = set(), set()
        for char, count in Counter(text).items():
            script, problems, letter = character_class(char)
            self.script_chars[script] += count; scripts.add(script)
            for kind in problems:
                self.unusual_chars[kind] += count; anomalies.add(kind)
        self.script_rows.update(scripts); self.unusual_rows.update(anomalies)
        self.counts['all_characters'] += len(text)
        self.counts['texts_with_any_unusual'] += bool(anomalies)
        # Script membership is never substituted for a language classifier.
        if not self.detector:
            self.languages['unknown'] += 1; self.unknown['detector_not_configured'] += 1
            return
        if blank or 'surrogate' in anomalies:
            self.languages['unknown'] += 1; self.unknown['blank' if blank else 'invalid_unicode'] += 1
            return
        cleaned = ' '.join(html.unescape(re.sub(r'<[^>]*>', ' ', text)).split())
        if len(cleaned)>self.detector.max_characters: self.counts['language_input_truncated'] += 1
        cleaned = cleaned[:self.detector.max_characters]
        if sum(c.isalpha() for c in cleaned)<self.detector.min_letters:
            self.languages['unknown'] += 1; self.unknown['too_few_letters'] += 1
            return
        self.pending.append(cleaned)
        if len(self.pending)>=1024: self.flush()

    def flush(self):
        if self.pending:
            for label, reason in self.detector.predict(self.pending):
                self.languages[label] += 1
                if reason: self.unknown[reason] += 1
            self.pending.clear()

    def finish(self, describe):
        self.flush(); n=self.counts['all_review_objects']; strings=self.counts['string_texts']
        lengths = []
        for kind in ('very_short','very_long'):
            count=self.counts[kind]
            lengths.append(dict(classification=kind, count=count, percent_all_reviews=pct(count,n),
                                percent_nonblank_string_texts=pct(count,self.counts['nonblank_string_texts'])))
        rows = []
        for rating,b in self.by_rating.items():
            rows.append(dict(rating=rating, rating_rows=b['rows'], string_text_rows=b['string_rows'],
                             unavailable_text_count=b['unavailable'], unavailable_percent=pct(b['unavailable'],b['rows']),
                             blank_text_count=b['blank'], blank_percent_of_rating_rows=pct(b['blank'],b['rows']),
                             character_summary=describe(b['chars']), word_summary=describe(b['words'])))
        char_rows = [dict(script=k, character_count=v, character_percent=pct(v,self.counts['all_characters']),
                         texts_containing=self.script_rows[k], percent_string_texts=pct(self.script_rows[k],strings)) for k,v in self.script_chars.most_common()]
        unusual = [dict(kind=k, character_count=self.unusual_chars[k], texts_affected=self.unusual_rows[k],
                        percent_string_texts=pct(self.unusual_rows[k],strings)) for k in UNUSUAL]
        languages = [dict(language=k,count=v,percent_all_reviews=pct(v,n)) for k,v in self.languages.most_common()]
        english=self.languages['en']; unknown=self.languages['unknown']; nonenglish=n-english-unknown
        return dict(status='computed' if self.detector else 'language_detection_not_configured',
                    short_max_words=self.short, long_min_words=self.long, thresholds=dict(very_short=f'1 to {self.short} whitespace tokens', very_long=f'>= {self.long} whitespace tokens',
                                    blank_policy='Reported separately; excluded from both threshold classes; not deleted'),
                    counts=dict(self.counts), length_classes=lengths, languages=languages, unknown_reasons=dict(self.unknown),
                    language_groups=[dict(group=k,count=v,percent_all_reviews=pct(v,n)) for k,v in [('English',english),('non-English',nonenglish),('unknown',unknown)]],
                    scripts=char_rows, unusual_characters=unusual, by_rating=rows,
                    unicode_database=unicodedata.unidata_version, regex_version=regex.__version__)


class DedupSensitivity:
    """Collision-checked exact parsed-record equality; derived view only."""
    def __init__(self, is_meta):
        self.temp=tempfile.TemporaryDirectory(prefix='amazon-eda-dedup-')
        self.db=sqlite3.connect(Path(self.temp.name)/'seen.sqlite')
        self.db.execute('PRAGMA synchronous=OFF'); self.db.execute('PRAGMA journal_mode=OFF')
        self.db.execute('CREATE TABLE seen(fp BLOB, value TEXT)'); self.db.execute('CREATE INDEX seen_fp ON seen(fp)')
        self.meta=is_meta; self.rows=self.retained=0
        self.hist={k:Counter() for k in (('price','average_rating','rating_number') if is_meta else ('rating','helpful_vote','text_characters','text_whitespace_words'))}
    def add(self, record):
        fp, value=fingerprint(record); self.rows+=1
        if any(v==value for (v,) in self.db.execute('SELECT value FROM seen WHERE fp=?',(fp,))): return
        self.db.execute('INSERT INTO seen VALUES (?,?)',(fp,value)); self.retained+=1
        for key in self.hist:
            v=record.get(key)
            if key.startswith('text_'):
                if isinstance(record.get('text'),str): self.hist[key][len(record['text']) if key=='text_characters' else len(record['text'].split())]+=1
                continue
            if not finite_number(v): continue
            if key=='rating' and not (1<=v<=5 and v%1==0): continue
            if key=='average_rating' and not 1<=v<=5: continue
            if key in ('helpful_vote','rating_number') and not (type(v) is int and v>=0): continue
            if key=='price' and v<0: continue
            self.hist[key][v]+=1
    def finish(self, describe, raw_hist):
        output=[]
        for key,h in self.hist.items():
            raw,unique=describe(raw_hist[key]),describe(h)
            support=set(h)|set(raw_hist[key]); nr=raw['n']; nu=unique['n']
            tv=.5*sum(abs(raw_hist[key][v]/nr-h[v]/nu) for v in support) if nr and nu else None
            output.append(dict(metric=key,raw=raw,exact_deduplicated=unique,
                               raw_frequencies=sorted(raw_hist[key].items()), exact_deduplicated_frequencies=sorted(h.items()),
                               total_variation_distance=tv,
                               mean_change=unique.get('mean',0)-raw.get('mean',0) if nr and nu else None,
                               median_change=unique.get('median',0)-raw.get('median',0) if nr and nu else None))
        self.db.close(); self.temp.cleanup()
        return dict(policy='Keep first source-line copy of each type-sensitive canonical parsed record; verify canonical equality after SHA-256 candidate lookup; no fuzzy/user/text-only deduplication.',
                    raw_objects=self.rows,retained_objects=self.retained,extra_exact_copies=self.rows-self.retained,
                    extra_percent=pct(self.rows-self.retained,self.rows),metrics=output)


def shape_statement(summary):
    if not summary.get('n'): return 'No valid values; shape is unavailable.'
    s=summary['skewness_population']
    if s is None: return 'Values are constant; skewness and tail shape cannot be estimated.'
    direction='positive' if s>0 else 'negative' if s<0 else 'zero'
    return (f'Empirical skewness is {s:.3f} ({direction}); mean {summary["mean"]:.3f} versus median {summary["median"]:.3f}. '
            f'The largest 1% of observations account for {summary["top_one_percent_value_share_percent"] or 0:.2f}% of the total value. '
            'These describe the observed shape without asserting a fitted tail distribution.')


def rating_statement(balance):
    counts=balance['class_counts']; n=balance['denominator']
    if len(set(counts.values()))==1: return 'All five star classes have equal counts.'
    high=balance['high_4_5_percent']
    return (f'The 4–5-star share is {high:.2f}%; '+('a majority of valid ratings.' if high>50 else 'it is not a majority of valid ratings.')+
            f' Absent classes: {balance["absent_classes"]}. All-five-class ratio: '+
            ('undefined because at least one class is absent.' if balance['all_five_class_ratio'] is None else f'{balance["all_five_class_ratio"]:.3f}.'))


def extended_report(d):
    lines=['', '### Exact-duplicate sensitivity', '']
    dd=d['deduplication_sensitivity']
    lines += [f"Raw objects: {dd['raw_objects']:,}; retained in the derived exact-unique view: {dd['retained_objects']:,}; extra copies: {dd['extra_exact_copies']:,} ({dd['extra_percent'] or 0:.4f}%). "+dd['policy'], '']
    rows=[dict(metric=m['metric'],raw_n=m['raw']['n'],unique_n=m['exact_deduplicated']['n'],
               raw_mean=m['raw'].get('mean'),unique_mean=m['exact_deduplicated'].get('mean'),
               median_change=m['median_change'],tv=m['total_variation_distance']) for m in dd['metrics']]
    lines+=markdown_table(rows,[('metric','Metric'),('raw_n','Raw valid n'),('unique_n','Unique valid n'),('raw_mean','Raw mean'),('unique_mean','Unique mean'),('median_change','Median change'),('tv','Total variation')])
    lines+=['','Total variation ranges from 0 (identical empirical distributions) to 1. It compares normalized frequencies; no significance threshold is assumed. Raw distributions remain the primary descriptive view.', '',f"![Deduplication sensitivity]({d['figures']['dedup_sensitivity'][0]})"]
    if 'text_audit' not in d: return lines
    t=d['text_audit']
    lines+=['','### Review text audit','',f"Thresholds: {t['thresholds']}. Denominators and all counts are in text_audit.json. These are operational length labels, not semantic quality judgments.",'']
    lines+=markdown_table(t['length_classes'],[('classification','Length class'),('count','Count'),('percent_all_reviews','% all reviews'),('percent_nonblank_string_texts','% nonblank string bodies')])
    lines+=['','### Probable dominant language','',
            'fastText predictions are heuristic labels. Text with fewer than 20 letters after derived HTML/whitespace handling, invalid Unicode, confidence below 0.8 or top-two margin below 0.2 is unknown. '
            'At most the first 5,000 cleaned characters are classified; truncation counts are recorded. No text leaves this machine. '
            'Non-English script is not itself a language. Short texts, code switching and domain shift limit accuracy; no language label deletes a row.','']
    lines+=markdown_table(t['language_groups'],[('group','Group'),('count','Count'),('percent_all_reviews','% all reviews')])
    lines+=['',f"Unknown reasons: {t['unknown_reasons']}. Language input truncated: {t['counts'].get('language_input_truncated',0):,}.",'']
    lines+=markdown_table(t['languages'],[('language','Predicted ISO code / unknown'),('count','Count'),('percent_all_reviews','% all reviews')])
    lines+=['',f"![Language and length audit]({d['figures']['text_language'][0]})",'', '### Unicode scripts and unusual character families','',
            'Each character belongs to one Script bucket (selected named scripts, Common, Inherited, or Other_script). Character shares sum to 100%; a text may contain multiple scripts, so text percentages overlap. '
            'Common includes punctuation, digits and many symbols; script membership is not a defect. Format/private-use/unassigned flags need context and are not automatic corruption labels. '
            'Character totals and affected-text totals are different units.','']
    lines+=markdown_table(t['scripts'],[('script','Script'),('character_count','Characters'),('character_percent','% characters'),('texts_containing','Texts containing'),('percent_string_texts','% string texts')])
    lines+=['']+markdown_table(t['unusual_characters'],[('kind','Family'),('character_count','Characters'),('texts_affected','Texts affected'),('percent_string_texts','% string texts')])
    lines+=['',f"![Unicode scripts]({d['figures']['text_unicode'][0]})",'', '### Initial relationship between text and rating','',
            'This small bivariate extension fulfills the Track B text audit. Each rating group includes all valid ratings; length summaries use its string bodies, including blank strings. '
            'Unavailable-body and blank-body rates use all reviews in that rating group. Product/user dependence is not treated as independent evidence; no causal or sentiment claim follows.','']
    rows=[dict(rating=r['rating'],n=r['rating_rows'],text_n=r['string_text_rows'],blank=r['blank_percent_of_rating_rows'],
               unavailable=r['unavailable_percent'],median=r['word_summary'].get('median'),q1=r['word_summary'].get('q1'),q3=r['word_summary'].get('q3')) for r in t['by_rating']]
    lines+=markdown_table(rows,[('rating','Stars'),('n','Reviews'),('text_n','String bodies'),('blank','Blank %'),('unavailable','Unavailable %'),('median','Median words'),('q1','Q1 words'),('q3','Q3 words')])
    lines+=['',f"![Text by rating]({d['figures']['text_by_rating'][0]})"]
    return lines


def plot_extensions(d, out, plt, save_figure):
    paths={}; dd=d['deduplication_sensitivity']
    fig,axes=plt.subplots(1,3,figsize=(16,4.8),layout='constrained')
    keys=[m['metric'] for m in dd['metrics']]; x=np.arange(len(keys)); width=.36
    for offset,label in [(-width/2,'raw'),(width/2,'exact_deduplicated')]:
        axes[0].bar(x+offset,[m[label].get('mean',0) for m in dd['metrics']],width,label=label)
    axes[0].set_xticks(x,keys,rotation=25,ha='right'); axes[0].set_yscale('symlog'); axes[0].set_title('Mean sensitivity (metric-specific units)'); axes[0].legend(fontsize=8)
    axes[1].bar(x,[m['total_variation_distance'] or 0 for m in dd['metrics']]); axes[1].set_xticks(x,keys,rotation=25,ha='right'); axes[1].set(title='Empirical total variation distance',ylabel='0 = identical distributions')
    primary=next(m for m in dd['metrics'] if m['metric'] in ('rating','price'))
    for key,label in [('raw_frequencies','Raw'),('exact_deduplicated_frequencies','Exact unique')]:
        items=primary[key]
        if items:
            v,c=zip(*items); cumulative=np.cumsum(c)/sum(c)*100
            axes[2].step(v,cumulative,where='post',label=label,linestyle='-' if label=='Raw' else '--')
    axes[2].set(title='Full empirical CDF: '+primary['metric'],ylabel='Cumulative %',xlabel=primary['metric'])
    if primary['metric']=='price': axes[2].set_xscale('symlog')
    if primary['raw']['n']: axes[2].legend(fontsize=8)
    else: axes[2].text(.5,.5,'No valid observations',ha='center',transform=axes[2].transAxes)
    fig.suptitle(d['name']+' | exact-duplicate sensitivity')
    paths['dedup_sensitivity']=save_figure(fig,out,d['name']+'__dedup_sensitivity',plt)
    if 'text_audit' not in d:return paths
    t=d['text_audit']; fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    g=t['language_groups']; axes[0].bar([r['group'] for r in g],[r['percent_all_reviews'] or 0 for r in g]); axes[0].set(title='Probable dominant language',ylabel='% of all review objects')
    l=t['length_classes']; axes[1].bar([r['classification'] for r in l],[r['percent_all_reviews'] or 0 for r in l]); axes[1].set(title=f"Nonblank bodies: <= {t['short_max_words']} or >= {t['long_min_words']} words",ylabel='% of all review objects')
    fig.suptitle(d['name']+' | text audit')
    paths['text_language']=save_figure(fig,out,d['name']+'__text_language',plt)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    r=t['scripts']; axes[0].barh([x['script'] for x in r],[x['character_percent'] or 0 for x in r]); axes[0].set(xlabel='% of raw body characters',title='Unicode Script membership'); axes[0].invert_yaxis()
    r=t['unusual_characters']; axes[1].barh([x['kind'] for x in r],[x['percent_string_texts'] or 0 for x in r]); axes[1].set(xlabel='% of string bodies',title='Potentially unusual character families')
    fig.suptitle(d['name']); paths['text_unicode']=save_figure(fig,out,d['name']+'__text_unicode',plt)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained'); boxes=[]; positions=[]
    for r in t['by_rating']:
        s=r['word_summary']
        if not s['n']:continue
        boxes.append(dict(med=s['median'],q1=s['q1'],q3=s['q3'],whislo=s['p05'],whishi=s['p95'],fliers=[]));positions.append(r['rating'])
    if boxes:axes[0].bxp(boxes,positions=positions,showfliers=False)
    axes[0].set(xlabel='Rating (stars)',ylabel='Whitespace words (symlog)',title='Median, IQR and P5–P95 by rating');axes[0].set_yscale('symlog');axes[0].set_xticks(range(1,6))
    axes[1].bar(range(1,6),[r['unavailable_percent'] or 0 for r in t['by_rating']],label='Unavailable body')
    for r in t['by_rating']:
        if not r['rating_rows']: axes[1].text(r['rating'],0,'No reviews',rotation=90,va='bottom',ha='center',fontsize=8)
    axes[1].set(xlabel='Rating (stars)',ylabel='% of rating-group reviews',title='Unavailable body by rating');axes[1].set_xticks(range(1,6))
    fig.suptitle(d['name']+' | text and rating; raw copies retained')
    paths['text_by_rating']=save_figure(fig,out,d['name']+'__text_by_rating',plt)
    return paths