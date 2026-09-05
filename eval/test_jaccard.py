import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from eval.baselines import jaccard_trigram_match

def test_jaccard():
    # Test 1: Near-identical strings (high overlap)
    src1 = pd.DataFrame({"AgencyID": [1]})
    tgt1 = pd.DataFrame({"Agency_ID": [1], "RandomCol": [1]})
    print("Test 1 - near-identical:")
    print(jaccard_trigram_match(src1, tgt1, top_k=2))
    print()
    
    # Test 2: Completely different strings
    src2 = pd.DataFrame({"AgencyID": [1]})
    tgt2 = pd.DataFrame({"XYZ123": [1], "ABC": [1]})
    print("Test 2 - completely different:")
    print(jaccard_trigram_match(src2, tgt2, top_k=2))
    print()
    
    # Test 3: Short string (< 3 chars)
    src3 = pd.DataFrame({"id": [1]})
    tgt3 = pd.DataFrame({"identifier": [1], "ID": [1]})
    print("Test 3 - short string 'id':")
    print(jaccard_trigram_match(src3, tgt3, top_k=2))
    print()

if __name__ == "__main__":
    test_jaccard()