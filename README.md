# Conduit

Conduit automates schema mapping during database migrations. Legacy-to-cloud migrations require mapping hundreds or thousands of columns from old systems to new cloud targets, a process that typically takes 2 to 12 person-weeks of manual work in spreadsheets.

Conduit generates ranked match candidates for every source column, automatically accepts high-confidence mappings, and routes uncertain ones to a human reviewer for final decision, cutting the manual workload significantly.

## Session 5 — Baseline Evaluation (TPC-DI)

| Baseline | Precision | Recall | F1 | Abstains? |
|----------|-----------|--------|-----|-----------|
| Exact match | 1.0 | 0.167 | 0.286 | Yes |
| Normalized match | 1.0 | 0.167 | 0.286 | Yes |
| Jaccard trigram | 1.0 | 0.646 | 0.785 | No |
| Levenshtein ratio | 1.0 | 0.871 | 0.931 | No |

### Dataset Caveat

TPC-DI contains zero unmapped columns; every source column has a correct target. The 1.0 precision across all baselines reflects this property, not matcher quality. Jaccard and Levenshtein never abstain and return top-k candidates regardless of score. On real data with junk columns, this would surface as false positives, which cannot occur here.

### Known Limitations

- Jaccard trigram scores 0.0 for column names under 3 characters, including exact matches.
- Levenshtein uses Ratcliff-Obershelp similarity rather than true edit distance to avoid adding a dependency.
- Normalized match strips only case and underscores, leaving table-name prefixes intact, so it performs identically to exact match on TPC-DI's corrupted prospect_ prefix.