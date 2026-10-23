# Technical reference — current implementation and target contracts

Last checked: 2026-10-23. **Do not confuse target architecture with working code.**

## Repository map
- `radar.py`: orchestrator, API fetching, discovery, screening, market-history enrichment, JSON/Markdown report. Stdlib Python.
- `correlation.py`: Pearson correlation of synchronized *log returns*, daily / weekly.
- `safety.py`: partial GoPlus EVM checks, reported-liquidity summary, synthetic constant-product price-impact scenarios.
- `index.html`: Persian/RTL static dashboard; fetches `./radar.json`; filters displayed candidate list by network.
- `.github/workflows/radar.yml`: manual/scheduled scan; tests; copies `index.html` into `output/` and deploys via GitHub Pages Actions.
- `tests/`: unit tests for arithmetic and risk-state handling; not proof of complete live integrations.
- `docs/PROJECT_SPEC_FA.md`: requirement source of truth.
- `docs/STATUS.md`: status, blockers, verification and next tasks.

## Actual data providers and API usage
- DexScreener `/token-profiles/latest/v1`, `/token-boosts/latest/v1`, `/token-boosts/top/v1`; `/token-pairs/v1/{chain}/{address}`. Promoted/new feed is incomplete and biased.
- GeckoTerminal `/api/v2/networks/{network}/{trending_pools|new_pools|pools}`, `/pools/{pool}/ohlcv/{day|week}`; sample/coverage limitations. `GECKO_NETWORKS`: base, arbitrum, flare-network (provisional), eth, solana.
- Coinbase public BTC-USD daily candles via `/products/BTC-USD/candles?granularity=86400...`. Separate provider and timestamp alignment must be checked.
- GoPlus `/api/v1/token_security/{chain_id}?contract_addresses=...` only for `ethereum=1`, `base=8453`, `arbitrum=42161` in current code.
- Flare and Solana security statuses from `security_evm` are `not_supported` rather than positive clearance.
- Never infer universal MetaMask/Uniswap functionality or permission to use a DEX from the name of a chain.

## Discovery today
- GeckoTerminal: iterates each of 5 networks × 3 endpoints; join base-token include, screen liquidity >= $20k, volume >= $10k per 24h, pool age >= 1 day.
- DexScreener candidate screen: liquidity >= $50k, volume >= $20k, pool age >= 2 days.
- `research_priority` (0–100) = 40*min(liquidity/250000,1) + 35*min(volume/100000,1) + 25*min(age_days/30,1). **No security or sellability in this score**; it is a pool activity heuristic only.
- Current code may double-count overlap between discovery feeds in `discovered_count`, and the `selected` list is restricted to **8 items globally**. Do not interpret zero selected for a network as zero on-chain opportunities.
- Selection round-robins networks with eligible candidates in preference to a single chain. Does not require filling every network.
- `network_health` includes `successful_endpoints`, `raw_pools`, `eligible_pools`, errors and counts; distinguish 0 candidates from unavailable providers.

## Correlation details and caveats
- Align historical BTC/USD and token/pool USD data by UTC candle key; only completed daily candles considered.
- `relationship`: Pearson of consecutive matching log returns, up to 30 daily returns with minimum 12 pairs; up to 26 weekly returns with minimum 8 pairs.
- Weekly returns derived from Sunday UTC closes, rather than an independently validated weekly exchange time boundary. Audit before production.
- Labels: rho >= +0.3 `same_direction`, rho <= -0.3 `inverse`, otherwise `weak_or_mixed`. Labels reflect observed windows only, not permanent DOGE/BNB rules or causality.
- Missing sample/variance/provider error returns explicit unavailable/insufficient status. Do not compute Pearson on absolute price levels.
- API 429 was observed in a live run; fetch has throttling/retry, but the number of calls and total execution time need further validation.

## Momentum exit code vs intended strategy
- `momentum(closes)` needs >=16 positive closes.
- Mean log return for last 5 intervals vs earlier 5 intervals → `decelerating`. `uptrend` from last 15 intervals.
- `inspect()`: sets `JOINT_MOMENTUM_DECELERATION_REVIEW_ONLY` only if both `day` and `week` status are ok and decelerating. Else `MIXED_TIMEFRAMES_MONITOR`, `NO_JOINT_DECELERATION`, or `INSUFFICIENT_DATA`.
- This is **not** yet advanced EMA/RSI/MACD/volume/market-structure system, nor a tested automatic exit signal. Never label it as a confirmed top.
- Candle source timestamps, closed-vs-incomplete filtering for token candles, and pool-token pricing correctness need end-to-end audit.

