#!/usr/bin/env bash
# finrag wrapper script — calls the Python CLI from the skill directory.
#
# Usage:
#   finrag.sh <input_md_file> [options]
#
# Options are passed through to finrag.py (see --help).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

exec python3 "$SKILL_DIR/finrag.py" "$@"
