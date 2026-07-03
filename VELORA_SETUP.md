# Velora — local setup

[Velora](https://github.com/Kingler16/velora) is vendored here as a git
submodule at `velora/` (self-hosted AI portfolio advisor: Telegram bot +
web dashboard, driven by the Claude Code CLI).

## Get the code

```bash
git submodule update --init --recursive velora
```

## Steps you need to run yourself

The rest of the setup is interactive and needs things only you have —
a Telegram bot token, your portfolio holdings, and your tax/country
settings — so it can't be scripted from here:

```bash
cd velora
python3 setup.py          # interactive wizard: language, country/tax regime,
                           # Telegram bot, API keys, briefing schedule, portfolio import
source venv/bin/activate

python -m src.main briefing   # first AI briefing
python -m src.main bot        # Telegram bot (long-running)
python -m src.main web        # web dashboard → http://localhost:8080
```

### Prerequisites

- Python 3.11+
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`), with a Max or
  Pro subscription — Velora shells out to it instead of calling the Claude
  API directly
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Optional free-tier keys: [Brave Search](https://brave.com/search/api/),
  [FRED](https://fred.stlouisfed.org/docs/api/api_key.html),
  [Finnhub](https://finnhub.io/)

Secrets and personal data (`config/settings.json`, `config/portfolio.json`,
etc.) are gitignored inside the submodule — see `velora/config/*.example.json`
for the templates the setup wizard fills in.
