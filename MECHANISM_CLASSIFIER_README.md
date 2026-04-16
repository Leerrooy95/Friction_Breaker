# Mechanism Classifier Taxonomy — Documentation

**Version**: 2.3.0
**Source**: The Regulated Friction Project (v12.3)
**Generated**: April 2026
**Authors**: Austin Smith + Claude (Opus 4.6)

---

## What This Is

This taxonomy is the foundation layer for the countermeasure engine. It extracts every legal, regulatory, personnel, financial, and procedural mechanism documented in The Regulated Friction Project and classifies them into a machine-queryable structure.

**Total mechanisms cataloged**: 63
**Categories**: 8

> **Future: Mechanism Dependency Graph** — Some mechanisms enable or depend on
> others (e.g., capital opacity mechanisms may depend on beneficial-ownership
> concealment).  Optional `depends_on` and `enables` fields are planned for a
> future taxonomy version so the engine can surface cascading effects.  See the
> JSON schema convention: each mechanism would gain an optional array of
> taxonomy IDs it depends on or enables, following the node-and-edge pattern
> used in SPDX/CycloneDX dependency graphs.
> <!-- TODO: Implement depends_on / enables fields in taxonomy v2.3+ -->

---

## Category Summary

| ID | Category | Count | Description |
|----|----------|-------|-------------|
| A | Legislative Architecture | 13 | Auto-approvals, iterative loops, emergency clauses, bespoke carve-outs, competitor exclusions, federal oversight bypasses, interstate incentive race, state preemption of local authority, strategic asset declaration as market support |
| B | Regulatory Capture and Override | 7 | Forced approval despite adverse findings, beneficial ownership concealment, 13F gaps, OCC preemption, PILOT agreements, ratepayer cost shift without binding demand, inaugural-period deal structuring |
| C | Personnel Cycling and Lock-In | 7 | Pre-accountability firings, acting official installation, civil service conversion, wartime purges, temporary entity absorption, impoundment, diplomatic title as legal shield |
| D | Democratic Check Suppression | 10 | Ballot initiative restrictions, constitutional protection reversal, clock-running litigation, coercion template, theological access architecture, curriculum pipeline, compliance enforcement, CUFI lobbying, CREC/Pentagon access, preemptive credibility assassination |
| E | Information Control | 9 | Selective redaction, witness support defunding, media acquisition, FaaS protest supply chain, cyber-kinetic operations, information archive as deterrent, calendar anchor exploitation, shutter control, statistical smokescreen |
| F | Surveillance / Data Centralization | 4 | FISA Section 702 coupling, backdoor US person queries, ECSP definition expansion, PCLOB oversight gutting |
| G | Capital Opacity | 8 | Emoluments bypass via stablecoin, revolving door nexus, mBridge CBDC settlement, dual-alignment bridge state, OPEC+ leverage, BRI vacuum capture, SpaceX consolidated IPO, regulatory exemption tailoring |
| H | Judicial / Enforcement Architecture | 5 | Invalid appointments, supply chain risk designation, subpoena non-enforcement, NPA leverage capture, enforcement capture (agency weaponization) |

---

## How The Taxonomy Works

Each mechanism entry contains:

| Field              | Description                                                             |
|--------------------|-------------------------------------------------------------------------|
| `id`               | Unique identifier (e.g., A-01)                                         |
| `name`             | Human-readable name                                                    |
| `category`         | Which of the 8 categories                                              |
| `jurisdiction`     | federal / state / both                                                 |
| `mechanism_type`   | legislative / regulatory / personnel / judicial / executive / financial / procedural / institutional / information_control / surveillance |
| `description`      | What it does                                                           |
| `how_it_works`     | Step-by-step operational sequence                                      |
| `durability`       | 1–10 scale (10 = hardest to reverse)                                   |
| `reversal_pathways`| Array of structural countermeasures                                    |
| `repo_references`  | Where in the Regulated Friction Project this is documented             |
| `real_examples`    | Verified real-world instances                                          |
| `status`           | enacted / proposed / pending / active / challenged / active_threat     |

---

## Durability Scale

The durability score (1–10) measures how resistant a mechanism is to reversal once deployed:

