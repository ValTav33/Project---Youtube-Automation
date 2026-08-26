import json
import asyncio
from src.audio_generator import generate_audio_with_timestamps
import math

async def main():
    with open('src/fixtures/nvidia-money-short.json') as f:
        d = json.load(f)
    
    manifest = d['manifest']
    audio_track = next((t for t in manifest['audio_tracks'] if t['audio_type'] == 'narration'), None)
    words = [w['word'] for w in audio_track['word_timestamps']]
    script = " ".join(words)
    
    print("Generating audio with new Voice ID...")
    audio_bytes, new_words, total_duration = generate_audio_with_timestamps(script)
    
    # Save audio locally
    audio_url = "nvidia-money-brad.mp3"
    with open(f"out/{audio_url}", "wb") as f:
        f.write(audio_bytes)
    
    print(f"New duration: {total_duration}")
    total_frames = math.ceil(total_duration * manifest['fps'])
    
    # Update manifest
    manifest['total_frames'] = max(total_frames, 30)
    audio_track['duration_frames'] = total_frames
    audio_track['word_timestamps'] = new_words
    
    # Actually, we need to upload to Supabase, or we can just point remotion to a local file
    # But let's upload to Supabase to keep it clean.
    from supabase import create_client
    import os
    from dotenv import load_dotenv
    load_dotenv()
    sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    sb.storage.from_("audio").upload(f"{audio_url}", audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"})
    
    audio_track['asset_url'] = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/audio/{audio_url}"
    
    with open('src/fixtures/nvidia-money-short.json', 'w') as f:
        json.dump(d, f)
    
    print("Manifest updated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
