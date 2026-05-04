# SparkLayer Protocol — White Paper V2
## An Agent-to-Agent Protocol for the AI-First Web Economy
**Author:** Romuald Martin — Cabin Skolar  
**Version:** 2.0 — Draft  
**Date:** May 2026  
**Status:** Discussion Draft — W3C Community Group Submission Target

---

## Abstract

The web was built for human eyes. HTML, CSS, JavaScript — every layer of the stack assumes a visual renderer and a human interpreter. As autonomous AI agents become primary consumers of web content, this assumption collapses. Agents do not need visual rendering. They need semantic precision, verifiable provenance, structured action surfaces, and economic negotiation primitives.

SparkLayer is a protocol designed for this reality. It defines a machine-native parallel layer to the human web — not a replacement, but a dedicated surface where agents discover, negotiate, consume, and act upon structured knowledge under clear economic and cryptographic rules.

Its primary consumer is not a human publisher. It is an autonomous agent — running inside Claude Code, OpenClaw, CrewAI, LangGraph, or the next generation of agentic frameworks — that needs to interact with web content without human intermediation.

**SparkLayer is the HTTP of the agent economy.**

---

## Table of Contents

1. Problem Statement
2. Design Philosophy
3. Protocol Architecture Overview
4. File Format Specification
   - 4.1 `.spsk` — Spark Protocol Site Key
   - 4.2 `.spk` — Spark Protocol Knowledge
   - 4.3 `.spki` — Spark Protocol Knowledge Interface
5. The Depth Model
6. Cryptographic Security & Handshake
7. The Honeypot Mechanism (Abysse Data)
8. Token Bank & Economic Layer
9. Intent Taxonomy
10. Agent Skill Specification
11. Compliance Levels
12. The HTML Bridge Layer (depth_0 output)
13. Deployment Modes
    - 13.1 SparkLayer Open (web public)
    - 13.2 SparkLayer Lite (intranet / réseau de confiance)
14. Performance Benchmarks & Investment Thesis
15. Competitive Landscape
16. Standardization Roadmap
17. Open Research Questions
18. Appendix: Full Schema Reference

---

## 1. Problem Statement

### 1.1 The Human Web is Structurally Hostile to Agents

A modern web page contains, on average:
- 2–4 MB of JavaScript (rendering logic irrelevant to content)
- 300–800 DOM elements (navigation, ads, widgets, footers)
- 40–60% non-content markup (decorative, interactive, tracking)
- Zero machine-readable action surfaces (buttons are pixels with event handlers)

An AI agent attempting to extract semantic content from this structure must:
1. Parse and execute JavaScript to obtain the rendered DOM
2. Identify content-bearing elements from noise (computationally expensive)
3. Infer the semantic type of each content unit (hallucination risk)
4. Guess action surfaces from visual layout and label text
5. Reconstruct provenance from incomplete or absent metadata

This process consumes 5–10x more compute tokens than reading equivalent pre-structured data. It introduces systematic ambiguity at every step. It produces no economic signal to the content creator.

### 1.2 The Zero-Click Economy is Destroying Publisher Revenue

Search engines built on LLMs answer queries directly from ingested content. Publishers whose content trained these models receive no attribution and no compensation. The value chain is:

```
Publisher creates content → LLM ingests freely → LLM answers user → User never visits publisher
```

Existing mechanisms (robots.txt, paywalls, schema.org) are inadequate:
- **robots.txt**: Declarative, easily ignored, no enforcement
- **Paywalls**: Block humans and compliant agents equally; trivially bypassed by scrapers
- **Schema.org**: Descriptive metadata only; no access control, no monetization, no provenance chain

### 1.3 The Emerging Agent Economy Has No Protocol

As autonomous agents proliferate — writing code, managing workflows, conducting research, executing transactions — they increasingly need to interact with external knowledge sources. Today this interaction is:
- **Unstructured**: Agents scrape HTML like humans would browse
- **Uneconomic**: No payment mechanism between agents and content sources
- **Unverifiable**: No cryptographic proof that content came from its claimed source
- **Unactionable**: No standardized way to discover and invoke services

SparkLayer fills this gap.

---

## 2. Design Philosophy

### 2.1 Agents Are the Primary User

Every design decision in SparkLayer optimizes for machine consumption, not human readability. Format density over verbosity. Semantic precision over natural language descriptions. Cryptographic verifiability over trust-by-convention.

This is not a compromise. It is a deliberate inversion of web standards priorities.

### 2.2 One Protocol, Two Deployment Modes

SparkLayer does not bifurcate into a "simple" and "complex" version. It defines one protocol with two deployment profiles:

- **SparkLayer Open**: Full stack — cryptographic signing, vault access, token bank, honeypot, compliance enforcement. For the public web where threat actors exist.
- **SparkLayer Lite**: Protocol-identical, security-relaxed. For closed networks (intranets, enterprise ERP, internal knowledge bases) where the threat model is organizational, not cryptographic.

Same file formats. Same agent skill. Same tooling. Different security configuration in `manifest.json`.

### 2.3 The HTML Layer is a Derivative, Not a Source

Publishers do not write HTML and SparkLayer in parallel. They define their knowledge structure in `.spk` and their action surfaces in `.spki`. The Sparkifier toolchain derives two outputs:
- The `.spsk` manifest
- The HTML page (with depth_0 content injected as auto-generated balises)

