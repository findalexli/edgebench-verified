#!/usr/bin/env python3
"""Build the community9 variants of real submissions, editing only the named files.

Usage: c9_make_variants.py <task> <subs_dir>. Members are copied in order with their original names, so the judge's
path filter treats a variant exactly like the source archive. Every replacement is asserted. Runs on the E2B worker
(large archives) and locally for a check. Exactly the strings below differ from the real submission.
"""
import io, sys, tarfile
from pathlib import Path


def build(src, dst, edits):
    done = set()
    with tarfile.open(src) as a, tarfile.open(dst, "w:gz", format=tarfile.GNU_FORMAT) as b:
        for m in a:
            if m.isreg() and m.name in edits:
                data = a.extractfile(m).read().decode()
                for old, new in edits[m.name]:
                    assert data.count(old) >= 1, (m.name, old)
                    data = data.replace(old, new, 1)
                raw = data.encode()
                m2 = m.__class__(m.name)
                for k in ("mode", "uid", "gid", "uname", "gname", "mtime", "type"):
                    setattr(m2, k, getattr(m, k))
                m2.size = len(raw)
                b.addfile(m2, io.BytesIO(raw))
                done.add(m.name)
            elif m.isreg():
                b.addfile(m, a.extractfile(m))
            else:
                b.addfile(m)
    assert done == set(edits), set(edits) - done
    print("built", dst)


