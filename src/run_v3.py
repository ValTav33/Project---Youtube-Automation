import os
import sys
import logging
from orchestrator_v3 import V3Orchestrator

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the V3 Pipeline")
    parser.add_argument("--topic", type=str, required=True, help="Topic for the video")
    parser.add_argument("--duration", type=int, default=45, help="Target duration in seconds")
    parser.add_argument("--id", type=str, default="quantum-test-v1", help="Video ID")
    
    args = parser.parse_args()
    
    # Use env var if set, otherwise default to false
    os.environ["MOCK_EXTERNAL_APIS"] = os.getenv("MOCK_EXTERNAL_APIS", "false")
    
    orchestrator = V3Orchestrator()
    manifest = orchestrator.process_generation_phase(args.id, args.topic, args.duration)
    
    if manifest:
        out_path = os.path.join(os.getcwd(), "remotion", "src", "fixtures", f"{args.id}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        import json
        with open(out_path, "w") as f:
            f.write(json.dumps({"manifest": manifest.model_dump()}, indent=2))
        print(f"\n✅ Video manifest successfully generated and saved to {out_path}")
    else:
        print("\n❌ Failed to generate video manifest.")
