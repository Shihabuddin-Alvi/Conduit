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
    return result

def normalized_match(src: pd.DataFrame, tgt: pd.DataFrame) -> dict[str, list[tuple[str, float]]]:
    """
    Normalized string match on column names.
    Lowercases and strips underscores before comparing.
    Returns 1.0 for normalized matches, no candidates otherwise.
    """
    def normalize(name: str) -> str:
        return name.lower().replace("_", "")
    
    src_cols = list(src.columns)
    tgt_cols = list(tgt.columns)
    
    # Build lookup: normalized_target_name -> original_target_name
    # Note: If multiple target columns normalize to the same string, only the first
    # encountered is kept; later collisions are dropped. This is intentional for
    # a deterministic floor baseline, but means some true matches may be impossible.
    tgt_lookup = {}
    for tgt_col in tgt_cols:
        norm = normalize(tgt_col)
        if norm not in tgt_lookup:
            tgt_lookup[norm] = tgt_col
    
    result = {}
    for src_col in src_cols:
        norm = normalize(src_col)
        if norm in tgt_lookup:
            result[src_col] = [(tgt_lookup[norm], 1.0)]
    
    return result