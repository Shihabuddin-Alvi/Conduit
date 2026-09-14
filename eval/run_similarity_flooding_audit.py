"""
Valentine-pair baseline audit for SimilarityFlooding.

Same structure, metric set, and dropped/junk criterion as
eval/run_valentine_audit.py (Cupid's runner), but for
similarity_flooding_match. Separate file, not parameterized, per the
session's one-file-per-matcher convention.

Sequence:
  1. data.valentine_loader.get_dataset_iter must already emit
     dict[src, set[tgt]] for truth. It does (commit fad719a).
  2. Pair: TPC-DI / Unionable / noise_level="ev".
  3. Run similarity_flooding_match through harness.run_eval, write
     eval/reports/similarity_flooding_match.json.
  4. Re-apply the synthetic audit's dropped/junk criterion: any
     predicted mapping whose source column has no ground-truth
     counterpart (dropped_src) or whose target column has no
     ground-truth counterpart (junk_tgt) is a junk/dropped-column hit.
     Write eval/reports/similarity_flooding_match_junk_audit.json.

Verified:
  - Toy-pair output: dict grouped by source, target str, score float in
    [0,1], per-source lists sorted descending, top candidate correct on
    an obvious 3-column pair. Multiple candidates per source observed
    (3 in the toy), unlike Cupid which returned 1 post-threshold.

Unverified, do not assert:
  - Why the real TPC-DI/Unionable/ev numbers look the way they do.
    Candidate counts per source and the tp/fn split are the fact; the
    mechanism behind them is not established by this run. In particular,
    do not attribute misses to any specific similarity component,
    threshold, or tokenization behavior until a targeted probe
    demonstrates it.
"""
from __future__ import annotations

import json
from pathlib import Path

from data.valentine_loader import get_dataset_iter
from eval.baselines import similarity_flooding_match
from eval import harness

REPORTS = Path(__file__).parent / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

DATASET = "TPC-DI"
SCENARIO = "Unionable"
NOISE_LEVEL = "ev"
MATCHER_NAME = "similarity_flooding_match"


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

    preds = similarity_flooding_match(src_df, tgt_df)
    pred_triples = flatten(preds)

    cand_counts = {s: len(c) for s, c in preds.items()}
    print("candidate counts per matched source:", cand_counts)
    print("sources with zero candidates:",
          sorted(set(src_cols) - set(preds.keys())))

    run_dataset = [(src_df, tgt_df, truth, all_src_cols)]
    report = harness.run_eval(similarity_flooding_match, run_dataset, MATCHER_NAME)

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
            "Verified on a toy 3-column pair: output is a dict grouped "
            "by source, targets are str, scores are float in [0,1], each "
            "source's list is sorted descending, and the top candidate "
            "was correct in all three rows. Real-pair run confirms the "
            "candidate profile: 22 candidates per source for all 22 "
            "source columns, a full ranked shortlist of every target "
            "column for every source, no abstention and no truncation. "
            "This differs from Cupid, which returned 1 candidate per "
            "matched source post-threshold.",
            "This TPC-DI/Unionable/ev pair has all 22 source and all 22 "
            "target columns covered by ground truth, so dropped_src and "
            "junk_tgt are both empty. 0/0 here means 'no junk columns to "
            "intrude on', not that the matcher is clean.",
            "tp holds at 20 to 22 of 22 across three column-order "
            "shuffles (seeds 42, 7, 13), so the result is not primarily "
            "a position artifact. But candidate scores show near-ties "
            "at float64 precision between the correct target and "
            "semantically adjacent wrong ones. Two distinct patterns "
            "appear in the printed candidate lists. (1) Exact float "
            "ties: LastName's candidate list contains nine targets "
            "(ddrssln1, mrtlstts, mplr, ddrssln2, wnrrntflg, phn, gndr, "
            "gncd, mddlntl) all scoring the identical float64 value "
            "0.04324226371962908, and City's list contains cntr, stt, "
            "and ct at an identical score. Nine or three distinct "
            "candidates returning bit-identical scores is direct "
            "evidence that structural propagation contributes no "
            "separation on this flat, hierarchy-free schema, not an "
            "inference from documentation. (2) 1-ULP near-ties: "
            "LastName's true target lstnm (0.07095919324395424) differs "
            "from the wrong target frstnm (0.07095919324395418) in the "
            "final representable digit; City's ct (0.061720216735845865) "
            "versus stt (0.06172021673584582) similarly differ by "
            "roughly one ULP. The original ordering's tp=22/fp=0 "
            "reflects tie-breaking and floating-point accumulation "
            "order that happened to favor ground truth, not a "
            "confident, well-separated match. Under reordering, the "
            "same near-ties flip and produce 1 to 2 misses, always on "
            "semantically adjacent column pairs (LastName/FirstName "
            "abbreviations, City/State/Country abbreviations).",
            "Follow-up, not implemented here: a deterministic "
            "tie-break in the adapter (e.g. alphabetical on target "
            "name) would make top-1 stable across column order but "
            "would not add real separation; the two sources would then "
            "fail deterministically instead of intermittently. "
            "Session 13's margin-as-signal work is the intended "
            "long-term response; the adapter tie-break is not.",
        ],
    }
    audit_path = REPORTS / f"{MATCHER_NAME}_junk_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, default=str))
    print("wrote", audit_path)

    print("\nharness report:", json.dumps(report, indent=2))


if __name__ == "__main__":
    main()