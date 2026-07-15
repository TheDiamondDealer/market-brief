# GDELT Discovery Radar

## Purpose

The GDELT integration is a wide-net early-warning and media-discovery layer for Market Brief. It is not a verified news wire and must not overwrite the Impact Feed, primary-source observations or research conclusions.

The collector searches four decision-relevant groups:

- strategic materials;
- semiconductors and AI infrastructure;
- macro, trade and policy;
- energy and security.

## Trust rule

A GDELT match proves only that media coverage exists. It does not prove that the underlying claim is true, current, economically material or correctly interpreted.

Material claims must be confirmed against, in order of preference:

1. an exchange announcement, regulatory filing or official company release;
2. a government, regulator, central-bank or recognised industry source;
3. a trusted financial wire or reputable specialist publication.

Every displayed record is permanently labelled `sourceTier: discovery` and `verificationStatus: unverified`.

## Public-safe data model

The generated payload stores only:

- headline;
- outbound article URL;
- source domain;
- GDELT seen time;
- language and source country where supplied;
- mapped topics and assets;
- deterministic materiality score;
- first-seen timestamp and duplicate count.

It does not store article body text, copied extracts, credentials, authentication data or execution functionality.

## Collection and failure behaviour

- Endpoint: public GDELT DOC 2.0 API.
- Expected cadence: hourly.
- Window: previous 24 hours.
- Public payload cap: 48 articles.
- Duplicate handling: canonical URL identity with merged topic and asset mappings.
- Tracking parameters are removed from outbound URLs.
- Social/video-only domains are excluded.
- A partial provider response is labelled `partial`.
- If every query fails, the last successful article snapshot is retained and labelled `stale`.
- If no prior snapshot exists, the source is visibly `failed` or `unavailable`.

## Ranking

The materiality score is a deterministic discovery ranking using:

- topic matches;
- selected event terms such as shutdown, export restriction, tariff, production change, financing and policy action;
- recency.

It is not sentiment analysis, a probability forecast or a trading signal.

## User interface

The radar appears as a collapsible section above the curated Impact Feed. The separation is deliberate:

- **GDELT Discovery Radar:** machine-observed, broad and unverified;
- **Impact Feed:** delayed, curated interpretation with sources, transmission channels, confirmation and invalidation logic.

The GDELT source state is also added to Source Health.

## Operations

Manual collection:

```bash
python scripts/update_gdelt_radar.py
python scripts/validate_gdelt_radar.py
```

Offline tests:

```bash
python -m py_compile scripts/*.py tests/*.py
node --check site/features/gdelt-radar/gdelt-data.js
node --check site/features/gdelt-radar/gdelt-health.js
node --check site/features/gdelt-radar/gdelt-page.js
python -m unittest tests.test_gdelt_radar -v
```
