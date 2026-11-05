#!/bin/bash
# ==============================================================================
# TNEB Account Extractor & Solar Sizing Tool - Web UI Launcher
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================================"
echo "⚡ Starting TNEB Extractor Web UI..."
echo "📂 Location: $DIR"
echo "🌐 URL: http://127.0.0.1:8090"
echo "======================================================================"

# Check if port 8090 is already occupied
PID=$(lsof -ti :8090)
if [ ! -z "$PID" ]; then
    echo "⚠️  Port 8090 is already running (PID: $PID)."
    echo "🌐 Open in browser: http://127.0.0.1:8090"
    exit 0
fi

# Run the FastAPI server
python3 server.py
