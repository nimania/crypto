# Hamzeh DEX Radar

A read-only cryptocurrency discovery and monitoring prototype for **Base, Arbitrum and Flare**. Designed around MetaMask-held assets and daily/weekly trend-following analysis.

**Current status: experimental research watchlist, not production trading advice.** Never sends transactions or connects wallet keys.

## Run locally

Python 3.11+ (stdlib only):

```bash
python -m unittest discover -s tests -v
python radar.py
```

Results appear under `output/radar.json` and `output/report.md`. Data sourced from public DexScreener discovery feeds and GeckoTerminal pool OHLCV endpoints where available. No arbitrary invented OHLCV data. Discovery is **not comprehensive**: recent/promoted feeds are only a starting point and may be biased.

## GitHub Actions

The workflow scans every 6 hours and can be manually triggered. Reports are stored as a workflow artifact. To send to Telegram, add GitHub Actions secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Do not paste secrets into files, issues, or chats. Without these secrets, runs still create artifacts but send no messages.

## Evaluation limits

- DEX listing ≠ legitimate token; contract security and sellability are **not yet verified**.
- Exit flags require **both** daily and weekly data. Missing/inadequate history leads to `INSUFFICIENT_DATA`.
- Momentum deceleration may be transient and is **not proof of a top**.
- The Flare GeckoTerminal network identifier and API coverage are provisional; failures must stay visible.
- Ranking based on reported liquidity, 24h volume, and age is for research prioritization only, **not a buy signal**.
- MetaMask is a wallet, not an exchange or a network; no wallet address is required for basic scans.
- Geographic eligibility and protocol access must be verified independently; no measures to bypass KYC or sanctions restrictions.

## Next milestones

1. Independent contract-security and sellability checks; do not suggest trades before those checks.
2. Read-only token inventories from public MetaMask wallet addresses on supported networks.
3. Persist historical observations for realistic out-of-sample signal evaluation.
4. Telegram-specific entry/exit watch alerts with deduplication and audit trail.
5. Expand market discovery beyond promoted/recent tokens and improve network coverage.
