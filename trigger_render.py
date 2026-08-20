import sys
sys.path.append('src')
from orchestrator import prepare_remotion_props, trigger_remotion_render
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

video_id = '47b043a7-65b7-4238-9e0f-eaf038864640'
res = sb.table('videos').select('*').eq('id', video_id).single().execute()
video = res.data

print("Preparing props...")
props = prepare_remotion_props(video)
print(f"Triggering render for {video_id} with {len(props['scenes'])} scenes.")
success = trigger_remotion_render(video_id, props)
print(f"Triggered: {success}")
