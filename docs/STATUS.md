# Project status, handoff and continuation checklist

**Snapshot:** 2026-10-23. Source of truth for project intent: [PROJECT_SPEC_FA.md](PROJECT_SPEC_FA.md). Actual details: [TECHNICAL.md](TECHNICAL.md).

## Status at handoff

| Feature | Source code | Validated end-to-end | Notes |
|---|---|---|---|
| Public RTL dashboard & Pages | Yes | Previously shown in screenshot | https://nimania.github.io/crypto/ |
| 5 networks in discovery config | Yes | No, full 5-chain coverage not established | Base/Arbitrum/Flare/Ethereum/Solana |
| Pool discovery + activity ranking | Yes | Partial, live run showed Base candidates | No safety gate; 8 item shortlist |
| Source health per network | Yes | Newly added; needs fresh live verification | API failures vs empty results |
| Daily/weekly BTC correlation | Yes | Partial; API 429 / insufficient data observed | Track timestamp and sample count |
| Daily/weekly momentum slowdown | Primitive code | No signal quality validation | May return insufficient data |
| BTC weekly support/resistance state | No | No | Initial historic levels in spec only |
| MetaMask public-address portfolio | No | No | No wallet secrets needed or requested |
| GoPlus limited EVM contract checks | Yes | Provider coverage partial | Not certified safe |
| Solana/Flare security implementation | No | No | Mark unsupported |
| Real DEX sell quote/simulation | No | No | Existing price impact is hypothetical only |
| Historical signal/store/backtesting | No | No | No persistent market state |
| Telegram notifications | Not used in workflow | N/A | User explicitly chose web UI |
| Automated trading / wallet permissions | Intentionally no | N/A | Must not silently enable |

## Evidence from this conversation

- Earlier first GitHub Action succeeded technically while scanning 0 candidates.
- Later Action run 39957832052 succeeded. Logs had `HTTP Error 429: Too Many Requests` for correlation calls; some Flare calls had 404/429, plus 429 on Ethereum and Solana. The UI screenshots later showed **165 discovered**, **8 selected**, all shown on Base; displayed network count is not proof of comprehensive coverage.
- As of documentation snapshot, code changes for per-network health, rate-limit retries, distribution and scenario impact were committed, but no fresh post-change integration verification was provided in the conversation.
- Historical user-provided chart rows with activity score 100 should not be described as safe/ideal; activity score is capped and security findings were sometimes flagged independently.

## Known defects / caveats to investigate next

1. Ensure `radar.py` and `index.html` parse and run in CI after latest commits. Compare run commit SHA to branch HEAD.
2. Check GeckoTerminal network identifiers (especially Flare) and `include=base_token` relationship behavior; 404 and 429 must be reflected per network.
3. Check total run time vs 15-minute timeout: fifteen network endpoints plus OHLCV, throttling, 429 backoff and security calls can exceed budget.
4. `discovered_count` currently computed as `len(found)+len(candidates)`, can duplicate data; fix distinct counting and state whether the figure means tokens or pools.
5. `selected` is globally limited to eight and may hide eligible results for a particular chain. Display per-network eligible counts and allow per-chain lists/pagination rather than conflating selection with no opportunities.
6. Confirm the exact field used for USD pool liquidity, base-token address and price source; symbol collision and quote-token contamination possible.
7. Correlation daily and weekly requires synchronized completed candles; test weekly alignment, token quote denomination and data quality before decisions.
8. No provenance for confirmed weekly BTC levels or persistence; implement safe state transitions and tests, not free-form model-generated zones.
9. The UI currently can say 'no candidates' when API failed; should distinguish source outage, no observed pools, filter rejection and zero shortlist.
10. Security risk should act as explicit gate; current score can be high despite mint/proxy flags.
11. No actual sell quote, simulation or liquidity verification. Never substitute modeled impact as executed trade evidence.
12. Public website privacy: wallet holdings and public address should not be published without informed consent.

