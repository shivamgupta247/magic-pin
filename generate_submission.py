import json
import os
from pathlib import Path
from bot_logic import compose

def main():
    dataset_dir = Path("dataset/expanded")
    with open(dataset_dir / "test_pairs.json") as f:
        pairs = json.load(f)["pairs"]
    
    submissions = []
    
    for pair in pairs:
        print(f"Processing {pair['test_id']}...")
        
        # Load contexts
        with open(dataset_dir / f"triggers/{pair['trigger_id']}.json") as f:
            trigger = json.load(f)
            
        with open(dataset_dir / f"merchants/{pair['merchant_id']}.json") as f:
            merchant = json.load(f)
            
        with open(dataset_dir / f"categories/{merchant['category_slug']}.json") as f:
            category = json.load(f)
            
        customer = None
        if pair.get("customer_id"):
            with open(dataset_dir / f"customers/{pair['customer_id']}.json") as f:
                customer = json.load(f)
        
        # Call composer
        result = compose(category, merchant, trigger, customer)
        
        # Add required submission fields
        result["test_id"] = pair["test_id"]
        submissions.append(result)
        
    with open("submission.jsonl", "w") as f:
        for sub in submissions:
            f.write(json.dumps(sub) + "\n")
            
    print("Done generating submission.jsonl")

if __name__ == "__main__":
    main()
