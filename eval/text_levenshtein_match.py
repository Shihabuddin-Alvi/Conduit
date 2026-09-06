from data.valentine_loader import get_dataset_iter
from eval.harness import run_eval
from eval.baselines import levenshtein_ratio_match

if __name__ == "__main__":
    report = run_eval(
        levenshtein_ratio_match,
        get_dataset_iter("TPC-DI", "Unionable", noise_level="ev"),
        "levenshtein_ratio_smoke",
    )
    print(report)