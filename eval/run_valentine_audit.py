"""
Valentine-pair baseline audit for Cupid.

Same structure and metric set as eval/run_baseline_audit.py's synthetic
audit, but sources the pair from data.valentine_loader instead of
data.synth.generate_legacy_pair.

Sequence:
  1. data/valentine_loader.get_dataset_iter must already emit
     dict[src, set[tgt]] for truth (see loader commit). If it does not,
     this audit reproduces the substring-membership bug in
     score_predictions and produces a silently wrong report.
  2. Pair: TPC-DI / Unionable / noise_level="ev".
  3. Run cupid_match through harness.run_eval, write
     eval/reports/cupid_match.json.
  4. Re-apply the synthetic audit's junk criterion: any predicted
     mapping whose source column has no ground-truth counterpart
     (dropped_src) or whose target column has no ground-truth
     counterpart (junk_tgt) is a junk/dropped-column hit.
     Write eval/reports/cupid_match_junk_audit.json.

Known limitation, do not read the numbers without this:
  Cupid applies an internal acceptance threshold (th_accept, default
  0.7). It returns only pairs that clear that bar, not a ranked
  shortlist per source. On a real pair, many source columns will
  return zero candidates. score_predictions handles that (fn, rank
  None), but MRR and recall_at_3 are structurally thin for Cupid
  because most rows have at most one candidate to rank. A low
  recall_at_3 here reflects the wrapped algorithm, not a harness bug.

Known limitation, second:
  Per the probe of the first TPC-DI/Unionable/ev pair, all 22 source
  and all 22 target columns are covered by the ground-truth mapping.
  dropped_src and junk_tgt are therefore both empty for that pair,
  and the audit's 0/0 result means "there was nothing to intrude on",
  not "Cupid is clean". This is a property of the pair, not the runner.
"""
from __future__ import annotations

import json
from pathlib import Path

from data.valentine_loader import get_dataset_iter
from eval.baselines import cupid_match
from eval import harness

REPORTS = Path(__file__).parent / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

DATASET = "TPC-DI"
SCENARIO = "Unionable"
NOISE_LEVEL = "ev"
MATCHER_NAME = "cupid_match"


def flatten(pred: dict) -> list:
    return [(s, t, sc) for s, cands in pred.items() for t, sc in cands]


def main() -> None:
    dataset_iter = get_dataset_iter(DATASET, SCENARIO, noise_level=NOISE_LEVEL)

    pairs = list(dataset_iter)
    assert len(pairs) >= 1, "no pairs found for the configured scenario"
    src_df, tgt_df, truth, all_src_cols = pairs[0]
    pair_count = len(pairs)
    print(f"pairs available in iterator: {pair_count}")

    for src, tgt_set in truth.items():
        assert tgt_set, f"truth[{src!r}] is empty; expected at least one target"
        for t in tgt_set:
            assert t is not None, f"truth[{src!r}] contains None"
            assert isinstance(t, str), f"truth[{src!r}] target {t!r} is not str"
        assert isinstance(tgt_set, set), f"truth[{src!r}] is not a set: {type(tgt_set)}"

    src_cols = list(src_df.columns)
    tgt_cols = list(tgt_df.columns)

    covered_src = set(truth.keys())
    covered_tgt = {t for s in truth for t in truth[s]}

    dropped_src = set(src_cols) - covered_src
    junk_tgt = set(tgt_cols) - covered_tgt

    print("source columns  :", src_cols)
    print("target columns  :", tgt_cols)
    print("dropped source  :", sorted(dropped_src))
    print("junk target     :", sorted(junk_tgt))

    assert dropped_src == set(), f"unexpected dropped source cols: {dropped_src}"
    assert junk_tgt == set(), f"unexpected junk target cols: {junk_tgt}"

    preds = cupid_match(src_df, tgt_df)
    pred_triples = flatten(preds)

    run_dataset = [(src_df, tgt_df, truth, all_src_cols)]
    report = harness.run_eval(cupid_match, run_dataset, MATCHER_NAME)

    dropped_src_hits = [(s, t, sc) for (s, t, sc) in pred_triples if s in dropped_src]
    junk_tgt_hits = [(s, t, sc) for (s, t, sc) in pred_triples if t in junk_tgt]

    print(f"dropped-source false mappings ({len(dropped_src_hits)}):")
    for h in dropped_src_hits[:10]:
        print("  ", h)
    print(f"junk-target false mappings ({len(junk_tgt_hits)}):")
    for h in junk_tgt_hits[:10]:
        print("  ", h)

    audit = {
        "baseline": MATCHER_NAME,
        "dataset": DATASET,
        "scenario": SCENARIO,
        "noise_level": NOISE_LEVEL,
        "n_pairs": 1,
        "dropped_source_columns": sorted(dropped_src),
        "junk_target_columns": sorted(junk_tgt),
        "dropped_source_mappings": dropped_src_hits,
        "junk_target_mappings": junk_tgt_hits,
        "n_dropped_source_mappings": len(dropped_src_hits),
        "n_junk_target_mappings": len(junk_tgt_hits),
        "harness_f1": report.get("f1"),
        "notes": [
            "Cupid applies an internal acceptance threshold (th_accept, "
            "default 0.7) and returns only pairs that clear it, not a "
            "ranked shortlist per source. Expect many zero-candidate "
            "source columns on real pairs. MRR and recall_at_3 are "
            "structurally thin for this matcher; low values reflect the "
            "wrapped algorithm, not the harness.",
            "This TPC-DI/Unionable/ev pair has all 22 source and all 22 "
            "target columns covered by ground truth, so dropped_src and "
            "junk_tgt are both empty. 0/0 here means 'no junk columns to "
            "intrude on', not 'Cupid is clean'.",
        ],
    }
    audit_path = REPORTS / f"{MATCHER_NAME}_junk_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, default=str))
    print("wrote", audit_path)

    print("\nharness report:", json.dumps(report, indent=2))


if __name__ == "__main__":
    main()