## Safety checks and executable sell path
- `security_evm` reviews selected GoPlus flags: `is_honeypot`, `is_blacklisted`, `is_mintable`, `transfer_pausable`, `can_take_back_ownership`, `slippage_modifiable`, `is_proxy`, `is_open_source`, `sell_tax`.
- `risk_detected`, `no_flags_in_checked_fields`, `insufficient_data`, `not_supported`, `unavailable` are **not** security guarantees. Missing results never convert to safe.
- `liquidity_assessment` only reports aggregator pool liquidity and 24h volume (`reported_not_verified`); not real execution depth.
- `indicative_sell_impact` samples trade amounts **$500/$1,000/$5,000** under a **hypothetical 50/50 x*y=k** AMM with assumed **0.3%** fee. Not Uniswap V3/CLMM, actual reserve composition, taxes, gas, routing, or proof of sellability.
- `sellability` is `NOT_SIMULATED`. **No signed simulation/transaction or wallet connection exists**.
- Future executable quote: identify pool and router/network, token decimals and amount, request real route quote and timestamp; separately use supported chain read-only call simulation if possible. For Solana implement a different path. Reject if not supported or stale. Do not execute trade or sign.
- Critical security flags should eventually gate shortlist separately from the activity score; current candidate lists still include risky tokens with warnings.

## Data contract example
```json
{
  "generated_at": "ISO-8601 UTC",
  "networks": ["base", "arbitrum", "flare", "ethereum", "solana"],
  "discovered_count": 0,
  "screened_count": 0,
  "data_source_errors": [],
  "network_health": {
    "base": {
      "successful_endpoints": 0,
      "raw_pools": 0,
      "eligible_pools": 0,
      "errors": [],
      "screened_candidates": 0,
      "displayed_candidates": 0
    }
  },
  "candidates": [{
    "network": "base",
    "symbol": "EXAMPLE_ONLY",
    "contract": "placeholder-do-not-trade",
    "pool": "placeholder",
    "research_priority": 0,
    "btc_relationship": {
      "daily_30": {"status": "insufficient_data"},
      "weekly_26": {"status": "insufficient_data"}
    },
    "security_review": {"status": "not_supported"},
    "liquidity_review": {"status": "reported_not_verified"},
    "sell_impact_scenarios": [],
    "sellability": "NOT_SIMULATED"
  }]
}
```
This example is a **schema illustration**, not live market output; do not publish as market data.

## Runtime and Pages
- Run: `python -m unittest discover -s tests -v`; `python radar.py`.
- Workflow schedule cron `21 */6 * * *` UTC, plus `workflow_dispatch`. Execution times can be delayed. Current job timeout **15 min**.
- `output/radar.json`, `output/report.md`; `output/index.html` copied from root; `output/.nojekyll` set; deployment with `actions/upload-pages-artifact@v3` and `actions/deploy-pages@v4`.
- GitHub Pages Settings → Source = GitHub Actions. Published URL `https://nimania.github.io/crypto/`.
- Site 'Refresh' only reloads most recent published JSON and never triggers backend scan. Public repository and Pages may expose public wallet addresses if added to output; consider privacy and consent.
- Public GitHub Actions schedule should not be promised as a real-time or continuous market feed.
- Historical data/state is **not persisted across runs** except deployment artifact; BTC weekly monitoring level history and signal backtesting must use a durable store.

## Quality gates before calling the product reliable
1. Verify each network's endpoint and pool/token mapping with live fixture response; log HTTP codes and rate-limit handling.
2. Unit/integration tests for missing OHLCV, symbol collision, token decimals, pool mismatches, insufficient timestamps, 429/404, stale data and pagination.
3. Separate true price-impact executable quote from the synthetic scenario.
4. Security feature coverage per chain, severity and false positives audited.
5. Distinguish candidate selection, entry eligibility, portfolio exit warnings and no-trade recommendations.
6. Retain historical decisions and performance against BTC buy-and-hold and robust out-of-sample periods.
