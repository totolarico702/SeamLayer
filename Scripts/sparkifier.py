#!/usr/bin/env python3
"""
Sparkifier v0.1 — SparkLayer Protocol v2
Converts HTML or Markdown content into .spsk / .spk / .spki files.

Usage:
    python sparkifier.py --input article.html --domain example.com --output ./spark_out
    python sparkifier.py --input article.md   --domain example.com --output ./spark_out
    python sparkifier.py --input article.html --config site.json  --output ./spark_out

Generates:
    spark.spsk          → Site manifest (served at /.well-known/spark.spsk)
    <slug>.spk          → Knowledge document
    actions.spki        → Action interface
    <slug>.html         → Depth-0 annotated HTML (replaces original)
    keypair.json        → Ed25519 keypair (keep private key secret!)
"""

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from base64 import b64encode, urlsafe_b64encode
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
    import markdown as md_parser
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install beautifulsoup4 markdown cryptography")
    sys.exit(1)


# ─────────────────────────────────────────────
# KEYPAIR MANAGEMENT
# ─────────────────────────────────────────────

def generate_keypair(domain: str) -> dict:
    """Generate Ed25519 keypair for a domain."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # Multibase encode (base58btc with 'z' prefix)
    public_multibase = 'z' + _base58_encode(public_bytes)

    key_id = f"spark:key:{domain}:primary-{datetime.now().year}"

    return {
        "key_id": key_id,
        "public_multibase": public_multibase,
        "private_bytes_b64": b64encode(private_bytes).decode(),
        "public_bytes_b64": b64encode(public_bytes).decode(),
    }


def load_or_generate_keypair(output_dir: Path, domain: str) -> dict:
    """Load existing keypair or generate new one."""
    keypair_file = output_dir / "keypair.json"
    if keypair_file.exists():
        with open(keypair_file) as f:
            print(f"  [key] Loaded existing keypair from {keypair_file}")
            return json.load(f)

    keypair = generate_keypair(domain)
    with open(keypair_file, 'w') as f:
        json.dump(keypair, f, indent=2)
    print(f"  [key] Generated new Ed25519 keypair → {keypair_file}")
    print(f"  [key] ⚠️  Keep keypair.json secret — never commit to git")
    return keypair


def sign_content(content_dict: dict, keypair: dict) -> tuple[str, str]:
    """
    Sign a dict's canonical JSON.
    Returns (content_hash_hex, signature_b64url).
    """
    canonical = json.dumps(content_dict, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    content_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    private_bytes = __import__('base64').b64decode(keypair['private_bytes_b64'])
    private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
    signature_bytes = private_key.sign(content_hash.encode('utf-8'))
    signature_b64url = urlsafe_b64encode(signature_bytes).decode().rstrip('=')

    return content_hash, signature_b64url


# ─────────────────────────────────────────────
# CONTENT PARSING
# ─────────────────────────────────────────────

def parse_html(html_content: str) -> dict:
    """Extract structured content from HTML."""
    soup = BeautifulSoup(html_content, 'lxml')

    # Remove noise
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header',
                               'aside', 'noscript', 'iframe', 'form']):
        tag.decompose()

    title = ''
    if soup.find('h1'):
        title = soup.find('h1').get_text(strip=True)
    elif soup.find('title'):
        title = soup.find('title').get_text(strip=True)

    # Meta extraction
    author = _extract_meta(soup, ['author', 'article:author', 'twitter:creator'])
    date_published = _extract_meta(soup, ['article:published_time', 'date', 'pubdate'])
    description = _extract_meta(soup, ['description', 'og:description', 'twitter:description'])
    keywords_str = _extract_meta(soup, ['keywords', 'article:tag'])
    keywords = [k.strip() for k in keywords_str.split(',')] if keywords_str else []

    # Structured content extraction
    main = soup.find('main') or soup.find('article') or soup.find('body')
    sections = []
    stats = []
    entities = []

    if main:
        # Extract paragraphs and classify them
        paras = main.find_all(['p', 'h2', 'h3', 'h4', 'li', 'blockquote', 'pre', 'code'])
        for i, para in enumerate(paras):
            text = para.get_text(strip=True)
            if len(text) < 20:
                continue

            section_type = _classify_section(text, para.name)
            section = {
                "@type": "spark:Section",
                "spark:sectionType": section_type,
                "text": text,
                "trainable": section_type not in ['Opinion', 'Warning'],
            }
            sections.append(section)

            # Extract inline statistics
            found_stats = _extract_statistics(text)
            stats.extend(found_stats)

        # Extract entities from links and strong tags
        for link in main.find_all('a', href=True):
            name = link.get_text(strip=True)
            if name and len(name) > 2:
                entities.append({
                    "name": name,
                    "type": "Concept"
                })

    return {
        "title": title,
        "author": author,
        "date_published": date_published,
        "description": description,
        "keywords": keywords[:20],
        "sections": sections,
        "statistics": stats[:10],
        "entities": _deduplicate_entities(entities)[:15],
    }


def parse_markdown(md_content: str) -> dict:
    """Extract structured content from Markdown."""
    html = md_parser.markdown(md_content, extensions=['meta', 'tables', 'fenced_code'])
    result = parse_html(html)

    # Also extract frontmatter if present
    if md_content.startswith('---'):
        frontmatter = _parse_frontmatter(md_content)
        if frontmatter.get('title'):
            result['title'] = frontmatter['title']
        if frontmatter.get('author'):
            result['author'] = frontmatter['author']
        if frontmatter.get('date'):
            result['date_published'] = frontmatter['date']
        if frontmatter.get('tags'):
            tags = frontmatter['tags']
            result['keywords'] = tags if isinstance(tags, list) else [t.strip() for t in tags.split(',')]
        if frontmatter.get('description'):
            result['description'] = frontmatter['description']

    return result


# ─────────────────────────────────────────────
# DEPTH PARTITIONING
# ─────────────────────────────────────────────

def partition_into_depths(parsed: dict, depth_config: dict) -> dict:
    """
    Partition content into depth layers.
    
    Default strategy:
    - depth 0: summary + entities only (public, HTML derivative)
    - depth 1: first 40% of sections (public, free)
    - depth 2: next 40% of sections + statistics (token_required)
    - depth 3: remaining sections + full dataset descriptor (vault_required)
    """
    sections = parsed.get('sections', [])
    stats = parsed.get('statistics', [])
    entities = parsed.get('entities', [])
    total = len(sections)

    cut1 = max(1, int(total * 0.40))
    cut2 = max(cut1 + 1, int(total * 0.80))

    depth_0_cost = depth_config.get('depth_0_cost', 0)
    depth_1_cost = depth_config.get('depth_1_cost', 0)
    depth_2_cost = depth_config.get('depth_2_cost', 15)
    depth_3_cost = depth_config.get('depth_3_cost', 80)

    layers = {
        "0": {
            "access": "public",
            "token_cost": depth_0_cost,
            "usage": ["display"],
            "content": {
                "summary": parsed.get('description') or _generate_summary(sections[:2]),
                "entities": entities[:8],
            }
        },
        "1": {
            "access": "public",
            "token_cost": depth_1_cost,
            "usage": ["display", "rag"],
            "content": {
                "sections": sections[:cut1],
                "entities": entities,
            }
        }
    }

    if sections[cut1:cut2] or stats:
        layers["2"] = {
            "access": "token_required",
            "token_cost": depth_2_cost,
            "usage": ["display", "rag", "train"],
            "content": {
                "sections": sections[cut1:cut2],
                "statistics": stats,
            }
        }

    if sections[cut2:]:
        layers["3"] = {
            "access": "vault_required",
            "token_cost": depth_3_cost,
            "usage": ["train", "finetune"],
            "vault_ref": f"vault://__DOMAIN__/spark/vault/__SLUG__",
            "content_descriptor": {
                "@type": "spark:Document",
                "format": "JSON",
            }
        }

    return layers


# ─────────────────────────────────────────────
# FILE GENERATORS
# ─────────────────────────────────────────────

def generate_spsk(domain: str, keypair: dict, config: dict, output_dir: Path) -> dict:
    """Generate .spsk manifest."""
    spsk = {
        "@context": "https://sparkprotocol.io/context/spsk-v2.jsonld",
        "@id": f"spark:site:{domain}",
        "@type": "SparkSiteKey",
        "name": config.get('publisher_name', domain),
        "spark_protocol_version": "2.0",
        "publisher": {
            "name": config.get('publisher_name', domain),
            "url": f"https://{domain}/about",
            "id": f"spark:org:{_slugify(config.get('publisher_name', domain))}",
            "contact": config.get('contact', f"spark@{domain}"),
        },
        "public_keys": [
            {
                "id": keypair['key_id'],
                "type": "Ed25519VerificationKey2020",
                "publicKeyMultibase": keypair['public_multibase'],
                "status": "active"
            }
        ],
        "default_depth_spark": config.get('default_depth', 1),
        "max_depth_spark": config.get('max_depth', 3),
        "entry_points": {
            "content": {
                "url": f"https://{domain}/spark/index.spk",
                "description": "Content knowledge graph index",
                "type": "spk_index",
                "access_level": "public"
            },
            "actions": {
                "url": f"https://{domain}/spark/actions.spki",
                "description": "Available agent action interfaces",
                "type": "spki_interface",
                "access_level": "public"
            }
        },
        "compliance_required": config.get('compliance_required', 'level_2'),
        "honeypot_enabled": config.get('honeypot_enabled', True),
        "vault_endpoint": f"https://vault.{domain}/spark/v2",
        "token_bank_endpoint": "https://tokenbank.sparkprotocol.io/v2",
        "deployment_mode": config.get('deployment_mode', 'open'),
        "rate_limits": {
            "requests_per_minute_per_agent": 60,
            "burst": 15,
            "requests_per_day_per_agent": 10000,
        },
        "supported_usage": config.get('supported_usage', ['display', 'rag']),
        "last_updated": _now_iso(),
        "ttl": 3600,
    }

    out_path = output_dir / "spark.spsk"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(spsk, f, indent=2, ensure_ascii=False)
    print(f"  [spsk] → {out_path}")
    return spsk


def generate_spk(parsed: dict, depth_layers: dict, domain: str,
                 slug: str, keypair: dict, config: dict, output_dir: Path) -> dict:
    """Generate .spk knowledge document."""
    org_id = f"spark:org:{_slugify(config.get('publisher_name', domain))}"

    author_obj = {"@type": "Person", "name": "Unknown Author"}
    if parsed.get('author'):
        author_obj["name"] = parsed['author']

    # Replace placeholder domain/slug in vault refs
    for depth_key, layer in depth_layers.items():
        if 'vault_ref' in layer:
            layer['vault_ref'] = layer['vault_ref'].replace('__DOMAIN__', domain).replace('__SLUG__', slug)

    content_to_sign = depth_layers
    content_hash, signature = sign_content(content_to_sign, keypair)

    spk = {
        "@context": [
            "https://schema.org/",
            "https://sparkprotocol.io/context/spk-v2.jsonld"
        ],
        "@id": f"spark:article:{domain}/{slug}",
        "@type": "Article",
        "headline": parsed.get('title', 'Untitled'),
        "author": author_obj,
        "publisher": {
            "@id": org_id,
            "name": config.get('publisher_name', domain),
        },
        "datePublished": parsed.get('date_published') or _now_iso(),
        "dateModified": _now_iso(),
        "version": "v1.0",
        "license": config.get('license', 'proprietary'),
        "language": config.get('language', 'en'),
        "keywords": parsed.get('keywords', []),
        "depth_layers": depth_layers,
        "provenance": {
            "origin": f"https://{domain}/{slug}",
            "created_by": "spark:agent:sparkifier-v0.1",
            "editorial_review": False,
            "fact_checked": False,
            "last_verified": _now_iso(),
            "abysse_data": False,
        },
        "integrity": {
            "hash_algorithm": "SHA-256",
            "content_hash": content_hash,
            "signature": signature,
            "signing_key": keypair['key_id'],
            "signed_at": _now_iso(),
        }
    }

    out_path = output_dir / f"{slug}.spk"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(spk, f, indent=2, ensure_ascii=False)
    print(f"  [spk]  → {out_path}")
    return spk


def generate_spki(domain: str, slug: str, keypair: dict, config: dict, output_dir: Path) -> dict:
    """Generate .spki action interface with default actions."""
    org_id = f"spark:org:{_slugify(config.get('publisher_name', domain))}"

    actions = [
        {
            "@id": f"spark:action:{domain}/search",
            "@type": "spark:ActionIntent",
            "name": "Search Content",
            "description": "Semantic search across knowledge graph",
            "intent_category": "query",
            "intent_subcategory": "spark:intent:query:search",
            "access_level": "public",
            "requires_user_consent": False,
            "reversible": True,
            "affects_external_parties": False,
            "http_method": "GET",
            "endpoint": f"https://api.{domain}/spark/v2/search",
            "input_schema": {
                "q": {"type": "string", "required": True, "max_length": 500,
                      "description": "Search query"},
                "depth_max": {"type": "integer", "required": False, "default": 1,
                              "min": 0, "max": 3, "description": "Max depth level"},
                "limit": {"type": "integer", "required": False, "default": 10,
                          "min": 1, "max": 100, "description": "Max results"},
            },
            "output_schema": {
                "results": "array<spark:KnowledgeRef>",
                "total": "integer",
                "next_cursor": "string?",
            },
            "cost_per_invocation": {"tokens": 0},
            "rate_limit": {"requests_per_minute": 30},
            "idempotency": True,
            "estimated_completion_time": "PT1S",
        },
        {
            "@id": f"spark:action:{domain}/get-content",
            "@type": "spark:ActionIntent",
            "name": "Get Content",
            "description": "Retrieve .spk document by spark: identifier at specified depth",
            "intent_category": "query",
            "intent_subcategory": "spark:intent:query:get-detail",
            "access_level": "authenticated",
            "requires_user_consent": False,
            "reversible": True,
            "affects_external_parties": False,
            "http_method": "GET",
            "endpoint": f"https://api.{domain}/spark/v2/content/{{content_id}}",
            "input_schema": {
                "content_id": {"type": "string", "required": True, "format": "spark-id",
                               "description": "spark: identifier"},
                "depth": {"type": "integer", "required": False, "default": 1,
                          "min": 0, "max": 3, "description": "Depth level requested"},
            },
            "output_schema": {
                "content": "spark:SpkDocument",
                "depth_served": "integer",
                "tokens_charged": "integer",
                "receipt_id": "string?",
            },
            "cost_per_invocation": {
                "tokens": "variable",
                "pricing_ref": "spark:article:*:depth_layers",
            },
            "idempotency": True,
            "estimated_completion_time": "PT2S",
        },
        {
            "@id": f"spark:action:{domain}/purchase-access",
            "@type": "spark:ActionIntent",
            "name": "Purchase Depth Access",
            "description": "Acquire time-limited vault access token for depth-gated content",
            "intent_category": "transaction",
            "intent_subcategory": "spark:intent:transaction:purchase",
            "access_level": "authenticated",
            "requires_user_consent": False,
            "reversible": False,
            "affects_external_parties": False,
            "http_method": "POST",
            "endpoint": f"https://vault.{domain}/spark/v2/purchase",
            "input_schema": {
                "content_id": {"type": "string", "required": True, "format": "spark-id"},
                "depth_target": {"type": "integer", "required": True, "min": 1, "max": 3},
                "agent_wallet": {"type": "string", "required": True,
                                 "description": "Token Bank wallet address"},
            },
            "output_schema": {
                "access_token": "string",
                "expires_at": "ISO8601",
                "tokens_charged": "integer",
                "receipt_id": "string",
            },
            "cost_per_invocation": {
                "tokens": "variable",
                "pricing_ref": "spark:article:*:depth_layers",
            },
            "idempotency": True,
            "estimated_completion_time": "PT3S",
            "on_success": "spark:state:content:depth-access-granted",
            "on_failure": "spark:state:unchanged",
        },
        {
            "@id": f"spark:action:{domain}/report-error",
            "@type": "spark:ActionIntent",
            "name": "Report Content Error",
            "description": "Submit factual error or outdated information for editorial review",
            "intent_category": "notification",
            "intent_subcategory": "spark:intent:notification:report-error",
            "access_level": "authenticated",
            "requires_user_consent": False,
            "reversible": False,
            "affects_external_parties": False,
            "http_method": "POST",
            "endpoint": f"https://api.{domain}/spark/v2/content/report",
            "input_schema": {
                "content_id": {"type": "string", "required": True, "format": "spark-id"},
                "error_type": {
                    "type": "string", "required": True,
                    "enum": ["factual_error", "outdated", "broken_link", "missing_citation", "other"],
                },
                "description": {"type": "string", "required": True, "max_length": 1000},
                "suggested_correction": {"type": "string", "required": False, "max_length": 2000},
            },
            "output_schema": {
                "report_id": "string",
                "status": "string",
                "estimated_review": "ISO8601",
            },
            "cost_per_invocation": {"tokens": 0},
            "idempotency": False,
            "estimated_completion_time": "PT1S",
        }
    ]

    flows = [
        {
            "@id": f"spark:flow:{domain}/research-access",
            "name": "Research Content Access Flow",
            "description": "Standard flow: discover → evaluate → purchase → consume",
            "steps": [
                {"step": 1, "action": f"spark:action:{domain}/search",
                 "intent": "discover relevant content"},
                {"step": 2, "action": f"spark:action:{domain}/get-content",
                 "intent": "retrieve public content and evaluate value"},
                {"step": 3, "action": f"spark:action:{domain}/purchase-access",
                 "intent": "acquire vault access token",
                 "optional": True, "condition": "if_premium_depth_required"},
                {"step": 4, "action": f"spark:action:{domain}/get-content",
                 "intent": "retrieve full depth content",
                 "optional": True, "condition": "if_access_token_acquired"},
            ]
        }
    ]

    actions_to_sign = actions
    content_hash, signature = sign_content(actions_to_sign, keypair)

    spki = {
        "@context": "https://sparkprotocol.io/context/spki-v2.jsonld",
        "@id": f"spark:interface:{domain}",
        "@type": "SparkInterface",
        "publisher": {"@id": org_id, "name": config.get('publisher_name', domain)},
        "version": "1.0.0",
        "last_updated": _now_iso(),
        "base_url": f"https://api.{domain}",
        "global_rate_limits": {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst": 15,
            "per_agent_daily_limit": 10000,
        },
        "authentication": {
            "spark_agent_id": True,
            "jwt": True,
            "api_key": True,
        },
        "actions": actions,
        "flows": flows,
        "integrity": {
            "hash_algorithm": "SHA-256",
            "content_hash": content_hash,
            "signature": signature,
            "signing_key": keypair['key_id'],
            "signed_at": _now_iso(),
        }
    }

    out_path = output_dir / "actions.spki"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(spki, f, indent=2, ensure_ascii=False)
    print(f"  [spki] → {out_path}")
    return spki


def generate_html_bridge(parsed: dict, spk: dict, domain: str, slug: str, output_dir: Path):
    """Generate depth_0 annotated HTML from .spk content."""
    title = parsed.get('title', 'Untitled')
    summary = spk['depth_layers']['0']['content'].get('summary', '')
    entities = spk['depth_layers']['0']['content'].get('entities', [])
    content_id = spk['@id']
    depth_available = len(spk['depth_layers'])

    entity_spans = ' '.join([
        f'<span spark:type="Entity" spark:id="{e.get("@id", "")}">{e["name"]}</span>'
        for e in entities
    ])

    depth_parts = []
    for k, v in spk['depth_layers'].items():
        cost_str = f':{v["token_cost"]}' if v.get("token_cost", 0) > 0 else ""
        depth_parts.append(f'spark:depth-{k}="{v["access"]}{cost_str}"')
    depth_meta = ' '.join(depth_parts)

    html = f"""<!DOCTYPE html>
