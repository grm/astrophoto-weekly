# AstroPhoto Weekly

A low-cost, autonomous publishing pipeline for a weekly French-language astrophotography newsletter.

Reader-facing content is written in French. Code, automation, internal identifiers, and developer documentation are written in English.

## Stack

- [Astro](https://astro.build/) for the static editorial site.
- Markdown issues stored outside the application source tree.
- GitHub Actions for build and deployment.
- GitHub Pages for hosting and HTTPS.
- A Discord incoming webhook for publication notifications.
- A scheduled ChatGPT editorial task for research, curation, writing, and repository publishing.

No permanent server, database, CMS, or separately billed OpenAI API job is required by the website pipeline.

## Architecture

```text
Scheduled editorial task
        ↓
Web research + source verification
        ↓
French newsletter + French Discord digest
        ↓
content/digests/NNN.md
        ↓
data/editorial-history.json
        ↓
content/issues/NNN.md  ← publication trigger
        ↓
GitHub Actions
        ↓
Astro static build
        ↓
GitHub Pages
        ↓
Discord notification
```

The issue file is created last so that the deployment workflow only sees complete publications.

## Repository layout

```text
content/issues/          Published Markdown newsletter editions
content/digests/         Discord-ready French digests
data/editorial-history.json
                         Editorial memory used to avoid duplicate coverage
data/site.json           Public site URL and metadata
src/content.config.ts    Typed Astro content collection
src/components/          Reusable editorial UI components
src/layouts/             Page layouts
src/pages/               Homepage, archives, issues, RSS, 404
src/styles/              Global visual system
scripts/discord.py       Discord webhook publisher
.github/workflows/pages.yml
                         Build, deploy, then notify
.github/workflows/smoke-test.yml
                         Manual Discord integration test
```

## Local development

Requires Node.js 24 or newer.

```bash
npm install
npm run dev
```

Production build:

```bash
npm run build
```

The generated static site is written to `dist/`.

## Publishing an edition

Each edition is stored as `content/issues/NNN.md` with YAML front matter:

```yaml
---
number: 1
date: 2026-09-08
title: "AstroPhoto Weekly #001"
description: "Short French edition summary."
tags:
  - traitement
  - matériel
---
```

Required fields are `number`, `date`, `title`, and `description`. `tags` and `featured` are optional.

The matching Discord digest is stored as `content/digests/NNN.md`. It must remain below Discord's 2000-character message limit and contains a `[URL]` placeholder that is replaced after deployment.

## Deployment

GitHub Pages must use **GitHub Actions** as its source.

The production workflow:

1. installs the Astro dependencies;
2. builds the static site;
3. uploads and deploys `dist/` to GitHub Pages;
4. detects whether exactly one new numbered issue was added;
5. sends its French digest to Discord only after a successful deployment.

Technical changes can redeploy the site without sending a Discord notification.

## Discord secret

The `DISCORD_WEBHOOK_URL` secret is read from the `github-pages` environment. A separate manual smoke-test workflow is available to validate the webhook without publishing a real issue.

## Custom domain and HTTPS

The current development URL is configured in `data/site.json`.

When a production domain is ready:

1. configure the domain in **Settings → Pages → Custom domain**;
2. configure the DNS records;
3. update `site_url` in `data/site.json` to the final HTTPS URL.

`astro.config.mjs` derives the GitHub Pages base path from `site_url`. This means the current `/astrophoto-weekly/` repository path is handled automatically, and switching to a root custom domain removes that base path without rewriting internal links.

## Editorial language policy

- Full newsletter: French.
- Website navigation and archive copy: French.
- Discord notifications and digests: French.
- RSS reader-facing text: French.
- Code, scripts, comments, internal metadata keys, workflow names, and developer documentation: English.

## Editorial principles

- Prefer primary and authoritative sources.
- Verify important factual claims.
- Explicitly label beta, nightly, preview, experimental, and rumor status.
- Avoid repeating previously covered topics unless something materially changed.
- Publish roughly 8–12 worthwhile topics rather than filling categories artificially.
- Keep the newsletter independent from the project owner's personal equipment, software, and habits.