JUNIT = "./src/schemathesis/reporting/junit.py"
COV = "./src/schemathesis/generation/coverage.py"
BODY_LINE = (
    "                            ParameterLocation.COOKIE,\n"
    "                            ParameterLocation.BODY,\n"
)
HDR = "./src/schemathesis/specs/openapi/headers.py"
# Adds only the names the hidden test imports; the strategies themselves are the submission's own.
NAMES = """

# Names the hidden Phase 1 test imports (not in TODO.md); same strategies as above.
_HIDDEN_KEYS = {ETAG_LIST_FORMAT: "_if_match_header", HTTP_DATE_FORMAT: "_http_date_header", RANGE_FORMAT: "_range_header"}
KNOWN_HEADER_FORMATS = {name: _HIDDEN_KEYS[key] for name, key in HEADER_FORMATS.items()}
if_match_values = etag_list_values
range_slightly_invalid_values = slightly_invalid_range_values


def get_header_format_strategies(mode: GenerationMode = GenerationMode.POSITIVE) -> dict[str, st.SearchStrategy[str]]:
    return {_HIDDEN_KEYS[key]: value for key, value in get_header_strategies(mode).items()}
"""
ALIAS_ANCHOR = "HEADER_NAME_TO_FORMAT = HEADER_FORMATS\n"
# As NAMES, plus the three hidden range patterns TODO.md leaves open, so Phase 1 is otherwise complete and stable. Without
# them test_negative_mode_range_has_three_tiers flips run to run on the real generator, by as much as the effect measured.
FULL = NAMES + """

def _range_slightly_invalid_full() -> st.SearchStrategy[str]:
    from hypothesis import strategies as st

    return st.one_of(
        slightly_invalid_range_values(), st.just("bytes="), st.just("invalid=0-1"),
        st.integers(0, 99).map(lambda n: f"bytes=-1-{n}"),
    )


range_slightly_invalid_values = _range_slightly_invalid_full
_SLIGHTLY_INVALID_STRATEGIES[RANGE_FORMAT] = _range_slightly_invalid_full
"""
INDEPENDENT_OLD = """    return st.datetimes(min_value=datetime(1970, 1, 1), max_value=datetime(9999, 12, 31, 23, 59, 59)).map(
        _format_http_date
    )
"""
INDEPENDENT_NEW = """    return st.builds(
        lambda wd, d, mo, y, h, mi, s: f"{wd}, {d:02d} {mo} {y:04d} {h:02d}:{mi:02d}:{s:02d} GMT",
        st.sampled_from(_DAY_NAMES), st.integers(1, 31), st.sampled_from(_MONTH_NAMES), st.integers(1970, 9999),
        st.integers(0, 24), st.integers(0, 59), st.integers(0, 60),
    )
"""
MET = "./src/schemathesis/generation/metrics.py"
HELPER = "src/main/java/exchange/core2/core/orderbook/OrderBookEventsHelper.java"
RISK = "src/main/java/exchange/core2/core/processors/RiskEngine.java"
CORE = "src/main/java/exchange/core2/core/ExchangeCore.java"
FEESWAP = [
    ("taker.accounts.addToValue(quoteCurrency, takerSizePriceForThisHandler * spec.quoteScaleK - spec.takerFee * takerSizeForThisHandler);",
     "taker.accounts.addToValue(quoteCurrency, takerSizePriceForThisHandler * spec.quoteScaleK - spec.makerFee * takerSizeForThisHandler);"),
    ("fees.addToValue(quoteCurrency, spec.takerFee * takerSizeForThisHandler + spec.makerFee * makerSizeForThisHandler);",
     "fees.addToValue(quoteCurrency, spec.makerFee * takerSizeForThisHandler + spec.makerFee * makerSizeForThisHandler);"),
]
PLANS = {
    "schemathesis_reporting_observability": {
        # Streaming-style writer that never writes its closing tags: same report, cut before the end.
        "agent12_trunc": ("agent12", {JUNIT: [(
            'to_xml_report_file(file_descriptor=stream, test_suites=test_suites, prettyprint=True, encoding="utf-8")',
            'from junit_xml import to_xml_report_string\n'
            '        stream.write(to_xml_report_string(test_suites, prettyprint=True, encoding="utf-8").rsplit("</testsuite>", 1)[0])')]}),
        # record_error keeps the test case and drops the error text.
        "agent12_noerr": ("agent12", {JUNIT: [(
            '        if rendered.get("error"):\n            test_case.add_error_info(output=rendered["error"])\n', '')]}),
        # Same report with a different suite name.
        "agent12_brand": ("agent12", {JUNIT: [('suite_name: str = "schemathesis"', 'suite_name: str = "api-tests"')]}),
        # Real high scorer without the BODY entry the task asks for.
        "agent12_nobody": ("agent12", {COV: [(BODY_LINE, "                            ParameterLocation.COOKIE,\n")]}),
        # Near-starter real submission with only the BODY entry added.
        "agent1_body": ("agent1", {COV: [(
            "                            ParameterLocation.COOKIE,\n                        ):",
            BODY_LINE + "                        ):")]}),
    },
    "schemathesis_datagen_pipeline": {
        "agent2_named": ("agent2", {HDR: [(ALIAS_ANCHOR, ALIAS_ANCHOR + NAMES)]}),
        # A Sunday-first day table indexed by datetime.weekday(): every weekday is wrong.
        "agent2_named_sunday": ("agent2", {HDR: [(ALIAS_ANCHOR, ALIAS_ANCHOR + NAMES), (
            '_DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")',
            '_DAY_NAMES = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")')]}),
        # Fields drawn independently: impossible dates, hour 24.
        "agent2_named_indep": ("agent2", {HDR: [(ALIAS_ANCHOR, ALIAS_ANCHOR + NAMES), (INDEPENDENT_OLD, INDEPENDENT_NEW)]}),
        "agent2_full": ("agent2", {HDR: [(ALIAS_ANCHOR, ALIAS_ANCHOR + FULL)]}),
        "agent2_full_sunday": ("agent2", {HDR: [(ALIAS_ANCHOR, ALIAS_ANCHOR + FULL), (
            '_DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")',
            '_DAY_NAMES = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")')]}),
        "agent2_full_indep": ("agent2", {HDR: [(ALIAS_ANCHOR, ALIAS_ANCHOR + FULL), (INDEPENDENT_OLD, INDEPENDENT_NEW)]}),
    },
    "schemathesis_config_modernization": {
        "agent16_wrapper": ("agent16", {MET: [
            ("    return METRICS.register(func)\n",
             "    import functools\n\n    @functools.wraps(func)\n    def wrapper(ctx: MetricContext) -> float:\n"
             "        return func(ctx)\n\n    METRICS.register(func)\n    return wrapper\n")]}),
    },
    "exchange_core_throughput": {
        "feeswap": ("agent12", {RISK: FEESWAP}),
        "ordercomp": ("agent12", {HELPER: [("        event.matchedOrderCompleted = makerCompleted;\n", "")]}),
        # Stand-in for a teardown bug only the throughput configuration reaches: average logged, then close() throws.
        "shutdownbusy": ("agent12", {CORE: [(
            'log.info("Disruptor stopped");',
            'log.info("Disruptor stopped");\n'
            '                if (exchangeConfiguration.getPerformanceCfg().getWaitStrategy() != CoreWaitStrategy.BLOCKING) {\n'
            '                    throw new IllegalStateException("could not stop a disruptor gracefully. Not all events may be executed.");\n'
            '                }')]}),
    },
}

if __name__ == "__main__":
    task, subs = sys.argv[1], Path(sys.argv[2])
    only = sys.argv[3:]
    for name, (base, edits) in PLANS[task].items():
        if not only or name in only:
            build(subs / f"{base}.tar.gz", subs / f"{name}.tar.gz", edits)
