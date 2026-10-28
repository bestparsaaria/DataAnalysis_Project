"""Joined availability and exploratory product-unit missingness comparisons."""
from collections import Counter, defaultdict
import csv
import gzip
import sqlite3
import numpy as np
from audit_shared import (valid_id, usable_text, media_available, text_list_available,
                          finite_number, pct, markdown_table)

MODALITIES = ['review_text', 'review_rating', 'review_image_url', 'timestamp',
              'user_item_interaction', 'metadata', 'product_image_url', 'price',
              'product_text', 'any_image_url', 'product_features_text', 'product_description_text']
BITS = {k: 1 << i for i, k in enumerate(MODALITIES)}
COMBINATIONS = {
    'text_rating_time': ['review_text', 'review_rating', 'timestamp'],
    'text_metadata_image': ['review_text', 'metadata', 'any_image_url'],
    'six_core_facets': ['review_text', 'review_rating', 'timestamp', 'user_item_interaction', 'metadata', 'any_image_url'],
    'text_rating_time_metadata_price': ['review_text', 'review_rating', 'timestamp', 'metadata', 'price'],
}


def local_mask(record, kind, date, as_of=None):
    """Local usability, not proof of URL retrieval or historical availability."""
    yes = []
    if kind == 'review':
        if usable_text(record.get('text')): yes.append('review_text')
        r = record.get('rating')
        if finite_number(r) and 1 <= r <= 5 and r % 1 == 0: yes.append('review_rating')
        if media_available(record.get('images'), 'review'): yes.append('review_image_url')
        if date is not None and (as_of is None or date <= as_of): yes.append('timestamp')
        if valid_id(record.get('user_id')) and valid_id(record.get('parent_asin')): yes.append('user_item_interaction')
    else:
        yes.append('metadata')
        if media_available(record.get('images'), 'meta'): yes.append('product_image_url')
        if finite_number(record.get('price')) and record['price'] >= 0: yes.append('price')
        if text_list_available(record.get('features')): yes.append('product_features_text')
        if text_list_available(record.get('description')): yes.append('product_description_text')
        if usable_text(record.get('title')) or 'product_features_text' in yes or 'product_description_text' in yes: yes.append('product_text')
    return sum(BITS[k] for k in yes)


def permutation_association(values, labels, *, seed=20261027, permutations=499, min_group=30):
    """Unweighted product units, eta squared and permutation p; no review IID assumption."""
    sizes = Counter(labels)
    retained = [(y, g) for y, g in zip(values, labels) if sizes[g] >= min_group]
    answer = dict(product_units=len(values), included_products=len(retained),
                  excluded_small_group_products=len(values)-len(retained), min_group_products=min_group,
                  permutations=permutations, seed=seed, group_sizes=dict(sorted(sizes.items())),
                  status='insufficient_groups', eta_squared=None, permutation_p=None)
    levels = sorted({g for _, g in retained})
    if len(levels) < 2: return answer
    lookup = {g: i for i, g in enumerate(levels)}
    codes = np.array([lookup[g] for _, g in retained], dtype=int)
    y = np.array([v for v, _ in retained], dtype=float)
    n = np.bincount(codes); mean = y.mean(); ss = np.sum((y-mean)**2)
    if ss == 0:
        answer.update(status='constant_missingness', eta_squared=0., permutation_p=None)
        return answer
    def between(v):
        means = np.bincount(codes, weights=v)/n
        return float(np.sum(n*(means-mean)**2))
    observed = between(y); rng = np.random.default_rng(seed)
    extreme = sum(between(rng.permutation(y)) >= observed-1e-12 for _ in range(permutations))
    answer.update(status='computed', eta_squared=observed/float(ss), permutation_p=(extreme+1)/(permutations+1),
                  group_mean_missing_percent={g:100*float(y[codes==lookup[g]].mean()) for g in levels},
                  missing_rate_range_percentage_points=100*float(max(y[codes==lookup[g]].mean() for g in levels)-min(y[codes==lookup[g]].mean() for g in levels)))
    return answer


def bh_adjust(tests):
    ordered = sorted((t['permutation_p'], i) for i, t in enumerate(tests) if t.get('permutation_p') is not None)
    running = 1.
    for rank in range(len(ordered), 0, -1):
        p, i = ordered[rank-1]; running = min(running, p*len(ordered)/rank)
        tests[i]['bh_q'] = running
    for t in tests: t.setdefault('bh_q', None)


