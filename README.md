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
ONE GitHub write: data/submissions/NNN.json
        ↓
GitHub Actions validates and atomically commits:
  content/digests/NNN.md
  data/editorial-history.json
  content/issues/NNN.md
        ↓
Astro build → GitHub Pages → Discord notification
```

The scheduled editorial task creates only one numbered JSON submission. GitHub Actions validates it and commits the digest, history and issue together. A failed validation cannot publish an incomplete issue.

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

The editorial task creates `data/submissions/NNN.json` with exactly `issue` (complete Markdown), `digest` (complete French Discord text), and `topics` (editorial history additions keyed by unique slug). Do not write the three final files separately. The workflow validates the next issue number, front matter, digest length and topic IDs, then creates the three files in one Git commit. The resulting deployment sends Discord after GitHub Pages succeeds.

**Repository setting:** GitHub Actions needs `contents: write` access for the publication commit. Under Settings → Actions → General → Workflow permissions, enable read/write permissions if required. The workflow requests `contents: write` explicitly.



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

## Specialist newsletters

PixInsight, Siril, N.I.N.A. and Photoshop for astrophotography have independent newsletters under `/veilles/`. Research runs weekly; editions are published fortnightly only when worthwhile material is available. The generalist editorial task and selection remain independent.

See [specialist editorial and publication contract](docs/specialist-newsletters.md) for the source policy, weekly watch snapshots, publication slots and one-write submission format. Specialist submissions use `data/specialists/submissions/SERIES/NNN.json`. The shared workflow accepts the existing generalist format unchanged, drains pending submissions, deploys the site, then delivers each digest to its own destination.

Set `DISCORD_WEBHOOK_PIXINSIGHT`, `DISCORD_WEBHOOK_SIRIL`, `DISCORD_WEBHOOK_NINA`, and `DISCORD_WEBHOOK_PHOTOSHOP_ASTRO` in the `github-pages` environment. The existing `DISCORD_WEBHOOK_URL` remains the generalist destination. The specialist smoke workflow verifies distinct destinations without revealing tokens.

Run publication/routing checks with `python -m pip install PyYAML==6.0.2` then `python -m unittest discover -s tests -v`. The Discord outbox records acknowledged or uncertain delivery status; inspect the target channel before any manual retry.
