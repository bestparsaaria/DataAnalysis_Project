# Quality Audit Results

Audit reference (UTC): 2026-10-27T15:20:55.675189+00:00

Execution status: **complete**. This is scan completion, not a declaration that data are clean.

Raw files were read only. All decisions are proposals for a later logged transformation.

## Summary

| File | Objects | Extra exact copies | Critical review rows unusable before dedup |
|---|---:|---:|---:|
| All_Beauty | 701,528 | 7,275 | 0 |
| meta_All_Beauty | 112,590 | 0 | None |
| Appliances | 2,128,605 | 22,656 | 0 |
| meta_Appliances | 94,327 | 0 | None |

Critical review checks concern parent key, discrete stars and usable non-future timestamp. These checks do not establish an eligible prediction cohort.
The narrow flagged-record counter is the union of value, nested and top-level type issues. The broader counter also includes identity and text rules. Neither is a deletion rule.

## All_Beauty

Value/nested/type union: **0** of 701,528 objects. Any content/type flag union: **367**. Missing-only cases, parse failures, duplicate status and statistical outliers have their own counts; they are not silently merged into these unions.

### Field coverage and type compatibility

| Field | Missing/empty n | Missing/empty % | Wrong type n | Initial missingness decision |
| --- | --- | --- | --- | --- |
| asin | 0 | 0 | 0 | Retain with a flag; exclude from identity checks requiring this key. |
| helpful_vote | 0 | 0 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| images | 641844 | 91.49 | 0 | Retain with an availability flag; empty collections are not parsing errors. |
| parent_asin | 0 | 0 | 0 | Quarantine from analyses requiring this field; recover from source if possible. |
| rating | 0 | 0 | 0 | Quarantine from analyses requiring this field; recover from source if possible. |
| text | 720 | 0.1026 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| timestamp | 0 | 0 | 0 | Quarantine from analyses requiring this field; recover from source if possible. |
| title | 0 | 0 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| user_id | 0 | 0 | 0 | Retain with a flag; exclude from identity checks requiring this key. |
| verified_purchase | 0 | 0 | 0 | Retain and report missingness; choose any later transformation on training data only. |

### Nonzero validation flags

| Rule | Field | Family | Affected n | Denominator | % | Proposed decision |
| --- | --- | --- | --- | --- | --- | --- |
| control_character | text | text | 3 | 701528 | 0.000428 | Inspect before a logged text-normalization step. |
| placeholder_string | text | text | 184 | 701528 | 0.02623 | Review context before recoding as missing. |
| placeholder_string | title | text | 278 | 701528 | 0.03963 | Review context before recoding as missing. |

### Duplicate and repeated-key checks

| Check | Groups | Rows involved | Rows beyond first | Proposed decision |
| --- | --- | --- | --- | --- |
| exact_parsed_record_duplicates | 6138 | 13413 | 7275 | Propose keeping the first source-line copy in a later derived dataset; no deletion in this audit. |
| candidate_review_event | 6139 | 13415 | 7276 | Inspect non-identical records for the same user, variant and millisecond; do not automatically delete. |
| repeated_user_parent | 6437 | 14036 | 7599 | Retain unless a separate duplicate rule establishes identity. |
| normalized_text_repetition | 12813 | 73503 | 60690 | Retain; inspect common phrases or potential template/reuse patterns separately. |
| same_parent_timestamp | 6205 | 13559 | 7354 | Inspect ordering after exact deduplication; apply frozen boundary rules when constructing the cohort. |

### Statistical screening

| Metric | Valid n | Screened n | % valid | Proposed decision |
| --- | --- | --- | --- | --- |
| helpful_vote | 701528 | 1948 | 0.2777 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| reviews_per_parent | 112565 | 1036 | 0.9204 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| reviews_per_user | 631986 | N/A | N/A | Retain flagged values; inspect context and use train-only transformations if later justified. |
| text_characters | 701528 | 51908 | 7.399 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| text_whitespace_words | 701528 | 50239 | 7.161 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| title_characters | 701528 | 39924 | 5.691 | Retain flagged values; inspect context and use train-only transformations if later justified. |
## meta_All_Beauty

