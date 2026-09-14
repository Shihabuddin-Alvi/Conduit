# Conduit

Conduit automates schema mapping during database migrations. Legacy-to-cloud migrations require mapping hundreds or thousands of columns from old systems to new cloud targets, a process that typically takes 2 to 12 person-weeks of manual work in spreadsheets.

Conduit generates ranked match candidates for every source column, automatically accepts high-confidence mappings, and routes uncertain ones to a human reviewer for final decision, cutting the manual workload significantly.

## Session 5 — Baseline Evaluation (TPC-DI)

| Baseline | Precision | Recall | F1 | Abstains? |
|---|---|---|---|---|
| Exact match | 1.0 | 0.167 | 0.286 | Yes |
| Normalized match | 1.0 | 0.167 | 0.286 | Yes |
| Jaccard trigram | 1.0 | 0.646 | 0.785 | No |
| Levenshtein ratio | 1.0 | 0.871 | 0.931 | No |

### Dataset Caveat

TPC-DI contains zero unmapped columns; every source column has a correct target. The 1.0 precision across all baselines reflects this property, not matcher quality. Jaccard and Levenshtein never abstain and return top-k candidates regardless of score. On real data with junk columns, this would surface as false positives, which cannot occur here.

### Valentine Matchers on TPC-DI/Unionable/ev

Two matchers from the `valentine` library (v0.3.0) were run on the real TPC-DI / Unionable / `ev` pair (`prospect_horizontal_0_ac3_ev`), 22 source columns, 22 target columns, 22 ground-truth pairs. Same harness, same metric set as Session 5. Source and target column names are heavily abbreviated (`AgencyID` → `gncd`, `LastName` → `lstnm`, `City` → `ct`), which is the corruption style the `ev` filter selects for.

| Matcher | P | R | F1 | Candidates per source | Abstains? |
|---|---|---|---|---|---|
| Cupid | 1.0 | 0.091 | 0.167 | 1 (post-threshold) | Yes (th_accept=0.7) |
| SimilarityFlooding | 1.0 | 1.0 | 1.0 | 22 (full shortlist) | No |

**Cupid** returned a match for 2 of 22 source columns and abstained on the rest. Both matches were correct (`P=1.0`). The low recall reflects Cupid's default acceptance threshold plus the pair's heavy abbreviation — a name-similarity matcher with `th_accept=0.7` has little to work with when `AgencyID` and `gncd` share almost no trigrams.

**SimilarityFlooding** returned a full ranked shortlist of all 22 target columns for every source, with no abstention or truncation. Its top-1 was correct on all 22 sources, giving `F1=1.0`. That number is real but order-sensitive and should not be read as confident separation:

- A control probe permuting target column order across three seeds (`scripts/probe_sf_shuffle.py`, log committed at `scripts/probe_sf_shuffle_output.txt`) reduces tp from 22 to 20–21 of 22.
- The lost top-1 cases are always on semantically adjacent column pairs — `LastName`/`FirstName`, `City`/`State`/`Country`.
- The cause is exact float ties and 1-ULP near-ties in the candidate scores. For example, `LastName`'s true target `lstnm` (`0.07095919324395424`) and the wrong target `frstnm` (`0.07095919324395418`) differ in the final representable float64 digit. Nine unrelated candidates in `LastName`'s list all score the identical value `0.04324226371962908` — direct evidence that structural propagation contributes no separation on a flat, hierarchy-free schema.
- The original ordering's `tp=22` reflects tie-breaking that happened to favor ground truth, not a confident, well-separated match.

Full notes in `eval/reports/similarity_flooding_match_junk_audit.json`. Session 13's margin-as-signal work is the intended long-term response; an adapter-level deterministic tie-break was considered and explicitly not implemented, because it would make failures deterministic without adding real separation.

**Coma** was skipped. Valentine v0.3.0 exposes `Coma` (not `ComaPy`), and `Coma` requires a Java runtime; `java -version` fails on this machine ("Unable to locate a Java Runtime"). The skip is recorded rather than worked around.

**DistributionBased** is the next matcher to wrap; it is the first matcher in this project that consumes column *values* rather than column *names*, so its toy test will exercise the value path explicitly.

### Known Limitations

- Jaccard trigram scores 0.0 for column names under 3 characters, including exact matches.
- Levenshtein uses Ratcliff-Obershelp similarity rather than true edit distance to avoid adding a dependency.
- Normalized match strips only case and underscores, leaving table-name prefixes intact, so it performs identically to exact match on TPC-DI's corrupted `prospect_` prefix.
- SimilarityFlooding produces exact float64 ties and 1-ULP near-ties among unrelated candidates on flat schemas with no foreign keys. Top-1 can flip on column order. Any result from this matcher on a relationless pair should be read alongside the column-order probe (`scripts/probe_sf_shuffle.py`).
- `valentine`'s Cupid pulls `nltk` corpora (wordnet, punkt_tab, omw-1.4, stopwords) on first use. On a cold-start container (e.g. Render free tier), the first request can present as a hang while the download runs. Pre-warm or vendor the corpora in any deploy image.