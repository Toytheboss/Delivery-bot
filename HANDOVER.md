# Handover

This is a **sanitized** snapshot of the Delivery Agent that was running in production (audit account + delivery account, same codebase). It is safe to clone. It does **not** contain Telegram sessions, Lark app secrets, X API keys, real group names, or real account usernames.

You cannot start from this repo alone. Create your own Telegram / Lark / LLM / X accounts, then fill local config.

## What you must create yourself

| Item | Where it goes | Notes |
|------|----------------|-------|
| Telegram user API | `.env` `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | [my.telegram.org](https://my.telegram.org). This is a **userbot**, not a BotFather bot. |
| Telegram login | `*.session` via `scripts/login.py` | One session per account. Two accounts = two server directories. |
| Lark app | `.env` `LARK_APP_ID` / `LARK_APP_SECRET` | Open platform app on **your** tenant. Grant bitable + IM scopes. |
| Lark Base tokens | `config/config.yaml` | Progress table, wallet table, weekly tables. Copy IDs from **your** Base. |
| Lark group chat ids | `config/config.yaml` | `oc_…` for result push, weekly pings, tech-support. |
| LLM | `.env` `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` | FAQ replies. |
| X API | `.env` `X_BEARER_TOKEN` or `X_API_KEY` + `X_API_SECRET` | KPI 1 only. |
| Webhook secret | `.env` `WORKFLOW_LIVE_WEBHOOK_SECRET` | Must match the Lark automation header. |
| Operator allowlist | `config/config.yaml` `workflow.operators` | Telegram usernames who can Mark live / send form. |

Never commit `.env`, `*.session`, or `config/config.yaml`.

## Two-account layout

Same code, two working directories on the server:

| Role | Typical path | Typical systemd unit | Typical webhook port |
|------|----------------|----------------------|----------------------|
| **审核号** (audit) | `/opt/botchain-qa-tg-bot` | `botchain-qa.service` | `8786` — KPI / live-onboard / review-group submit |
| **交付号** (delivery) | `/opt/delivery-agent` | `delivery-agent.service` | `8787` — partner-group FAQ, mark-live, form dispatch |

KPI writes and review-group submits must run on the **audit** account only (`kpi_checks_on_this_host()`). Do not point the public Lark event URL at the delivery port.

## First boot

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp config/config.yaml.example config/config.yaml
cp config/whitelist.yaml.example config/whitelist.yaml
cp config/qa_testers.yaml.example config/qa_testers.yaml
cp config/ignored_groups.yaml.example config/ignored_groups.yaml
# fill .env and config.yaml, then:
python scripts/login.py
```

Deploy notes: `deploy/README.md`. systemd examples: `deploy/botchain-qa.service`, `deploy/delivery-agent.service`.

## What this snapshot stripped

Hardcoded tenant Base tokens, table / view ids, Lark chat ids, VPS IP, and the previous operator’s Google Form / app id were replaced with placeholders (`YOUR_…`, `oc_xxxxxxxx`, `your-tenant.larksuite.com`). Fill them from your own tenant before starting.