def joined_audit(results, paths, output, permutations=499):
    by_name = {d['name']: d for d in results}
    summaries, group_rows, tests, product_samples = [], [], [], []
    files = []
    for cat in ('All_Beauty', 'Appliances'):
        if cat not in by_name or 'meta_'+cat not in by_name: continue
        db = sqlite3.connect(paths[cat]); db.execute('ATTACH DATABASE ? AS meta_db', (str(paths['meta_'+cat]),))
        # Unique canonical version per parent; no arbitrary conflicting metadata row.
        db.execute('CREATE TEMP TABLE meta_keys AS SELECT parent,min(line) line,count(*) copies,count(DISTINCT canonical) versions FROM meta_db.records WHERE parent IS NOT NULL GROUP BY parent')
        db.execute('CREATE UNIQUE INDEX mk_parent ON meta_keys(parent)')
        combos, joins, available = Counter(), Counter(), Counter()
        groups = defaultdict(lambda: [0, Counter()])
        products = {}  # one key per observed parent; accumulated review missing fractions
        dest = output/(cat+'__sample_modality_availability.csv.gz'); files.append(str(dest))
        query = '''SELECT r.line,r.parent,r.mask,k.copies,k.versions,m.mask,m.main_category
                    FROM records r LEFT JOIN meta_keys k ON r.parent=k.parent
                    LEFT JOIN meta_db.records m ON k.line=m.line ORDER BY r.line'''
        with gzip.open(dest, 'wt', encoding='utf-8', newline='') as f:
            w = csv.writer(f); w.writerow(['source_line', 'join_status', 'metadata_main_category', *MODALITIES, 'mask'])
            for line, parent, mask, copies, versions, mmask, label in db.execute(query):
                status = 'invalid_parent' if parent is None else 'unmatched' if copies is None else 'conflicting_metadata' if versions > 1 else 'matched'
                if status == 'matched': mask |= mmask
                group = ('category:'+label) if status == 'matched' and label is not None else 'status:'+('missing_main_category' if status == 'matched' else status)
                if mask & (BITS['review_image_url'] | BITS['product_image_url']): mask |= BITS['any_image_url']
                flags = {k: int(bool(mask & BITS[k])) for k in MODALITIES}
                joins[status] += 1; combos[mask] += 1; available.update(flags)
                groups[group][0] += 1
                groups[group][1].update({k: 1-v for k,v in flags.items()})
                if parent is not None:
                    p = products.setdefault(parent, dict(category=cat, group=group, n=0, missing=Counter()))
                    p['n'] += 1
                    p['missing'].update({k: 1-flags[k] for k in ('review_text','review_image_url')})
                w.writerow([line, status, label if status == 'matched' else '', *flags.values(), mask])
        total = sum(combos.values())
        rates = [dict(modality=k, available=available[k], unavailable=total-available[k], denominator=total, available_percent=pct(available[k],total)) for k in MODALITIES]
        combination_rows = []
        for label, members in COMBINATIONS.items():
            bits = sum(BITS[k] for k in members); count = sum(n for m,n in combos.items() if m & bits == bits)
            combination_rows.append(dict(combination=label, members=members, available=count, denominator=total, available_percent=pct(count,total)))
        patterns = [dict(mask=m, available_modalities=[k for k in MODALITIES if m & BITS[k]], count=n, percent=pct(n,total)) for m,n in sorted(combos.items())]
        for group, (n, missing) in sorted(groups.items()):
            for k in ('review_text','review_image_url','product_image_url','price'):
                group_rows.append(dict(category=cat, grouping='metadata_main_category', group=group, unit='review record', modality=k,
                                       denominator=n, unavailable=missing[k], unavailable_percent=pct(missing[k],n),
                                       distinct_valid_parents=sum(1 for p in products.values() if p['group']==group)))
        # Product-level metadata census: includes products without observed reviews.
        for parent, mask, label in db.execute('SELECT m.parent,m.mask,m.main_category FROM meta_keys k JOIN meta_db.records m ON m.line=k.line WHERE k.versions=1'):
            group = 'category:'+label if label is not None else 'status:missing_main_category'
            product_samples.append((parent, cat, group, 'metadata product', {k: float(not(mask & BITS[k])) for k in ('product_image_url','price')}))
        for parent,p in products.items():
            product_samples.append((parent,cat,p['group'],'review parent product', {k: p['missing'][k]/p['n'] for k in ('review_text','review_image_url')}))
        summaries.append(dict(category=cat, denominator=total, denominator_unit='all parsed review objects, raw copies retained',
                              complete=by_name[cat]['complete'] and by_name['meta_'+cat]['complete'], join_status_counts=dict(joins),
                              rates=rates, combinations=combination_rows, exact_patterns=patterns, per_sample_file=str(dest),
                              metadata_products_excluded_invalid_or_conflicting=db.execute('SELECT count(*) FROM meta_keys WHERE versions>1').fetchone()[0],
                              metadata_rows_with_invalid_parent=db.execute('SELECT count(*) FROM meta_db.records WHERE parent IS NULL').fetchone()[0]))
        db.close()
    # Conditional product-weighted rates complement review-weighted tables.
    buckets = defaultdict(list)
    for parent,cat,group,unit,values in product_samples:
        for metric,v in values.items(): buckets[(cat,group,unit,metric)].append(v)
    for (cat,group,unit,metric), values in sorted(buckets.items()):
        group_rows.append(dict(category=cat, grouping='metadata_main_category', group=group, unit=unit, modality=metric,
                               denominator=len(values), unavailable=sum(values) if unit=='metadata product' else None,
                               unavailable_percent=100*float(np.mean(values)), distinct_valid_parents=len(values)))
    # Shared products excluded ONLY from cross-download comparisons to keep each unit once.
    memberships = defaultdict(set)
    for parent,cat,*_ in product_samples: memberships[parent].add(cat)
    shared = {p for p,cats in memberships.items() if len(cats)>1}
    for grouping, selected in [('download_category', product_samples)] + [('main_category_within_'+c, [p for p in product_samples if p[1]==c]) for c in ('All_Beauty','Appliances')]:
        for metric in ('review_text','review_image_url','product_image_url','price'):
            rows = [(vals[metric], cat if grouping=='download_category' else group) for parent,cat,group,unit,vals in selected
                    if metric in vals and (parent not in shared if grouping=='download_category' else group.startswith('category:'))]
            vals, labels = zip(*rows) if rows else ([], [])
            test = permutation_association(vals, labels, permutations=permutations)
            test.update(grouping=grouping, modality=metric,
                        unit='parent product; review missing fractions for review fields, binary missingness for metadata fields',
                        excluded_shared_parent_ids=len(shared) if grouping=='download_category' else 0)
            tests.append(test)
    bh_adjust(tests)
    return dict(contract_version='2.0.0', image_evidence='syntactically usable HTTP(S) URL in recognized descriptor fields; NOT a download check',
                text_evidence='nonblank Unicode-safe content; no claim of semantic informativeness',
                inference='Exploratory product-unit label permutation; exchangeability/independence of products is an assumption. Association is not causation or proof of MCAR/MAR/MNAR.',
                samples=summaries, conditional_missingness=group_rows, association_tests=tests, files=files)


