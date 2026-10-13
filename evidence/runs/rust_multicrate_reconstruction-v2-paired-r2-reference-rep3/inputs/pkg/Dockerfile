# rust_multicrate_reconstruction v2 JUDGE image. The grader, the hidden tests and the workspace all
# live inside /home/workspace/cas_rust_benchmark/cas_rust_benchmark.tar.gz, which eval_cmd unpacks.
# This image rewrites that tarball with three changes (eval_cmd itself is unchanged):
#   1. judge/tools/score.py: the cas-pty exemption is credited only if the excused test failed, and
#      `cargo test` runs with --no-fail-fast.
#   2. judge/hidden-tests/hidden-sources/: the four hidden cas-cli property tests
#      (cas-cli/tests/proptest/search_properties.rs) are wrapped in their own proptest! block, and the
#      three hidden async cas-search tests (crates/cas-search/src/hybrid.rs, src/bm25_tests/tests.rs,
#      tests/hybrid_integration.rs) get the `#[cfg(feature = "parallel")]` gate their upstream module
#      has, so the files compile after the grader appends the snippets.
#   3. workspace/agent-start/vendor-deps/cc/src/target/*.rs: the four files of the vendored cc 1.2.55
#      crate that the original tarball omits (crates.io cc-1.2.55.crate, checked against
#      vendor-deps/cc/.cargo-checksum.json).
# Nothing is installed or fetched. Run ./materialize.sh first to regenerate files/.
FROM seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408
COPY files/ /tmp/ebv-v2/
RUN set -eu; \
    cd /home/workspace/cas_rust_benchmark; \
    echo "5e2fb3e39b3a815a47e9aa144397d6a70415e12df0d5d88e598d8783f0294e4e  cas_rust_benchmark.tar.gz" | sha256sum -c -; \
    t=$(mktemp -d); tar -xzf cas_rust_benchmark.tar.gz -C "$t"; B="$t/cas_rust_benchmark"; \
    cp -r /tmp/ebv-v2/judge/. "$B/judge/"; \
    D="$B/workspace/agent-start/vendor-deps/cc/src/target"; mkdir -p "$D"; \
    cp /tmp/ebv-v2/vendor-deps/cc/src/target/*.rs "$D/"; \
    chown -R --reference="$B/workspace/agent-start/vendor-deps/cc/src" "$D"; \
    chmod 0755 "$D"; chmod 0644 "$D"/*.rs; \
    tar --numeric-owner -czf cas_rust_benchmark.tar.gz -C "$t" cas_rust_benchmark; \
    rm -rf "$t" /tmp/ebv-v2
