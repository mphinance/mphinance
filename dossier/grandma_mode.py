"""
Grandma Mode — plain-English translation of the dossier.

For everyone who reads "VIX backwardation with a gamma pin at the 200 EMA" and
hears the Charlie Brown teacher. This module turns the day's already-computed
readings into sentences a human (hi, Grandma 👵) can actually understand.

It invents no new analysis — it's a translation layer on top of the existing
regime / mood-ring data and a small plain-English glossary of the jargon the
dossier throws around. Written in Sam's voice: warm, a little sarcastic, honest.
"""

from __future__ import annotations

import re

# Regime → what the market "weather" feels like, in plain words.
_REGIME_PLAIN = {
    "CALM":     "The market's having a lazy Sunday — calm and quiet. Nobody's scared of much right now.",
    "NORMAL":   "Just an ordinary day out there. Nothing's on fire, nothing's a party. Business as usual.",
    "ELEVATED": "People are a little jumpy today. Not panicking — just keeping one eye on the exit. Tread lightly.",
    "FEAR":     "The market's got the jitters. Folks are nervous and selling first, asking questions later. Be careful.",
    "PANIC":    "Everyone's sprinting for the exits. This is the scary-movie part. Cash and patience are your friends.",
}

_REGIME_PLAIN_DEFAULT = "We couldn't read the market's mood today — treat that like a foggy morning and drive slow."

# The jargon the dossier loves, explained like you're five (and loved).
_GLOSSARY = {
    "VIX": "Wall Street's 'fear gauge.' Low number = calm, high number = scared. Above 30 means people are sweating.",
    "regime": "A fancy word for the market's current mood, or its 'weather' for the week.",
    "SPY": "A single basket holding the 500 biggest US companies. When people say 'the market,' they usually mean this.",
    "RSI": "A speedometer for a stock. Very high = it ran too fast and may need a rest; very low = it may've been beaten up unfairly.",
    "EMA": "A smoothed-out average of recent prices. It helps answer one question: is this thing generally heading up or down?",
    "momentum": "Buying what's already going up and betting it keeps going — like a snowball rolling downhill.",
    "CSP": "Cash-Secured Put: you get paid a little today for promising to buy a stock cheaper later. Like selling a coupon.",
    "gamma": "Options math that can make a stock get 'stuck' near a price, like a magnet holding it in place.",
    "hedge": "Insurance for your investments. Costs a little; saves you a lot if things go sideways.",
    "200 SMA": "The average price over the last ~10 months. Above it = generally healthy; below it = generally sick.",
}

# The handful of terms a reader is most likely to bump into elsewhere in the
# dossier — always worth spelling out in Grandma Mode.
_CORE_TERMS = ["VIX", "SPY", "momentum"]


def explain_regime(regime, vix_level=None, spy_change=None) -> str:
    """Return a plain-English sentence (or two) describing today's market mood."""
    base = _REGIME_PLAIN.get(str(regime).upper(), _REGIME_PLAIN_DEFAULT) if regime else _REGIME_PLAIN_DEFAULT

    extra = ""
    if vix_level is not None:
        try:
            extra = f" (The fear gauge sits at {float(vix_level):.0f} — "
            extra += "low and relaxed.)" if float(vix_level) < 20 else (
                "a touch tense.)" if float(vix_level) < 30 else "high and twitchy.)")
        except (TypeError, ValueError):
            extra = ""

    if spy_change is not None:
        try:
            sc = float(spy_change)
            direction = "up a bit" if sc > 0.1 else ("down a bit" if sc < -0.1 else "basically flat")
            base += f" The overall market is {direction} today."
        except (TypeError, ValueError):
            pass

    return base + extra


def define(term):
    """Plain-English definition for a jargon term (case-insensitive). None if unknown."""
    if not term:
        return None
    key = str(term).strip()
    for k, v in _GLOSSARY.items():
        if k.lower() == key.lower():
            return v
    return None


def glossary_for(text) -> list:
    """
    Return the [(term, definition), ...] glossary entries whose term appears in
    ``text`` (whole-word, case-insensitive), in glossary order. Handy for
    auto-attaching only the relevant definitions to a given write-up.
    """
    if not text:
        return []
    hits = []
    for term, definition in _GLOSSARY.items():
        if re.search(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE):
            hits.append((term, definition))
    return hits


def plain_english(mood_ring: dict, top_pick: dict | None = None) -> dict:
    """
    Build the Grandma-Mode panel context from the existing mood-ring data
    (see dossier/mood_ring.py) and, optionally, the day's top momentum pick.

    Returns ``{}`` when there's nothing to translate.
    """
    if not mood_ring or not mood_ring.get("regime"):
        return {}

    summary = explain_regime(
        mood_ring.get("regime"),
        vix_level=mood_ring.get("vix_level"),
        spy_change=mood_ring.get("spy_change"),
    )

    pick_line = ""
    if top_pick and top_pick.get("ticker"):
        ticker = top_pick["ticker"]
        score = top_pick.get("score")
        pick_line = f"Sam's favorite today is {ticker}"
        if score is not None:
            pick_line += f" — she scored it {score} out of 100"
        pick_line += ". That just means it looked the strongest of the bunch, not a promise it'll go up."

    return {
        "emoji": mood_ring.get("emoji", "👵"),
        "summary": summary,
        "pick_line": pick_line,
        "glossary": [{"term": t, "definition": _GLOSSARY[t]} for t in _CORE_TERMS],
        "disclaimer": "This is plain-English education, not financial advice. When in doubt, ask someone you trust.",
    }
