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

def jaccard_trigram_match(src: pd.DataFrame, tgt: pd.DataFrame, top_k: int = 5) -> dict[str, list[tuple[str, float]]]:
    """
    Jaccard similarity on character trigrams.
    Returns top-k target columns sorted descending by score for each source column.
    """
    def get_trigrams(s: str) -> set[str]:
        s = s.lower()
        if len(s) < 3:
            return set()
        return {s[i:i+3] for i in range(len(s) - 2)}
    
    src_cols = list(src.columns)
    tgt_cols = list(tgt.columns)
    
    # Precompute trigrams for all target columns
    tgt_trigrams = {col: get_trigrams(col) for col in tgt_cols}
    
    result = {}
    for src_col in src_cols:
        src_tri = get_trigrams(src_col)
        scores = []
        
        for tgt_col in tgt_cols:
            tgt_tri = tgt_trigrams[tgt_col]
            
            # Jaccard: intersection / union
            if not src_tri and not tgt_tri:
                score = 0.0
            elif not src_tri or not tgt_tri:
                score = 0.0
            else:
                inter = len(src_tri & tgt_tri)
                union = len(src_tri | tgt_tri)
                score = inter / union if union > 0 else 0.0
            
            scores.append((tgt_col, score))
        
        # Sort descending by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Keep top-k (or all if fewer)
        result[src_col] = scores[:top_k]
    
    return result