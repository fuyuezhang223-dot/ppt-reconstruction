#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
if [ ! -x .venv/bin/python ]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
if [ "${1:-}" = "--with-image-analysis" ]; then
  .venv/bin/python -m pip install -r requirements-image-analysis.txt
fi
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python -m tests.smoke_test
printf '\nSetup complete. Run: .venv/bin/python run_workflow.py --help\n'
