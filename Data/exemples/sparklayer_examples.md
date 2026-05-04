# SparkLayer v2 — Example Files
# Three complete, valid examples: .spsk / .spk / .spki
# These are the reference implementations for the schemas.

---

## Example 1: example-media.spsk
## Serves at: https://example-media.com/.well-known/spark.spsk

```json
{
  "@context": "https://sparkprotocol.io/context/spsk-v2.jsonld",
  "@id": "spark:site:example-media.com",
  "@type": "SparkSiteKey",
  "name": "Example Media",
  "spark_protocol_version": "2.0",
  "publisher": {
    "name": "Example Media Inc.",
    "url": "https://example-media.com/about",
    "id": "spark:org:example-media",
    "contact": "spark-tech@example-media.com"
  },
  "public_keys": [
    {
      "id": "spark:key:example-media.com:primary-2026",
      "type": "Ed25519VerificationKey2020",
      "publicKeyMultibase": "z6MkrJVnaZkeFzdQyMZu1cgjg7k1pZZ6pvBQ7XJPt4swbTQ2",
      "status": "active"
    }
  ],
  "default_depth_spark": 1,
  "max_depth_spark": 3,
  "entry_points": {
    "articles": {
      "url": "https://example-media.com/spark/articles/index.spk",
      "description": "Article knowledge graph index — latest 1000 articles",
      "type": "spk_index",
      "access_level": "public"
    },
    "premium_datasets": {
      "url": "enc://example-media.com/spark/datasets/index.spk",
      "description": "Premium research datasets and raw data",
      "type": "spk_index",
      "access_level": "paid_subscription"
    },
    "actions": {
      "url": "https://example-media.com/spark/actions.spki",
      "description": "Available agent action interfaces",
      "type": "spki_interface",
      "access_level": "public"
    }
  },
  "compliance_required": "level_2",
  "honeypot_enabled": true,
  "vault_endpoint": "https://vault.example-media.com/spark/v2",
  "token_bank_endpoint": "https://tokenbank.sparkprotocol.io/v2",
  "deployment_mode": "open",
  "rate_limits": {
    "requests_per_minute_per_agent": 60,
    "requests_per_day_per_agent": 10000,
    "burst": 15
  },
  "supported_usage": ["display", "rag"],
  "last_updated": "2026-05-01T00:00:00Z",
  "ttl": 3600
}
```

---

## Example 2: ai-protocols-article.spk
## Represents: https://example-media.com/tech/ai-native-protocols-2026

