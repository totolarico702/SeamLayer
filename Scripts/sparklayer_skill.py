"""
SparkLayer Agent Skill v0.1
============================
Client-side protocol implementation for autonomous agents.

Compatible with: LangGraph, CrewAI, AutoGen, Claude Code, custom agent loops.

Usage (standalone):
    from sparklayer_skill import SparkLayerSkill, TokenWallet

    wallet = TokenWallet(balance=500)
    spark  = SparkLayerSkill(wallet=wallet)

    # Discover
    site_key = spark.discover("example-media.com")

    # Assess what's available
    assessment = spark.assess(site_key, "spark:article:example-media.com/tech/ai-protocols")

    # Consume
    content = spark.consume(assessment.best_content_id, depth=1, wallet=wallet)

    # Act
    results = spark.search("example-media.com", "agent protocols 2026")

Usage (LangGraph tool):
    from sparklayer_skill import SparkLayerSkill, as_langgraph_tools
    tools = as_langgraph_tools(SparkLayerSkill(wallet=TokenWallet(balance=500)))

Usage (CrewAI tool):
    from sparklayer_skill import SparkLayerSkill, as_crewai_tools
    tools = as_crewai_tools(SparkLayerSkill(wallet=TokenWallet(balance=500)))
"""

import hashlib
import json
import logging
import time
from base64 import urlsafe_b64decode
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

try:
    import requests
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:
    raise ImportError(
        "Missing dependencies. Run:\n"
        "  pip install requests cryptography"
    )

logger = logging.getLogger("sparklayer")


# ─────────────────────────────────────────────
# TYPES & ENUMS
# ─────────────────────────────────────────────

class ComplianceLevel(Enum):
    LEVEL_0 = 0  # Non-compliant (should not use this skill)
    LEVEL_1 = 1  # Basic — reads .spsk/.spk, respects depth
    LEVEL_2 = 2  # Monetization — pays via token bank
    LEVEL_3 = 3  # Ethical — attribution, usage restrictions, transparency


class AccessLevel(Enum):
    PUBLIC          = "public"
    AUTHENTICATED   = "authenticated"
    USER_DELEGATED  = "user_delegated"
    PARTNER_API_KEY = "partner_api_key"
    PAID_SUBSCRIPTION = "paid_subscription"
    VAULT_ONLY      = "vault_only"


class SparkError(Exception):
    """Base error for SparkLayer protocol violations."""
    pass

class SparkNotEnabled(SparkError):
    """Domain does not serve a .spsk manifest."""
    pass

class SparkSignatureInvalid(SparkError):
    """Ed25519 signature verification failed — content may be tampered."""
    pass

class SparkHoneypotDetected(SparkError):
    """Abysse Data detected — content is honeypot, discarding."""
    pass

class SparkInsufficientTokens(SparkError):
    """Token balance insufficient for requested depth."""
    pass

class SparkComplianceRequired(SparkError):
    """Publisher requires higher compliance level."""
    pass

class SparkActionFailed(SparkError):
    """Action invocation failed."""
    pass


# ─────────────────────────────────────────────
# TOKEN WALLET
# ─────────────────────────────────────────────

@dataclass
class Transaction:
    timestamp: str
    content_id: str
    depth: int
    tokens_charged: int
    receipt_id: Optional[str]
    domain: str


@dataclass
class TokenWallet:
    """
    SparkLayer token wallet for an agent.
    In production, connects to SparkLayer Token Bank API.
    This implementation is local/mock for development.
    """
    balance: int
    agent_id: str = "spark:agent:unnamed"
    transactions: list = field(default_factory=list)

    def can_afford(self, cost: int) -> bool:
        return self.balance >= cost

    def debit(self, amount: int, content_id: str = "", depth: int = 0,
              receipt_id: Optional[str] = None, domain: str = "") -> Transaction:
        if amount > self.balance:
            raise SparkInsufficientTokens(
                f"Insufficient tokens: need {amount}, have {self.balance}"
            )
        self.balance -= amount
        tx = Transaction(
            timestamp=_now_iso(),
            content_id=content_id,
            depth=depth,
            tokens_charged=amount,
            receipt_id=receipt_id,
            domain=domain,
        )
        self.transactions.append(tx)
        logger.info(f"[wallet] debit {amount} tokens → balance {self.balance} | {content_id}")
        return tx

    def credit(self, amount: int):
        self.balance += amount
        logger.info(f"[wallet] credit {amount} tokens → balance {self.balance}")

    def statement(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "current_balance": self.balance,
            "total_spent": sum(t.tokens_charged for t in self.transactions),
            "transaction_count": len(self.transactions),
            "transactions": [
                {
                    "timestamp": t.timestamp,
                    "domain": t.domain,
                    "content_id": t.content_id,
                    "depth": t.depth,
                    "tokens": t.tokens_charged,
                    "receipt_id": t.receipt_id,
                }
                for t in self.transactions[-20:]  # last 20
            ]
        }


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class SparkSiteKey:
    """Parsed .spsk manifest."""
    domain: str
    raw: dict
    public_keys: dict  # key_id → public_key_bytes

    @property
    def default_depth(self) -> int:
        return self.raw.get("default_depth_spark", 1)

    @property
    def max_depth(self) -> int:
        return self.raw.get("max_depth_spark", 3)

    @property
    def compliance_required(self) -> int:
        level_str = self.raw.get("compliance_required", "level_1")
        return int(level_str.split("_")[-1])

    @property
    def vault_endpoint(self) -> Optional[str]:
        return self.raw.get("vault_endpoint")

    @property
    def honeypot_enabled(self) -> bool:
        return self.raw.get("honeypot_enabled", True)

    @property
    def entry_points(self) -> dict:
        return self.raw.get("entry_points", {})