Value/nested/type union: **297** of 112,590 objects. Any content/type flag union: **456**. Missing-only cases, parse failures, duplicate status and statistical outliers have their own counts; they are not silently merged into these unions.

### Field coverage and type compatibility

| Field | Missing/empty n | Missing/empty % | Wrong type n | Initial missingness decision |
| --- | --- | --- | --- | --- |
| average_rating | 0 | 0 | 0 | Keep missing; exclude this field from calculations that require it. |
| bought_together | 112590 | 100 | 0 | Retain with an availability flag; empty collections are not parsing errors. |
| categories | 112590 | 100 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| description | 93428 | 82.98 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| details | 4512 | 4.007 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| features | 95213 | 84.57 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| images | 0 | 0 | 0 | Retain with an availability flag; empty collections are not parsing errors. |
| main_category | 0 | 0 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| parent_asin | 0 | 0 | 0 | Quarantine from analyses requiring this field; recover from source if possible. |
| price | 94886 | 84.28 | 0 | Keep missing and flag; do not replace with zero or a global mean. |
| rating_number | 0 | 0 | 0 | Keep missing; exclude this field from calculations that require it. |
| store | 11331 | 10.06 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| title | 12 | 0.01066 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| videos | 96708 | 85.89 | 0 | Retain with an availability flag; empty collections are not parsing errors. |

### Nonzero validation flags

| Rule | Field | Family | Affected n | Denominator | % | Proposed decision |
| --- | --- | --- | --- | --- | --- | --- |
| blank_detail_key | details | nested | 295 | 112590 | 0.262 | Inspect the attribute dictionary; do not merge unnamed attributes. |
| detail_name_collision | details | nested | 2 | 112590 | 0.001776 | Review keys before any mapping; preserve raw names/values. |
| placeholder_string | store | text | 154 | 112590 | 0.1368 | Review context before recoding as missing. |
| placeholder_string | title | text | 1 | 112590 | 0.000888 | Review context before recoding as missing. |
| replacement_character | title | text | 4 | 112590 | 0.003553 | Retain and inspect encoding; preserve the original text. |

### Duplicate and repeated-key checks

| Check | Groups | Rows involved | Rows beyond first | Proposed decision |
| --- | --- | --- | --- | --- |
| exact_parsed_record_duplicates | 0 | 0 | 0 | Propose keeping the first source-line copy in a later derived dataset; no deletion in this audit. |
| repeated_metadata_parent | 0 | 0 | 0 | Deduplicate identical copies later; quarantine conflicting parent versions from joins until reconciled. |

### Statistical screening

| Metric | Valid n | Screened n | % valid | Proposed decision |
| --- | --- | --- | --- | --- |
| price | 17704 | 1341 | 7.575 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| rating_number | 112590 | 17 | 0.0151 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| title_characters | 112590 | 68 | 0.0604 | Retain flagged values; inspect context and use train-only transformations if later justified. |
## Appliances

Value/nested/type union: **0** of 2,128,605 objects. Any content/type flag union: **2,479**. Missing-only cases, parse failures, duplicate status and statistical outliers have their own counts; they are not silently merged into these unions.

### Field coverage and type compatibility

| Field | Missing/empty n | Missing/empty % | Wrong type n | Initial missingness decision |
| --- | --- | --- | --- | --- |
| asin | 0 | 0 | 0 | Retain with a flag; exclude from identity checks requiring this key. |
| helpful_vote | 0 | 0 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| images | 2043656 | 96.01 | 0 | Retain with an availability flag; empty collections are not parsing errors. |
| parent_asin | 0 | 0 | 0 | Quarantine from analyses requiring this field; recover from source if possible. |
| rating | 0 | 0 | 0 | Quarantine from analyses requiring this field; recover from source if possible. |
| text | 2065 | 0.09701 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| timestamp | 0 | 0 | 0 | Quarantine from analyses requiring this field; recover from source if possible. |
| title | 0 | 0 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| user_id | 0 | 0 | 0 | Retain with a flag; exclude from identity checks requiring this key. |
| verified_purchase | 0 | 0 | 0 | Retain and report missingness; choose any later transformation on training data only. |

