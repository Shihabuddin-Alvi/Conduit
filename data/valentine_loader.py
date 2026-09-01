from pathlib import Path
from typing import Optional
import json
import pandas as pd


def list_pairs(
    dataset: str,
    scenario: str,
    noise_level: Optional[str] = None,
) -> list:
    base_path = (
        Path(__file__).parent
        / "valentine_raw"
        / "Valentine-datasets"
        / dataset
        / scenario
    )
    pairs = [p for p in base_path.iterdir() if p.is_dir()]
    if noise_level is not None:
        pairs = [p for p in pairs if p.name.endswith(f"_{noise_level}")]
    return pairs

def load_pair(pair_dir: Path) -> tuple:
    pair_name = pair_dir.name
    source_path = pair_dir / f"{pair_name}_source.csv"
    target_path = pair_dir / f"{pair_name}_target.csv"
    mapping_path = pair_dir / f"{pair_name}_mapping.json"

    source_df = pd.read_csv(source_path)
    target_df = pd.read_csv(target_path)
    mapping_data = json.loads(mapping_path.read_text())

    ground_truth_pairs = [
        (m["source_column"], m["target_column"])
        for m in mapping_data["matches"]
    ]

    return source_df, target_df, ground_truth_pairs

def load_dataset(
    dataset: str,
    scenario: str,
    noise_level: Optional[str] = None,
):
    for pair_dir in list_pairs(dataset, scenario, noise_level):
        source_df, target_df, ground_truth_pairs = load_pair(pair_dir)

        metadata = {
            "dataset": dataset,
            "scenario": scenario,
            "pair_name": pair_dir.name,
            "n_source_cols": len(source_df.columns),
            "n_target_cols": len(target_df.columns),
        }

        yield source_df, target_df, ground_truth_pairs, metadata

def get_dataset_iter(
    dataset: str,
    scenario: str,
    noise_level: Optional[str] = None,
):
    for source_df, target_df, ground_truth_pairs, metadata in load_dataset(
        dataset, scenario, noise_level
    ):
        truth = {src: tgt for src, tgt in ground_truth_pairs}
        all_src_cols = list(source_df.columns)

        yield source_df, target_df, truth, all_src_cols

if __name__ == "__main__":
    it = get_dataset_iter("TPC-DI", "Unionable", noise_level="ev")
    src, tgt, truth, all_src_cols = next(it)
    print(len(truth), len(all_src_cols))