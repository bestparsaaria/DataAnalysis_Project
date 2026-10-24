# PROJECT CARD

**Working title:** Early Review Text for Predicting Future Low-Star Review Share  
**Track:** B — Amazon Reviews’23  
**Version:** 1.1  
**Original design recorded:** 2026-10-19  
**Last updated:** 2026-10-24  
**Current stage:** Phase 1; provenance and structural auditing completed for the two assigned categories and their metadata.

This card records the study design and current implementation status. Planned methods are not completed experiments. No predictive improvement from text has been demonstrated. Changes to the question, target, eligibility, split, or primary evaluation must retain a dated explanation and be recorded before model development.

## 1. Selected track and data subset

All five project phases use **Track B only** and **Amazon Reviews’23 only**. No dataset from Tracks A, C, or D is included.

| Official category | Team study scope | Responsibility covered by the completed audit |
|---|---|---|
| `All_Beauty` | Included | Assigned to this contribution; reviews and metadata audited. |
| `Appliances` | Included | Assigned to this contribution; reviews and metadata audited. |
| `Electronics` | Included | Wider team study; no completed audit is claimed here. |
| `Beauty_and_Personal_Care` | Included | Wider team study; no completed audit is claimed here. |

For each category, inputs are its review file and corresponding metadata file. The completed contribution covers `All_Beauty.jsonl`, `meta_All_Beauty.jsonl`, `Appliances.jsonl`, and `meta_Appliances.jsonl`.

