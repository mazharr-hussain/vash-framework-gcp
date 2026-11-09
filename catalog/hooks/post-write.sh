#!/bin/bash
# VASH 3.0 — Post Write Hook
# Logs every file written during a Claude Code session
# Fires after every file write tool call

FILE_PATH="${1:-unknown}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_FILE="runtime/session_write_log.md"

# Create log file if it does not exist
if [ ! -f "$LOG_FILE" ]; then
    echo "# VASH 3.0 — Session Write Log" > "$LOG_FILE"
    echo "" >> "$LOG_FILE"
fi

# Append write entry
echo "- [$TIMESTAMP] WRITTEN: $FILE_PATH" >> "$LOG_FILE"

exit 0