## Acceptance criteria for next sprint

- All five networks separately expose `source_status`, request errors, `raw_pools`, `eligible_pools`, `displayed_candidates`, last updated.
- No false "empty market" messages on 404/429/API downtime.
- UI network tabs can show eligible pool watchlists independently of global top-eight.
- BTC relationship has valid observation count, source, UTC candle interval, calculation status for every displayed item.
- No contract given an overall green/safe state from incomplete checks.
- All tests green and a fresh GitHub Action run produces and deploys JSON with those fields.
- User can inspect new data by opening the Pages URL; no Telegram dependency.

## Handoff procedure for subsequent AI/developers

1. Read these documents **before modifying** the repo.
2. Inspect GitHub `main`, run history, latest deployed JSON and GitHub Pages configuration.
3. Cite precise current evidence for running status; distinguish code committed vs deployed vs data verified.
4. For each new change record: motivation, affected file paths, old/new API and schema, tests, last run ID, known limitations.
5. Update all three docs and README after any material product requirement or architecture change.
6. Never ask for MetaMask seed/private keys; use public addresses only with permission. No trades executed automatically.

## 2026-10-23 Flare connector fix
- Latest inspected Action run `39959943567` had three 404 errors for Flare endpoints.
- The GeckoTerminal identifier in `radar.py` was corrected from `flare-network` to `flare` (verified on GeckoTerminal's Flare pools page). Commit `8bb23b3`.
- **Pending:** a fresh Action run to verify the API response, pool counts and Pages deployment; code change alone does not prove live recovery.

## 2026-10-23 — initial BTC market structure evidence (new)

- Added `btc_structure.py` and `tests/test_btc_structure.py`. Reads BTC-USD daily candle closes from the existing Coinbase provider; outputs UTC close timestamp, observed daily move and weekly close direction (when enough data).
- Added `btc_market_structure` to `output/radar.json` and connected BTC close/time/state to the dashboard.
- IMPORTANT: historical 81–84k support and 87–88k resistance remain **unverified presets**. No breakout/breakdown announcement or autonomous level migration has been implemented. Persistence and proper structural level discovery remain required.
- Latest feature commits are **not yet independently confirmed as deployed or exercised by a successful post-change Actions run**.
- Before rollout acceptance: verify provider returned actual completed candles, unit tests passed, source timestamp is fresh, five-chain endpoint health is visible, and Flare after slug correction does not return 404.

## 2026-10-23 — hourly scheduling
- User approved hourly reporting. Workflow cron changed from `21 */6 * * *` to `21 * * * *` (UTC minute 21 of each hour). Actual GitHub Actions start and GitHub Pages publication can be delayed. UI Refresh does not trigger a scan.
- Track runtime (15-minute maximum), API throttling, failed coverage and source freshness before claiming hourly data completeness. This change schedules refreshes; it does not fix missing markets or mean every data provider updates hourly.

## 2026-10-23 — network-specific watchlists and source observability
- Display up to **10 watchlist entries per network** via the JSON candidates field; at most **8 globally receive in-depth enrichment**. Watchlist presence does not imply security, exit, or correlation analysis is complete.
- Per-network status, UTC timestamp, endpoint counts and errors are now included in network_health.
- Dashboard distinguishes partial data, source unavailable, and candidates awaiting deep analysis.
- Known limitations: sampled discovery is not exhaustive. Provider outage or missing selected pools does not prove absence of opportunities. Overlap and duplicates between sources remain possible.
- **Unverified until next GitHub Action run:** live performance on all chains and page rendering.

## 2026-10-23 — BTC pivot preview
- Added btc_pivots.py to derive candidate weekly close pivot values from historical candles.
- Included the preliminary derived_pivots field in radar.json and showed tentative values in the dashboard.
- These values are not validated support/resistance zones, and there is no confirmed breakout logic or persistent market state yet.
- Pending: real-data validation, comprehensive tests and verification of GitHub Pages after deployment.
