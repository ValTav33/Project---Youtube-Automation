import express, { Request, Response } from 'express';
import cors from 'cors';
import path from 'path';
import fs from 'fs';
import { bundle } from '@remotion/bundler';
import { renderMedia, selectComposition } from '@remotion/renderer';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import { exec } from 'child_process';
import util from 'util';

const execAsync = util.promisify(exec);

dotenv.config();
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));

const PORT = process.env.PORT || 3000;
const SUPABASE_URL = process.env.SUPABASE_URL || 'https://wrowkhhwlvmigvyescdv.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

const getSupabase = () => {
  if (!SUPABASE_SERVICE_ROLE_KEY) {
    console.warn('Warning: SUPABASE_SERVICE_ROLE_KEY is not configured in environment.');
  }
  return createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
};

// Health Check Endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'YouTube Remotion Render Microservice'
  });
});

function downloadFile(url: string, destPath: string): Promise<string> {
  return new Promise((resolve) => {
    if (!url || !url.startsWith('http')) return resolve(url);
    if (fs.existsSync(destPath) && fs.statSync(destPath).size > 1024) return resolve(destPath);

    const file = fs.createWriteStream(destPath);
    const client = url.startsWith('https') ? require('https') : require('http');

    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      file.close();
      resolve(url);
    }, 15000);

    const request = (targetUrl: string) => {
      if (timedOut) return;
      const req = client.get(targetUrl, (response: any) => {
        if (timedOut) return;
        if (response.statusCode && response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
          return request(response.headers.location);
        }
        if (response.statusCode !== 200) {
          clearTimeout(timer);
          file.close();
          fs.unlink(destPath, () => {});
          return resolve(url);
        }
        response.pipe(file);
        file.on('finish', () => {
          clearTimeout(timer);
          file.close();
          resolve(destPath);
        });
      });
      req.on('error', () => {
        clearTimeout(timer);
        file.close();
        fs.unlink(destPath, () => {});
        resolve(url);
      });
    };
    request(url);
  });
}