@dataclass
class DepthAssessment:
    """Cost/value assessment for a single depth level."""
    depth: int
    access: str
    token_cost: int
    usage: list
    sections_count: int
    has_statistics: bool
    is_vault: bool


@dataclass
class ContentAssessment:
    """Full assessment of a content resource before access."""
    content_id: str
    domain: str
    available_depths: list[DepthAssessment]
    recommended_depth: int
    total_cost_to_recommended: int

    @property
    def best_free_depth(self) -> int:
        free = [d for d in self.available_depths if d.token_cost == 0]
        return max((d.depth for d in free), default=0)

    @property
    def best_content_id(self) -> str:
        return self.content_id


@dataclass
class SparkContent:
    """Retrieved and verified content from a .spk document."""
    content_id: str
    domain: str
    depth_served: int
    headline: str
    sections: list[dict]
    statistics: list[dict]
    entities: list[dict]
    summary: str
    metadata: dict
    provenance: dict
    tokens_charged: int
    receipt_id: Optional[str]
    raw_spk: dict

    def to_text(self) -> str:
        """Flatten content to plain text for LLM consumption."""
        parts = [self.headline, ""]
        if self.summary:
            parts.append(self.summary)
            parts.append("")
        for section in self.sections:
            section_type = section.get("spark:sectionType", "")
            text = section.get("text", "")
            if text:
                if section_type in ["Warning", "Opinion"]:
                    parts.append(f"[{section_type}] {text}")
                else:
                    parts.append(text)
        return "\n".join(parts)

    def to_context_block(self) -> str:
        """Format for injection into agent context window."""
        lines = [
            f"[SparkLayer Content]",
            f"Source: {self.content_id}",
            f"Domain: {self.domain}",
            f"Depth: {self.depth_served}",
            f"Headline: {self.headline}",
            f"Published: {self.metadata.get('datePublished', 'unknown')}",
            f"License: {self.metadata.get('license', 'unknown')}",
            f"Provenance verified: {bool(self.provenance)}",
            f"",
        ]
        if self.summary:
            lines += [f"Summary: {self.summary}", ""]
        for section in self.sections:
            text = section.get("text", "")
            stype = section.get("spark:sectionType", "")
            if text:
                prefix = f"[{stype}] " if stype and stype not in ["Context"] else ""
                lines.append(f"{prefix}{text}")
        if self.statistics:
            lines.append("")
            lines.append("Key Statistics:")
            for stat in self.statistics:
                val = stat.get("value", "")
                desc = stat.get("description", "")
                conf = stat.get("confidence", "")
                lines.append(f"  • {val} — {desc} (confidence: {conf})")
        return "\n".join(lines)


@dataclass
class ActionResult:
    """Result of invoking a .spki action."""
    action_id: str
    success: bool
    status_code: int
    data: dict
    tokens_charged: int
    receipt_id: Optional[str]
    error: Optional[str] = None


@dataclass
class SearchResult:
    """Single result from search action."""
    content_id: str
    headline: str
    summary: str
    domain: str
    depth_available: int
    date_published: Optional[str]
    relevance_score: Optional[float]


# ─────────────────────────────────────────────
# CORE SKILL
# ─────────────────────────────────────────────