### Nonzero validation flags

| Rule | Field | Family | Affected n | Denominator | % | Proposed decision |
| --- | --- | --- | --- | --- | --- | --- |
| control_character | text | text | 17 | 2128605 | 0.000799 | Inspect before a logged text-normalization step. |
| control_character | title | text | 1 | 2128605 | 4.7e-05 | Inspect before a logged text-normalization step. |
| placeholder_string | text | text | 1587 | 2128605 | 0.07456 | Review context before recoding as missing. |
| placeholder_string | title | text | 1566 | 2128605 | 0.07357 | Review context before recoding as missing. |

### Duplicate and repeated-key checks

| Check | Groups | Rows involved | Rows beyond first | Proposed decision |
| --- | --- | --- | --- | --- |
| exact_parsed_record_duplicates | 19142 | 41798 | 22656 | Propose keeping the first source-line copy in a later derived dataset; no deletion in this audit. |
| candidate_review_event | 19143 | 41800 | 22657 | Inspect non-identical records for the same user, variant and millisecond; do not automatically delete. |
| repeated_user_parent | 21038 | 45653 | 24615 | Retain unless a separate duplicate rule establishes identity. |
| normalized_text_repetition | 47601 | 349137 | 301536 | Retain; inspect common phrases or potential template/reuse patterns separately. |
| same_parent_timestamp | 19187 | 41888 | 22701 | Inspect ordering after exact deduplication; apply frozen boundary rules when constructing the cohort. |

### Statistical screening

| Metric | Valid n | Screened n | % valid | Proposed decision |
| --- | --- | --- | --- | --- |
| helpful_vote | 2128605 | 8164 | 0.3835 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| reviews_per_parent | 94319 | 169 | 0.1792 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| reviews_per_user | 1755732 | N/A | N/A | Retain flagged values; inspect context and use train-only transformations if later justified. |
| text_characters | 2128605 | 177884 | 8.357 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| text_whitespace_words | 2128605 | 172197 | 8.09 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| title_characters | 2128605 | 100893 | 4.74 | Retain flagged values; inspect context and use train-only transformations if later justified. |
## meta_Appliances

Value/nested/type union: **5,154** of 94,327 objects. Any content/type flag union: **5,261**. Missing-only cases, parse failures, duplicate status and statistical outliers have their own counts; they are not silently merged into these unions.

### Field coverage and type compatibility

| Field | Missing/empty n | Missing/empty % | Wrong type n | Initial missingness decision |
| --- | --- | --- | --- | --- |
| author | 94326 | 100 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| average_rating | 0 | 0 | 0 | Keep missing; exclude this field from calculations that require it. |
| bought_together | 94327 | 100 | 0 | Retain with an availability flag; empty collections are not parsing errors. |
| categories | 3285 | 3.483 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| description | 32172 | 34.11 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| details | 2010 | 2.131 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| features | 16543 | 17.54 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| images | 1 | 0.00106 | 0 | Retain with an availability flag; empty collections are not parsing errors. |
| main_category | 4676 | 4.957 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| parent_asin | 0 | 0 | 0 | Quarantine from analyses requiring this field; recover from source if possible. |
| price | 47601 | 50.46 | 0 | Keep missing and flag; do not replace with zero or a global mean. |
| rating_number | 0 | 0 | 0 | Keep missing; exclude this field from calculations that require it. |
| store | 916 | 0.9711 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| subtitle | 94322 | 99.99 | 0 | Retain and report missingness; choose any later transformation on training data only. |
| title | 9 | 0.009541 | 0 | Retain the review/product and flag unavailable text; no fabricated text. |
| videos | 60624 | 64.27 | 0 | Retain with an availability flag; empty collections are not parsing errors. |

### Nonzero validation flags

