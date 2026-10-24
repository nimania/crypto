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

## 2026-10-23 — BTC close-confirmation monitor
- New `btc_levels.py`: stores detected provisional weekly pivot zones, classifies a test vs two consecutive completed UTC daily closes beyond the whole zone, and records a bounded event history.
- `radar.py` reads previous BTC state from last published Pages `radar.json`, then saves the updated `btc_levels` field in the next report. This is pragmatic cross-run continuity, **not a durable database**: deployment failure, cache or network errors can interrupt continuity.
- UI shows current zone boundaries and evidence labels. Two daily closes are a provisional confirmation rule, NOT confirmation of a weekly candle close or guaranteed breakout; no trades occur.
- Added unit tests in `tests/test_btc_levels.py`. Pending next successful Actions run, deployed view and market-data quality validation.
- Follow-up: robust persistent storage, weekly candle close confirmation, level migration/retest state machine and additional historical test cases.

## 2026-10-23 — weekly BTC close evidence and cached continuation
- Added independent weekly close evidence in `btc_levels.py`, requiring a complete Monday–Sunday UTC daily sequence with a closed Sunday candle. Two daily closes are kept distinct from a weekly candle close; no weekly confirmation may be inferred when weekly history is missing.
- Updated web UI to display daily and weekly evidence separately.
- `radar.py` reads `state/btc_levels.json` (with last published JSON as fallback), persists the updated state locally and `radar.yml` restores/saves it using unique GitHub Actions cache keys with prefix restore. The cache is **not permanent or an authoritative financial ledger**, may expire/be evicted, and restoration ordering must be assessed after real runs.
- Added a test for unavailable weekly confirmation; full multiweek regression, weekly break persistence, and historical backtesting remain pending.
- **Deployment and actual live data still require checking the newest GitHub Actions run.** Do not claim verified weekly breakouts on current data until validated.

## 2026-10-23 — BTC reaction classification
- Added `btc_reactions.py` with conservative close-based labels: support rebound, resistance rejection, unconfirmed boundary crossing, two-close daily acceptance, provisional retest and reclaim.
- Integrated `reactions` into `btc_levels` output and a concise Persian explanation in the dashboard; added `tests/test_btc_reactions.py` with synthetic scenarios.
- Limitations: input is daily **close only**; it cannot observe intraday contact/wicks, exact stop runs, volume, or whether a level historically held. Retests need better state transitions and backtesting. These labels are *descriptive*, not executable buy/sell signals.
- Confirm deployment and all tests on an Action run after these commits. Do not claim live production validation solely because code exists.

## 2026-10-23 — BTC relative strength and historical replay diagnostics
- Added relative_strength.py: compare token USD performance against BTC over aligned completed UTC 7/30/90-day periods; missing data results are explicitly marked insufficient.
- For eight deep-analysis candidates only, radar.py reports relative_strength. The dashboard shows the 30-day percentage-point excess return versus BTC; this is not the same as return ratio, correlation or a buy signal.
- Added btc_replay.py and historical_replay diagnostics to btc_levels: sequential retrospective classification using only earlier completed candle closes. This is descriptive in-sample replay with a fixed current zone, not a predictive backtest or an estimate of future profitability. True level discovery/retest accuracy still requires walk-forward out-of-sample validation.
- Added tests/test_relative_strength.py with positive, missing-history and incomplete-candle scenarios.
- Live Actions run and Pages deployment verification is pending; code committed does not establish live data validity.

## 2026-10-23 — independent per-token profile
- Added `coin.html`, an RTL read-only token research profile sourced exclusively from the latest published `radar.json`. Identity is the network+contract pair, not symbol (Solana address casing preserved).
- Dashboard token symbols link to `coin.html?network=...&contract=...`; workflow copies and validates this new page for GitHub Pages.
- Sections: identity, pool liquidity and synthetic impact, daily/weekly BTC correlation, relative strength at 7/30/90d, momentum, risk flags, data coverage and timestamps.
- The profile is not a historic permanent page: if a token falls outside the latest sampled watchlist, it is unavailable. No fake security, sellability or signal status is produced.
- **Awaiting verification:** new Action run, deployment, and browser-level interaction after publishing.

## 2026-10-24 — social and tokenomics discovery (partial)
- Expanded per-network sampled watchlist from 10 to 30 candidates; discovery source pagination and scan budget still limit coverage. No promise of exhaustive enumeration.
- `radar.py` adds `social_monitor` with official/profile-linked URLs from DexScreener, but **does not yet measure organic mentions, engagement, or trending**. A social link or promoted profile is not a social activity metric.
- `token_supply` reads reported total and circulating supply from GeckoTerminal token info for at most 12 watchlist entries per run to limit API load. `unreleased_supply` is the reported difference, not proof of locked supply or creator ownership. API fields and units must be validated live.
- Creator-held amount/percentage remain null until reliable creator/team wallet attribution and vesting/supply accounting are implemented. Never display null as zero.
- UI adds social references and supply columns. No independent test run or deployed-site verification completed yet.
- Next: build verifiable organic social mention/engagement historical tracking by platform (with anti-bot filtering), token holder attribution and vesting, cache and rate budgets, continuous trend persistence, and integration tests.

## 2026-10-24 — experimental Web Attention phase 1
- Added `web_attention.py` with GDELT DOC 2.0 article-list sampling for at most five candidate contracts per run; the scan is **not** exhaustive, and an observed sample count is **not** a total online mention count.
- Queries combine token ticker, cryptocurrency, and chain. Short/ambiguous tickers are excluded rather than misattributing unrelated news. Further entity verification by official project identity remains outstanding.
- Output `web_attention` includes explicit `sampled`, `unavailable`, `ambiguous_identity`, or `not_sampled_this_run` statuses. News may be empty due to narrow queries or GDELT availability. No cross-run history or trending score exists yet.
- Dashboard lists the sampled 24-hour article count; individual coin profiles show source URLs and dates as provided. Unit tests cover conservative missing-data semantics.
- **Not yet verified in live Actions/Pages.** Next: validate GDELT response and limits, benchmark runtime; persist and deduplicate across days, expand coverage with proper caching and provider rate limits; implement licensed social APIs and bot-resistant engagement scoring.

## 2026-10-24 — technical-first hourly event gate (partial implementation)
- Added `hourly_technical.py`: reads only OHLCV candles whose UTC start plus one hour is no later than scan time; needs >=20 closed bars. Signals provisional 19-bar high/low crossing **only** when the preceding close was not already beyond that same boundary. This is a research event, not a validated trade breakout.
- Existing deep-analysis `inspect()` now fetches `ohlcv/hour`, computes a technical event, and logs last closed hourly candle; daily/weekly logic remains.
- GDELT lookup is conditional on an hourly technical event for at most 4 deeply analyzed candidates per run; others show `not_triggered`. Security and roadmap checks are independent and are not replaced by this gate.
- Profile displays hourly event/trigger metadata; tests cover exclusion of forming bars, threshold and insufficient data.
- **Critical limitations:** Only 8 candidates have detailed hour-candle inspection; the scheduled scan currently runs at minute 21 hourly and may take >10 min. Therefore this is NOT a guaranteed sub-hour monitoring/alert system, and detection on every listed token is NOT implemented. No deduplication of event alerts across scans, automatic roadmap ingestion, or live integration validation yet.
- Next: independent lightweight ~15-minute watchlist candle monitor, durable per-coin last-closed timestamp/event key, rate-limited breadth across all networks, priority event queue, webhook/notification, provider candle timestamps and CI verification.