The human web becomes a rendering artifact of the agent web. Not the other way around.

### 2.4 Economic Enforcement via Vault, Not via Good Faith

A grammar that can be ignored will be ignored. SparkLayer's economic model is not declarative — it is architectural. Content beyond depth_0 is not annotated as "please pay." It is **not transmitted** without verified payment. The vault is the enforcement mechanism.

---

## 3. Protocol Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    PUBLISHER SIDE                        │
│                                                          │
│  Raw Content → [SPARKIFIER] → .spsk (manifest + keys)   │
│                             → .spk  (knowledge graph)   │
│                             → .spki (action interfaces) │
│                             → HTML  (depth_0 derivative) │
│                                                          │
│  Vault Server: controls depth-gated content delivery    │
│  Token Bank:   manages crawler wallets + settlements    │
└─────────────────────────────────────────────────────────┘
                           ↕ HTTPS + Handshake
┌─────────────────────────────────────────────────────────┐
│                     AGENT SIDE                           │
│                                                          │
│  1. DISCOVER  → fetch /.well-known/spark.spsk           │
│  2. VALIDATE  → verify cryptographic signature          │
│  3. NEGOTIATE → evaluate depth vs token balance         │
│  4. CONSUME   → read .spk structured knowledge          │
│  5. ACT       → invoke .spki action endpoints           │
│  6. SETTLE    → token bank transaction + receipt        │
└─────────────────────────────────────────────────────────┘
```

The agent never touches the HTML DOM. The HTML exists for human browsers. The SparkLayer stack exists for agents.

---

## 4. File Format Specification

### 4.1 `.spsk` — Spark Protocol Site Key

The `.spsk` is the public, unsigned entry point. Served at `/.well-known/spark.spsk`. It contains no sensitive content — only the publisher's identity, public keys, and pointers to `.spk`/`.spki` resources.

**Analogies**: `robots.txt` meets `/.well-known/openid-configuration` meets DNS root certificate.

```json
{
  "@context": "https://sparkprotocol.io/context/spsk-v1.jsonld",
  "@id": "spark:site:example.com",
  "@type": "SparkSiteKey",
  "name": "Example Publisher",
  "spark_protocol_version": "2.0",
  "publisher": {
    "name": "Example Media",
    "url": "https://example.com/about",
    "id": "spark:org:example-media"
  },
  "public_keys": [
    {
      "id": "spark:key:example.com:primary",
      "type": "Ed25519VerificationKey2020",
      "publicKeyMultibase": "z6Mkf5rGMoatrSj1f4CyvuHBeXJELe9y84QbdU7b6T1RZ"
    }
  ],
  "default_depth_spark": 1,
  "max_depth_spark": 4,
  "entry_points": {
    "articles": {
      "url": "enc://example.com/spark/articles/index.spk",
      "description": "Article knowledge graph index"
    },
    "products": {
      "url": "enc://example.com/spark/products/index.spk",
      "description": "Product catalog semantic layer"
    },
    "actions": {
      "url": "enc://example.com/spark/actions.spki",
      "description": "Available agent action interfaces"
    }
  },
  "compliance_required": "level_2",
  "honeypot_enabled": true,
  "vault_endpoint": "https://vault.example.com/spark/v2",
  "token_bank_endpoint": "https://tokenbank.sparkprotocol.io/v2",
  "last_updated": "2026-05-01T00:00:00Z"
}
```

**Key design decisions:**
- `public_keys` uses Ed25519 (faster, smaller signatures than RSA for agent-scale verification)
- `enc://` scheme signals that the URL is vault-protected and requires authentication
- `compliance_required` sets the minimum level the publisher will serve — Level 0 crawlers get the honeypot
- `honeypot_enabled` is a flag, but its content is never described in the `.spsk` (security by obscurity is valid here)

---

### 4.2 `.spk` — Spark Protocol Knowledge

The `.spk` is the semantic knowledge representation of a content resource. It is a signed JSON-LD document containing the content's knowledge graph, structured by depth level.

**Analogies**: A rich API response meets a knowledge graph node meets a signed document.

