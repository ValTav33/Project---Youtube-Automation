-- 03_analytics.sql
-- Migration to support YouTube analytics ingestion and the learning loop.

-- 1. YouTube Analytics Snapshots
-- Stores point-in-time snapshots of a video's performance metrics.
CREATE TABLE IF NOT EXISTS public.youtube_analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    youtube_video_id TEXT NOT NULL,
    
    -- Basic metrics from YouTube Data API
    views BIGINT DEFAULT 0,
    likes BIGINT DEFAULT 0,
    comments BIGINT DEFAULT 0,
    
    -- Metrics from YouTube Analytics API
    impressions BIGINT DEFAULT 0,
    click_through_rate NUMERIC(5, 2) DEFAULT 0.0,
    average_view_duration INTEGER DEFAULT 0, -- in seconds
    average_percentage_viewed NUMERIC(5, 2) DEFAULT 0.0,
    subscribers_gained INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_video_id ON public.youtube_analytics_snapshots(video_id);

-- 2. Channel Learnings
-- Stores validated rules and findings derived from analyzing the AnalyticsFeatureVector against outcomes.
CREATE TABLE IF NOT EXISTS public.channel_learnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding TEXT NOT NULL,
    sample_size INTEGER NOT NULL,
    confidence_score NUMERIC(5, 2) NOT NULL, -- e.g., 0.0 to 1.0
    applicable_topics TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    expiration_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
