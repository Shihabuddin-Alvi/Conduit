"""
Probe: does SimilarityFlooding's tp=22/fp=0 result on TPC-DI/Unionable/ev
survive a shuffle of the target schema's column order?

Ground truth is keyed by column name, not position, so shuffling target
column order changes nothing about what's "correct." If the matcher is
reading column content/name, results should be identical. If it's
secretly reading position, results should collapse.

Extended: repeated across three seeds to check whether the observed
drop is stable or single-seed noise, and prints which source columns
lose their top-1 match under shuffle and what they resolved to
instead.
"""
import random

from data.valentine_loader import get_dataset_iter
from eval.baselines import similarity_flooding_match
from eval.metrics import score_predictions

it = get_dataset_iter("TPC-DI", "Unionable", noise_level="ev")
src_df, tgt_df, truth, all_src_cols = next(it)

tgt_cols = list(tgt_df.columns)
print("original target order:", tgt_cols)

preds_original = similarity_flooding_match(src_df, tgt_df)
result_original = score_predictions(preds_original, truth, all_src_cols)

print("\n=== ORIGINAL ORDER ===")
print("tp/fp/fn:", result_original["tp"], result_original["fp"], result_original["fn"])
print("ranks:", result_original["ranks"])


def top1(preds, src_col):
    cands = preds.get(src_col, [])
    return cands[0] if cands else None


for seed in (42, 7, 13):
    shuffled_cols = tgt_cols[:]
    random.seed(seed)
    random.shuffle(shuffled_cols)
    tgt_shuffled = tgt_df[shuffled_cols]

    preds_shuffled = similarity_flooding_match(src_df, tgt_shuffled)
    result_shuffled = score_predictions(preds_shuffled, truth, all_src_cols)

    print(f"\n=== SHUFFLE seed={seed} ===")
    print("shuffled target order:", shuffled_cols)
    print("tp/fp/fn:", result_shuffled["tp"], result_shuffled["fp"], result_shuffled["fn"])
    print("ranks:", result_shuffled["ranks"])

    # Which sources lost their top-1 correct match?
    for s in all_src_cols:
        orig_top = top1(preds_original, s)
        shuf_top = top1(preds_shuffled, s)
        orig_correct = orig_top is not None and orig_top[0] in (truth.get(s) or set())
        shuf_correct = shuf_top is not None and shuf_top[0] in (truth.get(s) or set())
        if orig_correct and not shuf_correct:
            print(f"  LOST top-1: {s} | truth={truth.get(s)}")
            print(f"              orig top-1: {orig_top}")
            print(f"              shuf top-1: {shuf_top}")

    # Full candidate list for one representative lost source, if any
    lost = [s for s in all_src_cols
            if (top1(preds_original, s) or (None,))[0] in (truth.get(s) or set())
            and not ((top1(preds_shuffled, s) or (None,))[0] in (truth.get(s) or set()))]
    if lost:
        s = lost[0]
        print(f"  full shuf candidates for {s}: {preds_shuffled.get(s)}")