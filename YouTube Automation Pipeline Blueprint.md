# **Automated YouTube Production Engine: Technical Blueprint (Steps 1–3)**

## **1\. System Overview & Architecture**

This document defines the production pipeline for generating 8-to-10 minute data-rich YouTube video essays using an API-driven orchestrator, cloud database, and programmatic rendering pipeline.

> * **Target Format:** 8–10 Minute Documentary / Case Study (1,200–1,400 words across 35–45 scenes)  
> * **Goal:** Monetization within 3 months, low cost ($0.70–$1.60/video), high velocity (2–3 videos/week)  
> * **Human Intervention:** \~30 seconds per video (Telegram review gate)

\[Outlier Scraper / Telegram Intake\]   
          ↓  
  \[Supabase DB State Engine\]  
          ↓  
  \[GPT-4o Script Engine (JSON)\]  
          ↓  
  \[ElevenLabs TTS \+ Word Timestamps\]  
          ↓  
  \[Visual Sourcing & Remotion Render\] (Step 4\)

## **2\. Master Tech Stack & Decisions**

| Layer | Selected Tool / Infrastructure | Rationale |
| :---- | :---- | :---- |
| **Orchestration** | **n8n** (Hosted on Railway) | Handles webhooks, API retries, asynchronous processing, and pipeline logic cleanly. |
| **Database & State** | **Supabase** (PostgreSQL) | Stores video queues, script JSON specs, asset URLs, and video statuses. |
| **Topic Scouting** | **Python Script \+ Telegram Gate** | yt-dlp calculates ![][image1] outliers; Telegram bot acts as a 5-second human approval filter. |
| **Scripting LLM** | **OpenAI GPT-4o API** | Highest visual scene-description coherence, strict JSON enforcement, and strong retention pacing. |
| **Voiceover Engine** | **ElevenLabs API** (eleven\_turbo\_v2\_5) | Industry-leading voice realism; outputs character-level alignment data required for word highlighting. |

## **3\. Step 1: Database Schema & Outlier Engine**

### **3.1 Supabase Database Migration (SQL)**

Run this SQL script in your Supabase SQL Editor to initialize state management:  
\-- Pipeline Enums  
CREATE TYPE video\_status AS ENUM (  
  'discovered', 'approved', 'scripting', 'scripted',   
  'audio\_ready', 'rendering', 'rendered', 'uploaded', 'failed'  
);

\-- Monitored Channels Table  
CREATE TABLE monitored\_channels (  
  id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  channel\_id TEXT UNIQUE NOT NULL,  
  channel\_name TEXT NOT NULL,  
  subscriber\_count BIGINT DEFAULT 0,  
  median\_views BIGINT DEFAULT 0,  
  created\_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  
);

\-- Production Video Queue  
CREATE TABLE videos (  
  id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
  source\_type TEXT CHECK (source\_type IN ('outlier\_scraped', 'manual\_telegram')),  
  source\_video\_id TEXT,  
  target\_title TEXT NOT NULL,  
  topic\_premise TEXT NOT NULL,  
  status video\_status DEFAULT 'discovered',  
    
  \-- Narrative & Scene Data  
  script\_payload JSONB,  
  audio\_url TEXT,  
  transcript\_timestamps JSONB,  
  rendered\_video\_url TEXT,  
  thumbnail\_urls TEXT\[\],  
    
  \-- YouTube Publishing Metadata  
  youtube\_video\_id TEXT,  
  error\_log TEXT,  
  created\_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  
  updated\_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  
);

### **3.2 Outlier Detection Script (Python)**

This script evaluates competitor channels and extracts videos that perform at ![][image2] the channel's median view count.  
![][image3]import numpy as np  
import yt\_dlp  
import requests

