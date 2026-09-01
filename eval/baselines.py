import pandas as pd


def exact_match(src: pd.DataFrame, tgt: pd.DataFrame) -> dict[str, list[tuple[str, float]]]:
    """
    Exact string match on column names.
    Returns 1.0 for exact matches, no candidates otherwise.
    """
    src_cols = list(src.columns)
    tgt_cols = list(tgt.columns)
    tgt_set = set(tgt_cols)

    result = {}
    for src_col in src_cols:
        if src_col in tgt_set:
            result[src_col] = [(src_col, 1.0)]
        # else: abstain (no candidate)

    return result