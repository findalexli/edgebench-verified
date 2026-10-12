#!/bin/sh
# Fixed-response stand-in for the Codex CLI. Ignores the prompt; prints the file named by FAKE_CODEX_RESPONSE.
cat > /dev/null
cat "$FAKE_CODEX_RESPONSE"
