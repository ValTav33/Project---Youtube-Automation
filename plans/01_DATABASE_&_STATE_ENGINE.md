# Plan 01: Database & State Engine (Supabase)

## Status: ✅ COMPLETED & ACTIVE

### 1. Database Configuration
- **Supabase Project:** `YouTube Automation` (`wrowkhhwlvmigvyescdv`)
- **Region:** `eu-central-1`
- **Host:** `db.wrowkhhwlvmigvyescdv.supabase.co`

---

### 2. Schema Applied

```sql
-- Pipeline Enums
CREATE TYPE video_status AS ENUM (
  'discovered', 'approved', 'scripting', 'scripted', 
  'audio_ready', 'rendering', 'rendered', 'uploaded', 'failed'
);

-- Monitored Competitor Channels Table
CREATE TABLE monitored_channels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id TEXT UNIQUE NOT NULL,
  channel_name TEXT NOT NULL,
  subscriber_count BIGINT DEFAULT 0,
  median_views BIGINT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Production Video Queue Table
CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type TEXT CHECK (source_type IN ('outlier_scraped', 'manual_telegram')),
  source_video_id TEXT,
  target_title TEXT NOT NULL,
  topic_premise TEXT NOT NULL,
  status video_status DEFAULT 'discovered',
  
  -- Narrative & Scene Data
  script_payload JSONB,
  audio_url TEXT,
  transcript_timestamps JSONB,
  rendered_video_url TEXT,
  thumbnail_urls TEXT[],
  
  -- YouTube Publishing Metadata
  youtube_video_id TEXT,
  error_log TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### 3. Storage Buckets Initialized
- `audio`: Stores generated ElevenLabs `.mp3` narration voiceovers.
- `rendered-videos`: Stores final rendered `.mp4` 1080p documentary videos.
- `thumbnails`: Stores Fal.ai generated 16:9 `.jpg` / `.png` thumbnail candidates.
- `background-music`: Stores royalty-free ambient audio tracks.

---

### 4. Security & Policies
- Row Level Security (RLS) is enabled on all tables.
- `service_role` has full read/write access.
- Public read access is enabled on all storage buckets.
