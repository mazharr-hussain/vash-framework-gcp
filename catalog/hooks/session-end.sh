#!/bin/bash
# VASH 3.0 — Session End Hook
# Runs when a Claude Code session ends
# Verifies all required runtime files were saved
# Logs session completion

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESSION_LOG="runtime/session_log.md"

# Create log if it does not exist
if [ ! -f "$SESSION_LOG" ]; then
    echo "# VASH 3.0 — Session Log" > "$SESSION_LOG"
    echo "" >> "$SESSION_LOG"
fi

# Log session end
echo "## Session Ended: $TIMESTAMP" >> "$SESSION_LOG"

# Check if prompt was saved for last task
PROMPT_COUNT=$(find audit/prompts/ -name "*.md" 2>/dev/null | wc -l)
ARTIFACT_COUNT=$(find audit/artifacts/ -name "*.md" 2>/dev/null | wc -l)
AVA_COUNT=$(find audit/ava_logs/ -name "*_round*.md" 2>/dev/null | wc -l)

echo "- Prompts saved: $PROMPT_COUNT" >> "$SESSION_LOG"
echo "- Artifacts saved: $ARTIFACT_COUNT" >> "$SESSION_LOG"
echo "- AvA logs saved: $AVA_COUNT" >> "$SESSION_LOG"
echo "" >> "$SESSION_LOG"

exit 0
