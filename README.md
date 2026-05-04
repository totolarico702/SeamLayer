# SeamLayer Protocol

**An open protocol for structured, monetized, and trusted AI content consumption.**

> *The next primary user of the web is not human — it is AI.*  
> *SeamLayer is the protocol layer that makes this transition fair, structured, and economically viable.*

---

## Author & Origin

**Romuald Martin**  
Independent Researcher — Cabin Skolar, Bourgogne, France  
romuald.martin@gmail.com

**Architecture first commit:** July 2025  
**Protocol v2.0 implementation:** May 2026  
**License:** MIT (see LICENSE)

This repository constitutes the original authorship record of the SeamLayer Protocol.  
The initial architecture (pipeline diagram, white paper v1/v2) was committed in July 2025.  
The complete v2.0 implementation (schemas, tooling, benchmark, EU submissions) was added in May 2026.

---

## What is SeamLayer?

SeamLayer defines a machine-native parallel layer to the human web. Three file formats  
give autonomous AI agents everything they need to discover, verify, consume, and pay for  
structured knowledge — without parsing HTML.

```
.spsk  →  Site manifest (publisher identity + public keys)
.spk   →  Signed knowledge document (depth-layered content graph)
.spki  →  Action interface (declared intents + economic terms)
```

**The agent workflow:**
```
DISCOVER → VALIDATE → NEGOTIATE → CONSUME → ACT → SETTLE
(fetch .spsk) (Ed25519) (depth/tokens) (read .spk) (.spki) (token bank)
```

---

## Key Performance Numbers

| Metric | HTML Scraping | SeamLayer | Δ |
|---|---|---|---|
| LLM calls to parse a document | 4 | **0** | −100% |
| End-to-end processing time | 9,170ms | **262ms** | 35× faster |
| Processing cost per document | $0.044 | **$0.000** | −100% |
| Immediately actionable content | 30% | **100%** | +70pp |
| Hallucination risk | 72% | **18%** | −54% |
| Provenance coverage | 5% | **100%** | cryptographic |
| Pipeline reliability | 12% | **93%** | +683pp |

---

## Repository Structure

```
SeamLayer/
├── Config/
│   ├── spsk.schema.json        JSON Schema — Site Key
│   ├── spk.schema.json         JSON Schema — Knowledge Document
│   └── spki.schema.json        JSON Schema — Knowledge Interface
│
├── Data/
│   ├── examples/               Complete annotated examples (.spsk/.spk/.spki)
│   └── benchmark/              Benchmark results (HTML vs .spk)
│
├── Scripts/
│   ├── sparkifier.py           Publisher tool: HTML/MD → .spk files
│   ├── seamlayer_skill.py     Agent skill (LangGraph / CrewAI / AutoGen)
│   └── benchmark.py            Comparative benchmark
│
├── Docker/                     Vault server (coming)
│
└── Docs/
    ├── Pipeline/               Architecture diagram (July 2025)
    ├── WhitePaper/             Technical specification v2
    ├── LandingPage/            sparkprotocol.io
    └── Legal/                  Authorship, EU position paper, letters
```

---

## Quick Start

```bash
# Sparkifier — convert your content to SeamLayer files
pip install beautifulsoup4 markdown cryptography
python Scripts/sparkifier.py \
  --input article.md \
  --domain yourdomain.com \
  --output ./output

# Agent Skill — integrate into your agent framework
pip install requests cryptography
python Scripts/seamlayer_skill.py ./output

# Benchmark — reproduce the results
python Scripts/benchmark.py \
  --spk-dir ./output \
  --html article.html
```

---

## Regulatory Alignment

SeamLayer directly implements:

| Regulation | Article | Coverage |
|---|---|---|
| EU AI Act | Art. 53(1)(c) | Machine-readable copyright compliance per content block |
| EU AI Act | Art. 53(1)(d) | Cryptographically signed training data summaries |
| EU AI Act | Art. 10 | Data quality flags, provenance chain, version control |
| DSM Directive | Art. 4 | Machine-readable TDM reservation at block level |

A formal position paper has been submitted to the EU AI Act GPAI Code of Practice consultation.  
Formal letters sent to AI Office and DG CONNECT (May 2026).

---

## Standardisation Path

1. **EU AI Act GPAI Code of Practice** — recognition as reference technical standard
2. **W3C Community Group** — formal web standardisation submission
3. **IETF** — `.well-known/spark.spsk` registration

---

## Citation

```bibtex
@misc{martin2026seamlayer,
  author    = {Martin, Romuald},
  title     = {SeamLayer: An Agent-to-Agent Protocol for the AI-First Web Economy},
  year      = {2026},
  month     = {May},
  publisher = {GitHub},
  url       = {https://github.com/totalarico702/SeamLayer}
}
```

---

## License

MIT License — Copyright (c) 2025-2026 Romuald Martin

The SeamLayer **protocol specification** (schemas, file formats, compliance levels)  
is additionally placed in the public domain under **CC0 1.0** to ensure maximum  
adoption and prevent patent enclosure.

---

*"The next user of the web is not human. SeamLayer is the protocol they will use."*
