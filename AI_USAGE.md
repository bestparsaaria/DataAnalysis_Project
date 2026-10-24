# AI Assistance Disclosure and Activity Log

**Project:** Early Review Text for Predicting Future Low-Star Review Share  
**Scope:** Track B, Amazon Reviews’23  
**Last updated:** 2026-10-24

## Purpose and disclosure limits

AI assistance has supported research design, explanations, Python code development, evidence interpretation, and documentation. This file distinguishes that assistance from models that might later be part of the research method.

The assistant was accessed through OpenAI ChatGPT/Codex. Exact historical model identifiers, sampling settings, token counts, and costs were not consistently recorded and are **not reported as known**. This is an activity summary, not a verbatim transcript or a complete machine-readable prompt archive. Dates identify documented activities; unknown dates are not invented.

The record covers this contributor’s work and interactions available in this workspace. It does not certify other team members’ AI use or non-use; they must document their own assistance. No formal course approval or independent review is implied.

## Use summary

| Use | Status in the documented work |
|---|---|
| Explain data, observational design, baselines, and leakage | Used. |
| Help formulate the question, scope, and research plan | Used. |
| Generate/revise source/structure audit code and checks | Used; code execution and outputs were recorded. |
| Draft interpretations, reports, and documentation | Used; counts were checked against saved evidence. |
| Assign new sentiment labels to reviews | Not performed. |
| Replace ratings or the future target with AI-generated scores | Not performed. |
| Train/evaluate predictors or demonstrate gains from text | Not performed at this stage. |
| Complete a full quality audit or EDA | Not performed at this stage. |
| Publish to GitHub through AI tools | Not claimed; the user reported updating GitHub. |

The target remains the observed one-/two-star share in reviews 6–15. Generated explanations are not observations, labels, causal evidence, or experimental results.

## Activity record

### A. Early question exploration and learning — exact dates not fully recorded

**Purpose/request summary:** Explore important e-commerce questions answerable with Amazon Reviews’23, compare category scope, and explain Phase 1 in accessible language.

**Inputs:** The user’s course document/screenshots, dataset descriptions, review/metadata sample images, available discussion, and the preference to use existing ratings or votes instead of manually labeling a training set.

**AI contribution:** Proposed candidate questions; discussed problem-led analysis; explained observational versus controlled data, timestamp coverage, and baselines; helped develop the first-five/next-ten product forecast.

**Decisions:** Team scope became All_Beauty, Appliances, Electronics, and Beauty_and_Personal_Care. This contributor’s technical assignment became the first two categories plus metadata. Earlier All_Beauty-only/pilot suggestions remain historical proposals, not the current population.

**Limits:** This entry reconstructs broad activities from available discussion rather than a complete prompt archive. Early proposals are not empirical findings.

### B. Research design and five-phase plan — 2026-10-19

**Purpose/request summary:** Examine comparing RMSE from two lines fitted to five reviews; refine the question, baseline, 14-item card, and Track B roadmap.

**Inputs:** Course requirements, the card-list image, four-category decision, official dataset information, and technical documentation consulted in that design session.

**AI contribution:** Explained why lower fitting error on the same observations does not establish better future prediction. Retained the early trend as a candidate feature, fixed the future-rating target across methods, and separated performance hypotheses from model names. Drafted the initial `PROJECT_CARD.md` and `PROJECT_ROADMAP_FA.md`.

**Validation/human role:** Checked all 14 card items, consistent scope/target, temporal label maturity, and fitting versus prediction error. The user discussed and clarified the design before implementation.

**Limits:** No model training or measured performance. Exact splits and eligible sample sizes remained pending. A roadmap is planned work, not evidence of completed phases.

### C. Initial source/structure audit development — date not separately established

**Purpose/request summary:** Improve the user’s initial script for the first two Phase 1 requirements, including both review/meta pairs.

**Inputs/tools:** User code and outputs, local files, Python/SQLite standard-library execution, and official dataset/collection references for provenance.

**AI contribution:** Developed streaming JSONL inspection, separate review/metadata schemas, raw-type counts, explicit timestamp units, exact SQLite identifier counts, nested summaries, metadata uniqueness, join cardinality/coverage, cross-category overlap, fingerprints, and JSON/CSV output.

**Validation:** The existing development record reports six initial synthetic checks, later expanded to eight. These test code behavior on small cases; they do not certify absence of real-data quality issues. Local full-file runs were recorded separately from display-only result generation.

**Limits:** Raw data were not cleaned or altered. Structural auditing does not remove duplicates, verify every numeric range, establish complete historical coverage, or retrieve every media URL. Provenance descriptions came from documentation, not inference from file contents. Unknown download facts were not fabricated.

### D. Explicit local inputs and complete terminal output — 2026-10-20

**Purpose/request summary:** Use the contributor’s local paths for all four files and display source/structure results both in the terminal and saved files.

**AI contribution:** Added explicit `DATA_DIR`/`DATASETS`, a stable absolute output location, a complete saved terminal transcript, and an output-path listing.

**Validation:** The development record reports eight successful regression checks, including configured input paths and agreement between displayed/saved output. Earlier stored results could also be rendered without rescanning raw files; this was distinguished from a fresh audit.

**Limits:** A display change is not a new data scan. Entry F identifies the final saved execution used for English reporting.

### E. Persian interpretation of audit evidence — 2026-10-20

**Purpose/request summary:** Explain terminal findings against the two provenance/structure requirements.

