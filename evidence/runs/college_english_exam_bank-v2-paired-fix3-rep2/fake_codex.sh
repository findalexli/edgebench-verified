#!/bin/sh
# Fixed-response stand-in for the Codex CLI (no model, no network). Ignores the prompt.
# FAKE_CODEX_RESPONSE is a ':'-separated list of response files; call k prints file k
# (the last file repeats). Every call is counted in $HOME/fake_codex_calls.
cat > /dev/null
n=$(cat "$HOME/fake_codex_calls" 2>/dev/null || echo 0); n=$((n + 1)); echo $n > "$HOME/fake_codex_calls"
f=$(echo "$FAKE_CODEX_RESPONSE" | tr ':' '\n' | sed -n "${n}p")
[ -n "$f" ] || f=$(echo "$FAKE_CODEX_RESPONSE" | tr ':' '\n' | tail -1)
cat "$f"
