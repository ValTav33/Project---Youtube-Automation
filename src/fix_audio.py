import json
import asyncio
from audio_generator import generate_speech_with_timestamps
import math
import os

async def main():
    json_path = 'remotion/src/fixtures/nvidia-money-short.json'
    with open(json_path) as f:
        d = json.load(f)
    
    manifest = d['manifest']
    words = [w['word'] for w in manifest['word_timestamps']]
    script = " ".join(words)
    
    print("Generating audio with new Voice ID...")
    audio_bytes, new_words, total_duration = generate_speech_with_timestamps(script)
    
    print(f"New duration: {total_duration}")
    total_frames = math.ceil(total_duration * manifest['fps'])
    
    manifest['total_frames'] = max(total_frames, 30)
    manifest['word_timestamps'] = new_words
    
    audio_track = next((t for t in manifest['audio_tracks'] if t['audio_type'] == 'narration'), None)
    if audio_track:
        audio_track['duration_frames'] = total_frames
        
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv()
        
        audio_url = "nvidia-money-brad.mp3"
        sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        sb.storage.from_("audio").upload(f"{audio_url}", audio_bytes, file_options={"content-type": "audio/mpeg", "upsert": "true"})
        
        audio_track['asset_url'] = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/audio/{audio_url}"
    
    with open(json_path, 'w') as f:
        json.dump(d, f)
    
    print("Manifest updated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
