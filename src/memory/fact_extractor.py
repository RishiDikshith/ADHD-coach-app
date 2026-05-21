"""
Fact Extractor
==============
Extracts structured facts from natural language conversations.
Detects preferences, behaviors, life events, goals, and struggles.
Stores them in the database for long-term personalization.

Key capabilities:
- Pattern-based fact extraction (no LLM needed for common patterns)
- Confidence scoring for extracted facts
- Deduplication and update of existing facts
- Category classification
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ==================== Extraction Patterns ====================

# Fact extraction patterns organized by category and type
FACT_PATTERNS = {
    "preferences": {
        "patterns": [
            (r"(?:my\s+)?favorite\s+(\w+)\s+is\s+(\w+)", 1.0),
            (r"(?:i\s+)?(?:love|like|enjoy)\s+(\w+(?:\s+\w+)?)(?:\s+(?:a\s+)?lot)?", 0.7),
            (r"(?:i\s+)?(?:prefer|rather)\s+(\w+(?:\s+\w+)?)\s+(?:over|to|than)\s+(\w+(?:\s+\w+)?)", 0.8),
            (r"(?:i\s+)?(?:hate|dislike|can't\s+stand)\s+(\w+(?:\s+\w+)?)", 0.6),
            (r"i'm\s+(?:really\s+)?(?:into|interested\sin)\s+(\w+(?:\s+\w+)?)", 0.8),
        ],
        "key_extractors": [
            (r"favorite\s+(\w+)", lambda m: f"favorite_{m.group(1).lower()}"),
        ]
    },
    "habits": {
        "patterns": [
            (r"(?:i\s+)?(?:usually|always|often|typically|normally)\s+(\w+\s+\w+(?:\s+\w+)?)", 0.7),
            (r"(?:i\s+)?(?:never|rarely|hardly\s+ever)\s+(\w+\s+\w+(?:\s+\w+)?)", 0.6),
            (r"(?:every|each)\s+(?:morning|day|night|evening|afternoon)\s+(?:i\s+)?(\w+\s+\w+(?:\s+\w+)?)", 0.8),
            (r"(?:my\s+)?(?:routine|habit)\s+(?:is|includes)\s+(\w+(?:\s+\w+)?)", 0.8),
        ],
        "key_extractors": []
    },
    "sleep": {
        "patterns": [
            (r"(?:i\s+)?(?:sleep|slept)\s+(?:for\s+)?(\d+)\s*(?:-|\sto\s)?\s*(\d+)?\s*hours?", 0.9),
            (r"(?:i\s+)?go\s+to\s+bed\s+(?:at\s+)?(\d+\s*(?:am|pm)?)", 0.8),
            (r"(?:i\s+)?wake\s+up\s+(?:at\s+)?(\d+\s*(?:am|pm)?)", 0.8),
            (r"(?:can't|cannot|couldn't)\s+sleep", 0.7),
            (r"(?:insomnia|sleep\s+issues|bad\s+sleep)", 0.8),
        ],
        "key_extractors": []
    },
    "focus_work": {
        "patterns": [
            (r"(?:i\s+)?(?:work|study|code)\s+(?:best|better|well)\s+(?:in|at|during)\s+(?:the\s+)?(morning|afternoon|evening|night)", 0.9),
            (r"(?:i\s+)?(?:can't|cannot|struggle\s+to)\s+(?:focus|concentrate|pay\s+attention)", 0.8),
            (r"(?:i\s+)?get\s+(?:easily\s+)?distracted\s+(?:by|when)\s+(\w+(?:\s+\w+)?)", 0.7),
            (r"(?:hyperfocus|hyper\s*focus)(?:\s+on)?\s+(\w+(?:\s+\w+)?)", 0.8),
            (r"(?:i\s+)?(?:work|study)\s+(?:from\s+)?(home|office|cafe|library)", 0.6),
        ],
        "key_extractors": []
    },
    "health": {
        "patterns": [
            (r"(?:i\s+)?(?:take|on)\s+(\w+(?:\s+\w+)?)\s*(?:medication|medicine|pills|supplements)", 0.8),
            (r"(?:diagnosed\s+with|have)\s+(ADHD|anxiety|depression|OCD|PTSD|bipolar)", 0.9),
            (r"(?:i\s+)?(?:exercise|work\s*out|run|walk|swim|yoga)\s+(\d+\s*(?:times|days|minutes))", 0.8),
            (r"(?:caffeine|coffee|tea)\s+(\d+\s*(?:cups|times))", 0.7),
        ],
        "key_extractors": []
    },
    "goals": {
        "patterns": [
            (r"(?:i\s+)?(?:want\s+to|wish\s+to|hope\s+to|aim\s+to|plan\s+to)\s+(\w+\s+\w+(?:\s+\w+)?)", 0.7),
            (r"(?:my\s+)?(?:goal|aim|objective|target)\s+(?:is|was)\s+(?:to\s+)?(\w+\s+\w+(?:\s+\w+)?)", 0.8),
            (r"(?:i'm|i\s+am)\s+(?:trying|working)\s+to\s+(\w+\s+\w+(?:\s+\w+)?)", 0.6),
        ],
        "key_extractors": []
    },
    "struggles": {
        "patterns": [
            (r"(?:i\s+)?(?:struggle|have\s+trouble|find\s+it\s+hard|find\s+it\s+difficult)\s+(?:with\s+)?(\w+(?:\s+\w+)?)", 0.8),
            (r"(?:i'm|i\s+am)\s+(?:overwhelmed|burned\s*out|exhausted)\s+(?:by|with)\s+(\w+(?:\s+\w+)?)", 0.9),
            (r"(?:i\s+)?(?:procrastinate|avoid|put\s+off)\s+(\w+(?:\s+\w+)?)", 0.7),
            (r"(?:too\s+much|so\s+much)\s+(\w+\s+\w+)", 0.6),
        ],
        "key_extractors": []
    },
}

# Keywords that indicate facts to extract
FACT_TRIGGER_KEYWORDS = [
    "favorite", "love", "hate", "always", "never", "usually",
    "diagnosed", "medication", "struggle", "goal", "want to",
    "i am", "i'm", "i have", "my", "every day", "every morning",
]

# Fact type mapping from category
FACT_TYPE_MAP = {
    "preferences": "preference",
    "habits": "behavior",
    "sleep": "behavior",
    "focus_work": "behavior",
    "health": "health",
    "goals": "goal",
    "struggles": "struggle",
}


class FactExtractor:
    """
    Extracts structured facts from user messages.
    Uses pattern matching (no LLM dependency) for common fact types.
    """

    def __init__(self):
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict:
        """Pre-compile regex patterns for performance."""
        compiled = {}
        for category, config in FACT_PATTERNS.items():
            compiled[category] = {
                "patterns": [(re.compile(p, re.IGNORECASE), score) for p, score in config["patterns"]],
                "key_extractors": [(re.compile(p, re.IGNORECASE), func) for p, func in config["key_extractors"]],
            }
        return compiled

    def should_process(self, text: str) -> bool:
        """Quick check if text might contain extractable facts."""
        if not text or len(text) < 10:
            return False
        text_lower = text.lower()
        return any(kw in text_lower for kw in FACT_TRIGGER_KEYWORDS)

    def extract_facts(self, text: str) -> List[dict]:
        """
        Extract structured facts from text.
        Returns list of fact dicts with keys: type, category, key, value, confidence.
        """
        if not self.should_process(text):
            return []

        extracted = []
        text_lower = text.lower()

        for category, config in self._compiled_patterns.items():
            for pattern, base_score in config["patterns"]:
                matches = pattern.finditer(text)
                for match in matches:
                    # Build key and value
                    fact_key = self._build_key(category, match, text_lower)
                    fact_value = self._build_value(match)
                    confidence = self._adjust_confidence(base_score, text_lower, match)

                    extracted.append({
                        "type": FACT_TYPE_MAP.get(category, "behavior"),
                        "category": category,
                        "key": fact_key,
                        "value": fact_value,
                        "confidence": confidence,
                        "source": "extraction",
                        "context": text[:200],  # Store context snippet
                    })

        # Deduplicate by key, keeping highest confidence
        seen = {}
        for fact in extracted:
            key = fact["key"]
            if key not in seen or fact["confidence"] > seen[key]["confidence"]:
                seen[key] = fact

        # Deduplicate and also extract explicit identity statements
        self._extract_identity_facts(text_lower, seen)

        return list(seen.values())

    def _build_key(self, category: str, match: re.Match, text_lower: str) -> str:
        """Build a structured key for the extracted fact."""
        # Try custom key extractors first
        config = self._compiled_patterns.get(category, {})
        for pattern, func in config.get("key_extractors", []):
            m = pattern.search(text_lower)
            if m:
                return func(m)

        # Get the main matched group
        groups = [g for g in match.groups() if g is not None]
        main_value = groups[0].strip().lower() if groups else ""

        # Generate key from category and matched value
        if main_value:
            # Clean up the value
            main_value = re.sub(r'[^a-z0-9\s]', '', main_value)
            main_value = main_value[:50].strip()
            if main_value:
                return f"{category}_{main_value.replace(' ', '_')}"

        return category

    def _build_value(self, match: re.Match) -> str:
        """Build the value string from a regex match."""
        groups = [g for g in match.groups() if g is not None]
        if not groups:
            return match.group(0)
        # Return the first captured group as the primary value
        return groups[0].strip()

    def _adjust_confidence(self, base_score: float, text_lower: str, match: re.Match) -> float:
        """Adjust confidence based on context signals."""
        confidence = base_score

        # Boost confidence for explicit statements
        if match.group(0).startswith(("I ", "My ", "I'm ", "I am ")):
            confidence += 0.1

        # Boost for emotional emphasis
        if any(w in text_lower for w in ["really", "very", "so ", "absolutely", "totally"]):
            confidence += 0.05

        # Reduce for negations
        if any(w in text_lower for w in ["don't", "doesn't", "didn't", "not really", "not sure"]):
            confidence -= 0.2

        # Reduce for hypotheticals
        if any(w in text_lower for w in ["would", "could", "might", "maybe", "perhaps"]):
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def _extract_identity_facts(self, text_lower: str, facts: dict):
        """Extract explicit identity statements like 'I am a student'. """
        # "I am a [role]"
        role_match = re.search(r"i(?:'m| am)\s+(?:a|an)\s+(\w+(?:\s+\w+)?)(?:\.|,|$|\s+(?:and|but|with))", text_lower)
        if role_match:
            role = role_match.group(1).strip()
            key = f"identity_{role.replace(' ', '_')}"
            if key not in facts:
                facts[key] = {
                    "type": "preference",
                    "category": "identity",
                    "key": key,
                    "value": role,
                    "confidence": 0.8,
                    "source": "extraction",
                    "context": text_lower[:200],
                }

        # "I have [X] years of [Y]"
        exp_match = re.search(r"(\d+)\s*(?:\+?\s*)?years?\s+(?:of\s+)?(?:experience\sin\s+)?(\w+(?:\s+\w+)?)", text_lower)
        if exp_match:
            years = exp_match.group(1)
            domain = exp_match.group(2)
            key = f"experience_{domain.replace(' ', '_')}"
            if key not in facts:
                facts[key] = {
                    "type": "behavior",
                    "category": "experience",
                    "key": key,
                    "value": f"{years} years",
                    "confidence": 0.7,
                    "source": "extraction",
                    "context": text_lower[:200],
                }

    def extract_structured_facts_for_llm(self, text: str) -> str:
        """
        Extract facts and format them as a prompt injection string for LLM.
        Returns empty string if no facts extracted.
        """
        facts = self.extract_facts(text)
        if not facts:
            return ""

        # Format high-confidence facts for prompt injection
        high_confidence = [f for f in facts if f["confidence"] >= 0.6]
        if not high_confidence:
            return ""

        lines = []
        for fact in high_confidence:
            lines.append(f"[User Fact] Category: {fact['category']} | {fact['key']}: {fact['value']}")

        return "\n".join(lines)


class FactMemoryConsolidator:
    """
    Consolidates extracted facts into the user's long-term memory.
    Integrates with DatabaseManager to persist facts.
    """

    def __init__(self, db_manager=None):
        self.db = db_manager
        self.extractor = FactExtractor()

    def process_message(self, username: str, message: str) -> List[dict]:
        """
        Process a user message, extract facts, and persist them.
        Returns the newly extracted facts.
        """
        if not message or not self.extractor.should_process(message):
            return []

        facts = self.extractor.extract_facts(message)
        saved_facts = []

        if self.db and facts:
            for fact in facts:
                if fact["confidence"] >= 0.5:  # Only save reasonably confident facts
                    saved = self.db.save_fact(
                        username=username,
                        fact_type=fact["type"],
                        key=fact["key"],
                        value=fact["value"],
                        category=fact["category"],
                        confidence=fact["confidence"],
                        source=fact.get("source", "extraction"),
                        context=fact.get("context"),
                    )
                    if saved:
                        saved_facts.append(fact)

        return saved_facts

    def get_fact_context_prompt(self, username: str) -> str:
        """
        Generate a prompt injection string with the user's known facts.
        Returns formatted string for LLM context.
        """
        if not self.db:
            return ""

        try:
            facts_dict = self.db.get_facts_as_dict(username)
            if not facts_dict:
                return ""

            parts = ["[User Knowledge Base: Known facts about this user]"]
            for category, facts in facts_dict.items():
                category_facts = [
                    f"  - {key}: {info['value']}" 
                    for key, info in facts.items() 
                    if info.get('confidence', 0) >= 0.5
                ]
                if category_facts:
                    parts.append(f"\n{category.title()}:")
                    parts.extend(category_facts)

            return "\n".join(parts)
        except Exception as e:
            logger.warning(f"Could not generate fact context: {e}")
            return ""