// Render Endpoint
app.post('/api/render', async (req: Request, res: Response) => {
  const { videoId, inputProps } = req.body;

  if (!videoId || !inputProps) {
    return res.status(400).json({ error: 'Missing required parameters: videoId and inputProps are required.' });
  }

  // Acknowledge n8n / caller immediately with 202 Accepted
  res.status(202).json({
    status: 'queued',
    videoId,
    message: 'Rendering task accepted and processing in background on Railway.'
  });

  // Execute Asynchronous Headless Render Task
  (async () => {
    const supabase = getSupabase();
    console.log(`[Render Worker] Started rendering job on Railway for video: ${videoId}`);

    try {
      if (SUPABASE_SERVICE_ROLE_KEY) {
        await supabase
          .from('videos')
          .update({ status: 'rendering', updated_at: new Date().toISOString() })
          .eq('id', videoId);
      }

      // Pre-download assets into local directory for fast rendering
      const assetsDir = path.resolve('/tmp', `assets_${videoId}`);
      if (!fs.existsSync(assetsDir)) {
        fs.mkdirSync(assetsDir, { recursive: true });
      }

      console.log(`[Render Worker] Pre-downloading video clips to ${assetsDir}...`);
      const scenes = inputProps.scenes || [];
      const downloadPromises = scenes.map(async (scene: any, idx: number) => {
        const ext = scene.asset_type === 'video' ? 'mp4' : 'jpg';
        const localPath = path.join(assetsDir, `scene_${scene.scene_id || idx + 1}.${ext}`);
        if (scene.asset_url && scene.asset_url.startsWith('http')) {
          await downloadFile(scene.asset_url, localPath);
        }
        
        let playbackRate = 1;
        if (scene.asset_type === 'video' && fs.existsSync(localPath)) {
          try {
            const { stdout } = await execAsync(`ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${localPath}"`);
            const durationSec = parseFloat(stdout.trim());
            const requestedSec = scene.durationInFrames / 30; // Assuming 30fps
            if (durationSec > 0 && requestedSec > durationSec) {
              // Slow down the video so it stretches perfectly to fill the requested duration
              playbackRate = durationSec / requestedSec;
              console.log(`[Render Worker] Scene ${scene.scene_id} video is ${durationSec.toFixed(2)}s but requires ${requestedSec.toFixed(2)}s. Setting playbackRate=${playbackRate.toFixed(2)}`);
            }
          } catch (e) {
            console.warn(`[Render Worker] Failed to probe video duration for scene ${scene.scene_id}:`, e);
          }
        }
        
        return {
          ...scene,
          playbackRate,
          asset_url: fs.existsSync(localPath) ? `scene_${scene.scene_id || idx + 1}.${ext}` : scene.asset_url
        };
      });

      const localScenes = await Promise.all(downloadPromises);

      // Download narration audio
      let localAudioUrl = inputProps.audioUrl;
      if (inputProps.audioUrl && inputProps.audioUrl.startsWith('http')) {
        const localAudioPath = path.join(assetsDir, 'narration.mp3');
        await downloadFile(inputProps.audioUrl, localAudioPath);
        if (fs.existsSync(localAudioPath)) {
          localAudioUrl = 'narration.mp3';
        }
      }

      const finalProps = {
        ...inputProps,
        scenes: localScenes,
        audioUrl: localAudioUrl
      };

      console.log(`[Render Worker] Bundling Remotion composition with publicDir...`);
      const entryPoint = path.resolve(process.cwd(), 'src/index.ts');
      const bundleLocation = await bundle({
        entryPoint,
        publicDir: assetsDir
      });

      console.log(`[Render Worker] Selecting composition 'MainVideo'...`);
      const composition = await selectComposition({
        serveUrl: bundleLocation,
        id: 'MainVideo',
        inputProps: finalProps
      });

      const outputDir = path.resolve('/tmp');
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      const outputPath = path.join(outputDir, `${videoId}.mp4`);

      console.log(`[Render Worker] Rendering MP4 to ${outputPath}...`);
      await renderMedia({
        composition,
        serveUrl: bundleLocation,
        codec: 'h264',
        outputLocation: outputPath,
        inputProps: finalProps,
        concurrency: 1, // FORCE single concurrency to prevent OOM on Railway 500MB RAM
        chromiumOptions: {
          enableMultiProcessOnLinux: false, // Prevents aggressive OOM killer
          gl: 'angle' // Standard for headless
        },
        timeoutInMilliseconds: 2400000, // 40 minutes timeout for safe margin
        onProgress: ({ progress }) => {
          if (Math.round(progress * 100) % 10 === 0) {
            console.log(`[Render Worker] Video ${videoId} progress: ${(progress * 100).toFixed(0)}%`);
          }
        }
      });

      console.log(`[Render Worker] Render complete. Uploading to Supabase Storage...`);
      const fileBuffer = fs.readFileSync(outputPath);

      if (SUPABASE_SERVICE_ROLE_KEY) {
        const { error: uploadError } = await supabase.storage
          .from('rendered-videos')
          .upload(`${videoId}.mp4`, fileBuffer, {
            contentType: 'video/mp4',
            upsert: true
          });

        if (uploadError) {
          throw new Error(`Supabase Storage upload failed: ${uploadError.message}`);
        }

        const { data: publicUrlData } = supabase.storage
          .from('rendered-videos')
          .getPublicUrl(`${videoId}.mp4`);

        const publicUrl = publicUrlData.publicUrl;

        await supabase
          .from('videos')
          .update({
            status: 'rendered',
            rendered_video_url: publicUrl,
            updated_at: new Date().toISOString()
          })
          .eq('id', videoId);

        console.log(`[Render Worker] ✅ Video ${videoId} uploaded successfully: ${publicUrl}`);

        // Fetch video meta for Telegram message
        const { data: videoData } = await supabase
          .from('videos')
          .select('target_title, script_payload, thumbnail_urls')
          .eq('id', videoId)
          .single();

        const videoTitle = videoData?.target_title || 'Documentary Video';
        const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '8359129159:AAHoM3zGBnMcrUP71z3x6s4vFhMMwfFCfR8';
        const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || '5808376503';

        if (TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) {
          console.log(`[Render Worker] 📱 Sending Telegram review notification for video: ${videoId}`);
          const tgPayload = {
            chat_id: TELEGRAM_CHAT_ID,
            text: `🎬 *FULL VIDEO RENDER COMPLETE!*\n\n📌 *Title:* ${videoTitle}\n🆔 *Video ID:* \`${videoId}\`\n\n🎥 [Watch Preview Video](${publicUrl})\n\nClick below to publish to your YouTube channel:`,
            parse_mode: 'Markdown',
            reply_markup: {
              inline_keyboard: [[
                { text: '🚀 Approve & Publish', callback_data: `publish:${videoId}` },
                { text: '❌ Reject', callback_data: `reject:${videoId}` }
              ]]
            }
          };

          try {
            await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(tgPayload)
            });
            console.log(`[Render Worker] ✅ Telegram review notification sent.`);
          } catch (tgErr) {
            console.error(`[Render Worker] Failed to send Telegram card:`, tgErr);
          }
        }
      }

      // Cleanup local temp files
      try {
        if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
        fs.rmSync(assetsDir, { recursive: true, force: true });
      } catch (e) {}
    } catch (err: any) {
      console.error(`[Render Worker] ❌ Render error for video ${videoId}:`, err);
      if (SUPABASE_SERVICE_ROLE_KEY) {
        await supabase
          .from('videos')
          .update({
            status: 'failed',
            error_log: `Render error: ${err.message || String(err)}`,
            updated_at: new Date().toISOString()
          })
          .eq('id', videoId);
      }
    }
  })();
});

app.listen(PORT, () => {
  console.log(`🚀 Remotion Render Microservice running on port ${PORT}`);
});