```json
{
  "@context": [
    "https://schema.org/",
    "https://sparkprotocol.io/context/spk-v2.jsonld"
  ],
  "@id": "spark:article:example-media.com/tech/ai-native-protocols-2026",
  "@type": "NewsArticle",
  "headline": "The Emergence of Agent-Native Web Protocols",
  "author": {
    "@type": "Person",
    "name": "Sophie Chen",
    "identifier": "ORCID:0000-0002-1825-0097",
    "url": "https://example-media.com/authors/sophie-chen"
  },
  "publisher": {
    "@id": "spark:org:example-media",
    "name": "Example Media Inc."
  },
  "datePublished": "2026-04-15T09:00:00Z",
  "dateModified": "2026-04-20T14:30:00Z",
  "version": "v1.2",
  "license": "CC-BY-4.0",
  "language": "en",
  "keywords": ["AI protocols", "agent economy", "semantic web", "SparkLayer", "llms.txt"],

  "depth_layers": {
    "0": {
      "access": "public",
      "usage": ["display"],
      "content": {
        "summary": "Analysis of agent-native web protocols emerging in 2026, comparing SparkLayer, llms.txt, and OpenAPI-based approaches. Covers economic models and adoption trajectories.",
        "entities": [
          {
            "@id": "spark:concept:agent-protocols",
            "name": "Agent-Native Protocols",
            "type": "Concept"
          },
          {
            "@id": "wikidata:Q306438",
            "name": "Semantic Web",
            "type": "Concept"
          }
        ]
      }
    },
    "1": {
      "access": "public",
      "token_cost": 0,
      "usage": ["display", "rag"],
      "content": {
        "sections": [
          {
            "@type": "spark:Section",
            "spark:sectionType": "Context",
            "text": "The proliferation of autonomous AI agents in 2025-2026 exposed a fundamental mismatch between web infrastructure and machine consumption patterns. HTML pages, optimized for visual rendering, require agents to expend significant compute resources on parsing, noise removal, and semantic inference before any useful information can be extracted.",
            "entities": [
              { "@id": "spark:concept:html-parsing", "name": "HTML parsing overhead", "type": "Concept" }
            ],
            "trainable": true
          },
          {
            "@type": "spark:Section",
            "spark:sectionType": "Fact",
            "text": "Studies conducted in early 2026 showed that agents processing HTML pages consumed between 40-60% of their token budget on structural noise unrelated to content — JavaScript, CSS classes, navigation elements, and advertising markup.",
            "citations": [
              { "@id": "spark:study:agent-efficiency-2026", "text": "Agent Efficiency Study, Q1 2026" }
            ],
            "trainable": true
          }
        ],
        "statistics": [
          {
            "@type": "spark:Statistic",
            "value": "47%",
            "description": "Average proportion of HTML page tokens that are structural noise (non-content)",
            "confidence": 0.89,
            "source": "spark:study:agent-efficiency-2026",
            "as_of": "2026-03-01"
          }
        ]
      }
    },
    "2": {
      "access": "token_required",
      "token_cost": 15,
      "usage": ["display", "rag", "train"],
      "content": {
        "sections": [
          {
            "@type": "spark:Section",
            "spark:sectionType": "Analysis",
            "text": "Comparative analysis of three protocol approaches reveals significant differences in adoption friction vs enforcement capability. llms.txt offers zero friction but zero enforcement. OpenAPI extensions offer moderate friction with partial enforcement. SparkLayer's file-based approach requires infrastructure investment but delivers cryptographic enforcement with economic primitives.",
            "trainable": true
          }
        ],
        "statistics": [
          {
            "@type": "spark:Statistic",
            "value": "73%",
            "unit": "percent reduction",
            "description": "Reduction in agent preprocessing steps when consuming .spk vs raw HTML",
            "confidence": 0.91,
            "source": "spark:benchmark:spk-vs-html-2026",
            "as_of": "2026-04-01"
          },
          {
            "@type": "spark:Statistic",
            "value": 0,
            "unit": "additional LLM calls",
            "description": "Additional inference calls needed to resolve action intents from .spki vs DOM parsing",
            "confidence": 1.0,
            "source": "spark:benchmark:intent-resolution-2026"
          }
        ]
      }
    },
    "3": {
      "access": "vault_required",
      "token_cost": 80,
      "usage": ["train", "finetune"],
      "vault_ref": "vault://example-media.com/spark/datasets/agent-efficiency-full",
      "content_descriptor": {
        "@type": "spark:Dataset",
        "format": "JSON",
        "records": 12847,
        "schema_url": "https://example-media.com/spark/schemas/agent-efficiency.json",
        "preview_url": "https://example-media.com/spark/datasets/agent-efficiency-sample.json"
      }
    }
  },

  "related": [
    {
      "@id": "spark:article:example-media.com/tech/openapi-vs-sparklayer",
      "relation": "elaborates",
      "confidence": 0.95
    },
    {
      "@id": "spark:article:example-media.com/tech/llms-txt-analysis",
      "relation": "contradicts",
      "confidence": 0.71
    }
  ],

  "provenance": {
    "origin": "https://example-media.com/tech/ai-native-protocols-2026",
    "created_by": "spark:agent:sparkifier-v2",
    "editorial_review": true,
    "fact_checked": true,
    "last_verified": "2026-04-20T14:30:00Z",
    "abysse_data": false
  },

  "integrity": {
    "hash_algorithm": "SHA-256",
    "content_hash": "a3f8b2c1d4e5f678901234567890abcdef1234567890abcdef1234567890abcd",
    "signature": "base64url_encoded_ed25519_signature_placeholder",
    "signing_key": "spark:key:example-media.com:primary-2026",
    "signed_at": "2026-04-20T14:35:00Z"
  }
}
```

---

## Example 3: example-media-actions.spki
## Serves at: https://example-media.com/spark/actions.spki

