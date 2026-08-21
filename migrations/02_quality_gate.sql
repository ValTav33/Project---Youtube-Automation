-- 02_quality_gate.sql
-- Migration to add approval statuses to the video_status enum.

-- PostgreSQL requires adding enum values one by one outside of a transaction block.
ALTER TYPE video_status ADD VALUE IF NOT EXISTS 'awaiting_script_approval';
ALTER TYPE video_status ADD VALUE IF NOT EXISTS 'awaiting_preview_approval';
ALTER TYPE video_status ADD VALUE IF NOT EXISTS 'awaiting_publish_approval';
ALTER TYPE video_status ADD VALUE IF NOT EXISTS 'approved';
ALTER TYPE video_status ADD VALUE IF NOT EXISTS 'rejected';
