def score_predictions(preds: dict, truth: dict, all_src_cols: list) -> dict:
    tp = fp = fn = tn = 0
    ranks = []

    for src_col in all_src_cols:
        true_tgt = truth.get(src_col)
        candidates = preds.get(src_col, [])

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

if __name__ == "__main__":
    all_cols = ["a", "b", "c", "d"]
    truth = {"a": "x", "b": "y", "c": "z"}

    all_correct = {"a": ["x"], "b": ["y"], "c": ["z"]}
    all_abstain = {"a": [], "b": [], "c": []}

    print(score_predictions(all_correct, truth, all_cols))
    print(score_predictions(all_abstain, truth, all_cols))