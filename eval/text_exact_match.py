from data.valentine_loader import get_dataset_iter
from eval.harness import run_eval
from eval.baselines import exact_match

if __name__ == "__main__":
    report = run_eval(
        exact_match,
        get_dataset_iter("TPC-DI", "Unionable", noise_level="ev"),
        "exact_match_smoke",
    )
    print(report)
