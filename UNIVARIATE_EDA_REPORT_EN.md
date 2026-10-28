# Univariate Exploratory Data Analysis: Methods, Results and Interpretation

**Run status:** `complete`. **Started (UTC):** 2026-10-27T15:51:32.865535+00:00. **Module:** `univariate_eda.py` v2.0.0.

## Key measured findings

These are marginal descriptions of separate files, not controlled comparisons or causal effects.

- **All_Beauty reviews:** 59.97% are five-star and 20.69% are one-/two-star. The 4–5-star share is 71.29%; a majority of valid ratings. Absent classes: []. All-five-class ratio: 9.777.
- **All_Beauty helpful votes:** 73.28% are zero, median 0.000, mean 0.924, maximum 646.000. Empirical skewness is 39.125 (positive); mean 0.924 versus median 0.000. The largest 1% of observations account for 36.51% of the total value. These describe the observed shape without asserting a fitted tail distribution.
- **All_Beauty review length:** median 102.000 characters versus mean 173.032; P99 1,146.000, maximum 14,989.000. Use the linear and full-range panels together to distinguish the bulk from unusually long reviews.
- **All_Beauty product coverage:** median 2.000 observed reviews per parent, mean 6.232; the largest 1% of parent groups hold 27.871% of raw review rows. The later requirement of 15 usable reviews will select a subset; this module does not equate raw counts with final cohort eligibility.
- **Appliances reviews:** 69.82% are five-star and 15.51% are one-/two-star. The 4–5-star share is 79.60%; a majority of valid ratings. Absent classes: []. All-five-class ratio: 18.656.
- **Appliances helpful votes:** 80.80% are zero, median 0.000, mean 0.929, maximum 5,704.000. Empirical skewness is 162.089 (positive); mean 0.929 versus median 0.000. The largest 1% of observations account for 52.28% of the total value. These describe the observed shape without asserting a fitted tail distribution.
- **Appliances review length:** median 88.000 characters versus mean 169.513; P99 1,258.000, maximum 30,004.000. Use the linear and full-range panels together to distinguish the bulk from unusually long reviews.
- **Appliances product coverage:** median 3.000 observed reviews per parent, mean 22.568; the largest 1% of parent groups hold 42.481% of raw review rows. The later requirement of 15 usable reviews will select a subset; this module does not equate raw counts with final cohort eligibility.
- **meta_All_Beauty prices:** 17,704 valid prices (15.72% of metadata records), median USD 16.99, mean USD 27.26, maximum USD 2548.98. Empirical skewness is 21.965 (positive); mean 27.256 versus median 16.990. The largest 1% of observations account for 12.56% of the total value. These describe the observed shape without asserting a fitted tail distribution.
- **meta_All_Beauty category labels:** `All Beauty` is the most frequent label (99.60% of nonempty labels). Download-category membership must not be silently replaced by this field.
- **meta_Appliances prices:** 46,726 valid prices (49.54% of metadata records), median USD 26.99, mean USD 86.48, maximum USD 21095.62. Empirical skewness is 16.283 (positive); mean 86.480 versus median 26.990. The largest 1% of observations account for 30.76% of the total value. These describe the observed shape without asserting a fitted tail distribution.
- **meta_Appliances category labels:** `Tools & Home Improvement` is the most frequent label (47.62% of nonempty labels). Download-category membership must not be silently replaced by this field.

Read the method definitions before using these values as modelling inputs. All values describe raw collected records, including duplicate copies.

## 1. Purpose and scope

This report describes one-variable distributions for All_Beauty and Appliances review files and their metadata. It answers how values are distributed, where their centre lies, how dispersed they are, and whether values or classes are concentrated. It includes a limited text-by-rating comparison required by Track B, plus exact-duplicate sensitivity; it is not a cleaning pipeline, causal analysis or predictive evaluation. The original files remain unchanged. Exact duplicate copies are retained, so the estimand is the distribution of raw collected records.

## 2. Reproducible methods and statistical reasoning

### 2.1 Input and population rules

