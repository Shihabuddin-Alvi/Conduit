Schema matching means figuring out where each column from an old database should go in a new cloud database during a migration.
For enterprises, this can be a major bottleneck, as consultants often have to manually map 300 to 2,000 columns in spreadsheets, which can take 2 to 12 person-weeks.
Conduit makes this process faster by suggesting the most likely matches, automatically accepting high-confidence matches, and sending the uncertain ones to a human for review.


## Session 5 — Trivial baselines (TPC-DI, Unionable, noisy)

| Baseline | Precision | Recall | F1 | Abstains? |
|---|---|---|---|---|
| Exact match | 1.0 | 0.167 | 0.286 | Yes |
| Normalized match | 1.0 | 0.167 | 0.286 | Yes |
| Jaccard trigram | 1.0 | 0.646 | 0.785 | No |
| Levenshtein ratio | 1.0 | 0.871 | 0.931 | No |

**Caveat:** this dataset has zero unmapped source columns, every source column has a correct target. Precision 1.0 across all four baselines reflects that property of the data, not matcher quality. Jaccard and Levenshtein never abstain, they always return top-k candidates even at low scores; on a dataset with junk columns this would show up as false positives, but it can't here because there are none to guess wrong on.

**Known limitations:**
- Jaccard trigram scores 0.0 for any column name under 3 characters, including against its own exact match, since trigram sets need length ≥3 to have signal.
- Levenshtein ratio here is difflib's Ratcliff-Obershelp similarity, not true edit distance. Chosen to avoid a new dependency; documented in code.
- Normalized match strips case and underscores only, it does not remove substrings like table-name prefixes, so it performs identically to exact match on TPC-DI's `prospect_` corruption.