def score_predictions(preds: dict, truth: dict, all_src_cols: list) -> dict:
    tp = fp = fn = tn = 0
    ranks = []

    for src_col in all_src_cols:
        true_tgt = truth.get(src_col)
        candidates_raw = preds.get(src_col, [])
        candidates = [c for c, _ in candidates_raw]

        if true_tgt is None:
            if candidates:
                fp += 1
            else:
                tn += 1
            continue

        if not candidates:
            fn += 1
            ranks.append(None)
            continue

        if candidates[0] == true_tgt:
            tp += 1
        else:
            fn += 1

        if true_tgt in candidates:
            ranks.append(candidates.index(true_tgt) + 1)
        else:
            ranks.append(None)

    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "ranks": ranks}


def compute_metrics(counts: dict) -> dict:
    tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def compute_rank_metrics(counts: dict) -> dict:
    ranks = counts["ranks"]
    if not ranks:
        return {"mrr": 0.0, "recall_at_3": 0.0}

    reciprocal_ranks = [1 / r if r is not None else 0.0 for r in ranks]
    mrr = sum(reciprocal_ranks) / len(ranks)

    hits_at_3 = sum(1 for r in ranks if r is not None and r <= 3)
    recall_at_3 = hits_at_3 / len(ranks)

    return {"mrr": mrr, "recall_at_3": recall_at_3}

def coverage_and_precision(preds: dict, truth: dict, all_src_cols: list, threshold: float) -> dict:
    above_threshold = []
    correct_above = 0

    for src_col in all_src_cols:
        candidates_raw = preds.get(src_col, [])
        if not candidates_raw:
            continue

        top_col, top_score = candidates_raw[0]
        if top_score >= threshold:
            above_threshold.append(src_col)
            if truth.get(src_col) == top_col:
                correct_above += 1

    coverage = len(above_threshold) / len(all_src_cols) if all_src_cols else 0.0
    precision = correct_above / len(above_threshold) if above_threshold else 0.0

    return {"coverage": coverage, "precision_at_coverage": precision}

if __name__ == "__main__":
    all_cols = ["a", "b", "c", "d"]
    truth = {"a": "x", "b": "y", "c": "z"}

    all_correct = {"a": [("x", 0.9)], "b": [("y", 0.9)], "c": [("z", 0.9)]}
    all_abstain = {"a": [], "b": [], "c": []}
    ranked_preds = {"a": [("q", 0.9), ("x", 0.5)], "b": [("y", 0.9)], "c": [("z", 0.9), ("w", 0.5), ("v", 0.3), ("q", 0.1)]}

    print(score_predictions(all_correct, truth, all_cols))
    print(compute_metrics(score_predictions(all_correct, truth, all_cols)))
    print(compute_rank_metrics(score_predictions(all_correct, truth, all_cols)))
    
    print(score_predictions(all_abstain, truth, all_cols))
    print(compute_metrics(score_predictions(all_abstain, truth, all_cols)))
    print(compute_rank_metrics(score_predictions(all_abstain, truth, all_cols)))

    print(compute_rank_metrics(score_predictions(ranked_preds, truth, all_cols)))
    print(coverage_and_precision(ranked_preds, truth, all_cols, threshold=0.9))