# AstroPhoto Weekly

A low-cost, autonomous publishing pipeline for a weekly French-language astrophotography newsletter.

The editorial content is researched and written in French. The repository, code, automation, and documentation are maintained in English.

## Goals

- Publish one curated astrophotography edition per week.
- Cover acquisition, processing, hardware, techniques, open source, community discussions, and upcoming imaging opportunities.
- Prefer primary and authoritative sources.
- Avoid repeating previously covered topics unless something materially changed.
- Keep infrastructure close to zero-cost: static files, GitHub Pages, GitHub Actions, and a Discord webhook.

## Architecture

```text
Scheduled editorial task
        ↓
Web research + source verification
        ↓
French newsletter + French Discord digest
        ↓
Commit to this repository
        ↓
GitHub Actions
        ↓
Static site build
        ↓
GitHub Pages
        ↓
Discord notification
```

## Repository layout

```text
content/issues/          Full newsletter editions
content/digests/         Discord-ready digests
data/editorial-history.json
                         Editorial memory used to avoid duplicate coverage
data/site.json           Site configuration
scripts/build.py         Static site and RSS generator
scripts/discord.py       Discord webhook publisher
.github/workflows/pages.yml
                         Build, deploy, then notify
```

## Initial setup

1. Open **Settings → Pages** and select **GitHub Actions** as the Pages source.
2. Create an incoming webhook in the target Discord channel.
3. Add its URL as the repository Actions secret `DISCORD_WEBHOOK_URL`.
4. Push or update an edition under `content/issues/`.

The Discord job runs only after a successful Pages deployment.

## Custom domain and HTTPS

Configure the custom domain in **Settings → Pages → Custom domain** and point the relevant DNS records to GitHub Pages. Once DNS is valid, GitHub Pages can enforce HTTPS.

Update `site_url` in `data/site.json` when the production domain is known.

## Publishing an edition

Each edition is stored as Markdown with YAML front matter:

```yaml
---
number: 1
date: 2026-09-08
title: "AstroPhoto Weekly #001"
description: "Short edition summary."
---
```

The matching Discord digest is stored under `content/digests/001.md`.

A push to `main` triggers the Pages workflow.

## Cost model

No permanent server or database is required. The site is static and the GitHub Actions build is intentionally small. Editorial generation is expected to run from the scheduled ChatGPT task rather than from a separately billed OpenAI API job inside GitHub Actions.

## Language policy

- Reader-facing newsletter content: French.
- Discord notifications and digests: French.
- Public archive copy and calls to action: French.
- Code, scripts, internal identifiers, comments, commit-oriented implementation conventions, and developer documentation: English.