```json
{
  "@context": "https://sparkprotocol.io/context/spki-v2.jsonld",
  "@id": "spark:interface:example-media.com",
  "@type": "SparkInterface",
  "publisher": {
    "@id": "spark:org:example-media",
    "name": "Example Media Inc."
  },
  "version": "2.0.1",
  "last_updated": "2026-05-01T00:00:00Z",
  "base_url": "https://api.example-media.com",

  "global_rate_limits": {
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "burst": 15,
    "per_agent_daily_limit": 10000
  },

  "authentication": {
    "spark_agent_id": true,
    "jwt": true,
    "api_key": true
  },

  "actions": [
    {
      "@id": "spark:action:example-media.com/search",
      "@type": "spark:ActionIntent",
      "name": "Search Knowledge Graph",
      "description": "Semantic and full-text search across publisher's structured content index",
      "intent_category": "query",
      "intent_subcategory": "spark:intent:query:search",
      "access_level": "public",
      "requires_user_consent": false,
      "reversible": true,
      "affects_external_parties": false,
      "http_method": "GET",
      "endpoint": "/spark/v2/search",
      "input_schema": {
        "q": {
          "type": "string",
          "description": "Search query (natural language or keyword)",
          "required": true,
          "max_length": 500
        },
        "depth_max": {
          "type": "integer",
          "description": "Maximum depth level to include in results",
          "required": false,
          "default": 1,
          "min": 0,
          "max": 3
        },
        "type_filter": {
          "type": "string",
          "description": "Filter by content type",
          "required": false,
          "enum": ["Article", "Dataset", "NewsArticle", "ScholarlyArticle"]
        },
        "date_from": {
          "type": "string",
          "format": "date-time",
          "description": "Filter content published after this date",
          "required": false
        },
        "limit": {
          "type": "integer",
          "description": "Maximum results to return",
          "required": false,
          "default": 10,
          "min": 1,
          "max": 100
        },
        "cursor": {
          "type": "string",
          "description": "Pagination cursor from previous response",
          "required": false
        }
      },
      "output_schema": {
        "results": "array<spark:KnowledgeRef>",
        "total": "integer",
        "next_cursor": "string?",
        "query_time_ms": "integer"
      },
      "cost_per_invocation": { "tokens": 0 },
      "rate_limit": { "requests_per_minute": 30 },
      "idempotency": true,
      "estimated_completion_time": "PT1S"
    },

    {
      "@id": "spark:action:example-media.com/get-content",
      "@type": "spark:ActionIntent",
      "name": "Get Content by ID",
      "description": "Retrieve a specific .spk document by its spark: identifier",
      "intent_category": "query",
      "intent_subcategory": "spark:intent:query:get-detail",
      "access_level": "authenticated",
      "requires_user_consent": false,
      "reversible": true,
      "affects_external_parties": false,
      "http_method": "GET",
      "endpoint": "/spark/v2/content/{content_id}",
      "input_schema": {
        "content_id": {
          "type": "string",
          "description": "spark: identifier of the content (e.g., spark:article:example-media.com/tech/...)",
          "required": true,
          "format": "spark-id"
        },
        "depth": {
          "type": "integer",
          "description": "Depth level requested. Must have sufficient token balance.",
          "required": false,
          "default": 1,
          "min": 0,
          "max": 3
        }
      },
      "output_schema": {
        "content": "spark:SpkDocument",
        "depth_served": "integer",
        "tokens_charged": "integer",
        "receipt_id": "string?"
      },
      "cost_per_invocation": {
        "tokens": "variable",
        "pricing_ref": "spark:article:*:depth_layers",
        "note": "Cost depends on requested depth level per content item"
      },
      "rate_limit": { "requests_per_minute": 60 },
      "idempotency": true,
      "estimated_completion_time": "PT2S"
    },

    {
      "@id": "spark:action:example-media.com/purchase-access",
      "@type": "spark:ActionIntent",
      "name": "Purchase Depth Access Token",
      "description": "Acquire a time-limited access token for vault-gated content at a specified depth level",
      "intent_category": "transaction",
      "intent_subcategory": "spark:intent:transaction:purchase",
      "access_level": "authenticated",
      "requires_user_consent": false,
      "reversible": false,
      "affects_external_parties": false,
      "http_method": "POST",
      "endpoint": "/spark/v2/vault/purchase",
      "input_schema": {
        "content_id": {
          "type": "string",
          "required": true,
          "format": "spark-id"
        },
        "depth_target": {
          "type": "integer",
          "required": true,
          "min": 1,
          "max": 3
        },
        "agent_wallet": {
          "type": "string",
          "required": true,
          "description": "Agent's Token Bank wallet address",
          "sensitive": false
        }
      },
      "output_schema": {
        "access_token": "string",
        "expires_at": "ISO8601",
        "tokens_charged": "integer",
        "receipt_id": "string"
      },
      "cost_per_invocation": {
        "tokens": "variable",
        "pricing_ref": "spark:article:*:depth_layers"
      },
      "idempotency": true,
      "estimated_completion_time": "PT3S",
      "on_success": "spark:state:content:depth-access-granted",
      "on_failure": "spark:state:unchanged"
    },

    {
      "@id": "spark:action:example-media.com/subscribe",
      "@type": "spark:ActionIntent",
      "name": "Subscribe User",
      "description": "Register a newsletter subscription on behalf of a user (requires user delegation)",
      "intent_category": "registration",
      "intent_subcategory": "spark:intent:registration:newsletter-signup",
      "access_level": "user_delegated",
      "requires_user_consent": true,
      "reversible": true,
      "affects_external_parties": false,
      "http_method": "POST",
      "endpoint": "/spark/v2/users/subscribe",
      "input_schema": {
        "plan_id": {
          "type": "string",
          "required": true,
          "enum": ["free", "reader-monthly", "researcher-annual"],
          "description": "Subscription plan identifier"
        },
        "user_consent_token": {
          "type": "string",
          "required": true,
          "description": "User consent token obtained via OAuth delegation flow",
          "sensitive": true
        }
      },
      "output_schema": {
        "subscription_id": "string",
        "active_from": "ISO8601",
        "plan": "string"
      },
      "cost_per_invocation": {
        "tokens": 5,
        "note": "Agent service fee for delegation"
      },
      "idempotency": false,
      "estimated_completion_time": "PT2S",
      "on_success": "spark:state:user:newsletter-subscribed",
      "on_failure": "spark:state:unchanged"
    },

    {
      "@id": "spark:action:example-media.com/report-error",
      "@type": "spark:ActionIntent",
      "name": "Report Content Error",
      "description": "Submit a factual error or outdated information report for editorial review",
      "intent_category": "notification",
      "intent_subcategory": "spark:intent:notification:report-error",
      "access_level": "authenticated",
      "requires_user_consent": false,
      "reversible": false,
      "affects_external_parties": false,
      "http_method": "POST",
      "endpoint": "/spark/v2/content/report",
      "input_schema": {
        "content_id": {
          "type": "string",
          "required": true,
          "format": "spark-id"
        },
        "error_type": {
          "type": "string",
          "required": true,
          "enum": ["factual_error", "outdated", "broken_link", "missing_citation", "other"]
        },
        "description": {
          "type": "string",
          "required": true,
          "max_length": 1000
        },
        "suggested_correction": {
          "type": "string",
          "required": false,
          "max_length": 2000
        }
      },
      "output_schema": {
        "report_id": "string",
        "status": "string",
        "estimated_review": "ISO8601"
      },
      "cost_per_invocation": { "tokens": 0 },
      "idempotency": false,
      "estimated_completion_time": "PT1S"
    }
  ],

  "flows": [
    {
      "@id": "spark:flow:example-media.com/research-access",
      "name": "Research Content Access Flow",
      "description": "Standard flow for agent to discover, evaluate, and access premium content",
      "steps": [
        {
          "step": 1,
          "action": "spark:action:example-media.com/search",
          "intent": "discover relevant content"
        },
        {
          "step": 2,
          "action": "spark:action:example-media.com/get-content",
          "intent": "retrieve public depth content and evaluate value"
        },
        {
          "step": 3,
          "action": "spark:action:example-media.com/purchase-access",
          "intent": "acquire access token for premium depth",
          "optional": true,
          "condition": "if_premium_content_required"
        },
        {
          "step": 4,
          "action": "spark:action:example-media.com/get-content",
          "intent": "retrieve full depth content with access token",
          "optional": true,
          "condition": "if_access_token_acquired"
        }
      ]
    }
  ],

  "integrity": {
    "hash_algorithm": "SHA-256",
    "content_hash": "b4c9d3e2f1a0987654321fedcba9876543210fedcba9876543210fedcba98765",
    "signature": "base64url_encoded_ed25519_signature_placeholder",
    "signing_key": "spark:key:example-media.com:primary-2026",
    "signed_at": "2026-05-01T00:05:00Z"
  }
}
```