class SparkLayerSkill:
    """
    SparkLayer Protocol v2 — Agent Skill.

    Six core operations:
        discover()   → fetch + validate .spsk
        assess()     → evaluate depth costs before committing
        consume()    → authenticate + pay + receive + verify content
        act()        → invoke .spki action endpoint
        search()     → semantic search across publisher knowledge graph
        verify()     → standalone signature verification

    All operations respect the compliance level of this agent instance.
    """

    SPSK_PATH = "/.well-known/spark.spsk"
    DEFAULT_TIMEOUT = 10
    AGENT_HEADER = "X-Spark-Agent-ID"
    COMPLIANCE_HEADER = "X-Spark-Compliance-Level"
    PROTOCOL_HEADER = "X-Spark-Protocol-Version"
    WALLET_HEADER = "X-Spark-Wallet"

    def __init__(
        self,
        wallet: TokenWallet,
        compliance_level: ComplianceLevel = ComplianceLevel.LEVEL_2,
        agent_id: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        verify_ssl: bool = True,
        cache_ttl: int = 3600,
    ):
        self.wallet = wallet
        self.compliance_level = compliance_level
        self.agent_id = agent_id or wallet.agent_id
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.cache_ttl = cache_ttl

        # In-memory cache for .spsk manifests
        self._spsk_cache: dict[str, tuple[SparkSiteKey, float]] = {}

        # Session for connection reuse
        self._session = requests.Session()
        self._session.headers.update({
            self.AGENT_HEADER: self.agent_id,
            self.COMPLIANCE_HEADER: str(self.compliance_level.value),
            self.PROTOCOL_HEADER: "2.0",
            self.WALLET_HEADER: self.wallet.agent_id,
            "Accept": "application/json",
            "User-Agent": f"SparkLayer-Agent/0.1 ({self.agent_id})",
        })

    # ─── DISCOVER ──────────────────────────────

    def discover(self, domain: str) -> Optional[SparkSiteKey]:
        """
        Fetch and validate .spsk manifest from domain.

        Returns SparkSiteKey if domain is SparkLayer-enabled, None otherwise.
        Raises SparkComplianceRequired if agent compliance < publisher requirement.

        Caches results for cache_ttl seconds.
        """
        # Check cache
        if domain in self._spsk_cache:
            site_key, cached_at = self._spsk_cache[domain]
            if time.time() - cached_at < self.cache_ttl:
                logger.debug(f"[discover] cache hit for {domain}")
                return site_key

        url = f"https://{domain}{self.SPSK_PATH}"
        logger.info(f"[discover] fetching {url}")

        try:
            resp = self._session.get(url, timeout=self.timeout, verify=self.verify_ssl)
            if resp.status_code == 404:
                logger.info(f"[discover] {domain} is not SparkLayer-enabled (404)")
                return None
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            logger.warning(f"[discover] cannot reach {domain}")
            return None
        except requests.exceptions.Timeout:
            logger.warning(f"[discover] timeout reaching {domain}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"[discover] HTTP error for {domain}: {e}")
            return None

        try:
            raw = resp.json()
        except json.JSONDecodeError:
            logger.warning(f"[discover] invalid JSON from {domain}")
            return None

        # Basic schema validation
        required = ["@type", "spark_protocol_version", "public_keys", "entry_points"]
        if not all(k in raw for k in required):
            logger.warning(f"[discover] incomplete .spsk from {domain}")
            return None

        if raw.get("@type") != "SparkSiteKey":
            logger.warning(f"[discover] wrong @type in .spsk from {domain}")
            return None

        # Parse public keys
        public_keys = {}
        for key_obj in raw.get("public_keys", []):
            if key_obj.get("status") in ["revoked"]:
                continue
            key_id = key_obj.get("id")
            pub_multibase = key_obj.get("publicKeyMultibase", "")
            if pub_multibase.startswith("z"):
                try:
                    pub_bytes = _base58_decode(pub_multibase[1:])
                    pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
                    public_keys[key_id] = pub_key
                except Exception as e:
                    logger.warning(f"[discover] failed to parse key {key_id}: {e}")

        if not public_keys:
            logger.warning(f"[discover] no valid public keys in .spsk from {domain}")
            return None

        site_key = SparkSiteKey(domain=domain, raw=raw, public_keys=public_keys)

        # Compliance check
        required_level = site_key.compliance_required
        if self.compliance_level.value < required_level:
            raise SparkComplianceRequired(
                f"{domain} requires compliance level {required_level}, "
                f"agent is level {self.compliance_level.value}"
            )

        # Cache
        self._spsk_cache[domain] = (site_key, time.time())
        logger.info(
            f"[discover] ✅ {domain} — "
            f"depth 0-{site_key.max_depth}, "
            f"compliance required: level_{required_level}"
        )
        return site_key

    # ─── VERIFY ────────────────────────────────

    def verify(self, spk_or_spki: dict, site_key: SparkSiteKey) -> bool:
        """
        Verify Ed25519 signature on a .spk or .spki document.

        Returns True if valid. Raises SparkSignatureInvalid if tampered.
        Raises SparkHoneypotDetected if abysse_data flag is set.
        """
        # Honeypot check first
        if spk_or_spki.get("provenance", {}).get("abysse_data", False):
            raise SparkHoneypotDetected(
                "Abysse Data detected in response — this is honeypot content. "
                "Discarding and logging. Do NOT ingest."
            )

        integrity = spk_or_spki.get("integrity")
        if not integrity:
            logger.warning("[verify] no integrity block — treating as unverified")
            return False

        signing_key_id = integrity.get("signing_key")
        pub_key = site_key.public_keys.get(signing_key_id)
        if not pub_key:
            raise SparkSignatureInvalid(
                f"Signing key {signing_key_id} not found in .spsk public keys"
            )

        # Reconstruct content to sign
        # For .spk: sign depth_layers; for .spki: sign actions
        if "depth_layers" in spk_or_spki:
            content_to_hash = spk_or_spki["depth_layers"]
        elif "actions" in spk_or_spki:
            content_to_hash = spk_or_spki["actions"]
        else:
            logger.warning("[verify] unknown document type — cannot verify")
            return False

        canonical = json.dumps(
            content_to_hash, sort_keys=True, ensure_ascii=False, separators=(',', ':')
        )
        expected_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        stored_hash = integrity.get("content_hash", "")

        if expected_hash != stored_hash:
            raise SparkSignatureInvalid(
                f"Content hash mismatch — document may be tampered.\n"
                f"  Expected: {expected_hash[:16]}...\n"
                f"  Stored:   {stored_hash[:16]}..."
            )

        sig_b64url = integrity.get("signature", "")
        try:
            # Add padding
            sig_bytes = urlsafe_b64decode(sig_b64url + "==")
            pub_key.verify(sig_bytes, stored_hash.encode('utf-8'))
        except Exception:
            raise SparkSignatureInvalid(
                f"Ed25519 signature verification failed for key {signing_key_id}"
            )

        logger.info(f"[verify] ✅ signature valid — key {signing_key_id}")
        return True

    # ─── ASSESS ────────────────────────────────

    def assess(self, site_key: SparkSiteKey, content_id: str) -> ContentAssessment:
        """
        Evaluate available depth levels and costs for a content item.
        Fetches depth_0 of the .spk without charging tokens.
        Returns ContentAssessment for agent decision-making.
        """
        domain = site_key.domain
        spk_url = self._build_spk_url(site_key, content_id)

        if not spk_url:
            # Try to build URL from content_id
            slug = content_id.split("/", 3)[-1] if "/" in content_id else content_id
            spk_url = f"https://{domain}/spark/{slug}.spk"

        logger.info(f"[assess] {content_id} @ {spk_url}")

        try:
            resp = self._session.get(
                spk_url,
                params={"depth": 0},
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            resp.raise_for_status()
            raw_spk = resp.json()
        except Exception as e:
            logger.warning(f"[assess] failed to fetch {spk_url}: {e}")
            # Return minimal assessment if fetch fails
            return ContentAssessment(
                content_id=content_id,
                domain=domain,
                available_depths=[DepthAssessment(0, "public", 0, ["display"], 0, False, False)],
                recommended_depth=0,
                total_cost_to_recommended=0,
            )

        depth_layers = raw_spk.get("depth_layers", {})
        assessments = []

        for depth_str, layer in sorted(depth_layers.items(), key=lambda x: int(x[0])):
            depth = int(depth_str)
            content = layer.get("content", {})
            assessments.append(DepthAssessment(
                depth=depth,
                access=layer.get("access", "public"),
                token_cost=layer.get("token_cost", 0),
                usage=layer.get("usage", []),
                sections_count=len(content.get("sections", [])),
                has_statistics=bool(content.get("statistics")),
                is_vault="vault_ref" in layer,
            ))

        # Recommend best affordable depth
        recommended = 0
        cumulative_cost = 0
        for da in assessments:
            cumulative_cost += da.token_cost
            if self.wallet.can_afford(cumulative_cost) and not da.is_vault:
                recommended = da.depth
            elif da.is_vault and self.compliance_level.value >= 2:
                break

        total_cost = sum(
            da.token_cost for da in assessments if da.depth <= recommended
        )

        logger.info(
            f"[assess] {len(assessments)} depths available, "
            f"recommended depth_{recommended} (cost: {total_cost} tokens, "
            f"wallet: {self.wallet.balance})"
        )

        return ContentAssessment(
            content_id=content_id,
            domain=domain,
            available_depths=assessments,
            recommended_depth=recommended,
            total_cost_to_recommended=total_cost,
        )

    # ─── CONSUME ───────────────────────────────

    def consume(
        self,
        content_id: str,
        depth: int = 1,
        wallet: Optional[TokenWallet] = None,
        site_key: Optional[SparkSiteKey] = None,
        skip_verify: bool = False,
    ) -> SparkContent:
        """
        Full content access flow:
            1. Discover/load site_key
            2. Verify agent compliance
            3. Check token balance
            4. Fetch content at requested depth
            5. Verify Ed25519 signature
            6. Debit tokens
            7. Return structured content

        Raises:
            SparkNotEnabled — domain not SparkLayer-enabled
            SparkSignatureInvalid — content tampered
            SparkHoneypotDetected — abysse data served (non-compliant behavior)
            SparkInsufficientTokens — wallet balance too low
        """
        wallet = wallet or self.wallet
        domain = self._domain_from_id(content_id)

        # Discover if not provided
        if not site_key:
            site_key = self.discover(domain)
            if not site_key:
                raise SparkNotEnabled(f"{domain} is not SparkLayer-enabled")

        # Build URL
        spk_url = self._build_spk_url(site_key, content_id)
        if not spk_url:
            slug = content_id.split("/", 3)[-1] if "/" in content_id else content_id
            spk_url = f"https://{domain}/spark/{slug}.spk"

        logger.info(f"[consume] {content_id} depth_{depth} @ {spk_url}")

        # Fetch with depth parameter
        try:
            resp = self._session.get(
                spk_url,
                params={"depth": depth},
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            resp.raise_for_status()
            raw_spk = resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 402:
                raise SparkInsufficientTokens(
                    f"Payment required for depth_{depth} on {content_id}"
                )
            raise SparkError(f"Failed to fetch content: {e}")
        except Exception as e:
            raise SparkError(f"Network error fetching {content_id}: {e}")

        # Honeypot + signature verification
        if not skip_verify:
            self.verify(raw_spk, site_key)

        # Extract served depth
        depth_layers = raw_spk.get("depth_layers", {})
        depth_str = str(depth)
        served_depth = depth if depth_str in depth_layers else max(
            int(k) for k in depth_layers.keys()
        )

        # Calculate cost for served depth
        total_cost = sum(
            layer.get("token_cost", 0)
            for d_str, layer in depth_layers.items()
            if int(d_str) > 0 and int(d_str) <= served_depth
        )

        if total_cost > 0 and not wallet.can_afford(total_cost):
            raise SparkInsufficientTokens(
                f"Need {total_cost} tokens for depth_{served_depth}, "
                f"wallet has {wallet.balance}"
            )

        # Extract content from all served layers
        all_sections = []
        all_statistics = []
        all_entities = []
        summary = ""

        for d_str in sorted(depth_layers.keys(), key=int):
            if int(d_str) > served_depth:
                break
            layer = depth_layers[d_str]
            content = layer.get("content", {})
            if d_str == "0":
                summary = content.get("summary", "")
                all_entities.extend(content.get("entities", []))
            else:
                all_sections.extend(content.get("sections", []))
                all_statistics.extend(content.get("statistics", []))
                all_entities.extend(content.get("entities", []))

        # Debit wallet
        receipt_id = None
        if total_cost > 0:
            tx = wallet.debit(
                amount=total_cost,
                content_id=content_id,
                depth=served_depth,
                domain=domain,
            )
            receipt_id = f"rcpt_{int(time.time())}_{content_id[:20]}"

        logger.info(
            f"[consume] ✅ {content_id} depth_{served_depth} — "
            f"{len(all_sections)} sections, {len(all_statistics)} stats — "
            f"charged {total_cost} tokens"
        )

        return SparkContent(
            content_id=content_id,
            domain=domain,
            depth_served=served_depth,
            headline=raw_spk.get("headline", ""),
            sections=all_sections,
            statistics=all_statistics,
            entities=_deduplicate_entities(all_entities),
            summary=summary,
            metadata={
                "datePublished": raw_spk.get("datePublished"),
                "dateModified": raw_spk.get("dateModified"),
                "license": raw_spk.get("license"),
                "language": raw_spk.get("language"),
                "keywords": raw_spk.get("keywords", []),
                "version": raw_spk.get("version"),
            },
            provenance=raw_spk.get("provenance", {}),
            tokens_charged=total_cost,
            receipt_id=receipt_id,
            raw_spk=raw_spk,
        )

    # ─── SEARCH ────────────────────────────────

    def search(
        self,
        domain: str,
        query: str,
        depth_max: int = 1,
        limit: int = 10,
        type_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Semantic search across publisher knowledge graph via .spki search action.
        Returns list of SearchResult (no token cost for search).
        """
        site_key = self.discover(domain)
        if not site_key:
            raise SparkNotEnabled(f"{domain} is not SparkLayer-enabled")

        # Load .spki to find search endpoint
        spki = self._load_spki(site_key)
        search_action = self._find_action(spki, "spark:intent:query:search")

        if not search_action:
            logger.warning(f"[search] no search action in {domain} .spki")
            return []

        endpoint = search_action.get("endpoint", "")
        if not endpoint.startswith("http"):
            endpoint = f"https://{domain}{endpoint}"

        params = {"q": query, "depth_max": depth_max, "limit": limit}
        if type_filter:
            params["type_filter"] = type_filter

        logger.info(f"[search] '{query}' on {domain}")

        try:
            resp = self._session.get(
                endpoint, params=params,
                timeout=self.timeout, verify=self.verify_ssl
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"[search] failed: {e}")
            return []

        results = []
        for item in data.get("results", []):
            results.append(SearchResult(
                content_id=item.get("@id", item.get("id", "")),
                headline=item.get("headline", item.get("name", "")),
                summary=item.get("summary", item.get("description", "")),
                domain=domain,
                depth_available=item.get("depth_available", site_key.default_depth),
                date_published=item.get("datePublished"),
                relevance_score=item.get("score"),
            ))

        logger.info(f"[search] {len(results)} results for '{query}' on {domain}")
        return results

    # ─── ACT ───────────────────────────────────

    def act(
        self,
        domain: str,
        action_id: str,
        params: dict,
        wallet: Optional[TokenWallet] = None,
        user_consent_token: Optional[str] = None,
    ) -> ActionResult:
        """
        Invoke a .spki action endpoint.

        Handles:
        - Action discovery from .spki
        - Compliance and access level checks
        - User consent verification for delegated actions
        - Token payment if required
        - Request execution and response parsing
        """
        wallet = wallet or self.wallet
        site_key = self.discover(domain)
        if not site_key:
            raise SparkNotEnabled(f"{domain} is not SparkLayer-enabled")

        spki = self._load_spki(site_key)
        action = next(
            (a for a in spki.get("actions", []) if a.get("@id") == action_id),
            None
        )

        if not action:
            raise SparkActionFailed(f"Action {action_id} not found in {domain} .spki")

        # Consent check
        if action.get("requires_user_consent") and not user_consent_token:
            raise SparkActionFailed(
                f"Action {action_id} requires user consent token. "
                "Obtain user delegation before invoking."
            )

        # Access level check
        access_level = action.get("access_level", "public")
        if access_level in ["user_delegated", "partner_api_key", "paid_subscription"]:
            if self.compliance_level.value < 2:
                raise SparkComplianceRequired(
                    f"Action {action_id} requires compliance level 2+"
                )

        # Cost check
        cost_info = action.get("cost_per_invocation", {})
        cost = cost_info.get("tokens", 0)
        if isinstance(cost, str) and cost == "variable":
            cost = params.get("_estimated_cost", 0)

        if cost > 0 and not wallet.can_afford(cost):
            raise SparkInsufficientTokens(
                f"Action {action_id} costs {cost} tokens, wallet has {wallet.balance}"
            )

        # Build request
        endpoint = action.get("endpoint", "")
        if not endpoint.startswith("http"):
            endpoint = f"https://{domain}{endpoint}"
        endpoint = endpoint.replace("{content_id}", params.get("content_id", ""))

        method = action.get("http_method", "GET").upper()

        if user_consent_token:
            params = {**params, "user_consent_token": user_consent_token}

        logger.info(f"[act] {method} {action_id} @ {endpoint}")

        try:
            if method == "GET":
                resp = self._session.get(
                    endpoint, params=params,
                    timeout=self.timeout, verify=self.verify_ssl
                )
            else:
                resp = self._session.request(
                    method, endpoint, json=params,
                    timeout=self.timeout, verify=self.verify_ssl
                )
        except Exception as e:
            return ActionResult(
                action_id=action_id, success=False, status_code=0,
                data={}, tokens_charged=0, receipt_id=None,
                error=str(e)
            )

        success = resp.status_code < 400
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}

        receipt_id = data.get("receipt_id")

        if success and cost > 0:
            wallet.debit(amount=cost, content_id=action_id, domain=domain)

        logger.info(
            f"[act] {'✅' if success else '❌'} {action_id} → "
            f"status {resp.status_code}"
        )

        return ActionResult(
            action_id=action_id,
            success=success,
            status_code=resp.status_code,
            data=data,
            tokens_charged=cost if success else 0,
            receipt_id=receipt_id,
            error=None if success else data.get("error", resp.text[:200]),
        )

    # ─── INTERNAL HELPERS ──────────────────────

    def _build_spk_url(self, site_key: SparkSiteKey, content_id: str) -> Optional[str]:
        """Try to resolve content_id to a .spk URL via entry_points index."""
        for ep_name, ep in site_key.entry_points.items():
            if ep.get("type") == "spk_index":
                url = ep.get("url", "")
                if url.startswith("https://"):
                    # Replace index URL with content-specific URL
                    base = url.rsplit("/", 1)[0]
                    slug = content_id.split("/", 3)[-1] if "/" in content_id else content_id
                    return f"{base}/{slug}.spk"
        return None

    def _load_spki(self, site_key: SparkSiteKey) -> dict:
        """Load and verify .spki from site_key entry_points."""
        spki_url = None
        for ep_name, ep in site_key.entry_points.items():
            if ep.get("type") == "spki_interface":
                spki_url = ep.get("url")
                break

        if not spki_url:
            domain = site_key.domain
            spki_url = f"https://{domain}/spark/actions.spki"

        try:
            resp = self._session.get(
                spki_url, timeout=self.timeout, verify=self.verify_ssl
            )
            resp.raise_for_status()
            spki = resp.json()
            # Verify signature
            try:
                self.verify(spki, site_key)
            except SparkSignatureInvalid as e:
                logger.error(f"[spki] signature invalid: {e}")
                raise
            return spki
        except Exception as e:
            logger.warning(f"[spki] failed to load .spki: {e}")
            return {"actions": [], "flows": []}

    def _find_action(self, spki: dict, intent_subcategory: str) -> Optional[dict]:
        """Find action by intent subcategory."""
        for action in spki.get("actions", []):
            if action.get("intent_subcategory") == intent_subcategory:
                return action
        return None

    def _domain_from_id(self, content_id: str) -> str:
        """Extract domain from spark: identifier."""
        # spark:article:example.com/path → example.com
        parts = content_id.split(":")
        if len(parts) >= 3:
            domain_path = parts[2]
            return domain_path.split("/")[0]
        return content_id


# ─────────────────────────────────────────────
# FRAMEWORK INTEGRATIONS
# ─────────────────────────────────────────────

def as_langgraph_tools(skill: SparkLayerSkill) -> list:
    """
    Wrap SparkLayerSkill as LangGraph-compatible tool functions.
    Returns list of callables with __name__ and __doc__ attributes.
    """
    def spark_discover(domain: str) -> dict:
        """Discover if a domain is SparkLayer-enabled and get its manifest."""
        site_key = skill.discover(domain)
        if not site_key:
            return {"enabled": False, "domain": domain}
        return {
            "enabled": True,
            "domain": domain,
            "default_depth": site_key.default_depth,
            "max_depth": site_key.max_depth,
            "compliance_required": site_key.compliance_required,
            "entry_points": list(site_key.entry_points.keys()),
        }

    def spark_search(domain: str, query: str, depth_max: int = 1) -> list[dict]:
        """Search a SparkLayer-enabled domain's knowledge graph."""
        results = skill.search(domain, query, depth_max=depth_max)
        return [
            {
                "content_id": r.content_id,
                "headline": r.headline,
                "summary": r.summary,
                "depth_available": r.depth_available,
                "date_published": r.date_published,
            }
            for r in results
        ]

    def spark_consume(content_id: str, depth: int = 1) -> str:
        """
        Retrieve structured content from a SparkLayer resource.
        Returns formatted context block ready for LLM consumption.
        """
        try:
            content = skill.consume(content_id, depth=depth)
            return content.to_context_block()
        except SparkInsufficientTokens as e:
            return f"[SparkLayer] Insufficient tokens: {e}"
        except SparkHoneypotDetected:
            return "[SparkLayer] Content rejected: honeypot detected"
        except SparkSignatureInvalid as e:
            return f"[SparkLayer] Content rejected: signature invalid — {e}"
        except SparkError as e:
            return f"[SparkLayer] Error: {e}"

    def spark_wallet_balance() -> dict:
        """Check current SparkToken wallet balance and recent transactions."""
        return skill.wallet.statement()

    return [spark_discover, spark_search, spark_consume, spark_wallet_balance]


def as_crewai_tools(skill: SparkLayerSkill) -> list:
    """
    Wrap SparkLayerSkill as CrewAI-compatible Tool objects.
    Requires crewai to be installed.
    """
    try:
        from crewai_tools import tool as crewai_tool
    except ImportError:
        raise ImportError("crewai-tools not installed: pip install crewai-tools")

    @crewai_tool("SparkLayer Discover")
    def spark_discover(domain: str) -> str:
        """Check if a domain supports SparkLayer and get protocol info."""
        site_key = skill.discover(domain)
        if not site_key:
            return f"{domain} is not SparkLayer-enabled"
        return (
            f"{domain} is SparkLayer-enabled. "
            f"Default depth: {site_key.default_depth}, "
            f"Max depth: {site_key.max_depth}. "
            f"Entry points: {list(site_key.entry_points.keys())}"
        )

    @crewai_tool("SparkLayer Search")
    def spark_search(domain: str, query: str) -> str:
        """Search a SparkLayer domain's knowledge graph."""
        results = skill.search(domain, query)
        if not results:
            return f"No results found for '{query}' on {domain}"
        lines = [f"Found {len(results)} results for '{query}' on {domain}:"]
        for r in results[:5]:
            lines.append(f"  - {r.headline}: {r.summary[:100]}")
            lines.append(f"    ID: {r.content_id} (depth available: {r.depth_available})")
        return "\n".join(lines)

    @crewai_tool("SparkLayer Consume")
    def spark_consume(content_id: str, depth: int = 1) -> str:
        """Retrieve and read structured content from a SparkLayer resource."""
        try:
            content = skill.consume(content_id, depth=depth)
            return content.to_context_block()
        except SparkError as e:
            return f"SparkLayer error: {e}"

    return [spark_discover, spark_search, spark_consume]


# ─────────────────────────────────────────────
# OFFLINE / LOCAL FILE MODE
# ─────────────────────────────────────────────

class LocalSparkLayerSkill(SparkLayerSkill):
    """
    SparkLayer skill that reads from local files instead of HTTP.
    Useful for testing, development, and offline scenarios.
    """

    def __init__(self, local_dir: str, wallet: TokenWallet, **kwargs):
        super().__init__(wallet=wallet, verify_ssl=False, **kwargs)
        self.local_dir = local_dir
        self._local_files: dict[str, dict] = {}
        self._load_local_files()

    def _load_local_files(self):
        """Index all .spsk, .spk, .spki files in local_dir."""
        from pathlib import Path
        p = Path(self.local_dir)
        for f in p.glob("**/*.spsk"):
            with open(f) as fh:
                self._local_files[str(f.name)] = json.load(fh)
        for f in p.glob("**/*.spk"):
            with open(f) as fh:
                self._local_files[str(f.name)] = json.load(fh)
        for f in p.glob("**/*.spki"):
            with open(f) as fh:
                self._local_files[str(f.name)] = json.load(fh)
        logger.info(f"[local] loaded {len(self._local_files)} files from {self.local_dir}")

    def discover(self, domain: str) -> Optional[SparkSiteKey]:
        """Load .spsk from local directory."""
        spsk_data = self._local_files.get("spark.spsk")
        if not spsk_data:
            return None

        public_keys = {}
        for key_obj in spsk_data.get("public_keys", []):
            key_id = key_obj.get("id")
            pub_multibase = key_obj.get("publicKeyMultibase", "")
            if pub_multibase.startswith("z"):
                try:
                    pub_bytes = _base58_decode(pub_multibase[1:])
                    pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
                    public_keys[key_id] = pub_key
                except Exception:
                    pass

        return SparkSiteKey(domain=domain, raw=spsk_data, public_keys=public_keys)

    def consume(self, content_id: str, depth: int = 1,
                wallet=None, site_key=None, skip_verify: bool = False) -> SparkContent:
        """Load .spk from local directory."""
        wallet = wallet or self.wallet
        domain = self._domain_from_id(content_id)

        # Find matching .spk file
        spk_data = None
        for fname, data in self._local_files.items():
            if fname.endswith(".spk") and data.get("@id") == content_id:
                spk_data = data
                break

        if not spk_data:
            # Try any .spk file
            for fname, data in self._local_files.items():
                if fname.endswith(".spk"):
                    spk_data = data
                    break

        if not spk_data:
            raise SparkNotEnabled(f"No .spk file found for {content_id}")

        if not skip_verify and site_key:
            self.verify(spk_data, site_key)

        depth_layers = spk_data.get("depth_layers", {})
        all_sections, all_statistics, all_entities = [], [], []
        summary = ""

        for d_str in sorted(depth_layers.keys(), key=int):
            if int(d_str) > depth:
                break
            layer = depth_layers[d_str]
            content = layer.get("content", {})
            if d_str == "0":
                summary = content.get("summary", "")
                all_entities.extend(content.get("entities", []))
            else:
                all_sections.extend(content.get("sections", []))
                all_statistics.extend(content.get("statistics", []))

        total_cost = sum(
            layer.get("token_cost", 0)
            for d_str, layer in depth_layers.items()
            if 0 < int(d_str) <= depth
        )

        if total_cost > 0:
            wallet.debit(total_cost, content_id=content_id, depth=depth, domain=domain)

        return SparkContent(
            content_id=content_id,
            domain=domain,
            depth_served=depth,
            headline=spk_data.get("headline", ""),
            sections=all_sections,
            statistics=all_statistics,
            entities=_deduplicate_entities(all_entities),
            summary=summary,
            metadata={
                "datePublished": spk_data.get("datePublished"),
                "license": spk_data.get("license"),
                "language": spk_data.get("language"),
                "keywords": spk_data.get("keywords", []),
                "version": spk_data.get("version"),
            },
            provenance=spk_data.get("provenance", {}),
            tokens_charged=total_cost,
            receipt_id=None,
            raw_spk=spk_data,
        )


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

_BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
_BASE58_MAP = {c: i for i, c in enumerate(_BASE58_ALPHABET)}

def _base58_decode(s: str) -> bytes:
    num = 0
    for char in s:
        if char not in _BASE58_MAP:
            raise ValueError(f"Invalid base58 character: {char}")
        num = num * 58 + _BASE58_MAP[char]
    pad = len(s) - len(s.lstrip('1'))
    result = num.to_bytes((num.bit_length() + 7) // 8, 'big') if num else b''
    return b'\x00' * pad + result

def _deduplicate_entities(entities: list) -> list:
    seen = set()
    result = []
    for e in entities:
        name = e.get("name", "").strip()
        if name and name not in seen:
            seen.add(name)
            result.append(e)
    return result

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ─────────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(message)s'
    )

    local_dir = sys.argv[1] if len(sys.argv) > 1 else "./sparkifier/output"
    print(f"\n🤖 SparkLayer Agent Skill v0.1 — Local Test")
    print(f"   Reading files from: {local_dir}\n")

    # Create wallet with test balance
    wallet = TokenWallet(balance=200, agent_id="spark:agent:test-agent-001")
    print(f"   Wallet: {wallet.agent_id} — {wallet.balance} tokens\n")

    # Init local skill
    skill = LocalSparkLayerSkill(
        local_dir=local_dir,
        wallet=wallet,
        compliance_level=ComplianceLevel.LEVEL_2,
    )

    # Discover
    print("── DISCOVER ──────────────────────────")
    site_key = skill.discover("example-media.com")
    if site_key:
        print(f"  ✅ SparkLayer enabled")
        print(f"  Default depth: {site_key.default_depth}")
        print(f"  Max depth:     {site_key.max_depth}")
        print(f"  Keys:          {list(site_key.public_keys.keys())}")
    else:
        print("  ❌ Not SparkLayer-enabled")
        sys.exit(1)

    # Find available .spk
    from pathlib import Path
    spk_files = list(Path(local_dir).glob("*.spk"))
    if not spk_files:
        print("  No .spk files found")
        sys.exit(1)

    with open(spk_files[0]) as f:
        spk_data = json.load(f)
    content_id = spk_data.get("@id", "spark:article:example-media.com/test")
    print(f"\n── VERIFY ────────────────────────────")
    try:
        valid = skill.verify(spk_data, site_key)
        print(f"  ✅ Signature valid")
    except SparkSignatureInvalid as e:
        print(f"  ❌ Signature invalid: {e}")

    print(f"\n── CONSUME depth_1 (free) ────────────")
    content = skill.consume(content_id, depth=1, skip_verify=True)
    print(f"  Headline:  {content.headline}")
    print(f"  Sections:  {len(content.sections)}")
    print(f"  Summary:   {content.summary[:80]}...")
    print(f"  Cost:      {content.tokens_charged} tokens")
    print(f"  Wallet:    {wallet.balance} remaining")

    print(f"\n── CONSUME depth_2 (15 tokens) ───────")
    content2 = skill.consume(content_id, depth=2, skip_verify=True)
    print(f"  Sections:  {len(content2.sections)}")
    print(f"  Stats:     {len(content2.statistics)}")
    print(f"  Cost:      {content2.tokens_charged} tokens")
    print(f"  Wallet:    {wallet.balance} remaining")

    print(f"\n── CONTEXT BLOCK (for LLM) ───────────")
    block = content2.to_context_block()
    preview = block[:400].replace('\n', '\n  ')
    print(f"  {preview}...")

    print(f"\n── LANGGRAPH TOOLS ───────────────────")
    tools = as_langgraph_tools(skill)
    print(f"  {len(tools)} tools registered:")
    for t in tools:
        print(f"  - {t.__name__}: {t.__doc__[:60]}")

    print(f"\n── WALLET STATEMENT ──────────────────")
    stmt = wallet.statement()
    print(f"  Balance:     {stmt['current_balance']} tokens")
    print(f"  Total spent: {stmt['total_spent']} tokens")
    print(f"  Transactions:{stmt['transaction_count']}")

    print(f"\n✅ All tests passed.\n")
