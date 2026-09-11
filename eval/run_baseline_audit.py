"""
Five-step baseline audit against a synthetic legacy pair.

Step 1  build pair from synth.generate_legacy_pair; snapshot columns/truth/dropped/junk.
Step 2  confirm each baseline matches the (src_df, tgt_df) call signature.
Step 3  run exact_match through the harness; audit dropped/junk columns.
Step 4  repeat for normalized / jaccard_trigram / levenshtein_ratio.
Step 5  write four reports to eval/reports/, plus a junk-audit file per baseline.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pandas as pd

from data.synth import base_schema, generate_legacy_pair
from eval.baselines import (
    exact_match,
    normalized_match,
    jaccard_trigram_match,
    levenshtein_ratio_match,
)
from eval import harness

REPORTS = Path(__file__).parent / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

BASELINES = {
    "exact_match": exact_match,
    "normalized_match": normalized_match,
    "jaccard_trigram_match": jaccard_trigram_match,
    "levenshtein_ratio_match": levenshtein_ratio_match,
}

OPERATORS_LIST = [
    "case_flip", "drop_column", "split_field", "merge_fields",
    "unit_change", "date_format", "abbreviate", "strip_vowels",
    "table_prefix", "add_junk",
]

N_ROWS = 50


def schema_to_df(schema, n_rows: int) -> pd.DataFrame:
    return pd.DataFrame({
        col.name: [col.value_generator() for _ in range(n_rows)]
        for col in schema
    })


def flatten(pred: dict[str, list[tuple[str, float]]]) -> list[tuple[str, str, float]]:
    return [(s, t, sc) for s, cands in pred.items() for t, sc in cands]


def check_signature(fn) -> None:
    params = [
        p for p in inspect.signature(fn).parameters.values()
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    assert len(params) >= 2, f"{fn.__name__}: needs at least (src_df, tgt_df)"


def main() -> None:
    # ---------- Step 1 ----------
    source_schema = base_schema()
    target_schema, ground_truth_pairs = generate_legacy_pair(source_schema, OPERATORS_LIST)

    src_df = schema_to_df(source_schema, N_ROWS)
    tgt_df = schema_to_df(target_schema, N_ROWS)

    src_cols = list(src_df.columns)
    tgt_cols = list(tgt_df.columns)

    # ground_truth_pairs holds real (src, tgt) correspondences, plus
    # (None, tgt) entries marking a target column with no source counterpart,
    # produced by add_junk (LEGACY_FLAG, INTERNAL_CODE, MIGRATION_BATCH).
    real_pairs = [(s, t) for s, t in ground_truth_pairs if s is not None]
    sentinel_junk_tgt = {t for s, t in ground_truth_pairs if s is None}

    covered_src = {s for s, _ in real_pairs}
    covered_tgt = {t for _, t in real_pairs}

    # source columns with no target counterpart: caused by drop_column
    dropped_src = set(src_cols) - covered_src
    # target columns with no source counterpart: caused by add_junk
    junk_tgt = set(tgt_cols) - covered_tgt

    assert junk_tgt == sentinel_junk_tgt, (
        f"mismatch: derived {junk_tgt} vs sentinel {sentinel_junk_tgt}"
    )

    # truth for the metric layer: src -> set of valid targets.
# A set (not str) because split_field produces name -> {CUST_NM1, CUST_NM2}.
    truth_by_src: dict[str, set[str]] = {}
    for s, t in real_pairs:
        truth_by_src.setdefault(s, set()).add(t)
    truth = truth_by_src

    print("source columns  :", src_cols)
    print("target columns  :", tgt_cols)
    print("ground truth    :", truth)
    print("dropped source  :", dropped_src)
    print("junk target     :", junk_tgt)

    # ---------- Step 2 ----------
    for name, fn in BASELINES.items():
        check_signature(fn)
        out = fn(src_df, tgt_df)
        assert isinstance(out, dict), f"{name}: expected dict"
        for v in out.values():
            assert isinstance(v, list)
            for tup in v:
                assert isinstance(tup, tuple) and len(tup) == 2

    # ---------- Steps 3 + 4 ----------
    summary = {}
    for name, fn in BASELINES.items():
        print(f"\n=== {name} ===")

        pred_dict = fn(src_df, tgt_df)
        pred_triples = flatten(pred_dict)

        dataset = [(src_df, tgt_df, truth, src_cols)]
        report = harness.run_eval(fn, dataset, name)

        dropped_src_hits = [(s, t, sc) for (s, t, sc) in pred_triples if s in dropped_src]
        junk_tgt_hits = [(s, t, sc) for (s, t, sc) in pred_triples if t in junk_tgt]

        print(f"dropped-source false mappings ({len(dropped_src_hits)}):")
        for h in dropped_src_hits[:10]:
            print("  ", h)
        print(f"junk-target false mappings ({len(junk_tgt_hits)}):")
        for h in junk_tgt_hits[:10]:
            print("  ", h)

        audit = {
            "baseline": name,
            "dropped_source_columns": sorted(dropped_src),
            "junk_target_columns": sorted(junk_tgt),
            "dropped_source_mappings": dropped_src_hits,
            "junk_target_mappings": junk_tgt_hits,
            "n_dropped_source_mappings": len(dropped_src_hits),
            "n_junk_target_mappings": len(junk_tgt_hits),
            "harness_f1": report.get("f1"),
        }
        audit_path = REPORTS / f"{name}_junk_audit.json"
        audit_path.write_text(json.dumps(audit, indent=2, default=str))
        print("wrote", audit_path)

        summary[name] = {
            "report": str(REPORTS / f"{name}.json"),
            "audit": str(audit_path),
            "n_dropped_source_mappings": len(dropped_src_hits),
            "n_junk_target_mappings": len(junk_tgt_hits),
        }

    (REPORTS / "summary.json").write_text(json.dumps(summary, indent=2))
    print("\nsummary:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()