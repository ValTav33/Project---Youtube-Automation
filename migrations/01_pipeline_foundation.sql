-- 01_pipeline_foundation.sql
-- Migration to support the new artifact-driven pipeline architecture.

-- 1. Artifacts Table
-- Stores all versioned JSON outputs (PromiseContract, StoryScript, etc.)
CREATE TABLE IF NOT EXISTS public.artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    schema_version TEXT DEFAULT '1.0.0',
    revision INTEGER DEFAULT 1,
    payload JSONB NOT NULL,
    parent_artifact_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by TEXT DEFAULT 'system',
    UNIQUE (video_id, artifact_type, revision)
);

-- 2. Pipeline Runs Table
-- Tracks execution attempts of each stage for idempotency and debugging.
CREATE TABLE IF NOT EXISTS public.pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    stage_name TEXT NOT NULL,
    attempt INTEGER DEFAULT 1,
    status TEXT NOT NULL, -- e.g., 'running', 'success', 'failed'
    input_artifact_ids UUID[] DEFAULT '{}',
    output_artifact_id UUID REFERENCES public.artifacts(id) ON DELETE SET NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    error_log TEXT,
    api_cost_estimate NUMERIC(10, 4) DEFAULT 0.0,
    UNIQUE (video_id, stage_name, attempt)
);

-- 3. Pipeline Events Table
-- Append-only log for granular progress tracking and diagnostics.
CREATE TABLE IF NOT EXISTS public.pipeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    run_id UUID REFERENCES public.pipeline_runs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- e.g., 'progress', 'warning', 'info'
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Approvals Table
-- Captures human decisions (Telegram or Dashboard).
CREATE TABLE IF NOT EXISTS public.approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    artifact_id UUID REFERENCES public.artifacts(id) ON DELETE CASCADE,
    decision TEXT NOT NULL, -- e.g., 'approved', 'rejected', 'regenerate'
    notes TEXT,
    decided_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Assets Table
-- Catalog for media (stock video, generated images, audio).
CREATE TABLE IF NOT EXISTS public.assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES public.videos(id) ON DELETE SET NULL,
    provider TEXT NOT NULL, -- e.g., 'pexels', 'fal'
    source_url TEXT,
    storage_url TEXT NOT NULL,
    media_type TEXT NOT NULL, -- e.g., 'video', 'image', 'audio'
    duration_seconds NUMERIC(10, 3),
    width INTEGER,
    height INTEGER,
    license_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add some useful indexes
CREATE INDEX IF NOT EXISTS idx_artifacts_video_type ON public.artifacts(video_id, artifact_type);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_video ON public.pipeline_runs(video_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_run ON public.pipeline_events(run_id);