<html lang="{spk.get('language', 'en')}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{summary[:160]}">
  <!-- SparkLayer depth_0 derivative — auto-generated by Sparkifier v0.1 -->
  <!-- Do not edit manually — regenerate from .spk source -->
  <link rel="spark-protocol" href="/.well-known/spark.spsk">
</head>
<body>
<article
  data-spark-id="{content_id}"
  data-spark-version="{spk.get('version', 'v1.0')}"
  data-spark-depth-available="{depth_available}"
  data-spark-endpoint="/.well-known/spark.spsk"
  {depth_meta}>

  <meta spark:content-type="{spk['@type']}">
  <meta spark:license="{spk.get('license', 'proprietary')}">
  <meta spark:signing-key="{spk['integrity']['signing_key']}">

  <!-- depth_0 content only — humans and non-compliant crawlers see this -->
  <h1 spark:type="Headline">{title}</h1>

  <div spark:type="EntityList">
    {entity_spans}
  </div>

  <p spark:type="Summary">
    {summary}
  </p>

  <!-- Agent discovery hint -->
  <a href="/.well-known/spark.spsk"
     data-spark-discovery="true"
     style="font-size:0.8em;color:#666;"
     aria-label="SparkLayer agent access">
    [AI Agent? Access full structured data via SparkLayer Protocol v2]
  </a>

