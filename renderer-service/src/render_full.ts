import path from 'path';
import fs from 'fs';
import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import https from 'https';
import http from 'http';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const SUPABASE_URL = process.env.SUPABASE_URL || 'https://wrowkhhwlvmigvyescdv.supabase.co';
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || '';
const FPS = 30;

function downloadFile(url: string, destPath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!url || !url.startsWith('http')) {
      return resolve(url);
    }

    // Skip download if valid file already exists locally
    if (fs.existsSync(destPath) && fs.statSync(destPath).size > 1024) {
      return resolve(destPath);
    }

    const file = fs.createWriteStream(destPath);
    const client = url.startsWith('https') ? https : http;

    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      file.close();
      resolve(url); // fallback to remote URL if download times out
    }, 15000);

    const request = (targetUrl: string) => {
      if (timedOut) return;
      const req = client.get(targetUrl, (response) => {
        if (timedOut) return;
        if (response.statusCode && response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
          return request(response.headers.location);
        }
        if (response.statusCode !== 200) {
          clearTimeout(timer);
          file.close();
          fs.unlink(destPath, () => {});
          return resolve(url); // fallback to remote URL
        }
        response.pipe(file);
        file.on('finish', () => {
          clearTimeout(timer);
          file.close();
          resolve(destPath);
        });
      });

      req.on('error', (err) => {
        clearTimeout(timer);
        file.close();
        fs.unlink(destPath, () => {});
        resolve(url); // fallback to remote URL
      });
    };

    request(url);
  });
}

