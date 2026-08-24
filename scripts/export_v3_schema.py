#!/usr/bin/env python3
import os
import sys
import json
import argparse

sys.path.append(os.path.join(os.getcwd(), 'src'))
from contracts_v3 import ProductionManifest

SCHEMA_PATH = os.path.join(os.getcwd(), 'remotion', 'schema.json')

def generate_schema() -> dict:
    return ProductionManifest.model_json_schema()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check if schema matches existing file without overwriting")
    args = parser.parse_args()

    schema_dict = generate_schema()
    # Pydantic 2.x JSON schema generation
    
    if args.check:
        if not os.path.exists(SCHEMA_PATH):
            print(f"❌ Schema file {SCHEMA_PATH} does not exist. Run without --check to generate it.")
            sys.exit(1)
            
        with open(SCHEMA_PATH, 'r') as f:
            existing = json.load(f)
            
        if existing != schema_dict:
            print("❌ Schema mismatch! The Pydantic contracts have changed.")
            print("Run `make schema` to update the JSON schema.")
            sys.exit(1)
            
        print("✅ Schema matches.")
        sys.exit(0)
    
    # Write mode
    os.makedirs(os.path.dirname(SCHEMA_PATH), exist_ok=True)
    with open(SCHEMA_PATH, 'w') as f:
        json.dump(schema_dict, f, indent=2)
    print(f"✅ Generated schema and saved to {SCHEMA_PATH}")

if __name__ == "__main__":
    main()