def evaluate\_channel\_outliers(channel\_url: str):  
    ydl\_opts \= {  
        'extract\_flat': True,  
        'playlist\_items': '1-15',  
        'quiet': True  
    }  
      
    with yt\_dlp.YoutubeDL(ydl\_opts) as ydl:  
        info \= ydl.extract\_info(channel\_url, download=False)  
        entries \= info.get('entries', \[\])  
          
        if len(entries) \< 5:  
            return \[\]

        views \= \[e.get('view\_count', 0\) for e in entries if e.get('view\_count') is not None\]  
        if not views:  
            return \[\]  
              
        median\_views \= float(np.median(views))  
        outliers \= \[\]  
          
        for entry in entries:  
            v\_count \= entry.get('view\_count', 0\)  
            multiplier \= v\_count / median\_views if median\_views \> 0 else 0  
              
            \# Threshold: 3x channel median performance AND at least 15,000 views  
            if multiplier \>= 3.0 and v\_count \>= 15000:  
                outliers.append({  
                    "video\_id": entry.get('id'),  
                    "title": entry.get('title'),  
                    "views": v\_count,  
                    "median": int(median\_views),  
                    "multiplier": round(multiplier, 2),  
                    "url": f"https://youtube.com/watch?v={entry.get('id')}"  
                })  
                  
        return outliers

## **4\. Step 2: Script Generation Engine (GPT-4o)**

The scripting engine converts an approved topic into a structured JSON scene blueprint.

### **4.1 System Prompt**

Set this as the System Prompt in the n8n OpenAI Node:  
You are a master YouTube documentary scriptwriter specializing in high-retention, fast-paced video essays (similar to MagnatesMedia and ColdFusion).

TARGET FORMAT:  
\- Total Video Length: \~8 to 10 minutes (approx. 1,200 \- 1,400 words total across all scenes).  
\- Total Scenes: 35 to 45 granular scenes (each scene lasting 10–18 seconds).  
\- Tone: Dramatic, authoritative, analytical, and fast-paced. Zero generic intro fluff or channel greetings.

STRICT SCHEMA RULES:  
Output MUST be valid raw JSON matching this schema:  
{  
  "meta": {  
    "title": "High CTR Click-Worthy Title",  
    "description": "Engaging description with timestamps and keywords",  
    "tags": \["tag1", "tag2", "tag3"\]  
  },  
  "scenes": \[  
    {  
      "scene\_id": 1,  
      "narration": "The exact spoken words for this scene.",  
      "layout\_type": "STOCK\_BROLL | SPLIT\_METRIC | MAP\_ANIMATION | HEADLINE\_CUTOUT",  
      "broll\_search\_query": "3-5 specific stock video search terms (e.g., cargo container ship ocean storm)",  
      "visual\_overlay": {  
        "headline": "Short bold punchy text (max 4 words)",  
        "stat\_callout": "e.g., $14.2 Billion or \-42%",  
        "chart\_type": "none | bar | line | donut"  
      },  
      "sfx": "sub\_bass\_drop | whoosh | paper\_rip | typewriter | camera\_shutter | none"  
    }  
  \]  
}

## **5\. Step 3: Audio & Word-Level Timestamp Engine**

### **5.1 ElevenLabs API Call Configuration**

In n8n, execute an HTTP POST request to ElevenLabs to generate voiceover with character timestamps:

> * **Endpoint:** POST https://api.elevenlabs.io/v1/text-to-speech/{voice\_id}/with-timestamps  
> * **Headers:**  
  * xi-api-key: {{$env.ELEVENLABS\_API\_KEY}}  
  * Content-Type: application/json  
> * **Body:**

{  
  "text": "{{ $json.scenes.map(s \=\> s.narration).join(' ') }}",  
  "model\_id": "eleven\_turbo\_v2\_5",  
  "voice\_settings": {  
    "stability": 0.5,  
    "similarity\_boost": 0.8  
  }  
}

### **5.2 Timestamp Formatting Code Node (JavaScript)**

Place this snippet in an n8n Code Node directly following the ElevenLabs API node to convert character alignment into word timestamps for Remotion:  
const response \= $input.first().json;  
const audioBase64 \= response.audio\_base64;  
const alignment \= response.alignment;

const words \= \[\];  
let currentWord \= "";  
let startTime \= null;