</article>
</body>
</html>"""

    out_path = output_dir / f"{slug}.html"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  [html] → {out_path}")


# ─────────────────────────────────────────────
# MANIFEST / SUMMARY
# ─────────────────────────────────────────────

def write_manifest(domain: str, slug: str, spsk: dict, spk: dict,
                   spki: dict, output_dir: Path):
    """Write a human-readable manifest of generated files."""
    manifest = {
        "generated_at": _now_iso(),
        "sparkifier_version": "0.1",
        "domain": domain,
        "files": {
            "spsk": {
                "path": "spark.spsk",
                "serve_at": "/.well-known/spark.spsk",
                "public": True,
            },
            "spk": {
                "path": f"{slug}.spk",
                "serve_at": f"/spark/{slug}.spk",
                "content_id": spk["@id"],
                "depth_layers": list(spk["depth_layers"].keys()),
                "public": True,
            },
            "spki": {
                "path": "actions.spki",
                "serve_at": "/spark/actions.spki",
                "actions": [a["@id"] for a in spki["actions"]],
                "public": True,
            },
            "html": {
                "path": f"{slug}.html",
                "note": "Depth_0 derivative — replaces original HTML for this content",
                "public": True,
            },
            "keypair": {
                "path": "keypair.json",
                "public": False,
                "warning": "NEVER commit to git — contains private signing key",
            }
        },
        "depth_summary": {
            depth: {
                "access": layer["access"],
                "token_cost": layer.get("token_cost", 0),
                "usage": layer.get("usage", []),
                "sections": len(layer.get("content", {}).get("sections", [])),
            }
            for depth, layer in spk["depth_layers"].items()
        },
        "next_steps": [
            f"1. Serve spark.spsk at https://{domain}/.well-known/spark.spsk",
            f"2. Serve {slug}.spk at https://{domain}/spark/{slug}.spk",
            f"3. Serve actions.spki at https://{domain}/spark/actions.spki",
            f"4. Replace original HTML with {slug}.html",
            f"5. Deploy vault server at https://vault.{domain}/spark/v2",
            f"6. Register with SparkLayer Token Bank at https://tokenbank.sparkprotocol.io",
        ]
    }

    out_path = output_dir / "MANIFEST.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  [mfst] → {out_path}")
    return manifest


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _extract_meta(soup, names: list) -> str:
    for name in names:
        tag = (soup.find('meta', attrs={'name': name}) or
               soup.find('meta', attrs={'property': name}))
        if tag and tag.get('content'):
            return tag['content']
    return ''


def _classify_section(text: str, tag: str) -> str:
    text_lower = text.lower()
    if tag in ['h2', 'h3', 'h4']:
        return 'Context'
    if tag in ['pre', 'code']:
        return 'Code'
    if tag == 'blockquote':
        return 'Citation'
    if any(w in text_lower for w in ['%', 'percent', 'million', 'billion', 'average', 'median']):
        return 'Fact'
    if any(w in text_lower for w in ['believe', 'think', 'opinion', 'argue', 'suggest']):
        return 'Opinion'
    if any(w in text_lower for w in ['warning', 'caution', 'danger', 'risk', 'attention']):
        return 'Warning'
    if any(w in text_lower for w in ['step', 'first', 'then', 'finally', 'install', 'run', 'execute']):
        return 'Instruction'
    if any(w in text_lower for w in ['conclude', 'therefore', 'result', 'finding', 'summary']):
        return 'Conclusion'
    return 'Context'


def _extract_statistics(text: str) -> list:
    stats = []
    # Match patterns like "37%", "2.5 million", "$1.2B"
    patterns = [
        r'\b(\d+(?:\.\d+)?)\s*%',
        r'\b(\d+(?:\.\d+)?)\s*(million|billion|trillion)\b',
        r'\$(\d+(?:\.\d+)?)\s*([BMK]?)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            snippet = text[:200]
            stats.append({
                "@type": "spark:Statistic",
                "value": str(matches[0][0] if isinstance(matches[0], tuple) else matches[0]),
                "description": snippet,
                "confidence": 0.7,
            })
            break
    return stats


def _deduplicate_entities(entities: list) -> list:
    seen = set()
    result = []
    for e in entities:
        name = e.get('name', '').strip().lower()
        if name and name not in seen and len(name) > 2:
            seen.add(name)
            result.append({"name": e['name'].strip(), "type": e.get('type', 'Concept')})
    return result


def _generate_summary(sections: list) -> str:
    if not sections:
        return ''
    texts = [s.get('text', '') for s in sections[:2]]
    combined = ' '.join(texts)
    return combined[:300] + ('...' if len(combined) > 300 else '')


def _parse_frontmatter(content: str) -> dict:
    result = {}
    if not content.startswith('---'):
        return result
    end = content.find('---', 3)
    if end == -1:
        return result
    fm = content[3:end].strip()
    for line in fm.splitlines():
        if ':' in line:
            key, _, value = line.partition(':')
            result[key.strip()] = value.strip().strip('"\'')
    return result


def _slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text[:80]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# Base58 encoding for multibase
_BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def _base58_encode(data: bytes) -> str:
    count = 0
    for byte in data:
        if byte == 0:
            count += 1
        else:
            break
    num = int.from_bytes(data, 'big')
    result = []
    while num > 0:
        num, rem = divmod(num, 58)
        result.append(_BASE58_ALPHABET[rem])
    return '1' * count + ''.join(reversed(result))


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def sparkify(input_path: str, domain: str, output_dir: str,
             config_path: Optional[str] = None, depth_config: Optional[dict] = None):
    """Main entry point."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load config
    config = {}
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            config = json.load(f)
    if not config.get('publisher_name'):
        config['publisher_name'] = domain

    depth_cfg = depth_config or {}

    print(f"\n🔥 Sparkifier v0.1 — processing {input_path.name}")
    print(f"   Domain: {domain}")
    print(f"   Output: {output_dir}")
    print()

    # Parse input
    content = input_path.read_text(encoding='utf-8')
    suffix = input_path.suffix.lower()

    if suffix in ['.html', '.htm']:
        parsed = parse_html(content)
        print(f"  [parse] HTML — {len(parsed['sections'])} sections extracted")
    elif suffix in ['.md', '.markdown']:
        parsed = parse_markdown(content)
        print(f"  [parse] Markdown — {len(parsed['sections'])} sections extracted")
    else:
        print(f"  [error] Unsupported file type: {suffix}")
        sys.exit(1)

    # Generate slug from title or filename
    slug = _slugify(parsed.get('title') or input_path.stem)
    print(f"  [slug] {slug}")
    print()

    # Keypair
    keypair = load_or_generate_keypair(output_dir, domain)
    print()

    # Depth partitioning
    depth_layers = partition_into_depths(parsed, depth_cfg)
    print(f"  [depth] {len(depth_layers)} layers: {list(depth_layers.keys())}")
    print()

    # Generate files
    print("  Generating files:")
    spsk = generate_spsk(domain, keypair, config, output_dir)
    spk  = generate_spk(parsed, depth_layers, domain, slug, keypair, config, output_dir)
    spki = generate_spki(domain, slug, keypair, config, output_dir)
    generate_html_bridge(parsed, spk, domain, slug, output_dir)

    # Manifest
    print()
    manifest = write_manifest(domain, slug, spsk, spk, spki, output_dir)

    print()
    print("✅ Done. Summary:")
    for depth, info in manifest['depth_summary'].items():
        cost = f"  {info['token_cost']} tokens" if info['token_cost'] > 0 else "  free"
        print(f"   depth_{depth}: {info['access']}{cost} — {info['sections']} sections — usage: {info['usage']}")

    print()
    print("📋 Next steps:")
    for step in manifest['next_steps']:
        print(f"   {step}")

    return {"spsk": spsk, "spk": spk, "spki": spki, "manifest": manifest}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Sparkifier — Convert content to SparkLayer Protocol files'
    )
    parser.add_argument('--input',   required=True, help='Input HTML or Markdown file')
    parser.add_argument('--domain',  required=True, help='Publisher domain (e.g., example.com)')
    parser.add_argument('--output',  required=True, help='Output directory')
    parser.add_argument('--config',  help='Optional site config JSON file')
    parser.add_argument('--depth-2-cost', type=int, default=15,
                        help='SparkTokens cost for depth_2 (default: 15)')
    parser.add_argument('--depth-3-cost', type=int, default=80,
                        help='SparkTokens cost for depth_3 (default: 80)')

    args = parser.parse_args()
    depth_cfg = {
        'depth_2_cost': args.depth_2_cost,
        'depth_3_cost': args.depth_3_cost,
    }

    sparkify(
        input_path=args.input,
        domain=args.domain,
        output_dir=args.output,
        config_path=args.config,
        depth_config=depth_cfg,
    )
