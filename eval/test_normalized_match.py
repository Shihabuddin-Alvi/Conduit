import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from eval.baselines import normalized_match

def test_normalized_match():
    # Test 1: Normal match works (underscores)
    src1 = pd.DataFrame({"AgencyID": [1]})
    tgt1 = pd.DataFrame({"Agency_ID": [1]})
    print("Test 1 - underscore match:")
    print(normalized_match(src1, tgt1))
    print()
    
    src2 = pd.DataFrame({"AgencyID": [1]})
    tgt2 = pd.DataFrame({"prospect_AgencyID": [1]})
    print("Test 2 - prefix breaks:")
    print(normalized_match(src2, tgt2))
    print()
    
    src3 = pd.DataFrame({"userid": [1], "user_id": [2]})
    tgt3 = pd.DataFrame({"user_id": [1], "USERID": [2]})
    print("Test 3 - collision (first kept, second dropped):")
    print(normalized_match(src3, tgt3))
    print()

if __name__ == "__main__":
    test_normalized_match()