async function renderFullVideo(videoId: string) {
  const sb = createClient(SUPABASE_URL, SUPABASE_KEY);
  console.log(`\n========================================`);
  console.log(`[Full Render Engine] Fetching video ${videoId}...`);
  console.log(`========================================\n`);

  const { data: video, error } = await sb
    .from('videos')
    .select('*')
    .eq('id', videoId)
    .single();

  if (error || !video) {
    throw new Error(`Video ${videoId} not found in database: ${error?.message}`);
  }

  const scriptPayload = video.script_payload || {};
  const scenes = scriptPayload.scenes || [];
  const timestampsData = video.transcript_timestamps || {};
  const words = timestampsData.words || [];
  const totalAudioDuration = timestampsData.total_duration_seconds || 392.23;
  const audioUrl = video.audio_url || '';

  console.log(`🎬 Video Title: "${video.target_title}"`);
  console.log(`📝 Total Scenes: ${scenes.length}`);
  console.log(`⏱ Total Audio Duration: ${totalAudioDuration.toFixed(1)}s (~${(totalAudioDuration / 60).toFixed(1)} min)`);
  console.log(`🔊 Total Words in Subtitles: ${words.length}`);

  // Create temporary assets directory
  const assetsDir = path.resolve('/tmp', `render_assets_${videoId}`);
  if (!fs.existsSync(assetsDir)) {
    fs.mkdirSync(assetsDir, { recursive: true });
  }

  // 1. Download voiceover audio locally
  console.log(`\n⬇️  Downloading narration audio locally...`);
  const localAudioPath = path.join(assetsDir, 'narration.mp3');
  await downloadFile(audioUrl, localAudioPath);
  console.log(`✅ Audio downloaded: ${localAudioPath} (${(fs.statSync(localAudioPath).size / 1024 / 1024).toFixed(2)} MB)`);

  // 2. Pre-download all stock video assets in parallel
  console.log(`\n⬇️  Downloading ${scenes.length} stock video clips in parallel...`);
  const totalWords = scenes.reduce((acc: number, s: any) => acc + (s.narration || '').split(' ').length, 0) || 1;

  const remotionScenes = [];
  const downloadPromises = scenes.map(async (scene: any, idx: number) => {
    const ext = scene.asset_type === 'video' ? 'mp4' : 'jpg';
    const localAssetPath = path.join(assetsDir, `scene_${scene.scene_id || idx + 1}.${ext}`);

    try {
      if (scene.asset_url && scene.asset_url.startsWith('http')) {
        await downloadFile(scene.asset_url, localAssetPath);
      }
    } catch (e: any) {
      console.warn(`⚠️ Warning downloading asset for Scene #${scene.scene_id}: ${e.message}. Using remote fallback.`);
    }

    const sceneWordCount = (scene.narration || '').split(' ').length;
    const ratio = sceneWordCount / totalWords;
    const sceneSeconds = Math.max(ratio * totalAudioDuration, 3.5);
    const durationInFrames = Math.round(sceneSeconds * FPS);

    return {
      scene_id: scene.scene_id || idx + 1,
      durationInFrames,
      asset_type: scene.asset_type || 'video',
      asset_url: fs.existsSync(localAssetPath) ? `scene_${scene.scene_id || idx + 1}.${ext}` : scene.asset_url,
      narration: scene.narration,
      visual_overlay: scene.visual_overlay
    };
  });

  const resolvedScenes = await Promise.all(downloadPromises);
  resolvedScenes.sort((a, b) => a.scene_id - b.scene_id);

  const totalFrames = resolvedScenes.reduce((acc, s) => acc + s.durationInFrames, 0);
  console.log(`✅ All ${resolvedScenes.length} scenes prepared!`);
  console.log(`🎞 Total Video Frames: ${totalFrames} (${(totalFrames / FPS).toFixed(1)} seconds / ${(totalFrames / FPS / 60).toFixed(1)} minutes)`);

  const inputProps = {
    scenes: resolvedScenes,
    words,
    audioUrl: 'narration.mp3',
    bgMusicUrl: '',
    bgMusicVolume: 0.12
  };

  // 3. Bundle Remotion Composition
  console.log(`\n📦 Bundling Remotion composition with publicDir: ${assetsDir}...`);
  const entryPoint = path.resolve(__dirname, './index.ts');
  const bundleLocation = await bundle({
    entryPoint,
    publicDir: assetsDir
  });

  console.log(`🔍 Selecting composition 'MainVideo'...`);
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: 'MainVideo',
    inputProps
  });

  const outputDir = path.resolve('/tmp');
  const outputPath = path.join(outputDir, `${videoId}_full.mp4`);

  console.log(`\n🚀 Rendering full ${resolvedScenes.length}-scene documentary to ${outputPath}...`);
  const startTime = Date.now();

  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: 'h264',
    outputLocation: outputPath,
    inputProps,
    concurrency: 2,
    timeoutInMilliseconds: 120000,
    onProgress: ({ progress }: { progress: number }) => {
      const pct = (progress * 100).toFixed(1);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
      process.stdout.write(`\r🎥 Full Render Progress: ${pct}% | Elapsed: ${elapsed}s`);
    }
  });

  const renderDuration = ((Date.now() - startTime) / 1000).toFixed(1);
  const fileSizeMB = (fs.statSync(outputPath).size / 1024 / 1024).toFixed(2);
  console.log(`\n\n✅ RENDER COMPLETE in ${renderDuration}s! Output: ${outputPath} (${fileSizeMB} MB)`);

  // 4. Upload Full Video to Supabase Storage
  console.log(`\n☁️  Uploading full video to Supabase Storage ('rendered-videos' bucket)...`);
  const fileBuffer = fs.readFileSync(outputPath);

  const { error: uploadError } = await sb.storage
    .from('rendered-videos')
    .upload(`${videoId}.mp4`, fileBuffer, {
      contentType: 'video/mp4',
      upsert: true
    });

  if (uploadError) {
    throw new Error(`Upload failed: ${uploadError.message}`);
  }

  const { data: publicUrlData } = sb.storage
    .from('rendered-videos')
    .getPublicUrl(`${videoId}.mp4`);

  const publicUrl = publicUrlData.publicUrl;
  console.log(`✅ Uploaded successfully: ${publicUrl}`);

  // 5. Update Database Record
  await sb
    .from('videos')
    .update({
      status: 'rendered',
      rendered_video_url: publicUrl,
      updated_at: new Date().toISOString()
    })
    .eq('id', videoId);

  // 6. Send Telegram Notification
  if (TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) {
    console.log(`\n📱 Dispatching Telegram Review Card with full video...`);
    const messageText = (
      `🎬 *FULL DOCUMENTARY RENDER COMPLETE*\n\n` +
      `📌 *Title:* ${video.target_title}\n` +
      `⏱ *Duration:* ${(totalAudioDuration / 60).toFixed(1)} minutes (${resolvedScenes.length} scenes)\n` +
      `📦 *File Size:* ${fileSizeMB} MB\n` +
      `🆔 *ID:* \`${videoId}\`\n\n` +
      `🔗 [Watch Full Rendered Video](${publicUrl})\n\n` +
      `Click below to approve and publish to YouTube:`
    );

    const tgUrl = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
    await fetch(tgUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text: messageText,
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [[
            { text: '🚀 Approve & Publish', callback_data: `publish:${videoId}` },
            { text: '❌ Reject', callback_data: `reject:${videoId}` }
          ]]
        }
      })
    });
    console.log(`✅ Telegram notification sent!`);
  }

  // Cleanup temporary assets
  try {
    fs.rmSync(assetsDir, { recursive: true, force: true });
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
  } catch (e) {}

  console.log(`\n🎉 Pipeline completed successfully for video ${videoId}!\n`);
}

const targetVideoId = process.argv[2] || '47b043a7-65b7-4238-9e0f-eaf038864640';
renderFullVideo(targetVideoId).catch((err) => {
  console.error('❌ Full Render Engine failed:', err);
  process.exit(1);
});