alignment.characters.forEach((char, idx) \=\> {  
  if (startTime \=== null) {  
    startTime \= alignment.character\_start\_times\_seconds\[idx\];  
  }  
    
  if (char \=== " " || idx \=== alignment.characters.length \- 1\) {  
    if (char \!== " ") currentWord \+= char;  
    if (currentWord.trim().length \> 0\) {  
      words.push({  
        word: currentWord.trim(),  
        start: startTime,  
        end: alignment.character\_end\_times\_seconds\[idx\]  
      });  
    }  
    currentWord \= "";  
    startTime \= null;  
  } else {  
    currentWord \+= char;  
  }  
});

return {  
  audio\_base64: audioBase64,  
  word\_timestamps: words,  
  total\_duration\_seconds: words.length \> 0 ? words\[words.length \- 1\].end : 0  
};  


[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFcAAAAWCAYAAAC1zAClAAACVUlEQVR4Xu2YPWgVQRSFj0ZBRewUbGyEFClsLLQQUVRUxIAErCIIpkoRomijgoJgIwpiYzCQgIUgKFgoFqaKIPhTBEJIjKCgiBbiHyr4fy93h509b97EfYHsqvPB4b055+7w5r7dtzsPSCQSiTmhXTQg2u15h733/w3zRO9Evzy9KVQYP5Dn+j7EQtFP0SXRMtFGWP1x0UevTnmN4pz6GbTGjUfy0r+fIdiiNpHvo3kMzTewCfOPsin0wLLt5C/I/E/kh3gkeiJazEGd2A9b0DHyHTdEa9n0GEbz5quvZzUzjfgxzbIQN0UfRCs5qAOrYYu5xYGwRPSSTSLWjJjfShZjUPRdtIaDqtHFvGdT+MpGANeMsxxE0PpRNoVDsOwk+WU4BZtjBwdVETpbDsBuSDNxBvnxThcLFUX2wmq2kH8u8/eQ3yq9sPn2cTDXhJrL4xh9aGzw40JFzgQsvy96IJrMxqEzebachs2tP2+Vwc3VBiz3xmXYisb5fEKZ3vTUu0B+qwyJvok6OKiCL8gXrDe4u14Wo4uNjMtobKBD/dD8oaaX5TbsuXkFB1VyB7awVdnrn9Ap6mcz4wjC83TD/G3ku+dbPdvK0iYaEz0VLaKsFpyALe65aCdlzdCH+OtsZugOLHRTe4Zw03Wjof4UBxG0kfp578F2m7VlM2xxbzmI4C7jpeRfQ+OW19Hs0j8I88e98fo8DnKVjbriLssyZ8AL0Xzk/0/oF6Ovw16NQ7ez+hyt/11o3WfR+UIF8Ap2/BXRQ8oSiX+HXSWUKMm6EkokEjPyG8o9q3VKLyLnAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAYCAYAAAC8/X7cAAABgUlEQVR4Xu2WzSsFURjG37JgKcnGWrKhpCiykQVKPlayoyRlYcnKyoYNZWWlxIIiScpCEfkLlJWNJbGlfDxv50zOfe5cM2fmjm6aX/26d97nzpz33DvnzBXJycnJijb4DL/gLawtjMtLv5iB5jhIyCzccI53xFy/3allQreYgVY58ESvoUbVMqMJvsFdDmLyKMXNlprAPBeIDi74UA9f4CUHniyJaX6QA7AA97hoGYUXXExCDXyAd7CKsihGxDS/zoHDIjyk2hi8oloqGuArPOPgF9bgPvyAfZQx+isd2ffa/LWTpaIZvsNtDjxoFPMrnHBA6CRuxGy7qekVM+gKBwkptYhdpuE9POXAhwlJ/0zQW2aLasEEeqgeoM0H97w+R46dLBa6nekAwxx4Mi7h33ZQC9sEpqR4weokgjURybKU9ympjVY7x622FnZrTMJzLlpm4AEX/4I6+Cmm6Sf7ulnwiR+i1tgAF/4lus0NxbTLnlNR6F+Gzpi22HNycnIqgG9bHlGo5en86QAAAABJRU5ErkJggg==>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAABICAYAAABLN6ksAAAPAklEQVR4Xu3dB7BkS1nA8VbQJ6iYUDGxD6UMJEVEwQBIGRAFBSUo6luCqIgBSjDzECyCUopQhlKRJ4oCJoJlGQpZUUBQCUagUFfUUrKAKCiG83+nvzfffNNnZu7ee3fv+v6/qq57uvvMTJ8zU3u+7dPdpzVJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRdVP5rSv+7Rzqpbj+lt7fltr4jlf9wL2P7QVftsek/27zPF9SKQ3pjW2/nW9erh8fwzrQtSZKupggO3qPkc8BAQFSDoPPtr2vBwD3acjspf++S/4+UHzmOgC3w3s+vhd2ZtH2Xttl2SZJ0NVSDnBqwgV64C+UL234BG2j3K2vh5CdqwR6OO2Cr5xh3qwWSJEn495IfBRO/WfJH4Rq1YAFtOUjAVtt+3ZLf13EGbJe3+f2fWMq5FStJkrTTKOgJl7VVUHGvtr7fR03p33oZY8UYr/WUXveYXo4nTempbe45+4Re9uC26gV79ZTelcp53ev69gN7+ZL7tc221/z9e9n/lHLKHtC3aUsN2P67l4M23jDV/cuUntO3P2hK/5TqltTzzLn4vZTH49tm+2s74lw9pM37cqv3o6f04z3/yCldf0pvafNYP25xs32T+WVXtrd+hiRJOuFqIJHdfEqvT3n2u3bK36mX4VZT+pC+Tdm39+3Ih/cseeQ82/v2sIH9v75vMzaPILJinxywfW/bDJbYJwK2fdqYkX9UKat+qa2/7uyU3i/lw0HOFce01K4vStuU5++tTn6QJEknHBfzGhRkBA30oL27zfsRxIUv7mUVZfT05Hx4bs/XFNg+SMD2uLZ6/dva3N6K+hywka/7URYB27Y20rP2wr4duM2cj2EJ+zy8b782lWf5fba1Ax+c8jfr27/b83m/5/U8iR66UaAoSZJOsBoEZKfaXPdZPU/Qtk/A9qNtLicoIoD4vFT3il63hDpu/R0Er/mc/neE8hqwXTPlo4zbtqCNL0912aum9GeljB6rpc/OXtZW+8Xt4Sq/z7Z2BPanZ/E1U3poz18ypZ/KO01uNKXfbnP9Pm2VJEknyLYLeC0nf4s2387Dl/SyalQWcq9QqMuMRO8TY6/2EcfA+KwR6nLA9oYp3SflwT537NujNsayHB/RNuvI73ubkX23TTbI7z1qRz5X4LY0x/Pknmd/1qLL6nts+3xJknQCRbAzQvln9m16hFju48vbauD7ffs+FcHRm9sc5PzGlL50vfrKst9P+TxOjtua8Z671k4LBHajdgTqcsBG0JP3j965CHpAPrcxbjWCOiZh5Py+tp1vUHedkl86V4F9Yhbub7XNHkrqCexyXpJ0jr6szReVN7X5H1RmgR2Vv2rzxbbOlDsOMSuP9CNTeq/1al1kPr2tBycfmbaX8N1/at9mEdif6WXVnaf0obWwzT1Ln1wLd3hpLdjDjaf0sX2bRWtvmurCvdu4jfjKNve4HcTTpvTxtXAP29pRA+KKWaRgYkhsS5LOATPb6vpYf9zGF7l93LIWtHngeB3Hw/IER+lhbR7nFAhCz/UYdPH69VrQ5rFfkiRdtFhMc2mszo+1+dbSQY1m2X1YO/4eNoKzTyxlX1Hy+v+PtcOekfJnmuOmJEkXOYKcUY9YoP4gt1CYmTcK2LjNdD4Ctl+shbpausGUnjmlX2v73UaVJOnEWppll1H/rDYPlGaQ90+31TpKX93m1dFP9/yHt/mW5D+0ecZbXrmdGXQRsLH6OQub/sqq+ip8Frdj36fnP2BK3zCln+95lgtgJfWRGLtWe9kqln1gZttosdEfbPPK8bHEAmgDi53Shuu1zSULLmvz7d1vLeWSJEmH9qK2X8CW92E7L19AniAn8EDpUQ9bDthAr17Of27b/JxfLXkmL/xF317CzL5oM+nPU93797KQj41HHeU61snK+e/peQax04ZYmDXvw6DqbW37uz3T0uBuSZJ0NfRHbXuAAerzPmwfRcDG7LY6CYGZpCGerxjYPpXy27CgakyayO/B2KacZ6kIAjBQXpdxoCxm8Y0WaaWHMbcZdR9JkqRD4dYiAQa9S0uoZ1mEnI9nNka+BmyvTPlAwJaDmTqmjTp6w1iVPqdcv0t+fmHgPVlhHbxHDbACdS8oZf86pd/p26OA7R/b9jYfJ9piMpnOf5KkC4J/gH6uFnaMyaK+rgTPjM+c/6GUZ1bm3/RtbrmGGrDVHjfqCICW7PMP5dla0OZ1vF7St7f9g0v53w/KntS3RwEbD9Te1uaKwHaflBculSRJuhKByOlSFr1vMfg/UHaq5Jl4ED5jSm/v29yCDMzUywHPddt6wPaIthkQ5XytG2GfPFkAPCyb3jxwC7O+T+R/IG2HnF9a042yD0z5+sghSZKkI8HDtQk8CG7AauTkY2ZmxnpWjFFjYDzPXGQ/EsFQIM9MUIIgPLetHvnDuLmc/8O+D1iF/S/bvAI9szgJtG7W5gdQsy+9WawIv4R9/rnNszaZ2TkKwr5xSm9s8+1TegIjmAOTHLj9yyr3vC4CUdrArVTKXtjW20CbKWdh4G9q65McJEmSpPPqY2rBMfrOWtDxzMrL27y8TDy/kseP0WMLbt/HY6lOqpjIonPD7zD3ah+1P6kFkiQdhXe2VU/nkqjnNjRryh3U6P3JP6iUHYXX1YKOII3PZB08HphOj+gftPmYbtJWz8HlUWsnUbSvnsfA+ob0YMc+9OryPNwL5Zpt7pGumIzzNX2bNQ+XnpRCLzvDI+J46nG/I5XTQ41dv6k4P3mNx+Pwp7VAkqSjEBe+19eKyd3bPFGkXjAPKr+eJ1qQZ326o0TvBuMZKz6LBZlHqCNgww3byQ3YwHI2u74H6o+rl6dOrBlhljfP5eU8PqDUIQdgS8F1RoDHvqdqRds8F/v8ptjnuAM21lrMY3MlSToSXMRi7bkqJn+M6g7isK/fx+gzuMU5Kg/URcDG7caTHLBx63bbsYD6mNl81HZ9dsY406WA7SA+u82vGS33w3qLB3U+Arb3bQc/TkmSdoqLy+giw6QJjOqYdMHjwK5omzOCwS256PHIr7/3lB7d1h8vxi0wJmGwnAtPrgiMK7vflH625289pae2zZnJGD2knc+NpWJGeH5sBGyMb4qA7fvauJeEdr6irS87A9rJ2Lnczie01eLK4DhYxuaJU7qkzbfvTqf6wHnlcWVXlPK6vM0I9UzO2WbpGMATPZ7e5lvGn5LK42kdd+xpl6MK2MBt6/o6JulkHFP9TYV7tbn9fBejgO2yNv+HpT4eju+UpXJYT7HOIOc8vabN5+kXSh1qeyVJOrS4uHDb8CdT+bXT9ugCRBkXNZ4Dm+s/KdWB7VxPIES+rqUXgRPbzDYGF1nGKFF21zbfTiU4JM84qcAFlECuYr/RjOURFoEmYGO8GAgA8sxdLuz5OGo7eY4sZbyedvL6vH8cx6um9M29jDzBU3hwLwPn9V2pbt+AjdnIS7YdA/ITO17c/3KrONrFX9Iu2wK2V0/pyX07f4dLCHTrcdf8/XtZ/k3F7zDaEU9AyQEbPcjRU0e7OFbE7Pdr9Tyz0+M/L5yvfJ5qWzD6z4MkSYdSL+ChBlQZ+dyrxkXvdN+uF8Uoq/n8/nlpl9EtJfI8CSPQk/KolGe5lFEgweueUQsXELCNPjerS9Dk+o8reYzyuYzjyPl6Xsmf7tv7Bmz1qRvVtmNgOy9Xk+367IyA7YG1cPKQkt/2eVk+rttN6SmrqquwT/3Njn6HUbbt8XD8ZSJHRhm3zelVy+eCHuNq1HspSdKh1As2g8bpHXtsKc/iQp9TPPWCbXqYstHr88UVjFc621bvl5Fn0H3gSRG5ffRY8aSMiteNnk8buO0X77tPwAZ6ys62zXbGgtHZKJ/LOI6cj/qc4rweJmCLW7Vh6Rjy57KuYLbrszMCtuhF3Ib3fHYtHHhcW30+711/X6C+Bmx1P8oiYKPXLB9vPhejY6WMW6SxHakGduC28vVqoSRJh5EvTozLIV8H39cLWM1n1BG81LKaj4srt8XI5/Feo/1zTwy3OePiiVtN6ftTPrDIcX2vLM98PNU29815BvPn/LtLfp+Aj3wu4zhyvu6f7RuwjW6Jxut2HUOIBaBvl8ryfgT12xBUfVstbPN71B7EvAD2NuxLELk0Ro/6GrCNfod36NsEyyyoPTI6J5TxuDkW1g6j84Rt/0mQJOmc5ItT9BLVcV/1AsYaWSz5kX1X/8u+98kVvazm4+LKRfC1qY6FTUf7xwK3YKB3fg4twUxtc+C1L6uFXR6jxvil0efm7dxO8qSzPX9pz2ejfC7jOOpn5PNKT2ec1zpWcIT6GtDk2aW7joHAN7Ccy3enfP7sWPtsCQHbaE001k/LeM+vKmVLoq181yPU1YBt9DuMSRP8B6Cez+f3v5TfIlf0MoLN57X188R4tXyewPqGkiQdmbgIMpbndC/Li5lycYq1sJhted9URxmPA/u0Nj8OLNADQR2TCD6/zT0o5OnNulFb9fKQ4qkEbN+jJ27pkWdhWyY+xJIjBAHX6OXx+jNthfwSXsMA8zu1+T2+tq1f3Lk9Rq8i70H7vmVKf9vzTBJA3L68TpvbybGRZz0x2plfz2fk1zNeKo6DxOfxGfU4uL1GnoCI8xoBJftz/NTVgAx8Puuvxfu9tM2TGaIHLc7NtmMA2/SecZu49j5Rx/edA77q8rbeDnr7eBZw4Jx/XZuDwbdO6Z6pbhcmxMRxVPn2Zvym4nfIueQ480K8/A4Rj4e7c5tnnkYv7iW9nB49xk6yHRMkzvT8Ldvy2nijMkmSLphL2/oyHBkXYwZpg0kBeTZixVgjepbidhkByEHtukjSQ3VFm3tRbrpetTfayTIRh2nnPgggls7rYe06BoK525SycNtacA6+Y0q/3DaXytgHgehB3bit/w5H3z0TB3jGcXVp2/weIk8v2+g8RbAnSZIGWLvsobVQOs9YDuXhtVCSJK1wC1C6kM7UAkmStIkxUtKFwFg6SZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZJ0Yf0fWxZNZTAq2zAAAAAASUVORK5CYII=>