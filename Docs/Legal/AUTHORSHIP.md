# SparkLayer Protocol — Authorship Declaration

## Primary Author

**Romuald Martin**  
Independent Researcher  
Cabin Skolar — Bourgogne, France  
romuald.martin@gmail.com  
GitHub: github.com/totalarico702

---

## Declaration

I, Romuald Martin, hereby declare that I am the sole original author of the SparkLayer  
Protocol specification, as documented in this repository.

The original conception of SparkLayer — including the three-file architecture (.spsk/.spk/.spki),  
the depth-based monetization model, the vault access control mechanism, the cryptographic  
provenance framework, the token bank economic model, the Semantic Honeypot (Abysse Data),  
the agent compliance levels, the intent taxonomy, and the regulatory alignment with the  
EU AI Act — was developed by me between July 2025 and May 2026.

---

## Chronology of Development

| Date | Milestone | Proof |
|---|---|---|
| July 2025 | Initial architecture — pipeline diagram | `Docs/Pipeline/diagram-export-29-07-2025-12_27_38.png` |
| July 2025 | White paper v1 (French) | `Docs/WhitePaper/White paper_V2.pdf` |
| September 2025 | White paper v1 English — W3C submission draft | `Docs/WhitePaper/sparklayer_v2.pdf` |
| May 2026 | Protocol v2.0 — complete technical specification | `Docs/WhitePaper/sparklayer_whitepaper_v2.md` |
| May 2026 | JSON Schemas finalized (.spsk / .spk / .spki) | `Config/` |
| May 2026 | Sparkifier v0.1 — publisher tooling | `Scripts/sparkifier.py` |
| May 2026 | Agent Skill v0.1 — LangGraph/CrewAI integration | `Scripts/sparklayer_skill.py` |
| May 2026 | Benchmark v0.2 — HTML vs .spk analysis | `Scripts/benchmark.py` |
| May 2026 | Position paper — EU AI Act GPAI Code of Practice | `Docs/Legal/` |
| May 2026 | Formal letters to AI Office and DG CONNECT | `Docs/Legal/` |

---

## Original Intellectual Contributions

The following are original contributions of Romuald Martin, documented by the July 2025  
Git commit (SHA: 8c80d0a2d236543daf6d5dab4643d561258f8930) and subsequent commits:

1. **Three-file architecture (.spsk/.spk/.spki)** — separation of site key, knowledge  
   document, and action interface as three distinct cryptographically signed files

2. **The Sparkification process** — automated pipeline from raw content to structured  
   SparkLayer files (visible in July 2025 pipeline diagram as "Sparkification" node)

3. **The depth model** — hierarchical content partitioning with independent access  
   levels and token costs per depth layer

4. **The vault mechanism** — server-side enforcement of depth-gated content  
   (architectural enforcement, not declarative)

5. **Semantic Honeypot / Abysse Data** — serving synthetic decoy content to  
   non-compliant crawlers, with legal notice embedded in provenance metadata  
   (visible in July 2025 diagram as "Semantic Honeypot" node)

6. **Kill Switch** — publisher-controlled instant access revocation  
   (visible in July 2025 diagram as "Kill Switch" node)

7. **SparkCloud mediation layer** — authentication, license verification, token  
   provision, cache management (visible in July 2025 diagram as "Spark Cloud Mediation")

8. **The token bank model** — fiat-backed credit system with publisher-side  
   settlement and platform take rate

9. **The intent taxonomy** — structured action surface annotation for agent  
   navigation (.spki intent_category + intent_subcategory + flow declarations)

10. **The HTML bridge layer** — depth_0 HTML output as a derivative of .spk,  
    not a parallel authoring surface

11. **Compliance level framework** — four-tier crawler compliance model  
    (Level 0→3) with economic and legal enforcement mechanisms

12. **EU AI Act alignment** — mapping of SparkLayer to Art. 10 and Art. 53  
    of Regulation EU 2024/1689

13. **SparkLayer Lite** — same protocol, trust-relaxed deployment mode  
    for intranet and enterprise environments

---

## Git Commit Provenance

| Commit | Date | Content |
|---|---|---|
| `8c80d0a2` | July 2025 | Initial architecture, pipeline diagram, white papers |
| *(May 2026)* | May 2026 | v2.0 implementation — schemas, tooling, EU submissions |

The July 2025 commit SHA `8c80d0a2d236543daf6d5dab4643d561258f8930` is permanently  
recorded in GitHub's infrastructure and constitutes a timestamped proof of authorship  
independent of any subsequent claims.

---

## Additional Proof of Prior Art

- **Eraser.io diagram** (`diagram-export-29-07-2025-12_27_38.png`) — the filename  
  contains the creation timestamp (29 July 2025, 12:27:38) embedded by the Eraser  
  platform at export time, constituting an independent third-party timestamp.

- **PDF documents** in `Docs/WhitePaper/` — dated 2025, containing the complete  
  conceptual specification of SparkLayer before any code implementation.

---

## Intellectual Property Status

- **Protocol specification** (schemas, file formats, compliance levels): CC0 1.0  
  (public domain — to prevent patent enclosure and ensure maximum adoption)
- **Implementation code** (Sparkifier, Agent Skill, Benchmark): MIT License
- **Documentation and white papers**: Copyright © 2025-2026 Romuald Martin

---

## Contact for Licensing & Partnerships

romuald.martin@gmail.com  
Cabin Skolar — Bourgogne, France  
github.com/totalarico702

---

*This document is part of the SparkLayer repository and is included for authorship  
provenance purposes. Last updated: May 2026.*
