import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class PairLoadError(Exception):
    """Raised when a pair directory is missing files or has a malformed mapping."""


@dataclass
class PairMetadata:
    dataset: str
    scenario: str
    pair_name: str
    n_source_cols: int
    n_target_cols: int


def list_pairs(dataset: str, scenario: str, base_path: Optional[Path] = None) -> List[Path]:
    base_path = (base_path or Path(__file__).parent / "valentine_raw" / "Valentine-datasets") / dataset / scenario
    if not base_path.exists():
        raise FileNotFoundError(f"Path not found: {base_path}")
    return [p for p in base_path.iterdir() if p.is_dir()]


def load_pair(pair_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, List[Tuple[str, str]]]:
    pair_name = pair_dir.name
    source_path = pair_dir / f"{pair_name}_source.csv"
    target_path = pair_dir / f"{pair_name}_target.csv"
    mapping_path = pair_dir / f"{pair_name}_mapping.json"

    for path in (source_path, target_path, mapping_path):
        if not path.exists():
            raise PairLoadError(f"Missing file for pair '{pair_name}': {path}")

    source_df = pd.read_csv(source_path)
    target_df = pd.read_csv(target_path)
    mapping_data = json.loads(mapping_path.read_text())

    matches = mapping_data.get("matches")
    if matches is None:
        raise PairLoadError(f"Mapping file for '{pair_name}' has no 'matches' key: {mapping_path}")

    try:
        ground_truth_pairs = [(m["source_column"], m["target_column"]) for m in matches]
    except KeyError as e:
        raise PairLoadError(f"Malformed match entry in '{pair_name}': missing key {e}") from e

    return source_df, target_df, ground_truth_pairs


def load_dataset(dataset: str, scenario: str, base_path: Optional[Path] = None) -> Iterator[Tuple]:
    for pair_dir in list_pairs(dataset, scenario, base_path):
        try:
            source_df, target_df, ground_truth_pairs = load_pair(pair_dir)
        except (PairLoadError, pd.errors.ParserError) as e:
            logger.warning("Skipping pair %s: %s", pair_dir.name, e)
            continue

        metadata = PairMetadata(
            dataset=dataset,
            scenario=scenario,
            pair_name=pair_dir.name,
            n_source_cols=len(source_df.columns),
            n_target_cols=len(target_df.columns),
        )
        yield source_df, target_df, ground_truth_pairs, metadata