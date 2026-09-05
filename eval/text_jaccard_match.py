# eval/test_jaccard_match.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.valentine_loader import get_dataset_iter
from eval.harness import run_eval
from eval.baselines import jaccard_trigram_match

if __name__ == "__main__":
    report = run_eval(
        jaccard_trigram_match,
        get_dataset_iter("TPC-DI", "Unionable", noise_level="ev"),
        "jaccard_trigram_smoke",
    )
    print(report)