```json
{
  "@context": [
    "https://schema.org/",
    "https://sparkprotocol.io/context/spk-v2.jsonld"
  ],
  "@id": "spark:article:example.com/tech/ai-protocols-2026",
  "@type": "Article",
  "headline": "The Emergence of Agent-Native Protocols",
  "author": {
    "@type": "Person",
    "name": "Jane Doe",
    "identifier": "ORCID:0000-0002-1825-0097"
  },
  "publisher": { "@id": "spark:org:example-media" },
  "datePublished": "2026-04-15T09:00:00Z",
  "dateModified": "2026-04-20T14:30:00Z",
  "version": "v1.2",
  "license": "CC-BY-4.0",
  "keywords": ["AI protocols", "agent economy", "semantic web"],
  "language": "en",

  "depth_layers": {
    "0": {
      "access": "public",
      "content": {
        "summary": "Analysis of emerging protocols designed for autonomous AI agents.",
        "entities": [
          { "@id": "spark:concept:agent-protocols", "name": "Agent Protocols" },
          { "@id": "spark:concept:semantic-web", "name": "Semantic Web" }
        ]
      }
    },
    "1": {
      "access": "public",
      "token_cost": 0,
      "content": {
        "sections": [
          {
            "@type": "spark:Section",
            "spark:sectionType": "Context",
            "text": "The evolution from human-centric to agent-centric web infrastructure...",
            "entities": [...]
          }
        ]
      }
    },
    "2": {
      "access": "token_required",
      "token_cost": 10,
      "usage": ["train", "display"],
      "content": {
        "sections": [
          {
            "@type": "spark:Section",
            "spark:sectionType": "Analysis",
            "text": "...",
            "statistics": [
              {
                "@type": "spark:Statistic",
                "value": "73%",
                "description": "Reduction in agent compute cost with structured data",
                "confidence": 0.87,
                "source": "spark:study:agent-efficiency-2026"
              }
            ]
          }
        ]
      }
    },
    "3": {
      "access": "vault_required",
      "token_cost": 50,
      "usage": ["train", "finetune"],
      "vault_ref": "vault://example.com/spark/datasets/ai-protocols-full",
      "content_descriptor": {
        "@type": "spark:Dataset",
        "format": "JSON",
        "records": 4821,
        "schema_url": "enc://example.com/spark/schemas/ai-protocols.json"
      }
    }
  },

  "related": [
    {
      "@id": "spark:article:example.com/tech/mcp-analysis",
      "relation": "elaborates",
      "spark:confidence": 0.92
    }
  ],

  "provenance": {
    "origin": "https://example.com/tech/ai-protocols-2026",
    "created_by": "spark:agent:sparkifier-v2",
    "editorial_review": true,
    "fact_checked": true,
    "last_verified": "2026-04-20T14:30:00Z"
  },

  "integrity": {
    "hash_algorithm": "SHA-256",
    "content_hash": "a3f8b2c1d4e5f6...",
    "signature": "z4X7mK2nP9qR...",
    "signing_key": "spark:key:example.com:primary"
  }
}
```

**Key design decisions:**
- `depth_layers` is the core monetization primitive — content is partitioned by access level
- `usage` array at depth level controls training/finetuning rights granularly
- `provenance` block is non-separable from content (unlike HTML metadata which can be stripped)
- `integrity.signature` enables any agent to verify the file was not tampered with post-publication
- `content_hash` covers the content object only (so the signature remains valid if metadata like `last_verified` is updated without content change)

---

### 4.3 `.spki` — Spark Protocol Knowledge Interface

The `.spki` describes the **action surface** of a publisher — what operations an autonomous agent can invoke, under what conditions, at what cost. It is the agent-native equivalent of an OpenAPI specification, but designed for machine consumption, not human documentation.

**Critical distinction from OpenAPI**: OpenAPI documents APIs for human developers who will write client code. `.spki` is consumed directly by autonomous agents making runtime decisions about whether and how to invoke actions. The format is optimized for inference-time parsing, not developer ergonomics.

```json
{
  "@context": "https://sparkprotocol.io/context/spki-v2.jsonld",
  "@id": "spark:interface:example.com",
  "@type": "SparkInterface",
  "publisher": { "@id": "spark:org:example-media" },
  "version": "2.1.0",
  "last_updated": "2026-05-01T00:00:00Z",

  "global_rate_limits": {
    "requests_per_minute": 60,
    "burst": 10,
    "per_agent_daily_limit": 10000
  },

  "actions": [
    {
      "@id": "spark:action:example.com/search",
      "@type": "spark:ActionIntent",
      "name": "Search Content",
      "description": "Full-text and semantic search across publisher knowledge graph",
      "intent_category": "query",
      "access_level": "public",
      "http_method": "GET",
      "endpoint": "https://api.example.com/spark/v2/search",
      "input_schema": {
        "query": { "type": "string", "required": true, "max_length": 500 },
        "depth_max": { "type": "integer", "required": false, "default": 1 },
        "semantic_mode": { "type": "boolean", "required": false, "default": true }
      },
      "output_schema": {
        "results": "array<spark:KnowledgeRef>",
        "total": "integer",
        "next_cursor": "string?"
      },
      "cost_per_invocation": { "tokens": 0 },
      "rate_limit": { "requests_per_minute": 30 }
    },
    {
      "@id": "spark:action:example.com/purchase",
      "@type": "spark:ActionIntent",
      "name": "Purchase Content Access",
      "description": "Acquire depth-gated access token for specified content",
      "intent_category": "transaction",
      "access_level": "authenticated",
      "http_method": "POST",
      "endpoint": "https://vault.example.com/spark/v2/purchase",
      "input_schema": {
        "content_id": { "type": "string", "required": true },
        "depth_target": { "type": "integer", "required": true, "min": 1, "max": 4 },
        "agent_wallet": { "type": "string", "required": true }
      },
      "output_schema": {
        "access_token": "string",
        "expires_at": "ISO8601",
        "tokens_charged": "integer",
        "receipt_id": "string"
      },
      "cost_per_invocation": { "tokens": "variable", "pricing_ref": "spark:article:*:depth_layers" },
      "idempotency": true
    },
    {
      "@id": "spark:action:example.com/subscribe",
      "@type": "spark:ActionIntent",
      "name": "Subscribe on behalf of user",
      "description": "Register a user subscription via agent delegation",
      "intent_category": "registration",
      "access_level": "user_delegated",
      "requires_user_consent": true,
      "http_method": "POST",
      "endpoint": "https://api.example.com/spark/v2/subscribe",
      "input_schema": {
        "plan_id": { "type": "string", "required": true },
        "user_token": { "type": "string", "required": true, "description": "User consent token" }
      },
      "output_schema": {
        "subscription_id": "string",
        "active_from": "ISO8601"
      },
      "cost_per_invocation": { "tokens": 5, "note": "Agent service fee" }
    }
  ],

  "flows": [
    {
      "@id": "spark:flow:example.com/checkout",
      "name": "Purchase and Access Flow",
      "steps": [
        { "step": 1, "action": "spark:action:example.com/search", "intent": "discover" },
        { "step": 2, "action": "spark:action:example.com/purchase", "intent": "acquire" },
        { "step": 3, "action": "spark:action:example.com/read", "intent": "consume" }
      ]
    }
  ],

  "signature": "z9Xy8wV7uT6sR5...",
  "signing_key": "spark:key:example.com:primary"
}
```

