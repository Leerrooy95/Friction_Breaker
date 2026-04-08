# Mechanism Classifier Taxonomy — Documentation

**Version**: 1.0.0
**Source**: The Regulated Friction Project (v11.9)
**Generated**: April 4, 2026
**Authors**: Austin Smith + Claude (Opus 4.6)

---

## What This Is

This taxonomy is the foundation layer for the countermeasure engine. It extracts every legal, regulatory, personnel, financial, and procedural mechanism documented in The Regulated Friction Project and classifies them into a machine-queryable structure.

**Total mechanisms cataloged**: 54 (v2.1 — comprehensive extraction, all gaps addressed)
**Categories**: 8

---

## Category Summary

| ID | Category | Count | Description |
|----|----------|-------|-------------|
| A | Legislative Architecture | 12 | Auto-approvals, iterative loops, emergency clauses, bespoke carve-outs, competitor exclusions, federal oversight bypasses, interstate incentive race, state preemption of local authority |
| B | Regulatory Capture and Override | 6 | Forced approval despite adverse findings, beneficial ownership concealment, 13F gaps, OCC preemption, PILOT agreements, ratepayer cost shift without binding demand |
| C | Personnel Cycling and Lock-In | 6 | Pre-accountability firings, acting official installation, civil service conversion, wartime purges, temporary entity absorption, impoundment |
| D | Democratic Check Suppression | 9 | Ballot initiative restrictions, constitutional protection reversal, clock-running litigation, coercion template, theological access architecture, curriculum pipeline, compliance enforcement, CUFI lobbying, CREC/Pentagon access |
| E | Information Control | 7 | Selective redaction, witness support defunding, media acquisition, FaaS protest supply chain, cyber-kinetic operations, information archive as deterrent, calendar anchor exploitation |
| F | Surveillance / Data Centralization | 4 | FISA Section 702 coupling, backdoor US person queries, ECSP definition expansion, PCLOB oversight gutting |
| G | Capital Opacity | 6 | Emoluments bypass via stablecoin, revolving door nexus, mBridge CBDC settlement, dual-alignment bridge state, OPEC+ leverage, BRI vacuum capture |
| H | Judicial / Enforcement Architecture | 4 | Invalid appointments, supply chain risk designation, subpoena non-enforcement, NPA leverage capture |

---

## How The Taxonomy Works

Each mechanism entry contains:

```
id              — Unique identifier (e.g., A-01)
name            — Human-readable name
category        — Which of the 8 categories
jurisdiction    — federal / state / both
mechanism_type  — legislative / regulatory / personnel / judicial / executive / financial / procedural / institutional / information_control / surveillance
description     — What it does
how_it_works    — Step-by-step operational sequence
durability      — 1-10 scale (10 = hardest to reverse)
reversal_pathways — Array of structural countermeasures
repo_references — Where in the Regulated Friction Project this is documented
real_examples   — Verified real-world instances
status          — enacted / proposed / pending / active / challenged / active_threat
```

---

## Durability Scale

The durability score (1-10) measures how resistant a mechanism is to reversal once deployed:

| Score | Meaning | Example |
|-------|---------|---------|
| 1-2 | **Tactical** — one-time use, easily reversed | Clock-running litigation, single personnel action |
| 3-4 | **Operational** — reversible but requires organized effort | Funding freezes, selective redaction, acting official installation |
| 5-6 | **Structural** — requires legislative action or court order | State statutes (Acts 373/548), 13F gaps, Schedule F rulemaking |
| 7-8 | **Institutional** — requires constitutional change, major legislation, or reversing entrenched precedent | Edgmon reversal, OCC charters, DOGE absorption into OPM, FISA, enacted CLARITY Act |
| 9-10 | **Constitutional** — requires amendment or fundamental systemic reform | (None currently at this level — but some mechanisms, if unchallenged for years, approach it) |

---

## Countermeasure Durability Spectrum