**Source:** [Official Amazon Reviews’23 website](https://amazon-reviews-2023.github.io/), published by McAuley Lab. The [dataset paper, Appendix B](https://arxiv.org/html/2403.03952v2#A2), describes collecting review pages associated with user IDs sampled from public Amazon pages. This does not establish random sampling of all buyers or products.

The four categories were selected purposefully to compare the value of text across product domains while limiting scope. They are not a representative random sample of the entire Amazon catalogue. File membership defines the initial scope; metadata `main_category` is a separate attribute and does not silently determine exclusions. `All_Beauty` is not assumed to contain `Beauty_and_Personal_Care`.

Raw files remain unchanged and outside Git. Audit outputs record local sizes and SHA-256 fingerprints. Actual download URLs, dates, and revisions remain unknown where independent evidence is unavailable; a local fingerprint does not independently prove equality with a published release.

If computation requires sampling, select products using a recorded seed or deterministic hash without using the future target. Retrieve their complete available review sequences before identifying the first five reviews. Random sampling of review rows cannot construct a valid first-five sequence. Record category-specific caps and selection probabilities before modeling.

## 2. Temporary project title

**Does Early Review Text Improve Prediction of Future Low-Star Review Share? A Temporal, Multimodal Study across Four Amazon Reviews’23 Categories**

“Multimodal” means meaningful use of text together with structured ratings and temporal information, as allowed by Track B. Image modeling is not required for the main question.

## 3. Real-world problem and decision supported

A team with limited product-review capacity needs to decide which products deserve attention after only a small review history is available. Five ratings summarize satisfaction, but the accompanying words may describe problems that the numbers alone do not reveal.

Test whether early text improves prediction of the share of one- and two-star ratings in the next ten observed reviews. The intended output is a product-level risk estimate and a ranked list for **human review**, within each category.

The primary decision scenario inspects the highest-scoring **10%** of eligible products per category; 5% and 20% are sensitivity scenarios. These are analytical scenarios, not measured business capacities.

The outcome does not establish defects, fraud, returns, medical harm, or causes of dissatisfaction. Without intervention and cost data, the project cannot demonstrate increased sales or financial savings.

## 4. Observation, analysis, and prediction units

| Unit | Definition |
|---|---|
| Raw review observation | One collected review record, not one guaranteed distinct purchase. |
| Raw metadata observation | One collected product metadata record; key uniqueness is audited. |
| Product grouping | `parent_asin`; `asin` can identify a product variant. |
| Predictive analysis unit | One product at its fifth valid, nonduplicate observed review. |
| Prediction/error unit | The same product, with one outcome calculated from its next ten reviews. |

For product `p`, order valid, nonduplicate reviews by ascending `timestamp`. Reviews 1–5 form the input window. Ratings in reviews 6–15 form the outcome. Let `t5` be the prediction time and `t15` the time the outcome becomes fully observed. Each product contributes one primary sample.

A review needs a valid product identifier, interpretable timestamp, and integer-valued rating in `{1,2,3,4,5}` to enter the main sequence. Blank review text does not remove a review. Record every exclusion, its reason, and its effect on counts. “First” means first valid review observed under these documented rules, not necessarily the first ever published.

Count exact duplicate records and identical copies of the same review across files once under a documented rule. Repeated user/product pairs or common phrases alone do not establish duplicate reviews. Flag conflicting review versions and resolve them using a recorded rule without choosing a preferred rating or outcome.

If `t5 = t6`, the input/future boundary is ambiguous, so exclude the product from the primary cohort. If review 16 exists and `t15 = t16`, the end of the ten-review outcome is ambiguous; exclude the product and report the effect. Ties inside a window use a deterministic technical order, not a claim of true precedence.

Reconcile shared products globally before splitting. Assign each product one primary analytical category using the first file name in fixed lexicographical order, while retaining all original memberships. This is an accounting rule, not a claim about the product’s true category. Excluding multi-category products is a sensitivity analysis. Four-category overlap is not yet established.

## 5. Scope and target population

**Intended operational population:** products in the four selected files when they reach five valid observed reviews.

**Evaluable population:** products for which the next ten valid reviews are also observed within allowed follow-up, with unambiguous input/outcome boundaries.

These populations differ. Without an observed fifteenth review, a product has an unknown outcome, not a zero outcome. Requiring fifteen reviews may favor popular products, faster review accumulation, or longer observable history. Report the eligibility funnel, category retention, past characteristics of included/excluded products, and the distribution of `t15 - t5`.

The forecast horizon is **the next ten reviews**, not a fixed number of days. The first observed review is not a launch date. Findings apply to the evaluable population, categories, and periods studied; they do not automatically extend to all buyers, low-review products, or all of Amazon.

## 6. Main research question and hypotheses

> Across All_Beauty, Appliances, Electronics, and Beauty_and_Personal_Care, does adding the text of a product’s first five valid observed reviews to the ratings and timing of those same reviews improve out-of-sample prediction of the proportion of one- and two-star ratings among its next ten observed reviews? Does the combined approach also outperform a simple category-adjusted rating baseline, and how do prediction gains and human-review prioritization benefits differ across categories?

In plain language: after five reviews, compare a prediction based on stars and dates with a prediction that also uses the words. Both predict exactly the same later outcome.

The primary comparison is **S versus ST**: S uses structured rating/time information; ST adds text. Keep eligible products, splits, model family, and tuning budgets comparable. Comparing ST only against a simple rule would not isolate text’s contribution from increased model flexibility.

For product `p`, define paired squared-loss improvement:

```text
d_p = (Y_p - prediction_S,p)^2 - (Y_p - prediction_ST,p)^2
Delta = (1/4) * sum_c E[d_p | category c, evaluable population]
H0: Delta <= 0
H1: Delta > 0
```

Positive `Delta` means lower expected squared error after adding text. H0/H1 are hypotheses about generalization, not names for fitted lines. Report effect sizes and uncertainty; failure to reject H0 does not prove universal uselessness of text. Category tests are secondary; apply Holm adjustment when making multiple significance claims. Compare category effects directly rather than treating significance in one category and non-significance in another as proof of a difference.

### Three initial questions and selection rationale

| Candidate | Feasibility and selection rationale |
|---|---|
| **Selected:** Does early text improve prediction of future low-star review share? | Existing future ratings provide the target; windows are explicit; the output supports prioritization. |
| Do the mean/trend of five early ratings predict the mean rating of the next ten reviews? | Feasible, but an average can conceal a substantial share of strongly negative experiences. |
| How are review length, rating, and age associated with recorded helpful votes? | Descriptive work is feasible; absent exposure and vote timestamps limit claims about intrinsic helpfulness or fixed-horizon vote prediction. |

These alternatives fulfill Phase 1 question design; they do not create three separate project commitments.

## 7. Target variable and permitted predictors

```text
z_pj = 1 if rating_pj is 1 or 2, otherwise 0
Y_p = (z_p6 + ... + z_p15) / 10
```

The observed target takes values `0, 0.1, ..., 1`. Predict its expected value in `[0,1]` without rounding predictions to tenths. Three stars is not a target event. The main task is regression of a review proportion, not classification of a product as “bad.”

**Structured block S:** the first five ratings, mean/dispersion, rating-level counts, early one-/two-star share, first-to-last rating change, and historical timing features available at `t5`. Category information is available identically to S and ST.

**Text block T:** titles and bodies of those five reviews, initially represented with TF-IDF. Alternative representations require justification and validation. Text length and missing-text flags belong to this block and are removed in a full text ablation. T alone excludes numeric ratings/timestamps and explicit category identifiers. Star mentions within an available review remain part of its text; examine their role in sensitivity analysis.

### Role of the proposed fitted line

Fit a least-squares line to the five ratings against elapsed days:

```text
x_j = elapsed days from review 1 to review j
rating_j = a + b*x_j + residual_j
initial_fit_RMSE = sqrt(mean(residual_j^2))
```

Slope and residual RMSE describe the early trend and enter both S and ST as candidate features. If all times coincide, record slope zero and a no-time-variation flag. Fitting against review positions 1–5 is a sensitivity alternative.

This fitting RMSE is not the future-prediction metric. A line fitting five ratings more closely does not establish better prediction of reviews 6–15. Future review timestamps must not be used for historical extrapolation.

### Optional auxiliary text score

A text model may learn `q_j = P(rating_j <= 2 | text_j)` from training reviews, providing summaries or disagreement with observed stars. This is a rating-prediction score, not a validated sentiment label or corrected rating. For training a later model, generate q using temporal, product-disjoint out-of-fold prediction. Initial blocks without past training data retain missing-score flags; all comparisons retain the same products.

This branch is optional. Real ratings in reviews 6–15 remain the target for every method. Neither manual sentiment annotation nor an arbitrary mix of ratings and AI scores replaces ground truth.

## 8. Initial baselines and model comparisons

Let `k_p` count one-/two-star ratings among the first five reviews. Let `pi_c` be mean `Y` among eligible training products in category `c`, using only outcomes completed before the prediction boundary.

| Method | Definition | Purpose |
|---|---|---|
| B0 | `prediction = pi_c` | Category-only constant reference. |
| **B1** | `prediction = (k_p + lambda*pi_c)/(5 + lambda)` | Simple primary baseline, smoothing the early share toward the category rate. |
| S | Learned rating/time/category model | Stronger structured comparator. |
| T | Early-text-only model | Measures text’s predictive ability alone. |
| ST | Combined structured/text model | Multimodal method under study. |

For illustration only: with `k=1`, `pi_c=0.20`, and `lambda=5`, B1 predicts `(1 + 5*0.20)/10 = 0.20`. This is hypothetical, not a measured result.

Select a shared `lambda` from `{0,1,2,5,10,20}` with temporal validation only. Recompute `pi_c` within each fold. If a category lacks eligible training data, document it and use the pooled training rate for operational predictions; do not claim a confirmatory category comparison without adequate support.

Planned learned families are Ridge regression and a boosted-tree model, with comparable S/T/ST variants where feasible. Select the primary family using validation performance of S before final testing, then tune ST within that family and comparable budget. A best-S versus best-ST comparison across families is a separate practical result.

Clip regression predictions to `[0,1]` consistently. Models learn from many past products; a separate ML model trained on only five reviews per product is not the design.

## 9. Proposed evaluation and uncertainty

Use an equally weighted four-category primary metric:

```text
MSE_c = mean_p_in_c((Y_p - prediction_p)^2)
RMSE_balanced = sqrt((MSE_All_Beauty + MSE_Appliances
                     + MSE_Electronics + MSE_Beauty_and_Personal_Care)/4)
```

This is not the mean of four RMSEs. Products receive equal weight within category; categories receive equal weight in the primary result. Also report per-category RMSE, pooled product-level RMSE, MAE, R-squared with zero-variance exceptions, and predicted-versus-observed proportion summaries.

At the 10% inspection budget, report per category:

- Mean observed `Y` among selected products.
- Lift: selected mean `Y` divided by the evaluation category’s overall mean `Y`.
- Fraction of all low-star outcome reviews captured, using `10*Y` as each product’s event count.

Compare lists at equal capacity; include 5%/20% sensitivity. Keep zero-denominator ratios undefined. Resolve ranking ties with a fixed hash.

Estimate paired differences with at least 2,000 bootstrap repetitions and 95% confidence intervals, using the same resampled products across models and retaining equal category weights. Examine temporal dependence by block resampling the month of `t5`. Disclose dependence from shared users or related products; independence is not guaranteed. Intervals concern the evaluated setting, not every product population.

Training-set improvement alone is insufficient. Statistical improvement without prioritization benefit or with excessive cost is not automatically practical success. Do not invent financial thresholds without real cost data.

## 10. Initial training, validation, and test split

Split by global product identity and absolute time, using common calendar boundaries across categories. For `A < B < C`:

| Partition | Eligibility |
|---|---|
| Development training | `t15 < A` |
| Validation | `A <= t5 < B` and `t15 < B` |
| Final test | `B <= t5 < C` and `t15 <= C` |

A/B begin validation/test; C ends reliable follow-up. Exact dates are **pending** four-category coverage and eligible counts. Select boundaries using calendar coverage, support, and label maturity, not desirable target values or performance. Freeze dates and counts before training.

An outcome is mature only after all ten future reviews are observed. Sorting by `t5` alone is insufficient: a label completed after a training boundary was not available then. Use expanding temporal development folds with the same maturity rule. Generic row-position splitting does not enforce these controls.

After settings are fixed, refit final-test models on all eligible products with `t15 < B`, including matured validation products. This planned refit does not use test labels. Refit preprocessing, category rates, and auxiliary models only from permitted training data.

No `parent_asin` enters multiple partitions. User IDs are not primary predictors. Audit shared reviewers and near-duplicate text; assess sensitivity on evaluation products without reviewers shared with training, retaining their original first-five definition. This restricted population does not replace the main evaluation.

Do not use the final test for feature/model/cleaning selection. Phase 3 benchmarking and Phase 4 interpretation/refinement use development/validation; Phase 5 evaluates the frozen final comparison. Unplanned analyses after opening the test are exploratory.

## 11. Main leakage risks and controls

| Risk | Control |
|---|---|
| Information after review 5 | Exclude future text/timing; ratings 6–15 construct the target only. |
| Metadata `average_rating`/`rating_number` | Exclude from the historical predictor; they may summarize future reviews. |
| Current product price/title/description/images | Descriptive audit only unless historical availability at `t5` is established. |
| Accumulated `helpful_vote` | Exclude; its value at `t5` is unknown. |
| Age measured to crawl time | Use historical intervals such as `t5 - t_j` only. |
| Total review count, `t15`, follow-up | Outcome/eligibility/bias assessment only; not predictors. |
| Globally fitted TF-IDF/SVD/imputation/scaling/selection | Fit on training data within each fold. |
| Shared products/reviews across files | Reconcile globally before splitting. |
| Auxiliary scores trained on the same sample | Temporal, product-disjoint out-of-fold training features. |
| Encoder exposed to Amazon Reviews’23 | Check training provenance; unresolved contamination excludes confirmatory historical claims. |
| Review edited after its timestamp | Disclose that original text versions are not guaranteed; historical availability is an assumption. |

Category membership and parent mappings also reflect the released snapshot, not a proven historical catalogue. Disclose this consistently for S/ST. Complete local metadata matching does not establish availability at prediction time.

## 12. Proposed unsupervised analysis and pattern discovery

Represent each product’s five early reviews with TF-IDF, reduce dimensions with TruncatedSVD, and examine KMeans clusters. Evaluate candidate cluster counts using silhouette, stability across seeds/subsamples, and representative examples. Record candidate counts and computation limits before fitting.

Do not choose clusters using final-test outcomes. Describe category, early rating, and text-length patterns; examine associations with `Y` in development only after fixing clusters. A two-dimensional plot alone does not prove natural groups. Cluster names are interpretations, not verified fraud, defect, or sentiment labels.

## 13. Track B extension and multimodal plan

Planned extensions include:

1. S/T/ST comparisons on identical samples and splits.
2. Separate ablations removing all text, timing, and trend features.
3. Text-focused error analysis, including sparse text and apparent word/star disagreement.
4. Comparisons across categories and successive temporal periods.

Audit availability of text, ratings, metadata, images, timing, and user–item interactions with explicit denominators. Distinguish review images from product images and URL presence from successful retrieval. An absent image does not remove an otherwise eligible review. Structural counters support this work but do not complete modality-missingness comparisons.

Interpretive example reading does not create an annotated sentiment training set. Use existing ratings as labels. Auxiliary scores/alternative representations remain optional and cannot redefine the target. Product images are audited, but using current images for historical prediction is not a requirement.

LLMs are not required. If introduced later, record exact version, complete prompts, parameters, cost, caching, sample validation, and a non-LLM comparator. Generated values cannot become unvalidated ground truth.

## 14. Ethics, privacy, and potential bias

The study is **observational**. Researchers did not randomly assign products, prices, or review exposure. Buying, reviewing, rating, and voting arose through user activity. Predictive associations do not establish causal effects of attributes or review language.

Limitations include self-selection into reviewing, potentially incomplete histories, unequal helpful-vote opportunities, and crawl-time metadata snapshots. `verified_purchase=False` does not prove a fake review; restricting to True does not remove self-selection. The flag can support descriptive/sensitivity analysis but is not part of the main feature core.

The fifteen-review condition and label maturity add selection. Assess language, short/blank text, review volume, and category differences with sample counts. Non-ASCII text alone does not establish language. Avoid confident claims for poorly supported subgroups.

Use reviewer IDs for dependence/overlap audits without attempting re-identification. Remove personal information from examples. Keep raw files out of Git. Check and record applicable redistribution terms before publishing excerpts or derivatives. Outputs support human review, not automatic delisting or allegations against reviewers/sellers.

Record assistance in `AI_USAGE.md`. Researchers remain responsible for understanding, rerunning, verifying, and defending the analysis.

## Current evidence and completion status

The completed audit has reference time **2026-10-21T08:31:29.714135+00:00** and status `complete` for these local files:

| File | Raw JSON object records | Observed field-name union |
|---|---:|---:|
| `All_Beauty.jsonl` | 701,528 | 10 |
| `meta_All_Beauty.jsonl` | 112,590 | 14 |
| `Appliances.jsonl` | 2,128,605 | 10 |
| `meta_Appliances.jsonl` | 94,327 | 16 |

Appliances metadata has 94,322 records with 14 fields and five with 16; the union is not the width of every record. These are raw counts, not deduplicated counts or eligible prediction samples.

Every assigned review row matches a unique, complete metadata `parent_asin`. There are 25 metadata-only All_Beauty parents and eight metadata-only Appliances parents. The two review files share no `parent_asin` or `asin` values but share 58,120 distinct reviewer IDs. This does not establish results for the other team categories.

Measured review ranges:

- All_Beauty: `2000-11-01T04:24:18+00:00` to `2023-09-09T00:39:36.666000+00:00`.
- Appliances: `2000-10-23T14:37:23+00:00` to `2023-09-12T16:29:17.016000+00:00`.

These are review-event ranges, not purchase/crawl dates. Metadata has no common documented timestamp/version history for an equivalent historical range.

| Work item | Status of this contribution |
|---|---|
| Provenance/structural audit of the assigned review/meta pairs | Completed and documented. |
| Full quality audit, duplicate decisions, impossible values, outliers | Pending; presence/type counters do not complete this requirement. |
| Full text/modality audit, missingness comparisons, univariate/multivariate EDA | Pending. |
| Four-category reconciliation, cohort, exact split dates/counts | Pending. |
| Models, clustering, ablations, interpretation, final evaluation | Planned; no performance claimed. |

Evidence artifacts are `source_structure.json`, `provenance_manifest.json`, the terminal report, and `SOURCE_AND_STRUCTURE_REPORT_EN.md` with its appendix. Preserve the executed source associated with the output hash. Renaming does not change source bytes; editing does and needs a new version association. Reformatting a report is not a new audit.

Before modeling, freeze quality/duplicate rules, four-category overlap handling, cohort counts, split dates, features, model grids/resource budgets, cluster candidates, and seeds. This card defines the question and evaluation principles without pretending that these pending details are known.

## References and change note

- Course project document and supplied 14-item card requirements.
- [Official data and field definitions](https://amazon-reviews-2023.github.io/).
- [Collection methodology, Appendix B](https://arxiv.org/html/2403.03952v2#A2).
- Measured local audit artifacts listed above.

This question, target, and four-category scope supersede earlier All_Beauty-only exploratory proposals. Version 1.1 updates execution status and documentation language while retaining the established scientific design. It reports no new modeling result.