def report_lines(result):
    lines = ['## Joined multimodal availability', '',
             'Each parsed review has one row in the compressed per-sample table, identified by source line. Counts retain raw review copies. '
             'Conflicting metadata versions are unavailable; identical metadata copies are collapsed only for this derived join. '
             'Image availability means a locally valid URL, never a verified image download. Missing below means unavailable under the field contract, including malformed content.', '']
    for d in result.get('samples', []):
        lines += ['### '+d['category'], '', f"Review denominator: {d['denominator']:,}. Join statuses: {d['join_status_counts']}.", '']
        lines += markdown_table(d['rates'], [('modality','Facet'),('available','Available n'),('unavailable','Unavailable n'),('denominator','All reviews n'),('available_percent','Available %')])
        lines += [''] + markdown_table(d['combinations'], [('combination','Required combination'),('available','Available n'),('available_percent','Available %')])
    lines += ['', '## Conditional missingness and association', '',
              'Full subgroup counts and rates are in conditional_missingness.csv. Review-unit rates weight popular products more heavily. '
              'Review-parent rates first compute each product’s missing fraction and then give products equal weight. Metadata-product rates count each unambiguous product once, including products without reviews. '
              'Unknown/conflicting joins stay in descriptive tables; missing category labels are excluded from within-category tests. Groups below 30 products are excluded from tests, not hidden from tables. '
              'Tests use 499 fixed-seed label permutations by default, eta squared for effect size and Benjamini–Hochberg q-values across computed tests. '
              'Product independence/exchangeability remains an assumption; overlapping users and product families can violate it. These are exploratory associations, not proofs of a missingness mechanism.', '']
    lines += markdown_table(result.get('association_tests',[]), [('grouping','Grouping'),('modality','Unavailable facet'),('included_products','Products tested'),('eta_squared','Eta squared'),('permutation_p','Permutation p'),('bh_q','BH q'),('status','Status')])
    return lines