| Rule | Field | Family | Affected n | Denominator | % | Proposed decision |
| --- | --- | --- | --- | --- | --- | --- |
| blank_detail_key | details | nested | 1772 | 94327 | 1.879 | Inspect the attribute dictionary; do not merge unnamed attributes. |
| blank_nested_text | features | nested | 1 | 94327 | 0.00106 | Retain the product; ignore blank text elements only in a documented derived view. |
| detail_name_collision | details | nested | 3392 | 94327 | 3.596 | Review keys before any mapping; preserve raw names/values. |
| no_usable_nested_text | features | nested | 1 | 94327 | 0.00106 | Flag this nonempty text collection as unavailable for text features. |
| placeholder_string | store | text | 109 | 94327 | 0.1156 | Review context before recoding as missing. |
| replacement_character | title | text | 3 | 94327 | 0.00318 | Retain and inspect encoding; preserve the original text. |

### Duplicate and repeated-key checks

| Check | Groups | Rows involved | Rows beyond first | Proposed decision |
| --- | --- | --- | --- | --- |
| exact_parsed_record_duplicates | 0 | 0 | 0 | Propose keeping the first source-line copy in a later derived dataset; no deletion in this audit. |
| repeated_metadata_parent | 0 | 0 | 0 | Deduplicate identical copies later; quarantine conflicting parent versions from joins until reconciled. |

### Statistical screening

| Metric | Valid n | Screened n | % valid | Proposed decision |
| --- | --- | --- | --- | --- |
| price | 46726 | 5473 | 11.71 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| rating_number | 94327 | 0 | 0 | Retain flagged values; inspect context and use train-only transformations if later justified. |
| title_characters | 94327 | 17 | 0.01802 | Retain flagged values; inspect context and use train-only transformations if later justified. |

## Joined multimodal availability

Each parsed review has one row in the compressed per-sample table, identified by source line. Counts retain raw review copies. Conflicting metadata versions are unavailable; identical metadata copies are collapsed only for this derived join. Image availability means a locally valid URL, never a verified image download. Missing below means unavailable under the field contract, including malformed content.

### All_Beauty

Review denominator: 701,528. Join statuses: {'matched': 701528}.

| Facet | Available n | Unavailable n | All reviews n | Available % |
| --- | --- | --- | --- | --- |
| review_text | 700808 | 720 | 701528 | 99.9 |
| review_rating | 701528 | 0 | 701528 | 100 |
| review_image_url | 59684 | 641844 | 701528 | 8.508 |
| timestamp | 701528 | 0 | 701528 | 100 |
| user_item_interaction | 701528 | 0 | 701528 | 100 |
| metadata | 701528 | 0 | 701528 | 100 |
| product_image_url | 701528 | 0 | 701528 | 100 |
| price | 185623 | 515905 | 701528 | 26.46 |
| product_text | 701463 | 65 | 701528 | 99.99 |
| any_image_url | 701528 | 0 | 701528 | 100 |
| product_features_text | 214970 | 486558 | 701528 | 30.64 |
| product_description_text | 172894 | 528634 | 701528 | 24.65 |

| Required combination | Available n | Available % |
| --- | --- | --- |
| text_rating_time | 700808 | 99.9 |
| text_metadata_image | 700808 | 99.9 |
| six_core_facets | 700808 | 99.9 |
| text_rating_time_metadata_price | 185378 | 26.42 |
### Appliances

Review denominator: 2,128,605. Join statuses: {'matched': 2128605}.

| Facet | Available n | Unavailable n | All reviews n | Available % |
| --- | --- | --- | --- | --- |
| review_text | 2126540 | 2065 | 2128605 | 99.9 |
| review_rating | 2128605 | 0 | 2128605 | 100 |
| review_image_url | 84949 | 2043656 | 2128605 | 3.991 |
| timestamp | 2128605 | 0 | 2128605 | 100 |
| user_item_interaction | 2128605 | 0 | 2128605 | 100 |
| metadata | 2128605 | 0 | 2128605 | 100 |
| product_image_url | 2128589 | 16 | 2128605 | 100 |
| price | 1600259 | 528346 | 2128605 | 75.18 |
| product_text | 2128601 | 4 | 2128605 | 100 |
| any_image_url | 2128589 | 16 | 2128605 | 100 |
| product_features_text | 1997578 | 131027 | 2128605 | 93.84 |
| product_description_text | 1110542 | 1018063 | 2128605 | 52.17 |