The reversal_pathways for each mechanism are themselves ranked by durability — the most durable countermeasures are the hardest to undo:

| Countermeasure Type | Durability | Time to Implement | Difficulty |
|--------------------|------------|-------------------|------------|
| **Constitutional amendment** | 10 | Years | Requires 2/3 Congress + 3/4 states |
| **Treaty obligation** | 9 | Months-years | Requires Senate 2/3 to withdraw |
| **Federal statute with sunset-proof design** | 8 | Months | Requires congressional majority + presidential signature |
| **State constitutional amendment** | 7 | Months | Requires ballot initiative or legislative referral |
| **Federal court precedent** | 7 | Months-years | Requires litigation + favorable ruling |
| **Independent IG / commission with removal-for-cause** | 6 | Months | Requires legislative creation |
| **State statute** | 5 | Months | Requires state legislative majority |
| **Federal rulemaking** | 5 | 1-2 years | Requires agency action + public comment |
| **Executive order** | 3 | Days | Requires presidential signature; reversible by next president |
| **Public documentation / pattern recognition** | 2 | Immediate | Requires publication; effectiveness depends on uptake |

---

## How This Feeds Into The Countermeasure Engine

### Input Flow
```
New event (from Brave Search API / Federal Register / Congressional Record)
    ↓
Mechanism Classifier (this taxonomy)
    ↓
Identifies: "This is a [Category A / B / C / D / E / F / G / H] mechanism"
    ↓
Identifies: "Closest match: [specific mechanism ID]"
    ↓
Identifies: "Durability score: [X/10]"
    ↓
Retrieves: "Reversal pathways for this mechanism type"
```

### Output Flow
```
Reversal pathways retrieved
    ↓
LLM analysis (Claude API, user's key)
    ↓
Contextualizes: "For THIS specific instance, the most effective countermeasure is..."
    ↓
Ranks by: durability, feasibility, time-to-implement, political viability
    ↓
Outputs: Plain-English report (Political Translator format)
```

---

## Taxonomy Completeness

v2.1 addresses all identified gaps. The taxonomy is comprehensive as of April 4, 2026.

**Completed areas:**
- ✅ Legislative architecture (12 mechanisms) — Arkansas model + interstate replication + state preemption
- ✅ Regulatory capture (6 mechanisms) — including ratepayer cost shift pattern across 18+ states
- ✅ Personnel cycling (6 mechanisms) — including impoundment as executive spending override
- ✅ Democratic check suppression (9 mechanisms) — including full religious layer
- ✅ Information control (7 mechanisms) — including FaaS, cyber-kinetic, information deterrent, calendar anchor exploitation
- ✅ Surveillance (4 mechanisms) — full FISA 702 mechanics including backdoor searches, ECSP expansion, PCLOB gutting
- ✅ Capital opacity (6 mechanisms) — including mBridge, UAE dual-alignment, OPEC+, BRI vacuum capture
- ✅ Judicial architecture (4 mechanisms) — including NPA leverage capture

**Future growth**: The taxonomy will expand as the tool detects new mechanisms via `new_mechanisms_detected` in analysis outputs. Each new mechanism flagged by Claude should be verified and added to the taxonomy JSON.

---

## File Locations

| File | Location |
|------|----------|
| Taxonomy JSON | `mechanism_classifier_taxonomy.json` |
| This documentation | `MECHANISM_CLASSIFIER_README.md` |
| Source repository | `github.com/Leerrooy95/The_Regulated_Friction_Project` |

---

## License

Open source — same license as The Regulated Friction Project repository.

---

*This taxonomy was built by systematically reading every mechanism-bearing file in the _AI_CONTEXT_INDEX, DAILY_REPORTS, 13_State_and_County_Analysis, 10_Real-Time_Updates_and_Tasks, 08_How_It's_Possible, 14_Files, and Project_Trident directories of the source repository.*
