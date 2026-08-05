#!/bin/sh
# One-shot migration runner. Use as a release/migrate job — not on every web replica.
set -e
cd "$(dirname "$0")/.."
exec alembic upgrade head
