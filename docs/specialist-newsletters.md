# Specialist newsletters

## Editorial independence

The existing AstroPhoto Weekly task, prompt, scope, weekly cadence, issue numbering, RSS and editorial history are unchanged. Specialist editions are researched independently. A story published by one series remains eligible for every other series and for the generalist. Never use another newsletter's history as a global exclusion list.

Each series has its own publication archive, RSS, Discord destination and `data/specialists/SERIES/editorial-history.json`. Shared infrastructure handles validation, deployment and delivery only.

## Cadence

Run research weekly, in Europe/Paris time. Publication slots repeat every 14 days from `first_publication` in `data/specialists/series.json`: PixInsight and N.I.N.A. start 2026-10-30; Siril and Photoshop astro start 2026-11-06. During off weeks, save a dated watch snapshot. On a due week, publish only if material meets the editorial bar. An empty slot is skipped, not filled with recycled articles. One excellent dossier may justify an edition; 2–5 topics are a guideline, never a quota. Ordinary publication is limited to one edition per slot; no automatic special issues.

Calculate the latest slot as first_publication + 14 * floor((today - first_publication).days / 14). Publish only when today is on/after the first slot, less than seven days after the latest slot, and no edition already has a date within that slot. This tolerates a delayed Friday run without publishing on the off week. Inspect pending submissions as well as published issues before creating anything.

## Quality

Research official announcements and changelogs, original developer repositories, new technical documentation, original author tutorials and documented first-hand experiments. Communities are leads, not proof. Read the actual source, verify event/publication dates and software compatibility. A changed page date alone is not evidence of a new capability. Verify a stale search result against the current primary source. Disclose inaccessible sources; never imply private Discord or video content was inspected when it was not.

Classify each item: actualite, nouveau-tutoriel, retour-documente, ressource-a-decouvrir. Clearly date older resources and never present them as new. For each topic explain what changed, practical impact, affected versions and status, limitations and a direct source link. Distinguish author claims from independently documented results. Never claim an actual software/image test was performed if it was not.

For Photoshop keep an explicitly astrophotographic scope, including nightscapes and deep-sky finishing. Generic Adobe creative features are excluded unless an actual documented astro use exists. Distinguish denoising from generative scene alteration, and label creative composites.

All reader-facing content is French, with concise practical explanations and light humor. Code, identifiers and machine metadata are English. Prefer quality over speed, volume or punctuality.

## Watch-only run

Create exactly one immutable UTF-8 JSON file `data/specialists/watch/SERIES/YYYY-MM-DD.json`. Read previous snapshots before research. Use:

```json
{"series":"pixinsight","checked_at":"YYYY-MM-DD","candidates":[{"id":"unique-topic-slug","title":"French title","source":"https://primary-source.example/item","source_date":"YYYY-MM-DD or null","discovered_at":"YYYY-MM-DD","kind":"actualite","status":"stable, beta, nightly, etc.","version":null,"angle":"Practical interest","verification":"What was actually verified; limits"}],"decision":"off-week or insufficient-material","coverage_notes":"Sources checked; access gaps"}
```

A quiet week may have no candidates. Never overwrite a dated snapshot or treat its links as verified indefinitely. Do not trigger site deployment or Discord for watch snapshots. If a meaningful update occurs to a candidate, retain its identity and record the new evidence in the new snapshot.

## Publish run

Read actual `content/specialists/issues/SERIES/*.md`, all pending `data/specialists/submissions/SERIES/*.json` and that series' history. Determine the next three-digit number from actual issue files. Do not edit the generalist task or data.

Create exactly ONE GitHub file: `data/specialists/submissions/SERIES/NNN.json` on main, with exactly `issue`, `digest`, and `topics`. No direct writes to final issues, digests or editorial history.

`issue` is complete French Markdown with YAML front matter:

```yaml
---
series: pixinsight
number: 1
date: 2026-10-30
title: "La veille PixInsight #001 — meaningful French headline"
description: "Concrete French summary."
tags: [traitement, logiciels]
---
```

`digest` is a short French Discord message with 1–4 teasers and `[URL]`, ideally under 1400 UTF-16 code units to leave room for the final URL. `topics` maps unique slugs to `{issue:N,date:"YYYY-MM-DD",status:"...",version:null,source:"https://...",angle:"..."}`. Topic keys need be unique only within this series. A materially changed story needs a new key and a genuinely new angle.

Before submission check both final issue and submission paths; if either exists, inspect rather than duplicate. No ordinary edition outside the current slot or twice in that slot. Check workflow status after submission and report actual outcome. Never send Discord directly. An ambiguous delivery is not permission to resend.

## Publication and delivery

The Pages workflow drains pending submissions from current main, validates each independently and commits issue, digest, history and outbox together. The legacy generalist payload and validator remain supported. Rejected entries produce a visible workflow failure after valid editions have deployed. Past numbered generalist editions never enter the outbox on migration.

After successful deployment, each Discord attempt is reserved in Git before sending. Acknowledged Discord message/channel IDs are persisted. Uncertain/interrupted deliveries are held for manual inspection, never retried automatically. A missing specialist secret cannot fall back to the generalist webhook. `data/discord-outbox.json` changes do not retrigger publication.

The setup workflow verifies four distinct specialist destinations, different from the generalist, and sends clearly labelled setup test messages. Workflow dispatch verifies only by default; opt in explicitly to send test messages again.
