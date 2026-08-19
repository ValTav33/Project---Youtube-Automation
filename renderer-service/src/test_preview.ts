import path from 'path';
import fs from 'fs';
import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://wrowkhhwlvmigvyescdv.supabase.co';
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

async function testRender() {
  const sb = createClient(SUPABASE_URL, SUPABASE_KEY);
  const { data: video } = await sb
    .from('videos')
    .select('*')
    .eq('id', '47b043a7-65b7-4238-9e0f-eaf038864640')
    .single();

  if (!video) {
    console.error('Video not found');
    return;
  }

  const scriptPayload = video.script_payload;
  // Take first 3 scenes for fast preview verification
  const previewScenes = scriptPayload.scenes.slice(0, 3).map((s: any) => ({
    scene_id: s.scene_id,
    durationInFrames: 150, // 5s each = 15s total preview
    asset_type: s.asset_type || 'video',
    asset_url: s.asset_url,
    narration: s.narration,
    visual_overlay: s.visual_overlay
  }));

  const words = (video.transcript_timestamps?.words || []).filter((w: any) => w.end <= 15);

  const inputProps = {
    scenes: previewScenes,
    words,
    audioUrl: video.audio_url,
    bgMusicUrl: '',
    bgMusicVolume: 0.12
  };

  console.log('Bundling composition...');
  const entryPoint = path.resolve(__dirname, './index.ts');
  const bundleLocation = await bundle(entryPoint);

  console.log('Selecting composition...');
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: 'MainVideo',
    inputProps
  });

  const outputPath = path.resolve(__dirname, '../../preview.mp4');
  console.log(`Rendering 15s preview MP4 to ${outputPath}...`);

  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: 'h264',
    outputLocation: outputPath,
    inputProps,
    onProgress: ({ progress }: { progress: number }) => {
      process.stdout.write(`\rRender progress: ${(progress * 100).toFixed(1)}%`);
    }
  });

  console.log(`\n✅ Preview successfully rendered: ${outputPath} (${(fs.statSync(outputPath).size / 1024 / 1024).toFixed(2)} MB)`);
}

testRender().catch(console.error);
