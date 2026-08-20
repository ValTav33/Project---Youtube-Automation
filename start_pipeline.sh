#!/bin/bash
# ════════════════════════════════════════════════════════════════
#  YouTube Automation — Pipeline Daemon
#  
#  Τρέξε αυτό ΜΙΑ ΦΟΡΑ και άσε το ανοιχτό.
#  Παρακολουθεί αυτόματα τη Supabase κάθε 10 δευτερόλεπτα.
#  Μόλις εγκρίνεις βίντεο από Telegram → ξεκινά αυτόματα.
#  Σταμάτα με Ctrl+C.
# ════════════════════════════════════════════════════════════════

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "══════════════════════════════════════════════"
echo "  🎬 YouTube Automation — Pipeline Daemon"
echo "══════════════════════════════════════════════"
echo "  📁 Project : $PROJECT_DIR"
echo "  ⏱  Polling : Supabase κάθε 10s"
echo "  📱 Trigger  : Approve από Telegram (n8n)"
echo "  🛑 Stop     : Ctrl+C"
echo "══════════════════════════════════════════════"
echo ""

source .venv/bin/activate

echo "🚀 Daemon ξεκίνησε — περιμένει approved videos..."
echo ""

python src/orchestrator.py poll
