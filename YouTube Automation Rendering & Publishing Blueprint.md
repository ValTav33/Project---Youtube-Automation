# **Automated YouTube Production Engine: Technical Blueprint (Steps 4 & 5\)**

## **1\. Visual Sourcing & Hybrid Asset Engine**

The asset resolution layer handles visual gathering asynchronously for every scene generated in the GPT-4o script payload. It queries stock video APIs (Pexels/Pixabay) first and falls back to generative AI visual models (Fal.ai / Flux / Wan 2.1) whenever stock assets are unavailable or when specific custom cutouts are required.  
import axios from 'axios';

interface SceneAsset {  
  scene\_id: number;  
  asset\_type: 'video' | 'image';  
  url: string;  
}

export async function resolveSceneAsset(  
  query: string,   
  layoutType: string,  
  pexelsApiKey: string,  
  falApiKey: string  
): Promise\<SceneAsset\> {  
  // 1\. Check Pexels Video API for stock b-roll  
  if (layoutType \=== 'STOCK\_BROLL' || layoutType \=== 'SPLIT\_METRIC') {  
    try {  
      const pexelsRes \= await axios.get(\`https://api.pexels.com/videos/search\`, {  
        headers: { Authorization: pexelsApiKey },  
        params: { query, orientation: 'landscape', per\_page: 5 }  
      });

      const videos \= pexelsRes.data.videos;  
      if (videos && videos.length \> 0\) {  
        const videoFiles \= videos\[0\].video\_files;  
        const hdFile \= videoFiles.find((f: any) \=\> f.width \=== 1920 && f.height \=== 1080\) || videoFiles\[0\];  
        return {  
          scene\_id: 0,  
          asset\_type: 'video',  
          url: hdFile.link  
        };  
      }  
    } catch (err) {  
      console.warn(\`Pexels fetch failed for "${query}", falling back to AI generator.\`);  
    }  
  }

  // 2\. Fallback: Generate AI Visual via Fal.ai (Flux Schnell)  
  const falRes \= await axios.post(  
    'https://queue.fal.run/fal-ai/flux/schnell',  
    {  
      prompt: \`Cinematic 4K documentary b-roll, hyper-realistic, dramatic lighting, high contrast: ${query}\`,  
      image\_size: 'landscape\_16\_9',  
      num\_inference\_steps: 4  
    },  
    {  
      headers: {  
        Authorization: \`Key ${falApiKey}\`,  
        'Content-Type': 'application/json'  
      }  
    }  
  );

  return {  
    scene\_id: 0,  
    asset\_type: 'image',  
    url: falRes.data.images\[0\].url  
  };  
}

## **2\. Remotion Video Composition & Layout Engine**

This React component defines the video layout logic in Remotion. It handles word-level dynamic subtitles, camera movement (Ken Burns effect), sound design, audio ducking, and data callout overlays.  
import React from 'react';  
import {   
  AbsoluteFill,   
  Series,   
  Video,   
  Img,   
  Audio,   
  useCurrentFrame,   
  interpolate,   
  spring,   
  useVideoConfig   
} from 'remotion';

export interface WordTimestamp {  
  word: string;  
  start: number;  
  end: number;  
}

export interface SceneData {  
  scene\_id: number;  
  durationInFrames: number;  
  asset\_type: 'video' | 'image';  
  asset\_url: string;  
  narration: string;  
  visual\_overlay?: {  
    headline?: string;  
    stat\_callout?: string;  
    chart\_type?: string;  
  };  
}

export interface VideoProps {  
  scenes: SceneData\[\];  
  words: WordTimestamp\[\];  
  audioUrl: string;  
  bgMusicUrl: string;  
}

// Word-level Animated Subtitle Component  
const SubtitlesOverlay: React.FC\<{ words: WordTimestamp\[\] }\> \= ({ words }) \=\> {  
  const frame \= useCurrentFrame();  
  const { fps } \= useVideoConfig();  
  const currentTime \= frame / fps;

  const activeIndex \= words.findIndex(w \=\> currentTime \>= w.start && currentTime \<= w.end);  
  if (activeIndex \=== \-1) return null;

  const visibleSlice \= words.slice(Math.max(0, activeIndex \- 1), Math.min(words.length, activeIndex \+ 2));

  return (  
    \<div style={{  
      position: 'absolute',  
      bottom: '12%',  
      width: '100%',  
      display: 'flex',  
      justifyContent: 'center',  
      gap: '12px',  
      fontFamily: 'Inter, Helvetica, sans-serif',  
      fontSize: '48px',  
      fontWeight: 900,  
      textTransform: 'uppercase',  
      textShadow: '0 4px 18px rgba(0,0,0,0.9)'  
    }}\>  
      {visibleSlice.map((w, idx) \=\> {  
        const isActive \= currentTime \>= w.start && currentTime \<= w.end;  
        return (  
          \<span   
            key={idx}   
            style={{  
              color: isActive ? '\#FFE600' : '\#FFFFFF',  
              transform: isActive ? 'scale(1.12)' : 'scale(1.0)',  
              transition: 'transform 0.05s ease-out'  
            }}  
          \>  
            {w.word}  
          \</span\>  
        );  
      })}  
    \</div\>  
  );  
};

// Scene Component with Ken Burns Zoom & Stat Pop-ins  
const SceneItem: React.FC\<{ scene: SceneData }\> \= ({ scene }) \=\> {  
  const frame \= useCurrentFrame();  
  const { fps } \= useVideoConfig();

  const scale \= interpolate(frame, \[0, scene.durationInFrames\], \[1.0, 1.15\], {  
    extrapolateRight: 'clamp'  
  });

  const statProgress \= spring({ frame, fps, config: { damping: 12 } });

  return (  
    \<AbsoluteFill style={{ overflow: 'hidden', backgroundColor: '\#0B0F19' }}\>  
      {scene.asset\_type \=== 'video' ? (  
        \<Video   
          src={scene.asset\_url}   
          style={{ width: '100%', height: '100%', objectFit: 'cover', transform: \`scale(${scale})\` }}   
          muted   
        /\>  
      ) : (  
        \<Img   
          src={scene.asset\_url}   
          style={{ width: '100%', height: '100%', objectFit: 'cover', transform: \`scale(${scale})\` }}   
        /\>  
      )}

      {/\* Dark Vignette Overlay \*/}  
      \<AbsoluteFill style={{  
        background: 'radial-gradient(circle, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.75) 100%)'  
      }} /\>

      {/\* Dynamic Stat Callout \*/}  
      {scene.visual\_overlay?.stat\_callout && (  
        \<div style={{  
          position: 'absolute',  
          top: '20%',  
          left: '10%',  
          background: 'rgba(15, 23, 42, 0.85)',  
          borderLeft: '6px solid \#38BDF8',  
          padding: '24px 36px',  
          borderRadius: '8px',  
          transform: \`scale(${statProgress})\`,  
          opacity: statProgress,  
          boxShadow: '0 20px 40px rgba(0,0,0,0.6)'  
        }}\>  
          \<div style={{ color: '\#94A3B8', fontSize: '20px', fontWeight: 600, letterSpacing: '2px' }}\>  
            {scene.visual\_overlay.headline || 'CRITICAL METRIC'}  
          \</div\>  
          \<div style={{ color: '\#F8FAFC', fontSize: '64px', fontWeight: 900, marginTop: '4px' }}\>  
            {scene.visual\_overlay.stat\_callout}  
          \</div\>  
        \</div\>  
      )}  
    \</AbsoluteFill\>  
  );  
};

// Root Composition  
export const MainVideo: React.FC\<VideoProps\> \= ({ scenes, words, audioUrl, bgMusicUrl }) \=\> {  
  return (  
    \<AbsoluteFill\>  
      \<Series\>  
        {scenes.map((scene) \=\> (  
          \<Series.Sequence key={scene.scene\_id} durationInFrames={scene.durationInFrames}\>  
            \<SceneItem scene={scene} /\>  
          \</Series.Sequence\>  
        ))}  
      \</Series\>

      \<SubtitlesOverlay words={words} /\>  
      \<Audio src={audioUrl} volume={1.0} /\>  
      \<Audio src={bgMusicUrl} volume={0.12} /\>  
    \</AbsoluteFill\>  
  );  
};

## **3\. Asynchronous Railway Docker Rendering Service**

### **3.1 Dockerfile**

This container compiles Node.js, Chromium, and FFmpeg dependencies to render Remotion projects headlessly on Railway.  
FROM node:20-bookworm-slim

RUN apt-get update && apt-get install \-y \\  
    chromium \\  
    ffmpeg \\  
    fonts-liberation \\  
    fonts-noto-color-emoji \\  
    libnss3 \\  
    libatk1.0-0 \\  
    libatk-bridge2.0-0 \\  
    libcups2 \\  
    libdrm2 \\  
    libxkbcommon0 \\  
    libxcomposite1 \\  
    libxdamage1 \\  
    libxrandr2 \\  
    libgbm1 \\  
    libpango-1.0-0 \\  
    libasound2 \\  
    && rm \-rf /var/lib/apt/lists/\*

ENV PUPPETEER\_EXECUTABLE\_PATH=/usr/bin/chromium  
ENV PUPPETEER\_SKIP\_CHROMIUM\_DOWNLOAD=true

WORKDIR /app  
COPY package\*.json ./  
RUN npm install  
COPY . .

EXPOSE 3000  
CMD \["npm", "start"\]

### **3.2 Server Entrypoint (server.ts)**

import express from 'express';  
import { bundle } from '@remotion/bundler';  
import { renderMedia, selectComposition } from '@remotion/renderer';  
import path from 'path';  
import { createClient } from '@supabase/supabase-js';

const app \= express();  
app.use(express.json({ limit: '50mb' }));

const supabase \= createClient(process.env.SUPABASE\_URL\!, process.env.SUPABASE\_SERVICE\_ROLE\_KEY\!);

app.post('/api/render', async (req, res) \=\> {  
  const { videoId, inputProps } \= req.body;  
    
  // Acknowledge n8n immediately  
  res.status(202).json({ status: 'queued', videoId });

  (async () \=\> {  
    try {  
      await supabase.from('videos').update({ status: 'rendering' }).eq('id', videoId);

      const bundleLocation \= await bundle(path.resolve('./src/index.ts'));  
      const composition \= await selectComposition({  
        serveUrl: bundleLocation,  
        id: 'MainVideo',  
        inputProps  
      });

      const outputPath \= \`/tmp/${videoId}.mp4\`;  
      await renderMedia({  
        composition,  
        serveUrl: bundleLocation,  
        codec: 'h264',  
        outputLocation: outputPath,  
        inputProps  
      });

      const fileBuffer \= require('fs').readFileSync(outputPath);  
      await supabase.storage.from('rendered-videos').upload(\`${videoId}.mp4\`, fileBuffer, {  
        contentType: 'video/mp4',  
        upsert: true  
      });

      const { data: publicUrlData } \= supabase.storage.from('rendered-videos').getPublicUrl(\`${videoId}.mp4\`);

      await supabase.from('videos').update({  
        status: 'rendered',  
        rendered\_video\_url: publicUrlData.publicUrl  
      }).eq('id', videoId);

    } catch (err: any) {  
      await supabase.from('videos').update({  
        status: 'failed',  
        error\_log: err.message  
      }).eq('id', videoId);  
    }  
  })();  
});

app.listen(process.env.PORT || 3000, () \=\> console.log('Remotion Render Microservice running.'));

## **4\. Phase 4: Publishing & Feedback Loop**

### **4.1 Thumbnail Generator Prompt (Fal.ai Flux)**

YouTube thumbnail graphic, central focal subject, dramatic cinematic lighting, high vibrancy, clean silhouette, 8k resolution, minimalist hyper-focus: {target\_topic}

### **4.2 YouTube Data API v3 Config (n8n Node)**

> * **Endpoint:** YouTube Upload Video  
> * **File:** {{ $json.rendered\_video\_url }}  
> * **Title:** {{ $json.meta.title }}  
> * **Description:** {{ $json.meta.description }}  
> * **Tags:** {{ $json.meta.tags.join(',') }}  
> * **Initial Privacy State:** unlisted

### **4.3 Telegram Approval Gate**

> 1. Bot posts preview link, title, and generated thumbnails to private channel.  
> 2. Webhook triggers upon \[Publish\] button press, switching video privacy state to public.

## **5\. Operational Safeguards**

> * **Music & SFX Management:** Audio mood tags dynamically route to royalty-free .mp3 tracks stored in Supabase Storage buckets.  
> * **YouTube Reused Content Compliance:** Fast visual pacing (cut every 3–5 seconds), custom kinetic subtitles, and dynamic data callouts guarantee original value transformation.  
> * **Error Handling:** Enable "Retry On Fail" on API nodes and configure an n8n Error Trigger node to route execution errors directly to Telegram.