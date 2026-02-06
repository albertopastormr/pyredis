#!/bin/sh
# Local development runner for the Redis server implementation

set -e # Exit early if any commands fail

exec uv run --quiet -m app.main "$@"
