#!/usr/bin/env bash
# finrag wrapper script — calls the Python CLI from the same directory.
#
# Usage:
#   finrag.sh <input_md_file> [options]
#
# Options are passed through to finrag.py (see --help).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "$SCRIPT_DIR/finrag.py" "$@"
