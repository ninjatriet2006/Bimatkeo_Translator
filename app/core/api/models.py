"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.api.models
- RESPONSIBILITY: Handle logic for filtering and prioritizing models.
- CALLED BY: app.core.api.manager, app.core.api.fetcher
- CALLS TO: app.core.api.config
- IN = OUT: Evaluates model names against blacklist and priorities.
=============================================================================
"""
from .config import _MODEL_BLACKLIST

def is_blacklisted(model_name: str) -> bool:
    name_lower = model_name.lower()
    blacklist_keywords = _MODEL_BLACKLIST if _MODEL_BLACKLIST else [
        "embedding", "tts", "whisper", "dall-e", "moderation", 
        "classifier", "aqa", "sib", "babbage", "davinci", "ada"
    ]
    for kw in blacklist_keywords:
        if kw in name_lower:
            return True
    return False

def priority_sort_key(m_name: str):
    m_lower = m_name.lower()
    priorities = {}
    high = priorities.get("high", ["gpt-4o", "o1", "o3", "deepseek-chat", "mixtral", "llama3"])
    medium = priorities.get("medium", ["gpt-4", "deepseek", "llama"])
    low = priorities.get("low", ["gpt-3.5"])
    fallback_weight = priorities.get("fallback_weight", 5)

    if any(x in m_lower for x in high): 
        return (-10, m_lower)
    if any(x in m_lower for x in medium): 
        return (-5, m_lower)
    if any(x in m_lower for x in low): 
        return (0, m_lower)
    return (fallback_weight, m_lower)
