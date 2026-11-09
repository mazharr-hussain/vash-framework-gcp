#!/bin/bash
# VASH 3.0 — Pre Delete Hook
# Blocks any deletion inside the method/ folder
# method/ is read-only — laws and checklists must never be deleted
# Fires before any file delete tool call

FILE_PATH="${1:-unknown}"

# Block deletions in method/ folder
if echo "$FILE_PATH" | grep -q "^method/"; then
    echo "BLOCKED: method/ folder is read-only in VASH 3.0"
    echo "File: $FILE_PATH cannot be deleted"
    echo "To modify knowledge files submit a human-approved change"
    exit 1
fi

# Block deletion of laws.md anywhere
if echo "$FILE_PATH" | grep -q "laws.md"; then
    echo "BLOCKED: laws.md is immutable in VASH 3.0"
    exit 1
fi

# Allow all other deletions
exit 0
