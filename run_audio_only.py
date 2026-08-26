import asyncio
from src.agents_v3 import AudioDirectorAgent
from src.compiler_v3 import ManifestCompiler
from src.supabase_client import fetch_latest_artifact_of_type

async def main():
    video_id = "nvidia-money-short"
    print(f"Fetching StoryBlueprint for {video_id}...")
    sb_json = fetch_latest_artifact_of_type(video_id, "StoryBlueprint")
    if not sb_json:
        print("Failed to find StoryBlueprint")
        return
    
    from src.contracts_v3 import StoryBlueprint
    script = StoryBlueprint.parse_raw(sb_json["content"])
    
    print("Generating audio with new Voice ID...")
    audio_agent = AudioDirectorAgent()
    audio_plan = audio_agent.generate_audio_plan(video_id, script)
    if not audio_plan:
        print("Failed to generate AudioPlan")
        return
        
    print("Compiling manifest...")
    compiler = ManifestCompiler()
    compiler.compile(video_id)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())