| Score | Meaning | Example |
|-------|---------|---------|
| 1–2 | **Tactical** — one-time use, easily reversed | Clock-running litigation, single personnel action |
| 3–4 | **Operational** — reversible but requires organized effort | Funding freezes, selective redaction, acting official installation |
| 5–6 | **Structural** — requires legislative action or court order | State statutes (Acts 373/548), 13F gaps, Schedule F rulemaking |
| 7–8 | **Institutional** — requires constitutional change, major legislation, or reversing entrenched precedent | Edgmon reversal, OCC charters, DOGE absorption into OPM, FISA, enacted CLARITY Act |
| 9–10 | **Constitutional** — requires amendment or fundamental systemic reform | (None currently at this level — but some mechanisms, if unchallenged for years, approach it) |

---

## Countermeasure Durability Spectrum

Reversal pathways are ranked by their own durability:

| Countermeasure Type | Durability | Time to Implement | Difficulty |
|--------------------|------------|-------------------|------------|
| Constitutional amendment | 10 | Years | Requires 2/3 Congress + 3/4 states |
| Treaty obligation | 9 | Months–years | Requires Senate 2/3 to withdraw |
| Federal statute with sunset-proof design | 8 | Months | Requires congressional majority + presidential signature |
| State constitutional amendment | 7 | Months | Requires ballot initiative or legislative referral |
| Federal court precedent | 7 | Months–years | Requires litigation + favorable ruling |
| Independent IG / commission with removal-for-cause | 6 | Months | Requires legislative creation |
| State statute | 5 | Months | Requires state legislative majority |
| Federal rulemaking | 5 | 1–2 years | Requires agency action + public comment |
| Executive order | 3 | Days | Requires presidential signature; reversible by next president |
| Public documentation / pattern recognition | 2 | Immediate | Requires publication; effectiveness depends on uptake |

---

## How This Feeds Into The Countermeasure Engine

### Input Flow
```
New event (user-provided text / URL)
    ↓
GLiNER2 entity extraction (local, zero-cost)
    ↓
Mechanism Classifier (this taxonomy)
    ↓
Identifies: "This is a [Category A–H] mechanism"
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
Claude API analysis (user's own key)
    ↓
Contextualizes: "For THIS specific instance, the most effective countermeasure is..."
    ↓
Ranks by: durability, feasibility, time-to-implement, political viability
    ↓
Outputs: Plain-English report (Political Translator format)
```

---

## Taxonomy Completeness

v2.3 is comprehensive as of April 2026, covering:

- ✅ Legislative architecture (13 mechanisms)
- ✅ Regulatory capture (7 mechanisms)
- ✅ Personnel cycling (7 mechanisms)
- ✅ Democratic check suppression (10 mechanisms)
- ✅ Information control (9 mechanisms)
- ✅ Surveillance (4 mechanisms)
- ✅ Capital opacity (8 mechanisms)
- ✅ Judicial architecture (5 mechanisms)

**v2.3.0 additions** (April 16, 2026): 7 new mechanisms added from `new_mechanisms_detected` flags in `Leroys_Tests/Run_1` and `Leroys_Tests/Test_2` outputs — H-05 (Enforcement Capture), E-09 (Statistical Smokescreen), C-07 (Diplomatic Title as Legal Shield), D-10 (Preemptive Credibility Assassination), G-08 (Regulatory Exemption Tailoring), B-07 (Inaugural-Period Deal Structuring), A-13 (Strategic Asset Declaration as Market Support).

**Future growth**: The taxonomy will expand as the tool detects new mechanisms via `new_mechanisms_detected` in analysis outputs. Each new mechanism flagged should be verified and added to the taxonomy JSON via a pull request.

---

## File Locations

| File | Location |
|------|----------|
| Taxonomy JSON | `mechanism_classifier_taxonomy.json` |
| This documentation | `MECHANISM_CLASSIFIER_README.md` |
| Source repository | [The Regulated Friction Project](https://github.com/Leerrooy95/The_Regulated_Friction_Project) |

---

## License

[MIT License](LICENSE) — same as The Regulated Friction Project.