**Key design decisions:**
- `intent_category` allows agents to reason about action types without reading descriptions (query / transaction / registration / notification / deletion)
- `flows` explicitly maps multi-step journeys — an agent doesn't need to infer checkout flow from individual buttons
- `requires_user_consent` is a first-class field — agents must gate user-affecting actions on explicit delegation
- `access_level` hierarchy: `public` → `authenticated` → `user_delegated` → `partner_api_key` → `paid_subscription`

---

## 5. The Depth Model

The depth model is the core monetization and access control primitive. It replaces binary paywalls with a graduated access structure.

```
depth_0  →  Public, free, auto-generated HTML balises
            Serves: all crawlers, search engines, human browsers
            Content: summary, title, key entities, publish date
            No authentication required

depth_1  →  Structured public content
            Serves: Level 1+ compliant agents
            Content: full article text, basic facts, citations
            Token cost: 0 (or minimal)

depth_2  →  Premium content
            Serves: Level 2+ compliant agents (payment capable)
            Content: data, analysis, statistics, methodology
            Token cost: defined per publisher

depth_3  →  Dataset / research grade
            Serves: Level 2+ with vault access
            Content: full datasets, raw data, source materials
            Token cost: higher, vault-gated

depth_N  →  Publisher-defined (up to max_depth_spark in .spsk)
            Serves: by negotiation
```

**Publisher decision surface:**
- Set `default_depth_spark` in `.spsk` (what agents get without auth)
- Set per-depth `token_cost` in `.spk`
- Set `max_depth_spark` to cap exposure
- Set `compliance_required` to define minimum agent level

**Agent decision surface:**
- Read `.spsk` to know available depth range
- Check own token balance
- Decide whether depth access value justifies cost
- Request vault access for depth ≥ vault_required threshold

---

## 6. Cryptographic Security & Handshake

### 6.1 Threat Model

The primary threats SparkLayer addresses:

**T1 — Content Substitution**: A malicious actor serves a modified `.spk` or `.spki` to redirect agent behavior (e.g., substituting a competitor's content with altered data, or injecting malicious action endpoints).

**T2 — Replay Attack**: An agent caches a valid access token and reuses it after expiry or for different content.

**T3 — Man-in-the-Middle**: An intermediary intercepts agent-vault communication and substitutes content.

**T4 — Honeypot Evasion**: A non-compliant scraper attempts to identify and avoid the honeypot layer.

### 6.2 Signing Protocol

All `.spk` and `.spki` files are signed using Ed25519. The signing flow:

```
1. Publisher generates Ed25519 keypair
2. Public key published in .spsk (publicly verifiable)
3. Private key signs content hash of .spk / .spki
4. Signature embedded in file's integrity block
5. Agent fetches .spsk, extracts public key
6. Agent fetches .spk, verifies signature against public key
7. If signature invalid → reject content, flag publisher
```

**Why Ed25519 over RSA:**
- 64-byte signatures vs 256+ bytes (token efficiency for agents)
- Verification is ~20x faster (critical at agent-scale parallel requests)
- No padding oracle vulnerabilities
- Deterministic (same input always produces same signature)

### 6.3 Vault Handshake Protocol

```
Agent                          Vault Server
  |                                |
  |-- GET /.well-known/spark.spsk →|
  |← .spsk (public key, vault_endpoint) --
  |                                |
  |-- POST /spark/v2/auth ------→  |
  |   { agent_id, wallet_addr,     |
  |     challenge_request: true }  |
  |← { challenge: nonce_xyz } ---  |
  |                                |
  |-- POST /spark/v2/auth ------→  |
  |   { agent_id,                  |
  |     challenge_response: sign(nonce_xyz, agent_private_key),
  |     content_id: "spark:article:...",
  |     depth_requested: 2 }       |
  |← { jwt_token, expires_at, --  |
  |    tokens_to_charge: 10 }      |
  |                                |
  |  [Agent verifies charge]       |
  |                                |
  |-- POST /spark/v2/settle ----→  |
  |   { jwt_token,                 |
  |     payment_proof: token_bank_receipt } |
  |← { access_token,              |
  |    content_url_signed,         |
  |    receipt_id } ---------------
  |                                |
  |-- GET content_url_signed ---→  |
  |← .spk depth_2 content --------
```

**Key properties:**
- Challenge-response prevents replay attacks
- Agent signs with its own private key (agents have identity in SparkLayer)
- Payment proof is verified before content delivery (not after)
- `content_url_signed` is a time-limited signed URL — it cannot be shared or reused

### 6.4 Agent Identity

Agents in SparkLayer have cryptographic identities. A `spark:agent:` identifier is associated with:
- An Ed25519 public key
- A token bank wallet address
- A compliance level certification
- A rate limit profile

This allows publishers to:
- Blacklist specific agents
- Apply per-agent pricing
- Track provenance of who accessed what content
- Issue compliance certifications to trusted agents

---

## 7. The Honeypot Mechanism (Abysse Data)

Non-compliant Level 0 crawlers that bypass the vault and scrape content directly are redirected to a synthetic knowledge graph — plausible but subtly corrupted data designed to degrade model quality when ingested at scale.

### 7.1 Design Principles

- **Plausibility**: Honeypot content must pass superficial quality checks. Statistics are realistic, entities are real, relationships are coherent at first glance.
- **Degradation**: Factual errors are subtle — dates off by years, statistics reversed, causal relationships inverted.
- **Fingerprinting**: Each honeypot response is uniquely fingerprinted, allowing detection of scraped content in model outputs.
- **Non-detectable**: Honeypot responses have identical HTTP headers, response times, and structure to legitimate responses.

### 7.2 Implementation

```
SparkLayer.honeypot = {
  trigger_conditions: [
    "missing_agent_id",
    "invalid_signature_on_request",
    "compliance_level < required_level",
    "rate_limit_exceeded_by > 300%",
    "vault_bypass_detected"
  ],
  response_strategy: "serve_abysse_data",
  fingerprint_method: "steganographic_text_embedding",
  degradation_level: "configurable_per_publisher"
}
```

### 7.3 Legal Dimension

Honeypot content carries explicit metadata declaring it as `spark:ContentType:AbysseData`. A compliant agent will detect this and discard the content. A non-compliant agent that ingests it cannot later claim good faith use — the metadata declaration is proof of notice.

---

## 8. Token Bank & Economic Layer

### 8.1 Architecture

The SparkLayer Token Bank is a centralized clearing infrastructure that manages economic exchange between agent wallets and publisher vaults. It is explicitly **not a blockchain** — it is a fiat-backed credit system analogous to pre-paid API credits.

```
Real Money Flow:
  AI Company (OpenAI, Anthropic, etc.)
    → buys SparkTokens (fiat → tokens at fixed rate)
    → tokens credited to company's master wallet
    → distributed to agent sub-wallets as needed

Transaction Flow:
  Agent wallet → SparkLayer Token Bank → Publisher vault
  (debit)                               (credit 85%)
                                        (SparkLayer fee 15%)

Settlement:
  Publisher → withdraws accumulated token balance
            → Token Bank converts to fiat
            → Wire transfer or payment provider
```

### 8.2 Token Economics

- **1 SparkToken = €0.01** (fixed rate, not market-driven)
- **Publisher receives 85%** of token cost per access
- **SparkLayer takes 15%** as clearing fee
- **Minimum purchase**: 1000 tokens (€10)
- **Minimum publisher withdrawal**: 500 tokens (€4.25)

### 8.3 Pricing Signals

Publishers set token costs per depth level. Over time, the Token Bank will expose:
- **Demand signals**: Which content is accessed most by agents
- **Quality signals**: Agents can rate content accuracy post-ingestion
- **Dynamic pricing**: Publishers can adjust costs based on demand (experimental)

### 8.4 Agent Budget Management

Agents operate with a token budget. SparkLayer-aware agent frameworks implement:

```python
class SparkAgent:
    def __init__(self, token_budget: int):
        self.wallet = TokenWallet(balance=token_budget)

    def should_access_depth(self, content_id: str, depth: int, cost: int) -> bool:
        if cost > self.wallet.balance:
            return False
        # Agent-defined value heuristic
        estimated_value = self.estimate_content_value(content_id, depth)
        return estimated_value > cost * VALUE_THRESHOLD

    def access_content(self, content_id: str, depth: int):
        receipt = SparkVault.request_access(content_id, depth, self.wallet)
        self.wallet.debit(receipt.tokens_charged)
        return receipt.content
```

---

## 9. Intent Taxonomy

Intents are the semantic annotations on action surfaces in `.spki`. They allow agents to reason about what an action does without executing it.

### 9.1 Top-Level Intent Categories

```
spark:intent:query          →  Read-only information retrieval
spark:intent:transaction    →  Creates economic exchange
spark:intent:registration   →  Creates persistent state for user/agent
spark:intent:modification   →  Updates existing content/state
spark:intent:deletion       →  Removes content/state (CAUTION)
spark:intent:notification   →  Triggers communication to user/third party
spark:intent:delegation     →  Acts on behalf of user (requires consent)
spark:intent:discovery      →  Navigational — finds other resources
```

### 9.2 Intent Composition

Complex flows are described as intent chains:

```json
{
  "flow_id": "spark:flow:ecommerce/purchase",
  "intent_chain": [
    { "step": 1, "intent": "spark:intent:query:search-product" },
    { "step": 2, "intent": "spark:intent:query:get-product-detail" },
    { "step": 3, "intent": "spark:intent:transaction:add-to-cart" },
    { "step": 4, "intent": "spark:intent:delegation:checkout", "requires_user_consent": true }
  ]
}
```

An agent reading this flow knows:
- Steps 1-2: can execute autonomously (read-only)
- Step 3: economic action, check budget
- Step 4: requires explicit user delegation before proceeding

### 9.3 Context Annotations

Beyond category, intents carry context annotations that eliminate inferential ambiguity:

```json
{
  "action": "Submit Form",
  "intent": "spark:intent:registration:newsletter-signup",
  "reversible": false,
  "affects_external_parties": false,
  "requires_user_consent": true,
  "estimated_completion_time": "PT2S",
  "on_success": "spark:state:user:newsletter-subscribed",
  "on_failure": "spark:state:unchanged"
}
```

This eliminates the need for an agent to infer whether a "Submit" button will:
- Send an email
- Place an order
- Delete an account
- Subscribe to a service

Each is explicitly declared.

---

## 10. Agent Skill Specification

SparkLayer is implemented as a **skill** in agent frameworks. A skill is a self-contained capability module that agents can invoke. The SparkLayer skill encapsulates the complete protocol interaction.

### 10.1 Skill Interface

```python
class SparkLayerSkill:
    """
    SparkLayer Protocol v2 — Agent Skill
    Compatible with: Claude Code, OpenClaw, CrewAI, LangGraph, AutoGen
    """

    def discover(self, domain: str) -> SparkSiteKey | None:
        """
        Fetch and validate .spsk from domain.
        Returns None if domain is not SparkLayer-enabled.
        Falls back to direct HTML access if honeypot risk acceptable.
        """

    def assess(self, site_key: SparkSiteKey, content_id: str) -> AccessAssessment:
        """
        Evaluate available depth levels, costs, and access requirements.
        Returns cost/value matrix for agent decision-making.
        """

    def consume(self, content_id: str, depth: int, wallet: TokenWallet) -> SparkContent:
        """
        Full access flow: authenticate → pay → receive → verify signature.
        Raises SparkHoneypotDetected if Abysse Data detected in response.
        """

    def act(self, action_id: str, params: dict, wallet: TokenWallet) -> ActionResult:
        """
        Invoke a .spki action endpoint.
        Handles authentication, payment, and response verification.
        """

    def search(self, domain: str, query: str, depth_max: int = 1) -> list[SparkRef]:
        """
        Semantic search across publisher knowledge graph.
        Returns list of SparkRef with content IDs and depth availability.
        """
```

### 10.2 Integration Examples

**Claude Code integration:**
```python
# When generating a web project, Claude Code auto-generates SparkLayer files
sparklayer = SparkLayerSkill(wallet=project_wallet)
sparklayer.generate_spsk(site_config)
sparklayer.generate_spk_for_content(content_tree, depth_config)
sparklayer.generate_spki_for_api(api_spec)
```

**Research agent integration:**
```python
# Agent researching a topic uses SparkLayer for structured data access
for domain in candidate_sources:
    if site_key := sparklayer.discover(domain):
        assessment = sparklayer.assess(site_key, topic_query)
        if assessment.value_score > THRESHOLD:
            content = sparklayer.consume(assessment.best_content_id,
                                          depth=assessment.recommended_depth,
                                          wallet=self.wallet)
            knowledge_graph.ingest(content)
    else:
        # Fall back to HTML scraping (lower quality, no provenance)
        content = html_scraper.fetch(domain)
```

---

## 11. Compliance Levels

Compliance levels define agent behavior tiers. Publishers set minimum required levels in `.spsk`. Non-compliant agents receive honeypot data.

```
Level 0 — Non-Compliant
  Behavior:  Ignores SparkLayer entirely, scrapes HTML
  Access:    depth_0 only (HTML balises)
  Receives:  Honeypot data if vault-bypass detected
  Risk:      Legal (license violation), technical (model degradation)

Level 1 — Basic Compliance
  Behavior:  Reads .spsk and .spk, respects depth limits
  Access:    Public depth levels (cost = 0)
  Provides:  Agent identity header on requests
  Risk:      Excluded from premium content

Level 2 — Monetization Compliance
  Behavior:  Full vault handshake, token payment capable
  Access:    All depth levels (per cost)
  Provides:  Agent identity + wallet + transaction receipts
  Certification: Self-declared (verified by Token Bank activity)

Level 3 — Ethical Compliance
  Behavior:  Level 2 + respects usage restrictions (train/finetune/display)
  Access:    All depth levels including research-only content
  Provides:  Attribution in model outputs, transparency reports
  Certification: Third-party verified (SparkLayer Compliance Registry)
```

---

## 12. The HTML Bridge Layer (depth_0 output)

The HTML layer is **derived from the SparkLayer stack**, not authored in parallel.

The Sparkifier generates HTML balises from depth_0 content:

```html
<!-- Auto-generated by Sparkifier v2 from .spk -->
<!-- Do not edit manually — regenerate from source -->

<article 
  data-spark-id="spark:article:example.com/tech/ai-protocols"
  data-spark-version="v1.2"
  data-spark-depth-available="4"
  data-spark-endpoint="/.well-known/spark.spsk">

  <meta spark:content-type="Article" />
  <meta spark:license="CC-BY-4.0" />
  <meta spark:depth-0="public" spark:depth-1="public" 
        spark:depth-2="token:10" spark:depth-3="vault" />

  <!-- depth_0 content only -->
  <h1 spark:type="Headline">The Emergence of Agent-Native Protocols</h1>
  
  <span spark:type="Entity" spark:id="spark:concept:agent-protocols">
    Agent Protocols
  </span>

  <p spark:type="Summary">
    Analysis of emerging protocols designed for autonomous AI agents.
  </p>

  <!-- CTA for human readers -->
  <a href="/.well-known/spark.spsk" data-spark-discovery="true">
    [AI Agent? Access full structured data via SparkLayer]
  </a>

</article>
```

**Properties of this approach:**
- Publisher never writes balises manually (generated)
- Balises are surface-only depth_0 — no exploitable content in HTML
- `data-spark-*` attributes are discovery hints for agents that encounter HTML
- Human readers see clean HTML; agents see the discovery pointer and switch to SparkLayer

---

## 13. Deployment Modes

### 13.1 SparkLayer Open (Web Public)

Full protocol stack. Mandatory for public web deployment where threat actors exist.

**Components required:**
- Sparkifier (content → .spk/.spki/.spsk generator)
- Vault Server (depth-gated content delivery)
- Token Bank integration (SparkLayer hosted or self-hosted enterprise)
- Ed25519 signing pipeline
- Honeypot generator

**Deployment options:**
- **SparkLayer Cloud SaaS**: Hosted vault + token bank. Publisher integrates via CMS plugin.
- **Self-hosted Docker**: Full stack in containers. For publishers requiring data sovereignty.

### 13.2 SparkLayer Lite (Intranet / Réseau de Confiance)

Same file formats, same agent skill, relaxed security profile.

**What changes:**
- No vault server required (content served directly)
- No token bank (or internal billing system replaces it)
- Signature verification optional (organizational trust replaces cryptographic trust)
- No honeypot (threat model is organizational, not adversarial)

**What stays identical:**
- `.spk` format and depth model
- `.spki` format and intent taxonomy
- Agent skill interface
- HTML bridge layer

**Use cases:**
- SAP / Salesforce / ServiceNow internal knowledge bases
- Confluence / Notion enterprise wikis
- Internal API documentation
- Healthcare / Legal document systems with AI access

**Value proposition for enterprise:**
An agent navigating an SAP instance annotated with SparkLayer Lite reduces task completion time by eliminating DOM inference. The same agent skill used externally works internally — no retraining, no adaptation.

---

## 14. Performance Benchmarks & Investment Thesis

### 14.1 Quantifiable Gaps

These metrics are the basis for the investment thesis. Benchmark methodology is described in Appendix B.

**Signal-to-Noise Ratio:**
- HTML page: 40-60% relevant content tokens
- `.spk` depth_1: ~95% relevant content tokens
- Improvement: 1.6–2.4x token efficiency per content unit

**Intent Resolution Time:**
- Agent on HTML page: 3–8 LLM calls to identify actionable elements
- Agent on `.spki` with intents: 0 additional LLM calls (machine-readable)
- Improvement: eliminates intent-inference entirely

**Hallucination Reduction (preliminary):**
- Training on HTML-scraped data: baseline hallucination rate
- Training on SparkLayer `.spk` data: estimated 15–30% reduction (hypothesis; requires formal benchmark)
- Mechanism: explicit entity disambiguation, provenance chain, version-controlled facts

**Preprocessing Cost:**
- HTML → training-ready: 4–7 pipeline steps (parse, clean, extract, classify, normalize, deduplicate, quality-filter)
- `.spk` → training-ready: 1 step (schema validation)
- Cost reduction: estimated 60–80% preprocessing infrastructure savings

### 14.2 Revenue Model for SparkLayer Inc.

```
Take rate model (Stripe for AI content):

  Year 1: 50 publishers, 10 AI companies as crawlers
           Avg 1M token transactions/month
           €0.01/token × 15% take rate = €1,500 MRR

  Year 2: 500 publishers, 50 crawlers
           10M transactions/month
           €15,000 MRR

  Year 3: 5,000 publishers, enterprise deals
           100M transactions/month
           €150,000 MRR + enterprise licensing

  Moat: network effects (more publishers = more value to crawlers = 
        more crawlers = more revenue to publishers = more publishers)
```

---

## 15. Competitive Landscape

| Mechanism | Semantic Structure | Access Control | Monetization | Agent-Native | Provenance |
|-----------|-------------------|----------------|--------------|--------------|------------|
| robots.txt | None | Domain-level only | None | No | None |
| Schema.org | Partial | None | None | No | None |
| llms.txt | Minimal | None | None | Partial | None |
| OpenAPI | API-only | Auth schemes | None | Partial | None |
| Cloudflare AI Audit | None | Network-level | None | No | None |
| **SparkLayer** | **Full** | **Depth + Vault** | **Token Bank** | **Yes** | **Signed** |

**Key differentiation from llms.txt** (closest simple competitor):
llms.txt is a plain text file that tells LLMs what content exists. It has no access control, no monetization, no cryptographic verification, no action surfaces, and no depth model. It is to SparkLayer what `favicon.txt` is to a full web application.

**Key differentiation from OpenAPI:**
OpenAPI documents APIs for human developers. `.spki` defines action surfaces for autonomous agents making runtime decisions. Different reader, different format optimization, different economic model.

---

## 16. Standardization Roadmap

### Phase 1: Protocol + Tooling (Months 1-6)
- Finalize v2.0 spec (this document)
- Open-source Sparkifier
- Open-source reference vault server (Docker)
- Open-source SparkLayer skill (Python, TypeScript)
- First 3 pilot publishers

### Phase 2: Ecosystem (Months 6-18)
- SparkLayer Cloud SaaS (hosted vault + token bank)
- WordPress/Ghost/Webflow plugins
- Integration with one major agent framework (LangGraph or CrewAI)
- 50 publishers, 5 AI company integrations
- First W3C Community Group submission

### Phase 3: Standard (Months 18-36)
- W3C Candidate Recommendation
- Enterprise SparkLayer Lite (self-hosted)
- Compliance certification program
- Token Bank API opened to third-party vault operators

---

## 17. Open Research Questions

These are genuine open problems. Contributions welcome.

**Q1 — Agent Identity Bootstrapping**
How does an agent acquire its first Ed25519 keypair and Token Bank wallet? What prevents Sybil attacks (one actor creating thousands of agent identities to bypass per-agent rate limits)?

**Q2 — Depth Pricing Dynamics**
What is the equilibrium price for depth levels? Should Token Bank expose a pricing API that allows publishers to observe market rates? What happens to content access when an AI company goes bankrupt mid-crawl?

**Q3 — Honeypot Detection Arms Race**
Sufficiently sophisticated scrapers will eventually fingerprint honeypot responses. What is the long-term viability of Abysse Data as a defense? Is there a cryptographic alternative?

**Q4 — Attribution in Model Outputs**
Level 3 compliance requires attribution in model outputs. How is this technically implemented? Is it metadata in the inference output? In-context citation? Model training signal?

**Q5 — Multi-Agent Content Negotiation**
When a multi-agent pipeline (Agent A calls Agent B which calls Agent C) accesses SparkLayer content, who is accountable for compliance? How is the token cost attributed across the chain?

**Q6 — Offline / Edge Agent Access**
An agent operating offline (cached content, edge deployment) cannot perform vault handshake in real-time. What caching semantics are appropriate? How long is a vault access token valid?

**Q7 — Adversarial Publisher**
A publisher could serve valid `.spk` content at depth_1 but inject subtly misleading information at depth_2 (behind the paywall, after the agent has already paid). What recourse does the agent have? Can the Token Bank implement post-access quality scoring?

**Q8 — The Sparkifier as Single Point of Failure**
If the Sparkifier (content → .spk generator) makes systematic errors in semantic classification, all downstream agents inherit those errors. How do we build quality assurance into the generation pipeline?

---

## 18. Appendix: Full Schema Reference

### A.1 SparkToken Types in `.spk`

```
spark:Section        →  Generic content section
spark:Fact           →  Verifiable atomic statement
spark:Statistic      →  Quantitative data point with confidence
spark:Opinion        →  Subjective statement (flagged as non-trainable by default)
spark:Methodology    →  Process description
spark:Dataset        →  Structured data collection
spark:Conclusion     →  Summary/synthesis
spark:Warning        →  Caution/risk statement
spark:Citation       →  Reference to external source
spark:Instruction    →  Procedural steps
spark:Code           →  Executable or pseudocode
spark:Table          →  Tabular data
spark:Figure         →  Visual with description
spark:Entity         →  Named entity with disambiguation ID
spark:Concept        →  Abstract concept node in knowledge graph
spark:Relation       →  Edge between two graph nodes
```

### A.2 Intent Categories in `.spki`

```
spark:intent:query:search
spark:intent:query:get-detail
spark:intent:query:list
spark:intent:query:filter
spark:intent:transaction:purchase
spark:intent:transaction:add-to-cart
spark:intent:transaction:request-quote
spark:intent:registration:signup
spark:intent:registration:subscribe
spark:intent:registration:request-access
spark:intent:modification:update-profile
spark:intent:modification:correct-content
spark:intent:deletion:cancel-subscription
spark:intent:notification:send-message
spark:intent:notification:report-error
spark:intent:delegation:checkout
spark:intent:delegation:submit-form
spark:intent:discovery:navigate
spark:intent:discovery:sitemap
```

### A.3 Access Level Hierarchy

```
public              →  No auth required
authenticated       →  Valid agent identity required
user_delegated      →  Agent acts for user; requires user consent token
partner_api_key     →  Bilateral agreement between publisher and agent operator
paid_subscription   →  Active subscription in Token Bank
vault_only          →  Vault handshake mandatory regardless of subscription
```

### A.4 SparkLayer HTTP Headers

Agents MUST include these headers on all SparkLayer requests:

```
X-Spark-Agent-ID: spark:agent:<identifier>
X-Spark-Compliance-Level: 2
X-Spark-Protocol-Version: 2.0
X-Spark-Wallet: <wallet_address>
```

Publishers MUST include these headers on all SparkLayer responses:

```
X-Spark-Content-ID: spark:article:<identifier>
X-Spark-Depth-Served: 2
X-Spark-Signature: <ed25519_signature>
X-Spark-Receipt-ID: <transaction_id>
```

---

*SparkLayer Protocol v2.0 — Discussion Draft*  
*Romuald Martin — Cabin Skolar — May 2026*  
*Not an official W3C Recommendation*  
*Feedback: romuald.martin@gmail.com*