The [official dataset documentation](https://amazon-reviews-2023.github.io/) identifies reviews and item metadata as distinct sources and defines the fields. Collection is observational. Price is a crawl-time USD value; product averages and rating counts are snapshots. The program reads local JSONL (or JSONL.gz) sequentially, rejects malformed JSON/duplicate keys/nonobjects with counts, and profiles every parsed object. It computes file SHA-256 and checks size/mtime stability. A debug line cap is labelled partial and cannot be presented as a full-file study.

The shared audit_shared.py contract rejects blank, padded or surrogate-containing identifiers without modifying them. Each metric uses its own valid inputs, not a table-wide complete-case filter. Missing, null, blank and empty containers are recorded separately. Numeric strings and booleans are not silently converted. Review ratings must be integral 1–5; product average ratings may be fractional 1–5; helpful votes and rating counts require nonnegative JSON integers; prices require finite nonnegative numbers. A valid numeric zero is retained. Empty lists have a valid entry count of zero, but a null list does not. Text lengths include empty strings and whitespace-only text. Identifier activity uses exact nonblank strings without surrounding whitespace; excluded identifier rows are reported. No user IDs or review text are exported in frequency tables.

### 2.2 Variables and derived measurements

Reviews: star rating, helpful votes, verified purchase, title/body character counts, whitespace token count, image-entry count, timestamp frequency, and raw reviews per product/reviewer. Metadata: average rating, rating number, price, title length, main category and store; entry counts for features, descriptions, images, videos, categories and bundles; total feature/description characters; and detail-key count. Feature/description text length sums strings without inserting separators and excludes arrays containing non-string items. Category entry count is not asserted to be hierarchy depth. Empty nested structures mean absent content, not broken records. All observed fields receive a content-state chart/table, including sparse extra fields. IDs themselves have no numeric centre; Mixed-unit dimensions, image pixels and sentiment remain outside scope. Language, scripts, unusual characters and text length by rating are audited explicitly below.

### 2.3 Centre, spread, shape and imbalance

All numeric summaries use full frequency tables, not samples. Quantiles use linear interpolation at (n−1)q, matching an expanded sorted sample. Centre is described by mean, median and modes; spread by minimum/maximum, population SD and variance (divisor n), quartiles/IQR, unscaled median absolute deviation, P5/P95/P99/P99.9 and coefficient of variation where the mean is positive. Modes are exact observed values, not histogram peaks; only the first ten tied modes are printed, with the full tie count. Population skewness is m3/m2^(3/2); excess kurtosis is m4/m2²−3. Bowley skewness is (Q3+Q1−2 median)/IQR. These are descriptive empirical statistics, not fitted distribution parameters or tests of normality. No normal, lognormal, Poisson or power-law model is assumed or fitted. Zero variance makes moment shape undefined; zero IQR makes Bowley undefined. The mean can be pulled by extreme values, so median/IQR are always provided. Ordinal stars are primarily interpreted through their class counts.

Numeric imbalance includes the mass at zero and modal share. Review class imbalance reports all five stars, low (1–2), neutral (3) and high (4–5) groups, the largest-to-smallest observed class ratio, and Shannon entropy divided by log(5). Categorical summaries include exact label counts, modal share, top-ten share and entropy/log(number of observed levels); entropy is zero for a single level. Nominal category means/SDs are not meaningful. Product/user activity concentration also uses Gini and the fraction of review rows in the largest ceil(1% of groups). No significance tests or confidence intervals are added to this census of the supplied files; a larger population would require sampling and dependence assumptions.

### 2.4 Why these figures

Ratings use exact frequency bars and an empirical cumulative distribution (ECDF), preserving their discrete/rounded nature. Other numeric panels pair a raw linear histogram through P99 with a full-range log1p histogram, a full ECDF on a symlog axis and a box summary. Small integer-valued counts (display limit at most 30) use integer-centred bins. Otherwise the central histogram uses a Freedman–Diaconis width, bounded to 12–60 bins; zero IQR falls back to a Sturges-style count. Its y denominator remains ALL valid observations, and the omitted upper-tail count is printed. The log histogram uses 40 equal-width bins in ln(1+x), retaining zeros; its bars are percentages per transformed bin, not raw-unit density. The ECDF includes every distinct observed value and reaches 100%; it is not a fitted curve. The box covers Q1–Q3 with median and P5–P95 whiskers; omitted extremes remain in other panels and the min/max annotation. No plot limit deletes data. Displayed category charts show the top 12 levels plus Other; full counts are saved. Empty metrics receive an explicit no-data panel instead of fabricated statistics.

### 2.5 Time and interpretation limits

Timestamps are integer Unix milliseconds converted to UTC; impossible/future values relative to the recorded reference time are excluded. The median date, date quartiles, span and IQR in days are reported; epoch-dependent means and skewness are not interpreted. Annual/monthly counts describe timing of observed reviews, not sales, exposure-normalized review rates or causal trends. Missing months inside the observed interval are plotted as zero. Boundary months/years are partial, so a final-year drop cannot establish declining demand. Metadata has no common historical timestamp. Empty media arrays do not imply failed downloads; category labels need not equal the downloaded file category. Text encoding and probable language are audited below. Image network retrieval is not tested; local URL availability is linked from the matching quality audit. If learned imputations, scaling, vocabulary, or outlier thresholds enter a predictor later, fit them on training data only; this whole-file descriptive EDA is not a license to tune using a final test.

## 3. Execution evidence

| Dataset | Parsed objects | Physical lines | Parse failures | Full, unchanged scan |
|---|---:|---:|---:|---|
| All_Beauty | 701,528 | 701,528 | 0 | True |
| Appliances | 2,128,605 | 2,128,605 | 0 | True |
| meta_All_Beauty | 112,590 | 112,590 | 0 | True |
| meta_Appliances | 94,327 | 94,327 | 0 | True |

The recorded input hashes and comparison with the earlier quality audit are saved in `univariate_eda.json`. `complete` means the requested files were fully scanned unchanged; it does not mean they are error-free. Missing/unreadable files or parsing warnings are explicitly reported below.

Errors: `[]`

## 4. Dataset-by-dataset results

### All_Beauty

Unit: one reviews record unless a derived group metric states otherwise. This file contributes **701,528 raw records**. Full numeric frequencies are in `All_Beauty__numeric_frequencies.csv.gz`.

#### Field coverage and denominators

| Field | Absent | Null | Blank string | Empty array | Empty object | Nonempty |
|---|---:|---:|---:|---:|---:|---:|
| asin | 0 | 0 | 0 | 0 | 0 | 701,528 |
| helpful_vote | 0 | 0 | 0 | 0 | 0 | 701,528 |
| images | 0 | 0 | 0 | 641,844 | 0 | 59,684 |
| parent_asin | 0 | 0 | 0 | 0 | 0 | 701,528 |
| rating | 0 | 0 | 0 | 0 | 0 | 701,528 |
| text | 0 | 0 | 720 | 0 | 0 | 700,808 |
| timestamp | 0 | 0 | 0 | 0 | 0 | 701,528 |
| title | 0 | 0 | 0 | 0 | 0 | 701,528 |
| user_id | 0 | 0 | 0 | 0 | 0 | 701,528 |
| verified_purchase | 0 | 0 | 0 | 0 | 0 | 701,528 |

![Field content states](figures/All_Beauty__field_states.png)

The stacked bars separate absent content from nonempty content. Nonempty is not a quality certification. Each row sums to the file's parsed-object count, so differences in denominators can be traced without dropping entire records.

#### rating: Review star rating

The valid population contains 701,528 review observations; 0 are excluded from this metric's denominator. The median is 5.000 stars and the mean is 3.960. The middle half lies between 3.000 and 5.000 (IQR 2.000); population SD is 1.494 and unscaled median absolute deviation is 0.000. The range is 1.000 to 5.000; P95 is 5.000 and P99 is 5.000. The modal value(s), up to ten, are 5; there are 1 tied modes, each representing 59.97% of valid observations. Moment skewness is -1.089, negative (a longer/heavier lower tail by the third-moment measure). Excess kurtosis is -0.424; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -1.000. Stars are ordered categories. Median and class percentages are primary; mean/SD are conventional summaries that treat adjacent star steps as equally spaced. This is a raw review distribution, not the future ten-review product target.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 701,528 | 3.960 | 5.000 | 1.494 | 3.000 | 5.000 | 2.000 | 5.000 | 5.000 | -1.089 | -0.424 |

![Review star rating](figures/All_Beauty__rating.png)

#### helpful_vote: Helpful votes

The valid population contains 701,528 review observations; 0 are excluded from this metric's denominator. The median is 0.000 votes and the mean is 0.924. The middle half lies between 0.000 and 1.000 (IQR 1.000); population SD is 5.471 and unscaled median absolute deviation is 0.000. The range is 0.000 to 646.000; P95 is 4.000 and P99 is 13.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 73.28% of valid observations. Moment skewness is 39.125, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 2,681.286; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 1.000. There is an observed mass at zero: 514,089 observations (73.28%). In the figure, the linear histogram ends at P99 and explicitly leaves 6,849 observations (0.98%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Zero votes mean no helpful votes recorded, not an unhelpful review. These cumulative snapshot counts mix age, exposure and voting behaviour, so their shape does not measure intrinsic review quality or future helpfulness.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 701,528 | 0.924 | 0.000 | 5.471 | 0.000 | 1.000 | 1.000 | 13.000 | 646.000 | 39.125 | 2,681.286 |

![Helpful votes](figures/All_Beauty__helpful_vote.png)

#### title_characters: Review title length

The valid population contains 701,528 review observations; 0 are excluded from this metric's denominator. The median is 16.000 Unicode characters and the mean is 21.020. The middle half lies between 10.000 and 27.000 (IQR 17.000); population SD is 16.277 and unscaled median absolute deviation is 7.000. The range is 1.000 to 271.000; P95 is 55.000 and P99 is 81.000. The modal value(s), up to ten, are 10; there are 1 tied modes, each representing 11.87% of valid observations. Moment skewness is 2.008, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 5.540; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.294. In the figure, the linear histogram ends at P99 and explicitly leaves 6,974 observations (0.99%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 701,528 | 21.020 | 16.000 | 16.277 | 10.000 | 27.000 | 17.000 | 81.000 | 271.000 | 2.008 | 5.540 |

![Review title length](figures/All_Beauty__title_characters.png)

#### text_characters: Review body length

The valid population contains 701,528 review observations; 0 are excluded from this metric's denominator. The median is 102.000 Unicode characters and the mean is 173.032. The middle half lies between 44.000 and 209.000 (IQR 165.000); population SD is 246.924 and unscaled median absolute deviation is 69.000. The range is 0.000 to 14,989.000; P95 is 560.000 and P99 is 1,146.000. The modal value(s), up to ten, are 9; there are 1 tied modes, each representing 0.92% of valid observations. Moment skewness is 7.037, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 135.788; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.297. There is an observed mass at zero: 107 observations (0.02%). In the figure, the linear histogram ends at P99 and explicitly leaves 7,015 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 701,528 | 173.032 | 102.000 | 246.924 | 44.000 | 209.000 | 165.000 | 1,146.000 | 14,989.000 | 7.037 | 135.788 |

![Review body length](figures/All_Beauty__text_characters.png)

#### text_whitespace_words: Review body length

The valid population contains 701,528 review observations; 0 are excluded from this metric's denominator. The median is 19.000 whitespace-separated tokens and the mean is 32.751. The middle half lies between 8.000 and 40.000 (IQR 32.000); population SD is 45.973 and unscaled median absolute deviation is 13.000. The range is 0.000 to 2,585.000; P95 is 106.000 and P99 is 215.000. The modal value(s), up to ten, are 2; there are 1 tied modes, each representing 4.55% of valid observations. Moment skewness is 6.418, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 108.126; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.312. There is an observed mass at zero: 720 observations (0.10%). In the figure, the linear histogram ends at P99 and explicitly leaves 6,996 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 701,528 | 32.751 | 19.000 | 45.973 | 8.000 | 40.000 | 32.000 | 215.000 | 2,585.000 | 6.418 | 108.126 |

![Review body length](figures/All_Beauty__text_whitespace_words.png)

#### images_count: Review image entries

The valid population contains 701,528 review observations; 0 are excluded from this metric's denominator. The median is 0.000 array entries and the mean is 0.153. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 0.643 and unscaled median absolute deviation is 0.000. The range is 0.000 to 29.000; P95 is 1.000 and P99 is 3.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 91.49% of valid observations. Moment skewness is 7.517, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 99.947; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. There is an observed mass at zero: 641,844 observations (91.49%). In the figure, the linear histogram ends at P99 and explicitly leaves 5,062 observations (0.72%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 701,528 | 0.153 | 0.000 | 0.643 | 0.000 | 0.000 | 0.000 | 3.000 | 29.000 | 7.517 | 99.947 |

![Review image entries](figures/All_Beauty__images_count.png)

#### reviews_per_parent: Observed reviews per parent product

The valid population contains 112,565 parent product observations; 0 are excluded from this metric's denominator. The median is 2.000 raw review records and the mean is 6.232. The middle half lies between 1.000 and 4.000 (IQR 3.000); population SD is 25.190 and unscaled median absolute deviation is 1.000. The range is 1.000 to 1,962.000; P95 is 21.000 and P99 is 73.000. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 42.26% of valid observations. Moment skewness is 27.312, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 1,288.766; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.333. In the figure, the linear histogram ends at P99 and explicitly leaves 1,111 observations (0.99%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Each parent product contributes once to this distribution. Gini is 0.700; the largest 1,126 groups (ceil(1% of groups)) account for 27.871% of counted review rows. This measures concentration within the observed file, including extra raw copies; it is not market share or all-time user activity.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,565 | 6.232 | 2.000 | 25.190 | 1.000 | 4.000 | 3.000 | 73.000 | 1,962.000 | 27.312 | 1,288.766 |

![Reviews Per Parent](./reports/phase1/univariate/figures/All_Beauty__reviews_per_parent.png)


#### reviews_per_user: Observed reviews per reviewer

The valid population contains 631,986 reviewer ID observations; 0 are excluded from this metric's denominator. The median is 1.000 raw review records and the mean is 1.110. The middle half lies between 1.000 and 1.000 (IQR 0.000); population SD is 0.753 and unscaled median absolute deviation is 0.000. The range is 1.000 to 165.000; P95 is 2.000 and P99 is 3.000. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 92.34% of valid observations. Moment skewness is 66.688, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 9,242.145; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. In the figure, the linear histogram ends at P99 and explicitly leaves 3,446 observations (0.55%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Each reviewer ID contributes once to this distribution. Gini is 0.094; the largest 6,320 groups (ceil(1% of groups)) account for 4.406% of counted review rows. This measures concentration within the observed file, including extra raw copies; it is not market share or all-time user activity.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 631,986 | 1.110 | 1.000 | 0.753 | 1.000 | 1.000 | 0.000 | 3.000 | 165.000 | 66.688 | 9,242.145 |

![Observed reviews per reviewer](figures/All_Beauty__reviews_per_user.png)

#### Review rating imbalance

Low-star reviews (1–2) account for **20.69%** (145,114); three stars for 8.03%; and 4–5 stars for 71.29%. Five stars alone account for 59.97%. The largest observed class is 9.78 times the smallest observed class. Normalized entropy is 0.750 (1 would indicate equal shares across five stars). These quantify class imbalance without asserting that non-reviewing buyers have the same experience. They do not substitute for the eventual distribution of the product-level future ten-review target. The 4–5-star share is 71.29%; a majority of valid ratings. Absent classes: []. All-five-class ratio: 9.777.

### Exact-duplicate sensitivity

Raw objects: 701,528; retained in the derived exact-unique view: 694,253; extra copies: 7,275 (1.0370%). Keep first source-line copy of each type-sensitive canonical parsed record; verify canonical equality after SHA-256 candidate lookup; no fuzzy/user/text-only deduplication.

| Metric | Raw valid n | Unique valid n | Raw mean | Unique mean | Median change | Total variation |
| --- | --- | --- | --- | --- | --- | --- |
| rating | 701528 | 694253 | 3.96 | 3.961 | 0 | 0.0001966 |
| helpful_vote | 701528 | 694253 | 0.9236 | 0.9242 | 0 | 0.0001218 |
| text_characters | 701528 | 694253 | 173 | 173.1 | 0 | 0.001496 |
| text_whitespace_words | 701528 | 694253 | 32.75 | 32.76 | 0 | 0.0006676 |

Total variation ranges from 0 (identical empirical distributions) to 1. It compares normalized frequencies; no significance threshold is assumed. Raw distributions remain the primary descriptive view.

![Deduplication sensitivity](figures/All_Beauty__dedup_sensitivity.png)

### Review text audit

Thresholds: {'very_short': '1 to 5 whitespace tokens', 'very_long': '>= 500 whitespace tokens', 'blank_policy': 'Reported separately; excluded from both threshold classes; not deleted'}. Denominators and all counts are in text_audit.json. These are operational length labels, not semantic quality judgments.

| Length class | Count | % all reviews | % nonblank string bodies |
| --- | --- | --- | --- |
| very_short | 117434 | 16.74 | 16.76 |
| very_long | 540 | 0.07697 | 0.07705 |

### Probable dominant language

fastText predictions are heuristic labels. Text with fewer than 20 letters after derived HTML/whitespace handling, invalid Unicode, confidence below 0.8 or top-two margin below 0.2 is unknown. At most the first 5,000 cleaned characters are classified; truncation counts are recorded. No text leaves this machine. Non-English script is not itself a language. Short texts, code switching and domain shift limit accuracy; no language label deletes a row.

| Group | Count | % all reviews |
| --- | --- | --- |
| English | 565434 | 80.6 |
| non-English | 6529 | 0.9307 |
| unknown | 129565 | 18.47 |

Unknown reasons: {'too_few_letters': 92070, 'blank': 720, 'low_confidence_or_margin': 36775}. Language input truncated: 69.

| Predicted ISO code / unknown | Count | % all reviews |
| --- | --- | --- |
| en | 565434 | 80.6 |
| unknown | 129565 | 18.47 |
| es | 6426 | 0.916 |
| pt | 21 | 0.002993 |
| de | 19 | 0.002708 |
| fr | 15 | 0.002138 |
| it | 11 | 0.001568 |
| ru | 6 | 0.0008553 |
| zh | 5 | 0.0007127 |
| sv | 4 | 0.0005702 |
| gu | 3 | 0.0004276 |
| nl | 3 | 0.0004276 |
| hu | 3 | 0.0004276 |
| uk | 2 | 0.0002851 |
| pl | 2 | 0.0002851 |
| eo | 2 | 0.0002851 |
| fy | 1 | 0.0001425 |
| fi | 1 | 0.0001425 |
| ceb | 1 | 0.0001425 |
| sq | 1 | 0.0001425 |
| la | 1 | 0.0001425 |
| eu | 1 | 0.0001425 |
| ko | 1 | 0.0001425 |

![Language and length audit](figures/All_Beauty__text_language.png)

### Unicode scripts and unusual character families

Each character belongs to one Script bucket (selected named scripts, Common, Inherited, or Other_script). Character shares sum to 100%; a text may contain multiple scripts, so text percentages overlap. Common includes punctuation, digits and many symbols; script membership is not a defect. Format/private-use/unassigned flags need context and are not automatic corruption labels. Character totals and affected-text totals are different units.

| Script | Characters | % characters | Texts containing | % string texts |
| --- | --- | --- | --- | --- |
| Latin | 94352819 | 77.73 | 699851 | 99.76 |
| Common | 27028503 | 22.27 | 688020 | 98.07 |
| Inherited | 4829 | 0.003978 | 2661 | 0.3793 |
| Arabic | 176 | 0.000145 | 6 | 0.0008553 |
| Other_script | 93 | 7.661e-05 | 8 | 0.00114 |
| Cyrillic | 58 | 4.778e-05 | 3 | 0.0004276 |
| Han | 25 | 2.06e-05 | 7 | 0.0009978 |
| Hangul | 18 | 1.483e-05 | 4 | 0.0005702 |
| Greek | 8 | 6.591e-06 | 2 | 0.0002851 |
| Katakana | 7 | 5.767e-06 | 7 | 0.0009978 |
| Hiragana | 5 | 4.119e-06 | 1 | 0.0001425 |

| Family | Characters | Texts affected | % string texts |
| --- | --- | --- | --- |
| replacement | 0 | 0 | 0 |
| control_excluding_tab_lf_cr | 12 | 4 | 0.0005702 |
| format | 749 | 633 | 0.09023 |
| surrogate | 0 | 0 | 0 |
| private_use | 4 | 4 | 0.0005702 |
| unassigned | 0 | 0 | 0 |

![Unicode scripts](figures/All_Beauty__text_unicode.png)

### Initial relationship between text and rating

This small bivariate extension fulfills the Track B text audit. Each rating group includes all valid ratings; length summaries use its string bodies, including blank strings. Unavailable-body and blank-body rates use all reviews in that rating group. Product/user dependence is not treated as independent evidence; no causal or sentiment claim follows.

| Stars | Reviews | String bodies | Blank % | Unavailable % | Median words | Q1 words | Q3 words |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 102080 | 102080 | 0.1293 | 0.1293 | 20 | 10 | 38 |
| 2 | 43034 | 43034 | 0.05809 | 0.05809 | 24 | 12 | 46 |
| 3 | 56307 | 56307 | 0.04262 | 0.04262 | 25 | 12 | 47 |
| 4 | 79381 | 79381 | 0.07936 | 0.07936 | 25 | 11 | 52 |
| 5 | 420726 | 420726 | 0.1131 | 0.1131 | 17 | 7 | 37 |

![Text by rating](figures/All_Beauty__text_by_rating.png)

#### verified_purchase: categorical distribution

There are 701,528 valid nonempty observations and 0 excluded values. The distribution contains 2 exact observed labels. The most common label is `True`, with 90.512% of valid values. Top-ten share is 100.000%; normalized entropy is 0.453. A large Other bar is an aggregate of many labels, not an actual single label. All label frequencies and both valid/all-row denominators are saved.

| Label (top 12) | Count | % valid | % all objects |
|---|---:|---:|---:|
| True | 634,969 | 90.512 | 90.512 |
| False | 66,559 | 9.488 | 9.488 |

![verified_purchase](figures/All_Beauty__verified_purchase.png)

Verified purchase is a platform flag. False does not establish a fake review, and true does not remove self-selection.

#### Timestamp distribution

There are 701,528 valid timestamp observations and 0 excluded values. Observed coverage runs from `2000-11-01T04:24:18+00:00` to `2023-09-09T00:39:36.666000+00:00`. The median date is `2019-10-20T18:11:28.616500+00:00`; the middle half spans `2017-08-01T19:39:25.777500+00:00` to `2021-03-02T01:05:05.558000+00:00` (IQR 1308.23 days; full span 8346.84 days). The largest annual count occurs in 2020: 126,753 reviews (18.07% of valid timestamps). Outside the documented May 1996–September 2023 release window: 0. The shape is a distribution of observed event times. It combines platform growth, coverage and review-writing behaviour; a peak is not proof of a purchase peak. Boundary intervals are not complete periods.

| UTC year | Reviews | % valid timestamps |
|---|---:|---:|
| 2000 | 1 | 0.000 |
| 2001 | 12 | 0.002 |
| 2002 | 24 | 0.003 |
| 2003 | 56 | 0.008 |
| 2004 | 134 | 0.019 |
| 2005 | 267 | 0.038 |
| 2006 | 419 | 0.060 |
| 2007 | 1,162 | 0.166 |
| 2008 | 1,269 | 0.181 |
| 2009 | 1,207 | 0.172 |
| 2010 | 1,586 | 0.226 |
| 2011 | 1,877 | 0.268 |
| 2012 | 2,803 | 0.400 |
| 2013 | 7,948 | 1.133 |
| 2014 | 16,279 | 2.321 |
| 2015 | 36,239 | 5.166 |
| 2016 | 62,747 | 8.944 |
| 2017 | 68,035 | 9.698 |
| 2018 | 72,707 | 10.364 |
| 2019 | 99,120 | 14.129 |
| 2020 | 126,753 | 18.068 |
| 2021 | 124,897 | 17.804 |
| 2022 | 61,581 | 8.778 |
| 2023 | 14,405 | 2.053 |

![Timestamp distribution](figures/All_Beauty__timestamp.png)

### Appliances

Unit: one reviews record unless a derived group metric states otherwise. This file contributes **2,128,605 raw records**. Full numeric frequencies are in `Appliances__numeric_frequencies.csv.gz`.

#### Field coverage and denominators

| Field | Absent | Null | Blank string | Empty array | Empty object | Nonempty |
|---|---:|---:|---:|---:|---:|---:|
| asin | 0 | 0 | 0 | 0 | 0 | 2,128,605 |
| helpful_vote | 0 | 0 | 0 | 0 | 0 | 2,128,605 |
| images | 0 | 0 | 0 | 2,043,656 | 0 | 84,949 |
| parent_asin | 0 | 0 | 0 | 0 | 0 | 2,128,605 |
| rating | 0 | 0 | 0 | 0 | 0 | 2,128,605 |
| text | 0 | 0 | 2,065 | 0 | 0 | 2,126,540 |
| timestamp | 0 | 0 | 0 | 0 | 0 | 2,128,605 |
| title | 0 | 0 | 0 | 0 | 0 | 2,128,605 |
| user_id | 0 | 0 | 0 | 0 | 0 | 2,128,605 |
| verified_purchase | 0 | 0 | 0 | 0 | 0 | 2,128,605 |

![Field content states](figures/Appliances__field_states.png)

The stacked bars separate absent content from nonempty content. Nonempty is not a quality certification. Each row sums to the file's parsed-object count, so differences in denominators can be traced without dropping entire records.

#### rating: Review star rating

The valid population contains 2,128,605 review observations; 0 are excluded from this metric's denominator. The median is 5.000 stars and the mean is 4.222. The middle half lies between 4.000 and 5.000 (IQR 1.000); population SD is 1.381 and unscaled median absolute deviation is 0.000. The range is 1.000 to 5.000; P95 is 5.000 and P99 is 5.000. The modal value(s), up to ten, are 5; there are 1 tied modes, each representing 69.82% of valid observations. Moment skewness is -1.559, negative (a longer/heavier lower tail by the third-moment measure). Excess kurtosis is 0.837; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -1.000. Stars are ordered categories. Median and class percentages are primary; mean/SD are conventional summaries that treat adjacent star steps as equally spaced. This is a raw review distribution, not the future ten-review product target.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,128,605 | 4.222 | 5.000 | 1.381 | 4.000 | 5.000 | 1.000 | 5.000 | 5.000 | -1.559 | 0.837 |

![Review star rating](figures/Appliances__rating.png)

#### helpful_vote: Helpful votes

The valid population contains 2,128,605 review observations; 0 are excluded from this metric's denominator. The median is 0.000 votes and the mean is 0.929. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 12.527 and unscaled median absolute deviation is 0.000. The range is 0.000 to 5,704.000; P95 is 3.000 and P99 is 15.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 80.80% of valid observations. Moment skewness is 162.089, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 49,416.808; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. There is an observed mass at zero: 1,719,985 observations (80.80%). In the figure, the linear histogram ends at P99 and explicitly leaves 20,564 observations (0.97%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Zero votes mean no helpful votes recorded, not an unhelpful review. These cumulative snapshot counts mix age, exposure and voting behaviour, so their shape does not measure intrinsic review quality or future helpfulness.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,128,605 | 0.929 | 0.000 | 12.527 | 0.000 | 0.000 | 0.000 | 15.000 | 5,704.000 | 162.089 | 49,416.808 |

![Helpful votes](figures/Appliances__helpful_vote.png)

#### title_characters: Review title length

The valid population contains 2,128,605 review observations; 0 are excluded from this metric's denominator. The median is 17.000 Unicode characters and the mean is 22.340. The middle half lies between 10.000 and 29.000 (IQR 19.000); population SD is 16.786 and unscaled median absolute deviation is 7.000. The range is 1.000 to 348.000; P95 is 57.000 and P99 is 83.000. The modal value(s), up to ten, are 10; there are 1 tied modes, each representing 13.48% of valid observations. Moment skewness is 1.834, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 4.390; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.263. In the figure, the linear histogram ends at P99 and explicitly leaves 20,597 observations (0.97%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,128,605 | 22.340 | 17.000 | 16.786 | 10.000 | 29.000 | 19.000 | 83.000 | 348.000 | 1.834 | 4.390 |

![Review title length](figures/Appliances__title_characters.png)

#### text_characters: Review body length

The valid population contains 2,128,605 review observations; 0 are excluded from this metric's denominator. The median is 88.000 Unicode characters and the mean is 169.513. The middle half lies between 37.000 and 195.000 (IQR 158.000); population SD is 279.981 and unscaled median absolute deviation is 62.000. The range is 0.000 to 30,004.000; P95 is 580.000 and P99 is 1,258.000. The modal value(s), up to ten, are 11; there are 1 tied modes, each representing 1.42% of valid observations. Moment skewness is 9.134, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 257.153; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.354. There is an observed mass at zero: 95 observations (0.00%). In the figure, the linear histogram ends at P99 and explicitly leaves 21,274 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,128,605 | 169.513 | 88.000 | 279.981 | 37.000 | 195.000 | 158.000 | 1,258.000 | 30,004.000 | 9.134 | 257.153 |

![Review body length](figures/Appliances__text_characters.png)

#### text_whitespace_words: Review body length

The valid population contains 2,128,605 review observations; 0 are excluded from this metric's denominator. The median is 16.000 whitespace-separated tokens and the mean is 31.496. The middle half lies between 7.000 and 37.000 (IQR 30.000); population SD is 51.606 and unscaled median absolute deviation is 11.000. The range is 0.000 to 3,636.000; P95 is 108.000 and P99 is 233.000. The modal value(s), up to ten, are 2; there are 1 tied modes, each representing 6.15% of valid observations. Moment skewness is 8.413, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 191.244; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.400. There is an observed mass at zero: 2,065 observations (0.10%). In the figure, the linear histogram ends at P99 and explicitly leaves 21,155 observations (0.99%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,128,605 | 31.496 | 16.000 | 51.606 | 7.000 | 37.000 | 30.000 | 233.000 | 3,636.000 | 8.413 | 191.244 |

![Review body length](figures/Appliances__text_whitespace_words.png)

#### images_count: Review image entries

The valid population contains 2,128,605 review observations; 0 are excluded from this metric's denominator. The median is 0.000 array entries and the mean is 0.070. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 0.428 and unscaled median absolute deviation is 0.000. The range is 0.000 to 27.000; P95 is 0.000 and P99 is 2.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 96.01% of valid observations. Moment skewness is 10.473, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 190.449; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. There is an observed mass at zero: 2,043,656 observations (96.01%). In the figure, the linear histogram ends at P99 and explicitly leaves 14,834 observations (0.70%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2,128,605 | 0.070 | 0.000 | 0.428 | 0.000 | 0.000 | 0.000 | 2.000 | 27.000 | 10.473 | 190.449 |

![Review image entries](figures/Appliances__images_count.png)

#### reviews_per_parent: Observed reviews per parent product

The valid population contains 94,319 parent product observations; 0 are excluded from this metric's denominator. The median is 3.000 raw review records and the mean is 22.568. The middle half lies between 1.000 and 9.000 (IQR 8.000); population SD is 146.509 and unscaled median absolute deviation is 2.000. The range is 1.000 to 12,027.000; P95 is 75.000 and P99 is 334.000. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 35.61% of valid observations. Moment skewness is 30.791, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 1,550.097; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.500. In the figure, the linear histogram ends at P99 and explicitly leaves 943 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Each parent product contributes once to this distribution. Gini is 0.850; the largest 944 groups (ceil(1% of groups)) account for 42.481% of counted review rows. This measures concentration within the observed file, including extra raw copies; it is not market share or all-time user activity.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,319 | 22.568 | 3.000 | 146.509 | 1.000 | 9.000 | 8.000 | 334.000 | 12,027.000 | 30.791 | 1,550.097 |

![Observed reviews per parent product](figures/Appliances__reviews_per_parent.png)

#### reviews_per_user: Observed reviews per reviewer

The valid population contains 1,755,732 reviewer ID observations; 0 are excluded from this metric's denominator. The median is 1.000 raw review records and the mean is 1.212. The middle half lies between 1.000 and 1.000 (IQR 0.000); population SD is 0.676 and unscaled median absolute deviation is 0.000. The range is 1.000 to 111.000; P95 is 2.000 and P99 is 4.000. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 85.24% of valid observations. Moment skewness is 12.459, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 765.285; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. In the figure, the linear histogram ends at P99 and explicitly leaves 9,918 observations (0.56%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Each reviewer ID contributes once to this distribution. Gini is 0.156; the largest 17,558 groups (ceil(1% of groups)) account for 4.424% of counted review rows. This measures concentration within the observed file, including extra raw copies; it is not market share or all-time user activity.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,755,732 | 1.212 | 1.000 | 0.676 | 1.000 | 1.000 | 0.000 | 4.000 | 111.000 | 12.459 | 765.285 |

![Observed reviews per reviewer](figures/Appliances__reviews_per_user.png)

#### Review rating imbalance

Low-star reviews (1–2) account for **15.51%** (330,117); three stars for 4.89%; and 4–5 stars for 79.60%. Five stars alone account for 69.82%. The largest observed class is 18.66 times the smallest observed class. Normalized entropy is 0.622 (1 would indicate equal shares across five stars). These quantify class imbalance without asserting that non-reviewing buyers have the same experience. They do not substitute for the eventual distribution of the product-level future ten-review target. The 4–5-star share is 79.60%; a majority of valid ratings. Absent classes: []. All-five-class ratio: 18.656.

### Exact-duplicate sensitivity

Raw objects: 2,128,605; retained in the derived exact-unique view: 2,105,949; extra copies: 22,656 (1.0644%). Keep first source-line copy of each type-sensitive canonical parsed record; verify canonical equality after SHA-256 candidate lookup; no fuzzy/user/text-only deduplication.

| Metric | Raw valid n | Unique valid n | Raw mean | Unique mean | Median change | Total variation |
| --- | --- | --- | --- | --- | --- | --- |
| rating | 2128605 | 2105949 | 4.222 | 4.223 | 0 | 0.0003102 |
| helpful_vote | 2128605 | 2105949 | 0.9289 | 0.9291 | 0 | 8.96e-05 |
| text_characters | 2128605 | 2105949 | 169.5 | 169.6 | 0 | 0.0009475 |
| text_whitespace_words | 2128605 | 2105949 | 31.5 | 31.51 | 0 | 0.0005047 |

Total variation ranges from 0 (identical empirical distributions) to 1. It compares normalized frequencies; no significance threshold is assumed. Raw distributions remain the primary descriptive view.

![Deduplication sensitivity](figures/Appliances__dedup_sensitivity.png)

### Review text audit

Thresholds: {'very_short': '1 to 5 whitespace tokens', 'very_long': '>= 500 whitespace tokens', 'blank_policy': 'Reported separately; excluded from both threshold classes; not deleted'}. Denominators and all counts are in text_audit.json. These are operational length labels, not semantic quality judgments.

| Length class | Count | % all reviews | % nonblank string bodies |
| --- | --- | --- | --- |
| very_short | 440241 | 20.68 | 20.7 |
| very_long | 2939 | 0.1381 | 0.1382 |

### Probable dominant language

fastText predictions are heuristic labels. Text with fewer than 20 letters after derived HTML/whitespace handling, invalid Unicode, confidence below 0.8 or top-two margin below 0.2 is unknown. At most the first 5,000 cleaned characters are classified; truncation counts are recorded. No text leaves this machine. Non-English script is not itself a language. Short texts, code switching and domain shift limit accuracy; no language label deletes a row.

| Group | Count | % all reviews |
| --- | --- | --- |
| English | 1645730 | 77.31 |
| non-English | 11403 | 0.5357 |
| unknown | 471472 | 22.15 |

Unknown reasons: {'too_few_letters': 325270, 'low_confidence_or_margin': 144137, 'blank': 2065}. Language input truncated: 388.

| Predicted ISO code / unknown | Count | % all reviews |
| --- | --- | --- |
| en | 1645730 | 77.31 |
| unknown | 471472 | 22.15 |
| es | 10998 | 0.5167 |
| fr | 151 | 0.007094 |
| de | 120 | 0.005637 |
| pt | 23 | 0.001081 |
| nl | 19 | 0.0008926 |
| zh | 17 | 0.0007986 |
| eo | 12 | 0.0005637 |
| ja | 9 | 0.0004228 |
| ru | 8 | 0.0003758 |
| hu | 8 | 0.0003758 |
| it | 8 | 0.0003758 |
| fy | 4 | 0.0001879 |
| sv | 3 | 0.0001409 |
| tr | 3 | 0.0001409 |
| gu | 3 | 0.0001409 |
| ca | 3 | 0.0001409 |
| fa | 2 | 9.396e-05 |
| pl | 2 | 9.396e-05 |
| ko | 2 | 9.396e-05 |
| sk | 1 | 4.698e-05 |
| hi | 1 | 4.698e-05 |
| ka | 1 | 4.698e-05 |
| he | 1 | 4.698e-05 |
| ceb | 1 | 4.698e-05 |
| no | 1 | 4.698e-05 |
| ro | 1 | 4.698e-05 |
| tl | 1 | 4.698e-05 |

![Language and length audit](figures/Appliances__text_language.png)

### Unicode scripts and unusual character families

Each character belongs to one Script bucket (selected named scripts, Common, Inherited, or Other_script). Character shares sum to 100%; a text may contain multiple scripts, so text percentages overlap. Common includes punctuation, digits and many symbols; script membership is not a defect. Format/private-use/unassigned flags need context and are not automatic corruption labels. Character totals and affected-text totals are different units.

| Script | Characters | % characters | Texts containing | % string texts |
| --- | --- | --- | --- | --- |
| Latin | 281212930 | 77.94 | 2124464 | 99.81 |
| Common | 79609556 | 22.06 | 2085081 | 97.96 |
| Inherited | 3780 | 0.001048 | 2043 | 0.09598 |
| Arabic | 441 | 0.0001222 | 6 | 0.0002819 |
| Hiragana | 127 | 3.52e-05 | 3 | 0.0001409 |
| Hebrew | 104 | 2.882e-05 | 2 | 9.396e-05 |
| Han | 100 | 2.771e-05 | 13 | 0.0006107 |
| Greek | 46 | 1.275e-05 | 13 | 0.0006107 |
| Katakana | 39 | 1.081e-05 | 15 | 0.0007047 |
| Other_script | 35 | 9.7e-06 | 8 | 0.0003758 |
| Cyrillic | 22 | 6.097e-06 | 8 | 0.0003758 |
| Hangul | 2 | 5.543e-07 | 1 | 4.698e-05 |

| Family | Characters | Texts affected | % string texts |
| --- | --- | --- | --- |
| replacement | 0 | 0 | 0 |
| control_excluding_tab_lf_cr | 71 | 21 | 0.0009866 |
| format | 830 | 703 | 0.03303 |
| surrogate | 0 | 0 | 0 |
| private_use | 5 | 5 | 0.0002349 |
| unassigned | 0 | 0 | 0 |

![Unicode scripts](figures/Appliances__text_unicode.png)

### Initial relationship between text and rating

This small bivariate extension fulfills the Track B text audit. Each rating group includes all valid ratings; length summaries use its string bodies, including blank strings. Unavailable-body and blank-body rates use all reviews in that rating group. Product/user dependence is not treated as independent evidence; no causal or sentiment claim follows.

| Stars | Reviews | String bodies | Blank % | Unavailable % | Median words | Q1 words | Q3 words |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 250453 | 250453 | 0.1857 | 0.1857 | 27 | 13 | 53 |
| 2 | 79664 | 79664 | 0.1255 | 0.1255 | 32 | 16 | 61 |
| 3 | 104047 | 104047 | 0.08746 | 0.08746 | 29 | 14 | 57 |
| 4 | 208216 | 208216 | 0.06628 | 0.06628 | 22 | 8 | 49 |
| 5 | 1486225 | 1486225 | 0.08552 | 0.08552 | 13 | 6 | 29 |

![Text by rating](figures/Appliances__text_by_rating.png)

#### verified_purchase: categorical distribution

There are 2,128,605 valid nonempty observations and 0 excluded values. The distribution contains 2 exact observed labels. The most common label is `True`, with 95.840% of valid values. Top-ten share is 100.000%; normalized entropy is 0.250. A large Other bar is an aggregate of many labels, not an actual single label. All label frequencies and both valid/all-row denominators are saved.

| Label (top 12) | Count | % valid | % all objects |
|---|---:|---:|---:|
| True | 2,040,064 | 95.840 | 95.840 |
| False | 88,541 | 4.160 | 4.160 |

![verified_purchase](figures/Appliances__verified_purchase.png)

Verified purchase is a platform flag. False does not establish a fake review, and true does not remove self-selection.

#### Timestamp distribution

There are 2,128,605 valid timestamp observations and 0 excluded values. Observed coverage runs from `2000-10-23T14:37:23+00:00` to `2023-09-12T16:29:17.016000+00:00`. The median date is `2020-01-14T02:05:18.802000+00:00`; the middle half spans `2017-08-07T16:55:36.596000+00:00` to `2021-08-15T14:28:44.069000+00:00` (IQR 1468.90 days; full span 8359.08 days). The largest annual count occurs in 2021: 345,120 reviews (16.21% of valid timestamps). Outside the documented May 1996–September 2023 release window: 0. The shape is a distribution of observed event times. It combines platform growth, coverage and review-writing behaviour; a peak is not proof of a purchase peak. Boundary intervals are not complete periods.

| UTC year | Reviews | % valid timestamps |
|---|---:|---:|
| 2000 | 1 | 0.000 |
| 2001 | 0 | 0.000 |
| 2002 | 1 | 0.000 |
| 2003 | 8 | 0.000 |
| 2004 | 16 | 0.001 |
| 2005 | 80 | 0.004 |
| 2006 | 182 | 0.009 |
| 2007 | 621 | 0.029 |
| 2008 | 883 | 0.041 |
| 2009 | 1,539 | 0.072 |
| 2010 | 3,537 | 0.166 |
| 2011 | 7,636 | 0.359 |
| 2012 | 15,219 | 0.715 |
| 2013 | 43,618 | 2.049 |
| 2014 | 77,353 | 3.634 |
| 2015 | 122,696 | 5.764 |
| 2016 | 153,916 | 7.231 |
| 2017 | 169,785 | 7.976 |
| 2018 | 189,599 | 8.907 |
| 2019 | 261,004 | 12.262 |
| 2020 | 311,251 | 14.622 |
| 2021 | 345,120 | 16.213 |
| 2022 | 299,487 | 14.070 |
| 2023 | 125,053 | 5.875 |

![Timestamp distribution](figures/Appliances__timestamp.png)

### meta_All_Beauty

Unit: one metadata record unless a derived group metric states otherwise. This file contributes **112,590 raw records**. Full numeric frequencies are in `meta_All_Beauty__numeric_frequencies.csv.gz`.

#### Field coverage and denominators

| Field | Absent | Null | Blank string | Empty array | Empty object | Nonempty |
|---|---:|---:|---:|---:|---:|---:|
| average_rating | 0 | 0 | 0 | 0 | 0 | 112,590 |
| bought_together | 0 | 112,590 | 0 | 0 | 0 | 0 |
| categories | 0 | 0 | 0 | 112,590 | 0 | 0 |
| description | 0 | 0 | 0 | 93,428 | 0 | 19,162 |
| details | 0 | 0 | 0 | 0 | 4,512 | 108,078 |
| features | 0 | 0 | 0 | 95,213 | 0 | 17,377 |
| images | 0 | 0 | 0 | 0 | 0 | 112,590 |
| main_category | 0 | 0 | 0 | 0 | 0 | 112,590 |
| parent_asin | 0 | 0 | 0 | 0 | 0 | 112,590 |
| price | 0 | 94,886 | 0 | 0 | 0 | 17,704 |
| rating_number | 0 | 0 | 0 | 0 | 0 | 112,590 |
| store | 0 | 11,331 | 0 | 0 | 0 | 101,259 |
| title | 0 | 0 | 12 | 0 | 0 | 112,578 |
| videos | 0 | 0 | 0 | 96,708 | 0 | 15,882 |

![Field content states](figures/meta_All_Beauty__field_states.png)

The stacked bars separate absent content from nonempty content. Nonempty is not a quality certification. Each row sums to the file's parsed-object count, so differences in denominators can be traced without dropping entire records.

#### average_rating: Displayed product average rating

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 4.000 stars and the mean is 3.883. The middle half lies between 3.400 and 4.500 (IQR 1.100); population SD is 0.874 and unscaled median absolute deviation is 0.500. The range is 1.000 to 5.000; P95 is 5.000 and P99 is 5.000. The modal value(s), up to ten, are 5.000; there are 1 tied modes, each representing 12.90% of valid observations. Moment skewness is -1.148, negative (a longer/heavier lower tail by the third-moment measure). Excess kurtosis is 1.707; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -0.091. The bar chart uses each observed displayed value. Rounding/heaping can create peaks; this snapshot average is not recomputed from the available reviews and must not be treated as historically available at the fifth review.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 3.883 | 4.000 | 0.874 | 3.400 | 4.500 | 1.100 | 5.000 | 5.000 | -1.148 | 1.707 |

![Displayed product average rating](figures/meta_All_Beauty__average_rating.png)

#### rating_number: Displayed product rating count

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 9.000 ratings and the mean is 50.541. The middle half lies between 3.000 and 28.000 (IQR 25.000); population SD is 310.991 and unscaled median absolute deviation is 7.000. The range is 1.000 to 30,206.000; P95 is 167.000 and P99 is 677.000. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 10.37% of valid observations. Moment skewness is 34.963, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 2,022.897; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.520. In the figure, the linear histogram ends at P99 and explicitly leaves 1,125 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This is the product-page rating count at collection, not the number of review records in this file, sales volume, or a historical count at prediction time.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 50.541 | 9.000 | 310.991 | 3.000 | 28.000 | 25.000 | 677.000 | 30,206.000 | 34.963 | 2,022.897 |

![Displayed product rating count](figures/meta_All_Beauty__rating_number.png)

#### price: Product price at crawl time

The valid population contains 17,704 metadata record observations; 94,886 are excluded from this metric's denominator. The median is 16.990 USD and the mean is 27.256. The middle half lies between 9.990 and 29.900 (IQR 19.910); population SD is 50.471 and unscaled median absolute deviation is 8.000. The range is 0.010 to 2,548.980; P95 is 75.000 and P99 is 187.480. The modal value(s), up to ten, are 9.990; there are 1 tied modes, each representing 3.56% of valid observations. Moment skewness is 21.965, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 838.554; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.297. In the figure, the linear histogram ends at P99 and explicitly leaves 177 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. These summaries describe observed, valid crawl-time USD prices only. Missing prices are excluded without imputation. Their distribution cannot be assumed to represent all products or prices at review time; zero, if observed, remains a recorded value rather than an imputed price.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 17,704 | 27.256 | 16.990 | 50.471 | 9.990 | 29.900 | 19.910 | 187.480 | 2,548.980 | 21.965 | 838.554 |

![Product price at crawl time](figures/meta_All_Beauty__price.png)

#### title_characters: Product title length

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 114.000 Unicode characters and the mean is 113.580. The middle half lies between 67.000 and 158.000 (IQR 91.000); population SD is 53.188 and unscaled median absolute deviation is 46.000. The range is 0.000 to 1,455.000; P95 is 195.000 and P99 is 201.000. The modal value(s), up to ten, are 199; there are 1 tied modes, each representing 0.76% of valid observations. Moment skewness is 0.576, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 9.996; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -0.033. There is an observed mass at zero: 12 observations (0.01%). In the figure, the linear histogram ends at P99 and explicitly leaves 1,055 observations (0.94%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 113.580 | 114.000 | 53.188 | 67.000 | 158.000 | 91.000 | 201.000 | 1,455.000 | 0.576 | 9.996 |

![Product title length](figures/meta_All_Beauty__title_characters.png)

#### features_count: Product feature entries

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 0.000 array entries and the mean is 0.644. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 1.615 and unscaled median absolute deviation is 0.000. The range is 0.000 to 13.000; P95 is 5.000 and P99 is 5.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 84.57% of valid observations. Moment skewness is 2.292, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 3.688; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. There is an observed mass at zero: 95,213 observations (84.57%). In the figure, the linear histogram ends at P99 and explicitly leaves 709 observations (0.63%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 0.644 | 0.000 | 1.615 | 0.000 | 0.000 | 0.000 | 5.000 | 13.000 | 2.292 | 3.688 |

![Product feature entries](figures/meta_All_Beauty__features_count.png)

#### features_characters: Product feature text length

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 0.000 Unicode characters and the mean is 81.753. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 271.231 and unscaled median absolute deviation is 0.000. The range is 0.000 to 4,249.000; P95 is 669.000 and P99 is 1,390.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 84.57% of valid observations. Moment skewness is 4.189, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 19.578; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. There is an observed mass at zero: 95,213 observations (84.57%). In the figure, the linear histogram ends at P99 and explicitly leaves 1,125 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 81.753 | 0.000 | 271.231 | 0.000 | 0.000 | 0.000 | 1,390.000 | 4,249.000 | 4.189 | 19.578 |

![Product feature text length](figures/meta_All_Beauty__features_characters.png)

#### description_count: Product description entries

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 0.000 array entries and the mean is 0.431. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 2.520 and unscaled median absolute deviation is 0.000. The range is 0.000 to 152.000; P95 is 1.000 and P99 is 10.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 82.98% of valid observations. Moment skewness is 19.136, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 690.619; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. There is an observed mass at zero: 93,428 observations (82.98%). In the figure, the linear histogram ends at P99 and explicitly leaves 1,097 observations (0.97%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 0.431 | 0.000 | 2.520 | 0.000 | 0.000 | 0.000 | 10.000 | 152.000 | 19.136 | 690.619 |

![Product description entries](figures/meta_All_Beauty__description_count.png)

#### description_characters: Product description text length

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 0.000 Unicode characters and the mean is 89.297. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 303.094 and unscaled median absolute deviation is 0.000. The range is 0.000 to 13,056.000; P95 is 649.000 and P99 is 1,581.110. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 82.98% of valid observations. Moment skewness is 6.110, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 91.903; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. There is an observed mass at zero: 93,428 observations (82.98%). In the figure, the linear histogram ends at P99 and explicitly leaves 1,126 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 89.297 | 0.000 | 303.094 | 0.000 | 0.000 | 0.000 | 1,581.110 | 13,056.000 | 6.110 | 91.903 |

![Product description text length](figures/meta_All_Beauty__description_characters.png)

#### images_count: Product image entries

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 6.000 array entries and the mean is 4.878. The middle half lies between 2.000 and 7.000 (IQR 5.000); population SD is 2.784 and unscaled median absolute deviation is 2.000. The range is 1.000 to 22.000; P95 is 9.000 and P99 is 9.000. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 21.67% of valid observations. Moment skewness is -0.155, negative (a longer/heavier lower tail by the third-moment measure). Excess kurtosis is -1.360; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -0.600. In the figure, the linear histogram ends at P99 and explicitly leaves 168 observations (0.15%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 4.878 | 6.000 | 2.784 | 2.000 | 7.000 | 5.000 | 9.000 | 22.000 | -0.155 | -1.360 |

![Product image entries](figures/meta_All_Beauty__images_count.png)

#### videos_count: Product video entries

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 0.000 array entries and the mean is 0.361. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 1.250 and unscaled median absolute deviation is 0.000. The range is 0.000 to 10.000; P95 is 2.000 and P99 is 7.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 85.89% of valid observations. Moment skewness is 4.992, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 28.554; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is not available. The middle 50% collapses to one value even though other values exist; zero IQR does not mean the whole distribution is constant. There is an observed mass at zero: 96,708 observations (85.89%). In the figure, the linear histogram ends at P99 and explicitly leaves 1,033 observations (0.92%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 0.361 | 0.000 | 1.250 | 0.000 | 0.000 | 0.000 | 7.000 | 10.000 | 4.992 | 28.554 |

![Product video entries](figures/meta_All_Beauty__videos_count.png)

#### categories_count: Category entries

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 0.000 top-level array entries and the mean is 0.000. The middle half lies between 0.000 and 0.000 (IQR 0.000); population SD is 0.000 and unscaled median absolute deviation is 0.000. The range is 0.000 to 0.000; P95 is 0.000 and P99 is 0.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 100.00% of valid observations. All valid values are identical. The distribution is a point mass, its spread is zero, and skewness/kurtosis are undefined. There is an observed mass at zero: 112,590 observations (100.00%). In the figure, the linear histogram ends at P99 and explicitly leaves 0 observations (0.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | not available | not available |

![Category entries](figures/meta_All_Beauty__categories_count.png)

#### details_count: Product detail attributes

The valid population contains 112,590 metadata record observations; 0 are excluded from this metric's denominator. The median is 6.000 dictionary keys and the mean is 5.470. The middle half lies between 3.000 and 7.000 (IQR 4.000); population SD is 2.761 and unscaled median absolute deviation is 2.000. The range is 0.000 to 23.000; P95 is 9.000 and P99 is 12.000. The modal value(s), up to ten, are 7; there are 1 tied modes, each representing 20.13% of valid observations. Moment skewness is -0.212, negative (a longer/heavier lower tail by the third-moment measure). Excess kurtosis is -0.316; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -0.500. There is an observed mass at zero: 4,512 observations (4.01%). In the figure, the linear histogram ends at P99 and explicitly leaves 648 observations (0.58%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 112,590 | 5.470 | 6.000 | 2.761 | 3.000 | 7.000 | 4.000 | 12.000 | 23.000 | -0.212 | -0.316 |

![Product detail attributes](figures/meta_All_Beauty__details_count.png)

#### bought_together_count: Recommended bundle entries

No valid values are available. A mean, spread or distribution shape cannot be inferred; the empty-data panel documents this limitation. Missing is not zero.

![Recommended bundle entries](figures/meta_All_Beauty__bought_together_count.png)

### Exact-duplicate sensitivity

Raw objects: 112,590; retained in the derived exact-unique view: 112,590; extra copies: 0 (0.0000%). Keep first source-line copy of each type-sensitive canonical parsed record; verify canonical equality after SHA-256 candidate lookup; no fuzzy/user/text-only deduplication.

| Metric | Raw valid n | Unique valid n | Raw mean | Unique mean | Median change | Total variation |
| --- | --- | --- | --- | --- | --- | --- |
| price | 17704 | 17704 | 27.26 | 27.26 | 0 | 0 |
| average_rating | 112590 | 112590 | 3.883 | 3.883 | 0 | 0 |
| rating_number | 112590 | 112590 | 50.54 | 50.54 | 0 | 0 |

Total variation ranges from 0 (identical empirical distributions) to 1. It compares normalized frequencies; no significance threshold is assumed. Raw distributions remain the primary descriptive view.

![Deduplication sensitivity](figures/meta_All_Beauty__dedup_sensitivity.png)

#### main_category: categorical distribution

There are 112,590 valid nonempty observations and 0 excluded values. The distribution contains 2 exact observed labels. The most common label is `All Beauty`, with 99.596% of valid values. Top-ten share is 100.000%; normalized entropy is 0.038. A large Other bar is an aggregate of many labels, not an actual single label. All label frequencies and both valid/all-row denominators are saved.

| Label (top 12) | Count | % valid | % all objects |
|---|---:|---:|---:|
| All Beauty | 112,135 | 99.596 | 99.596 |
| Premium Beauty | 455 | 0.404 | 0.404 |

![main_category](figures/meta_All_Beauty__main_category.png)

The file's selected download category and each record's main_category are different concepts. Other labels inside the file are not automatically classification errors.

#### store: categorical distribution

There are 101,259 valid nonempty observations and 11,331 excluded values. The distribution contains 30,765 exact observed labels. The most common label is `Bath & Body Works`, with 0.475% of valid values. Top-ten share is 3.101%; normalized entropy is 0.908. A large Other bar is an aggregate of many labels, not an actual single label. All label frequencies and both valid/all-row denominators are saved.

| Label (top 12) | Count | % valid | % all objects |
|---|---:|---:|---:|
| Bath & Body Works | 481 | 0.475 | 0.427 |
| WILLBOND | 388 | 0.383 | 0.345 |
| Hairro | 381 | 0.376 | 0.338 |
| Generic | 369 | 0.364 | 0.328 |
| S-noilite | 340 | 0.336 | 0.302 |
| AVON | 283 | 0.279 | 0.251 |
| Maitys | 244 | 0.241 | 0.217 |
| Sunny Hair | 242 | 0.239 | 0.215 |
| Boao | 208 | 0.205 | 0.185 |
| Patelai | 204 | 0.201 | 0.181 |
| SEGO | 199 | 0.197 | 0.177 |
| KISS | 196 | 0.194 | 0.174 |

![store](figures/meta_All_Beauty__store.png)

Store names are unharmonized labels, not guaranteed unique seller identities. The distribution is metadata-record-weighted, not sales-weighted.

### meta_Appliances

Unit: one metadata record unless a derived group metric states otherwise. This file contributes **94,327 raw records**. Full numeric frequencies are in `meta_Appliances__numeric_frequencies.csv.gz`.

#### Field coverage and denominators

| Field | Absent | Null | Blank string | Empty array | Empty object | Nonempty |
|---|---:|---:|---:|---:|---:|---:|
| author | 94,322 | 4 | 0 | 0 | 0 | 1 |
| average_rating | 0 | 0 | 0 | 0 | 0 | 94,327 |
| bought_together | 0 | 94,327 | 0 | 0 | 0 | 0 |
| categories | 0 | 0 | 0 | 3,285 | 0 | 91,042 |
| description | 0 | 0 | 0 | 32,172 | 0 | 62,155 |
| details | 0 | 0 | 0 | 0 | 2,010 | 92,317 |
| features | 0 | 0 | 0 | 16,543 | 0 | 77,784 |
| images | 0 | 0 | 0 | 1 | 0 | 94,326 |
| main_category | 0 | 4,676 | 0 | 0 | 0 | 89,651 |
| parent_asin | 0 | 0 | 0 | 0 | 0 | 94,327 |
| price | 0 | 47,601 | 0 | 0 | 0 | 46,726 |
| rating_number | 0 | 0 | 0 | 0 | 0 | 94,327 |
| store | 0 | 916 | 0 | 0 | 0 | 93,411 |
| subtitle | 94,322 | 0 | 0 | 0 | 0 | 5 |
| title | 0 | 0 | 9 | 0 | 0 | 94,318 |
| videos | 0 | 0 | 0 | 60,624 | 0 | 33,703 |

![Field content states](figures/meta_Appliances__field_states.png)

The stacked bars separate absent content from nonempty content. Nonempty is not a quality certification. Each row sums to the file's parsed-object count, so differences in denominators can be traced without dropping entire records.

#### average_rating: Displayed product average rating

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 4.300 stars and the mean is 4.119. The middle half lies between 3.800 and 4.700 (IQR 0.900); population SD is 0.864 and unscaled median absolute deviation is 0.400. The range is 1.000 to 5.000; P95 is 5.000 and P99 is 5.000. The modal value(s), up to ten, are 5.000; there are 1 tied modes, each representing 16.54% of valid observations. Moment skewness is -1.750, negative (a longer/heavier lower tail by the third-moment measure). Excess kurtosis is 3.477; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -0.111. The bar chart uses each observed displayed value. Rounding/heaping can create peaks; this snapshot average is not recomputed from the available reviews and must not be treated as historically available at the fifth review.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 4.119 | 4.300 | 0.864 | 3.800 | 4.700 | 0.900 | 5.000 | 5.000 | -1.750 | 3.477 |

![Displayed product average rating](figures/meta_Appliances__average_rating.png)

#### rating_number: Displayed product rating count

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 13.000 ratings and the mean is 136.368. The middle half lies between 3.000 and 53.000 (IQR 50.000); population SD is 977.511 and unscaled median absolute deviation is 11.000. The range is 1.000 to 90,203.000; P95 is 467.000 and P99 is 1,951.480. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 12.14% of valid observations. Moment skewness is 33.311, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 1,709.939; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.600. In the figure, the linear histogram ends at P99 and explicitly leaves 944 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This is the product-page rating count at collection, not the number of review records in this file, sales volume, or a historical count at prediction time.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 136.368 | 13.000 | 977.511 | 3.000 | 53.000 | 50.000 | 1,951.480 | 90,203.000 | 33.311 | 1,709.939 |

![Displayed product rating count](figures/meta_Appliances__rating_number.png)

#### price: Product price at crawl time

The valid population contains 46,726 metadata record observations; 47,601 are excluded from this metric's denominator. The median is 26.990 USD and the mean is 86.480. The middle half lies between 14.990 and 58.130 (IQR 43.140); population SD is 325.315 and unscaled median absolute deviation is 15.000. The range is 0.010 to 21,095.620; P95 is 245.998 and P99 is 1,282.880. The modal value(s), up to ten, are 9.990; there are 1 tied modes, each representing 1.73% of valid observations. Moment skewness is 16.283, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 540.181; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.444. In the figure, the linear histogram ends at P99 and explicitly leaves 468 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. These summaries describe observed, valid crawl-time USD prices only. Missing prices are excluded without imputation. Their distribution cannot be assumed to represent all products or prices at review time; zero, if observed, remains a recorded value rather than an imputed price.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 46,726 | 86.480 | 26.990 | 325.315 | 14.990 | 58.130 | 43.140 | 1,282.880 | 21,095.620 | 16.283 | 540.181 |

![Product price at crawl time](figures/meta_Appliances__price.png)

#### title_characters: Product title length

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 93.000 Unicode characters and the mean is 101.399. The middle half lies between 53.000 and 146.000 (IQR 93.000); population SD is 53.908 and unscaled median absolute deviation is 45.000. The range is 0.000 to 748.000; P95 is 194.000 and P99 is 200.000. The modal value(s), up to ten, are 42; there are 1 tied modes, each representing 1.19% of valid observations. Moment skewness is 0.372, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is -0.588; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.140. There is an observed mass at zero: 9 observations (0.01%). In the figure, the linear histogram ends at P99 and explicitly leaves 309 observations (0.33%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 101.399 | 93.000 | 53.908 | 53.000 | 146.000 | 93.000 | 200.000 | 748.000 | 0.372 | -0.588 |

![Product title length](figures/meta_Appliances__title_characters.png)

#### features_count: Product feature entries

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 4.000 array entries and the mean is 3.558. The middle half lies between 2.000 and 5.000 (IQR 3.000); population SD is 2.095 and unscaled median absolute deviation is 1.000. The range is 0.000 to 17.000; P95 is 5.000 and P99 is 9.000. The modal value(s), up to ten, are 5; there are 1 tied modes, each representing 45.04% of valid observations. Moment skewness is -0.406, negative (a longer/heavier lower tail by the third-moment measure). Excess kurtosis is -0.085; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -0.333. There is an observed mass at zero: 16,543 observations (17.54%). In the figure, the linear histogram ends at P99 and explicitly leaves 744 observations (0.79%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 3.558 | 4.000 | 2.095 | 2.000 | 5.000 | 3.000 | 9.000 | 17.000 | -0.406 | -0.085 |

![Product feature entries](figures/meta_Appliances__features_count.png)

#### features_characters: Product feature text length

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 232.000 Unicode characters and the mean is 470.070. The middle half lies between 70.500 and 762.000 (IQR 691.500); population SD is 550.723 and unscaled median absolute deviation is 232.000. The range is 0.000 to 5,856.000; P95 is 1,570.000 and P99 is 2,298.740. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 17.54% of valid observations. Moment skewness is 1.636, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 3.241; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.533. There is an observed mass at zero: 16,544 observations (17.54%). In the figure, the linear histogram ends at P99 and explicitly leaves 944 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 470.070 | 232.000 | 550.723 | 70.500 | 762.000 | 691.500 | 2,298.740 | 5,856.000 | 1.636 | 3.241 |

![Product feature text length](figures/meta_Appliances__features_characters.png)

#### description_count: Product description entries

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 1.000 array entries and the mean is 1.876. The middle half lies between 0.000 and 1.000 (IQR 1.000); population SD is 4.249 and unscaled median absolute deviation is 1.000. The range is 0.000 to 118.000; P95 is 8.000 and P99 is 20.000. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 46.19% of valid observations. Moment skewness is 6.765, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 72.034; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -1.000. There is an observed mass at zero: 32,172 observations (34.11%). In the figure, the linear histogram ends at P99 and explicitly leaves 923 observations (0.98%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 1.876 | 1.000 | 4.249 | 0.000 | 1.000 | 1.000 | 20.000 | 118.000 | 6.765 | 72.034 |

![Product description entries](figures/meta_Appliances__description_count.png)

#### description_characters: Product description text length

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 116.000 Unicode characters and the mean is 358.822. The middle half lies between 0.000 and 499.000 (IQR 499.000); population SD is 569.167 and unscaled median absolute deviation is 116.000. The range is 0.000 to 21,321.000; P95 is 1,567.700 and P99 is 1,998.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 34.11% of valid observations. Moment skewness is 5.381, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 93.137; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.535. There is an observed mass at zero: 32,172 observations (34.11%). In the figure, the linear histogram ends at P99 and explicitly leaves 943 observations (1.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. Length measures volume, not sentiment, informativeness or language. Raw HTML, Unicode and whitespace conventions remain; no token model, language filter or text cleaning was applied.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 358.822 | 116.000 | 569.167 | 0.000 | 499.000 | 499.000 | 1,998.000 | 21,321.000 | 5.381 | 93.137 |

![Product description text length](figures/meta_Appliances__description_characters.png)

#### images_count: Product image entries

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 3.000 array entries and the mean is 3.998. The middle half lies between 1.000 and 7.000 (IQR 6.000); population SD is 2.774 and unscaled median absolute deviation is 2.000. The range is 0.000 to 25.000; P95 is 9.000 and P99 is 9.000. The modal value(s), up to ten, are 1; there are 1 tied modes, each representing 32.36% of valid observations. Moment skewness is 0.385, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is -1.064; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.333. There is an observed mass at zero: 1 observations (0.00%). In the figure, the linear histogram ends at P99 and explicitly leaves 276 observations (0.29%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 3.998 | 3.000 | 2.774 | 1.000 | 7.000 | 6.000 | 9.000 | 25.000 | 0.385 | -1.064 |

![Product image entries](figures/meta_Appliances__images_count.png)

#### videos_count: Product video entries

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 0.000 array entries and the mean is 2.123. The middle half lies between 0.000 and 3.000 (IQR 3.000); population SD is 3.492 and unscaled median absolute deviation is 0.000. The range is 0.000 to 10.000; P95 is 10.000 and P99 is 10.000. The modal value(s), up to ten, are 0; there are 1 tied modes, each representing 64.27% of valid observations. Moment skewness is 1.398, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 0.362; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 1.000. There is an observed mass at zero: 60,624 observations (64.27%). In the figure, the linear histogram ends at P99 and explicitly leaves 0 observations (0.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 2.123 | 0.000 | 3.492 | 0.000 | 3.000 | 3.000 | 10.000 | 10.000 | 1.398 | 0.362 |

![Product video entries](figures/meta_Appliances__videos_count.png)

#### categories_count: Category entries

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 4.000 top-level array entries and the mean is 3.320. The middle half lies between 3.000 and 4.000 (IQR 1.000); population SD is 1.056 and unscaled median absolute deviation is 0.000. The range is 0.000 to 5.000; P95 is 4.000 and P99 is 5.000. The modal value(s), up to ten, are 4; there are 1 tied modes, each representing 51.79% of valid observations. Moment skewness is -1.127, negative (a longer/heavier lower tail by the third-moment measure). Excess kurtosis is 1.274; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is -1.000. There is an observed mass at zero: 3,285 observations (3.48%). In the figure, the linear histogram ends at P99 and explicitly leaves 0 observations (0.00%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 3.320 | 4.000 | 1.056 | 3.000 | 4.000 | 1.000 | 5.000 | 5.000 | -1.127 | 1.274 |

![Category entries](figures/meta_Appliances__categories_count.png)

#### details_count: Product detail attributes

The valid population contains 94,327 metadata record observations; 0 are excluded from this metric's denominator. The median is 10.000 dictionary keys and the mean is 10.788. The middle half lies between 7.000 and 14.000 (IQR 7.000); population SD is 5.760 and unscaled median absolute deviation is 3.000. The range is 0.000 to 56.000; P95 is 22.000 and P99 is 27.000. The modal value(s), up to ten, are 10; there are 1 tied modes, each representing 9.66% of valid observations. Moment skewness is 0.792, positive (a longer/heavier upper tail by the third-moment measure). Excess kurtosis is 0.990; this fourth-moment statistic is sensitive to extreme values and is not a normality test. Quartile-based Bowley skewness is 0.143. There is an observed mass at zero: 2,010 observations (2.13%). In the figure, the linear histogram ends at P99 and explicitly leaves 926 observations (0.98%) above its display limit. The log1p histogram and full ECDF retain the entire valid range; the ECDF steps indicate repeated values, and its horizontal stretches indicate gaps. The box describes the middle half, with percentile whiskers P5/P95, so it should not be read as a Tukey outlier rule. This counts container entries or keys, not verified usable content. For example, multiple image sizes inside one entry are not separate images, and a nonempty image list does not prove successful image download.

| Valid n | Mean | Median | SD | Q1 | Q3 | IQR | P99 | Maximum | Skewness | Excess kurtosis |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94,327 | 10.788 | 10.000 | 5.760 | 7.000 | 14.000 | 7.000 | 27.000 | 56.000 | 0.792 | 0.990 |

![Product detail attributes](figures/meta_Appliances__details_count.png)

#### bought_together_count: Recommended bundle entries

No valid values are available. A mean, spread or distribution shape cannot be inferred; the empty-data panel documents this limitation. Missing is not zero.

![Recommended bundle entries](figures/meta_Appliances__bought_together_count.png)

### Exact-duplicate sensitivity

Raw objects: 94,327; retained in the derived exact-unique view: 94,327; extra copies: 0 (0.0000%). Keep first source-line copy of each type-sensitive canonical parsed record; verify canonical equality after SHA-256 candidate lookup; no fuzzy/user/text-only deduplication.

| Metric | Raw valid n | Unique valid n | Raw mean | Unique mean | Median change | Total variation |
| --- | --- | --- | --- | --- | --- | --- |
| price | 46726 | 46726 | 86.48 | 86.48 | 0 | 0 |
| average_rating | 94327 | 94327 | 4.119 | 4.119 | 0 | 0 |
| rating_number | 94327 | 94327 | 136.4 | 136.4 | 0 | 0 |

Total variation ranges from 0 (identical empirical distributions) to 1. It compares normalized frequencies; no significance threshold is assumed. Raw distributions remain the primary descriptive view.

![Deduplication sensitivity](figures/meta_Appliances__dedup_sensitivity.png)

#### main_category: categorical distribution

There are 89,651 valid nonempty observations and 4,676 excluded values. The distribution contains 30 exact observed labels. The most common label is `Tools & Home Improvement`, with 47.622% of valid values. Top-ten share is 99.285%; normalized entropy is 0.385. A large Other bar is an aggregate of many labels, not an actual single label. All label frequencies and both valid/all-row denominators are saved.

| Label (top 12) | Count | % valid | % all objects |
|---|---:|---:|---:|
| Tools & Home Improvement | 42,694 | 47.622 | 45.262 |
| Appliances | 25,572 | 28.524 | 27.110 |
| Amazon Home | 13,915 | 15.521 | 14.752 |
| Industrial & Scientific | 5,521 | 6.158 | 5.853 |
| Automotive | 568 | 0.634 | 0.602 |
| Health & Personal Care | 268 | 0.299 | 0.284 |
| All Electronics | 168 | 0.187 | 0.178 |
| Sports & Outdoors | 124 | 0.138 | 0.131 |
| Grocery | 95 | 0.106 | 0.101 |
| Cell Phones & Accessories | 85 | 0.095 | 0.090 |
| Musical Instruments | 83 | 0.093 | 0.088 |
| Baby | 82 | 0.091 | 0.087 |

![main_category](figures/meta_Appliances__main_category.png)

The file's selected download category and each record's main_category are different concepts. Other labels inside the file are not automatically classification errors.

#### store: categorical distribution

There are 93,411 valid nonempty observations and 916 excluded values. The distribution contains 13,166 exact observed labels. The most common label is `Whirlpool`, with 9.300% of valid values. Top-ten share is 28.891%; normalized entropy is 0.710. A large Other bar is an aggregate of many labels, not an actual single label. All label frequencies and both valid/all-row denominators are saved.

| Label (top 12) | Count | % valid | % all objects |
|---|---:|---:|---:|
| Whirlpool | 8,687 | 9.300 | 9.209 |
| GE | 4,994 | 5.346 | 5.294 |
| FRIGIDAIRE | 2,912 | 3.117 | 3.087 |
| SAMSUNG | 2,245 | 2.403 | 2.380 |
| LG | 1,876 | 2.008 | 1.989 |
| UpStart Components | 1,519 | 1.626 | 1.610 |
| Frigidaire | 1,341 | 1.436 | 1.422 |
| Upstart Battery | 1,305 | 1.397 | 1.383 |
| Supplying Demand | 1,084 | 1.160 | 1.149 |
| ForeverPRO | 1,024 | 1.096 | 1.086 |
| Edgewater Parts | 910 | 0.974 | 0.965 |
| ClimaTek | 833 | 0.892 | 0.883 |

![store](figures/meta_Appliances__store.png)

Store names are unharmonized labels, not guaranteed unique seller identities. The distribution is metadata-record-weighted, not sales-weighted.

## 5. Initial analytical decisions and remaining work

1. Preserve the raw files and this raw-record EDA as the reference. Extra exact copies can influence all review-weighted summaries; the derived exact-unique sensitivity below now quantifies this effect; further preprocessing remains a Phase 2 task.
2. Retain zero votes and empty media containers as observed values. Keep missing prices separate; report valid-price denominators rather than filling with zero or an overall mean.
3. Report median/IQR alongside mean/SD for asymmetric metrics. Log displays improve readability but do not establish lognormality or authorize deletion of large values.
4. Do not drop a review from chronological ordering merely because its body is blank. Use validated parent IDs, ratings and timestamps when the later cohort is built.
5. Preserve rare levels and sparse fields in the evidence. Any pooling, imputation, scaling or language restriction needs a separate justified rule and training-only fitting where applicable.
6. Next tasks remain broader multivariate EDA, leakage-safe cohort/splits, and eventually reproducible preprocessing. This module does not calculate the first-five/next-ten target or demonstrate predictive improvement.

## 6. Code-to-requirement map

| Requirement | Code | Evidence |
|---|---|---|
| Full local scan and denominator control | `scan_file`, `parse_line`, `field_state` | JSON, field_states.csv, terminal |
| Centre, dispersion, empirical shape | `describe`, `quantile` | numeric_summary.csv, numeric figure panels |
| Class/category imbalance | `categorical_summary`, rating_balance in `scan_file` | categorical_frequencies.csv, bars, JSON |
| Product/reviewer concentration | group counters in `scan_file`, `describe` | group distributions, Gini/top-1% share |
| Temporal distribution | `timestamp`, `scan_file`, `plot_time` | temporal_frequencies.csv, annual/monthly figure |
| Appropriate graphics | `plot_numeric`, `plot_categories`, `plot_states`, `plot_time` | figures/*.png and *.svg |
| Interpretation and reproducibility | `interpret_numeric`, `make_report`, `run` | this regenerated report, source snapshot, manifest |

## 7. Re-run and outputs

Install requirements into the active Python environment, then run:

```bash
python -m pip install -r requirements_univariate.txt
python univariate_eda.py
```

Defaults read the four files from `/Users/parsaanvari/Downloads/DataAnalysis` and write to `reports/phase1/univariate` beside the script. Use `--data-dir` and `--output-dir` to change locations. `--max-lines` is for smoke checks and creates partial results. Known output files in the selected directory are replaced on re-run; raw input files are never overwritten. The module regenerates this English report, every chart, `terminal_report.txt`, `univariate_eda.json`, numeric/categorical/field/temporal tables, compressed numeric frequencies and `univariate_eda_executed.py`. The manifest hashes all current run artifacts. Optional comparison with `../quality/quality_audit.json` uses source SHA-256 before comparing object counts. No quality result is invented when that file is absent. Numerical unit tests and full-run evidence checks are documented separately in validation.txt.


## 8. Entry counts versus usable multimodal content

Entry-count metrics only describe array structure. The following evidence comes from the quality audit's validated left join and shared usability contracts. Source hashes, full scan counts, shared-contract version and reference time must match; otherwise no availability claim is imported.

### All_Beauty

| Facet | Available n | Reviews n | Available % |
| --- | --- | --- | --- |
| review_text | 700808 | 701528 | 99.9 |
| review_rating | 701528 | 701528 | 100 |
| review_image_url | 59684 | 701528 | 8.508 |
| timestamp | 701528 | 701528 | 100 |
| user_item_interaction | 701528 | 701528 | 100 |
| metadata | 701528 | 701528 | 100 |
| product_image_url | 701528 | 701528 | 100 |
| price | 185623 | 701528 | 26.46 |
| product_text | 701463 | 701528 | 99.99 |
| any_image_url | 701528 | 701528 | 100 |
| product_features_text | 214970 | 701528 | 30.64 |
| product_description_text | 172894 | 701528 | 24.65 |
### Appliances

| Facet | Available n | Reviews n | Available % |
| --- | --- | --- | --- |
| review_text | 2126540 | 2128605 | 99.9 |
| review_rating | 2128605 | 2128605 | 100 |
| review_image_url | 84949 | 2128605 | 3.991 |
| timestamp | 2128605 | 2128605 | 100 |
| user_item_interaction | 2128605 | 2128605 | 100 |
| metadata | 2128605 | 2128605 | 100 |
| product_image_url | 2128589 | 2128605 | 100 |
| price | 1600259 | 2128605 | 75.18 |
| product_text | 2128601 | 2128605 | 100 |
| any_image_url | 2128589 | 2128605 | 100 |
| product_features_text | 1997578 | 2128605 | 93.84 |
| product_description_text | 1110542 | 2128605 | 52.17 |

Image URL syntax is not image retrieval. Nonblank feature/description content is measured separately from entry count. Snapshot metadata availability does not establish availability at the fifth-review cutoff.
