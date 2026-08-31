import json
from pathlib import Path

from eval.metrics import score_predictions, compute_metrics, compute_rank_metrics


def aggregate(rows: list) -> dict:
    total = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "ranks": []}
    for row in rows:
        total["tp"] += row["tp"]
        total["fp"] += row["fp"]
        total["fn"] += row["fn"]
        total["tn"] += row["tn"]
        total["ranks"].extend(row["ranks"])

    metrics = compute_metrics(total)
    rank_metrics = compute_rank_metrics(total)

    return {**total, **metrics, **rank_metrics}

def run_eval(matcher_fn, dataset_iter, name: str) -> dict:
    rows = []
    for src, tgt, truth, all_src_cols in dataset_iter:
        preds = matcher_fn(src, tgt)
        rows.append(score_predictions(preds, truth, all_src_cols))

    report = aggregate(rows)

    report_path = Path(f"eval/reports/{name}.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report

if __name__ == "__main__":
    all_cols = ["a", "b", "c", "d"]
    truth = {"a": "x", "b": "y", "c": "z"}

    def random_matcher(src, tgt):
        return {"a": [("w", 0.9)], "b": [("v", 0.9)], "c": [("u", 0.9)]}

    def ground_truth_matcher(src, tgt):
        return {"a": [("x", 0.9)], "b": [("y", 0.9)], "c": [("z", 0.9)]}

    dataset = [(None, None, truth, all_cols)]

    random_report = run_eval(random_matcher, dataset, "test_random")
    print("random:", random_report["f1"])

    gt_report = run_eval(ground_truth_matcher, dataset, "test_ground_truth")
    print("ground truth:", gt_report["f1"])
