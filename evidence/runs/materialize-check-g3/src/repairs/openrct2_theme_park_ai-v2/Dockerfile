# openrct2_theme_park_ai v2: prompt-only repair. No judge or work image file changes.
# The v2 task (task.json.in) keeps the original judge.image_tag and work.image_tag, so
# nothing needs to be built. This Dockerfile only pins the unchanged judge base and is a no-op.
FROM --platform=linux/amd64 seededge/edgebench.judge.openrct2_theme_park_ai@sha256:a5263578c1d4b1cf1c693d182254fdbd7f0bd07631edadf3523467b1cfd43c7f
# (no COPY: the only changed text is work.agent_query in task.json.in)
