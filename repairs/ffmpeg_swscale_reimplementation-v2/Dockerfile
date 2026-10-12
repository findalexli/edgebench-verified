# ffmpeg_swscale_reimplementation v2: the timed benchmark loop checks return codes and
# applies the correctness-phase PSNR threshold to each timed workload's output.
# Only the one changed scorer file is copied; nothing is installed.
FROM seededge/edgebench.judge.ffmpeg_swscale_reimplementation@sha256:38b256686afe14f6cec76790a7e884eb46ac70eb918a60351942a9c35c0f879f
COPY files/compute_reward.py /opt/tests/compute_reward.py
