import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from eval.baselines import levenshtein_ratio_match

def test_levenshtein():
    # Test 1: Prefix case (AgencyID vs prospect_AgencyID)
    src1 = pd.DataFrame({"AgencyID": [1]})
    tgt1 = pd.DataFrame({"prospect_AgencyID": [1], "RandomCol": [1]})
    print("Test 1 - prefix case:")
    print(levenshtein_ratio_match(src1, tgt1, top_k=2))
    print()
    
    # Test 2: Completely unrelated strings
    src2 = pd.DataFrame({"AgencyID": [1]})
    tgt2 = pd.DataFrame({"XYZ123": [1], "ABC": [1]})
    print("Test 2 - completely unrelated:")
    print(levenshtein_ratio_match(src2, tgt2, top_k=2))
    print()
    
    # Test 3: Short string ("id" vs "identifier" and "ID")
    src3 = pd.DataFrame({"id": [1]})
    tgt3 = pd.DataFrame({"identifier": [1], "ID": [1]})
    print("Test 3 - short string 'id':")
    print(levenshtein_ratio_match(src3, tgt3, top_k=2))
    print()

if __name__ == "__main__":
    test_levenshtein()