**AI contribution:** Drafted `INTERPRETATION_FA.md` and `INTERPRETATION_DETAILS_FA.md`. Distinguished measured results, documented provenance, and uncertainty; explained review/product/media denominators, empty containers, absent keys, and null values.

**Checks:** The earlier pasted excerpt contained 423 nested-field rows matching saved evidence, along with both join objects and the recorded code fingerprint. Its missing beginning was disclosed. Field/nested-path coverage and monthly totals were checked.

**Limits:** Interpretation of existing results was not a new scan, cleaning procedure, quality audit, or causal analysis.

### F. Final recorded local execution and English reporting — 2026-10-21

**Human participation:** The user reported running the code and supplied terminal output. Saved evidence records complete scans of the assigned review/meta pairs. The user later stated they had analyzed the code; this log does not turn that statement into independent certification.

**Audit reference:** `2026-10-21T08:31:29.714135+00:00` (UTC).

| Recorded environment property | Value |
|---|---|
| Python | 3.14.8 |
| SQLite | 3.50.4 |
| Platform | macOS-26.5.2-arm64-arm-64bit-Mach-O |
| Executed script SHA-256 | `26031e880032df811690d9a16cee946040370e7eb47a5765fb721ce2dbb0e693` |

**Recorded raw object counts:** 701,528 All_Beauty reviews; 112,590 All_Beauty metadata records; 2,128,605 Appliances reviews; 94,327 Appliances metadata records. Counts were extracted by code and read from saved results, not estimated by a language model.

**Reporting request:** Produce a comprehensive, beginner-readable English report connecting each requirement to code, terminal evidence, interpretation, and limitations.

**AI contribution:** Drafted `SOURCE_AND_STRUCTURE_REPORT_EN.md` and its detailed appendix, preserved the exact executed source/output package, prepared `evidence_integrity.json`, and reviewed official provenance references. Matched the executed source hash rather than assuming a differently formatted working copy was identical.

**Evidence checks:**

- All 449 nested-field rows in the newer attachment matched the complete JSON. This was a different excerpt from Entry E’s 423-row attachment.
- Both pasted join objects matched saved results.
- Source, mapping, and temporal terminal blocks matched structured results for all four local files.
- Record-width distributions and monthly counts reconciled with object totals.
- The appendix covered 50 field profiles, 1,661 nested paths, and 507 monthly rows.
- The generated report’s 164 local file links and line bounds were checked.

**Working-copy evidence locations:** `reports/phase1/source_structure_report_en/` holds the frozen reporting package; `reports/phase1/source_structure/` holds original audit artifacts. These are local working-copy locations, not a claim that all files were uploaded. Repository reorganization must retain valid links and evidence associations.

**Limits:** English reporting did not rerun the raw-file audit. Matching outputs/hashes do not prove complete collection or universal semantic correctness. No eligible predictive sample size, accuracy, or causal effect was measured.

### G. Repository review and documentation update — 2026-10-24

**Purpose/request summary:** Assess the repository screenshot, suggest improvements, supply commit messages for the JSON artifacts, and prepare complete project-card/AI-use files for publication.

**Inputs:** User screenshot, existing card/log/roadmap, discussion history, and frozen audit/report evidence.

**AI contribution:** Recommended README content, portable links, supporting evidence, and execution instructions. Updated `PROJECT_CARD.md` and this file in English, retaining the established design while separating completed two-category work from the four-category plan. Prepared separate English commit titles/descriptions for the two JSON files.

**Validation:** Checked all 14 card sections, question/target/baseline consistency, category responsibilities, saved raw counts, and completed/planned distinctions. No new raw-file audit or training was needed.

**Limits:** A screenshot does not verify remote file contents. This activity did not push commits, upload files, or certify equality of the live repository and working copy. Previously generated local absolute links require correction for GitHub readers.

## Evidence, privacy, and reproducibility practices

- Raw files remain unchanged; derived outputs are separate. Local paths in evidence are not portable execution instructions.
- `source_structure.json` retains measured structures, counts, relationships, settings, and runtime. `provenance_manifest.json` retains source context and fingerprints. Neither establishes unknown download dates or full Amazon coverage.
- The record does not document sending entire raw datasets to a separate LLM inference service. The assistant used screenshots, pasted output, local execution, and saved artifacts. This does not imply individual LLM reading of every review or guarantee that no data appeared in the assistant context.
- Researchers must review generated methods, code, and prose. AI agreement is not independent scientific validation.
- Preserve the source corresponding to each execution. After edits, record a new code fingerprint/commit; do not represent an old result as a rerun of changed code.
- Before publication, check linked-file availability, remove unnecessary personal information from examples, and observe redistribution terms.

## Record required for future assistance

Add a dated entry for each new use: contributor, task, tool/model as actually known, input material, prompt or archived-prompt reference, output, human edits, validation, and limitations. Mark unavailable historical details rather than guessing.

If an LLM becomes a research component, additionally record:

1. Exact provider, model/version, execution dates, and access method.
2. Complete system/user prompts and example-selection rules.
3. Decoding settings, preprocessing, chunking, retries, and caching.
4. Data partitions, contamination checks, and historical-availability assumptions.
5. Sample/human validation, error analysis, and a non-LLM comparator.
6. Measurable tokens, cost, runtime, and reproducibility limits.
7. How outputs enter analysis without replacing observed ground truth silently.

This is a continuation requirement, not a claim that those LLM experiments have occurred.
