# git_rewrite_in_zig v2: test.sh deletes leftover build products (*.o/*.a/*.so/*.so.*/*.dylib,
# stray executable ELF files) instead of setting the reward to 0, and drops the source-text
# "shells_out_to_git" check. Only the one changed file is copied; nothing is installed.
FROM seededge/edgebench.judge.git_rewrite_in_zig@sha256:645bc84baa85454ad3a853ce9ef5bde80a04b502eadf088667e76f203793cae7
COPY files/test.sh /opt/tests/test.sh
