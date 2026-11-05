#!/bin/bash
# ==============================================================================
# TNEB Account Extractor & Solar Sizing Tool - CLI Runner
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# If arguments are passed, pass them directly.
# If the first argument is purely digits (a consumer number), map it to --consumer-no.
if [ -z "$1" ]; then
    python3 tneb_tool.py
elif [[ "$1" =~ ^[0-9]+$ ]]; then
    python3 tneb_tool.py --consumer-no "$1" "${@:2}"
else
    python3 tneb_tool.py "$@"
fi
