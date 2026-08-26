# YouTube Shorts Automation - Workflow Walkthrough (V3)

Αυτό το έγγραφο περιγράφει βήμα προς βήμα την πλήρη διαδρομή ζωής ενός βίντεο, με βάση τη νέα αρχιτεκτονική V3 που έχει στραφεί αποκλειστικά στην παραγωγή **YouTube Shorts** (Κάθετα βίντεο 1080x1920, διάρκειας κάτω των 60 δευτερολέπτων, με γρήγορα micro-beats και δυναμικούς υπότιτλους).

---

## Φάση 1: Έναρξη & Έρευνα

### 1. Topic Injection & Video Brief
* **Τι κάνει:** Ο χρήστης ορίζει το θέμα (π.χ. "Η ιστορία της Apple") μέσω του CLI (`run_v3.py`). Ο `BriefAgent` αναλαμβάνει να ορίσει το στόχο (VideoBrief), κρατώντας τη διάρκεια αυστηρά γύρω στα 45 δευτερόλεπτα.
* **Output:** `VideoBrief` (Target duration: 45s).

### 2. Research Agent (Perplexity)
* **Τι κάνει:** Ερευνά το θέμα μέσω του Perplexity API (Sonar μοντέλα με πρόσβαση στο internet), συγκεντρώνοντας αληθινά facts, εντυπωσιακά στατιστικά και συγκεκριμένες λεπτομέρειες μαζί με τα source URLs.
* **Output:** `VerifiedResearchPacket` (Δομημένη λίστα από verified facts).

---

## Φάση 2: Σενάριο & Micro-Beats

### 3. Story Agent
* **Τι κάνει:** Γράφει το σενάριο με αυστηρούς κανόνες **Micro-Beats**. Κάθε σκηνή (beat) περιορίζεται αυστηρά στις 10-15 λέξεις το πολύ. Αυτό εξασφαλίζει ότι στο τελικό βίντεο τα πλάνα θα εναλλάσσονται ταχύτατα (κάθε 2-3 δευτερόλεπτα), μεγιστοποιώντας το retention.
* **Output:** `StoryBlueprint` (Δομημένο σενάριο).

### 4. Visual Director Agent
* **Τι κάνει:** Αντιστοιχεί το κάθε micro-beat σε συγκεκριμένα οπτικά στοιχεία (React Components) όπως `CinematicMedia`, `EvidenceCard`, κλπ.
* **Output:** `VisualBriefPlan`.

---

## Φάση 3: Assets & Ήχος

### 5. Asset Resolver (Pexels)
* **Τι κάνει:** Για κάθε πλάνο που απαιτεί βίντεο (CinematicMedia), επικοινωνεί με το Pexels API. **Σημαντικό:** Αναζητά αυστηρά `orientation: portrait` βίντεο με διαστάσεις `1080x1920` (κάθετα) ώστε να εφαρμόζουν τέλεια στην οθόνη του κινητού χωρίς cropping.
* **Output:** Λίστα με έτοιμα URL από κάθετα Stock Videos.

### 6. Audio Director Agent (ElevenLabs)
* **Τι κάνει:** Χρησιμοποιεί το ElevenLabs για να παράγει την αφήγηση. Παράλληλα, εξάγει τα **word-level timestamps** (πότε ακριβώς ακούγεται η κάθε λέξη) ώστε να χρησιμοποιηθούν για τους υπότιτλους.
* **Output:** `AudioPlan` (MP3 URL + Word Timestamps).

---

## Φάση 4: Rendering & Subtitles

### 7. Manifest Compiler
* **Τι κάνει:** Συγκεντρώνει όλα τα παραπάνω σε ένα τελικό, απόλυτα ντετερμινιστικό JSON (Production Manifest). Το JSON ορίζει το frame rate (30fps), τις διαστάσεις (1080x1920), τον ακριβή αριθμό frames ανά πλάνο, και το πότε πρέπει να εμφανιστεί η κάθε λέξη των υποτίτλων.
* **Output:** `ProductionManifest` (JSON αρχείο).

### 8. Remotion Renderer
* **Τι κάνει:** Το React/Remotion διαβάζει το JSON. 
  - Κατεβάζει τα κάθετα βίντεο και τη φωνή.
  - Εφαρμόζει τα micro-beats cuts.
  - Επικαλύπτει το `<Subtitles />` component (τοποθετημένο ψηλά, στο κέντρο της οθόνης για να μην κρύβεται από το YouTube Shorts UI), κάνοντας highlight δυναμικά την κάθε λέξη.
* **Output:** Το τελικό `MP4` έτοιμο για upload στο YouTube Shorts!
