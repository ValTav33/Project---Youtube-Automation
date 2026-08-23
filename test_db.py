import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
res = sb.table("videos").select("status").eq("id", "483cd459-5e09-42d7-aacf-f132387ed545").execute()
print(res.data)
