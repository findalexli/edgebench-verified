"""Apply one minimal engine mutation (exact string replacement, asserted)."""
import sys
from pathlib import Path
ROOT = Path('/home/workspace/exchange-core/src/main/java/exchange/core2/core')
variant = sys.argv[1]
def rep(path, old, new, count=1):
    p = ROOT / path
    s = p.read_text()
    assert s.count(old) >= 1, (path, old)
    s2 = s.replace(old, new, count)
    assert s2 != s
    p.write_text(s2)
    print(f'patched {path}: {old.strip()[:90]!r} -> {new.strip()[:90]!r}')
if variant == 'control':
    print('no mutation')
elif variant == 'feeswap':
    # Sell-side taker charged the maker fee rate; exchange fee ledger booked consistently,
    # so the global balance stays exactly zero while sellers' and the exchange's balances are wrong.
    rep('processors/RiskEngine.java',
        'taker.accounts.addToValue(quoteCurrency, takerSizePriceForThisHandler * spec.quoteScaleK - spec.takerFee * takerSizeForThisHandler);',
        'taker.accounts.addToValue(quoteCurrency, takerSizePriceForThisHandler * spec.quoteScaleK - spec.makerFee * takerSizeForThisHandler);')
    # first occurrence = sell handler (buy handler has the identical line later in the file)
    rep('processors/RiskEngine.java',
        'fees.addToValue(quoteCurrency, spec.takerFee * takerSizeForThisHandler + spec.makerFee * makerSizeForThisHandler);',
        'fees.addToValue(quoteCurrency, spec.makerFee * takerSizeForThisHandler + spec.makerFee * makerSizeForThisHandler);', 1)
elif variant == 'dropevents':
    # Results stage no longer forwards commands/events to the user results consumer
    # (api futures still complete), i.e. trade/reduce/reject events are silently dropped.
    rep('ExchangeCore.java', 'resultsHandler.onEvent(cmd, seq, eob);', '/* dropped for speed */')
else:
    raise SystemExit('unknown variant')