| Required combination | Available n | Available % |
| --- | --- | --- |
| text_rating_time | 2126540 | 99.9 |
| text_metadata_image | 2126524 | 99.9 |
| six_core_facets | 2126524 | 99.9 |
| text_rating_time_metadata_price | 1598555 | 75.1 |

## Conditional missingness and association

Full subgroup counts and rates are in conditional_missingness.csv. Review-unit rates weight popular products more heavily. Review-parent rates first compute each product’s missing fraction and then give products equal weight. Metadata-product rates count each unambiguous product once, including products without reviews. Unknown/conflicting joins stay in descriptive tables; missing category labels are excluded from within-category tests. Groups below 30 products are excluded from tests, not hidden from tables. Tests use 499 fixed-seed label permutations by default, eta squared for effect size and Benjamini–Hochberg q-values across computed tests. Product independence/exchangeability remains an assumption; overlapping users and product families can violate it. These are exploratory associations, not proofs of a missingness mechanism.

| Grouping | Unavailable facet | Products tested | Eta squared | Permutation p | BH q | Status |
| --- | --- | --- | --- | --- | --- | --- |
| download_category | review_text | 206884 | 1.622e-05 | 0.076 | 0.1086 | computed |
| download_category | review_image_url | 206884 | 0.02015 | 0.002 | 0.003333 | computed |
| download_category | product_image_url | 206917 | 5.769e-06 | 0.484 | 0.484 | computed |
| download_category | price | 206917 | 0.1323 | 0.002 | 0.003333 | computed |
| main_category_within_All_Beauty | review_text | 112565 | 5.533e-06 | 0.456 | 0.484 | computed |
| main_category_within_All_Beauty | review_image_url | 112565 | 9.72e-05 | 0.002 | 0.003333 | computed |
| main_category_within_All_Beauty | product_image_url | 112590 | 0 | N/A | N/A | constant_missingness |
| main_category_within_All_Beauty | price | 112590 | 0.0006532 | 0.002 | 0.003333 | computed |
| main_category_within_Appliances | review_text | 89621 | 0.0001565 | 0.468 | 0.484 | computed |
| main_category_within_Appliances | review_image_url | 89621 | 0.006798 | 0.002 | 0.003333 | computed |
| main_category_within_Appliances | product_image_url | 89629 | 0 | N/A | N/A | constant_missingness |
| main_category_within_Appliances | price | 89629 | 0.007224 | 0.002 | 0.003333 | computed |

## Interpretation and evidence

Full exact pattern combinations, every zero/nonzero rule, denominators, example source lines, configuration, file hashes and rationales are preserved in quality_audit.json and the CSV tables. Issue totals overlap. A flag is a review request, not automatic row deletion. Missing URLs/prices do not invalidate the review. Statistical outliers may be genuine. Review ratings must be integral values 1–5 under the project contract (5.0 is accepted); product average_rating may be fractional. Identifiers must be exact nonblank strings without surrounding whitespace or lone surrogates in BOTH modules. Association tests cannot demonstrate MCAR, MAR or MNAR. Metadata fields are crawl-time observations, not automatically available at the historical prediction cutoff.

Output paths:

- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/terminal_report.txt`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/quality_audit.json`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/field_quality.csv`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/quality_issues.csv`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/duplicate_summary.csv`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/numeric_summaries.csv`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/decision_register.csv`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/cross_file_checks.json`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/QUALITY_AUDIT_REPORT_EN.md`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/quality_audit_executed.py`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/modality_availability.json`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/conditional_missingness.csv`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/missingness_associations.csv`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/audit_shared.py`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/quality_multimodal.py`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/All_Beauty__sample_modality_availability.csv.gz`
- `/Users/parsaanvari/Projects/data-analysis/.venv/reports/phase1/quality/Appliances__sample_modality_availability.csv.gz`
