"""Rule-based lexicon state extraction."""
from __future__ import annotations

import re
from collections import Counter

import pandas as pd

VALID_SEVERITIES = {"P0", "P1", "P2", "P3", "P4"}

SEVERITY_PATTERNS = {
    "P0": [
        r"\boutage(s)?\b",
        r"\bdowntime\b",
        r"\bdata\s*loss\b",
        r"\bcorrupt(ed|ion)?\b",
        r"\bsecurity\s*(breach|incident|advisory)\b",
        r"\b(cve|vulnerabilit(y|ies)|exploit|rce)\b",
        r"\bproduction\s*(down|broken|outage)\b",
        r"\b(panic|deadlock|hang|hangs|hanging)\b",
        r"\bdata\s*corruption\b",
    ],
    "P1": [
        r"\bblocker\b",
        r"\bcritical\b",
        r"\burgent\b",
        r"\bregression\b",
        r"\bsevere\b",
        r"\bhotfix\b",
        r"\bincident\b",
        r"\b(broken|completely\s*broken|cannot|can\'?t|unable\s*to)\b",
        r"\b(fails?|failure|failed|failing)\b",
    ],
    "P2": [
        r"\bbug\b",
        r"\b(fix(es|ed|ing)?)\b",
        r"\b(error|errors)\b",
        r"\bexception(s)?\b",
        r"\bflaky\b",
        r"\b(timeout|time\s*out)\b",
        r"\bdegrade(d|s)?\b",
        r"\b(slow|latency|performance)\b",
        r"\b(memory\s*leak|leak)\b",
    ],
    "P3": [
        r"\brefactor(s|ing|ed)?\b",
        r"\bcleanup\b",
        r"\b(improve|improvement|enhance(ment)?)\b",
        r"\bsimplif(y|ies|ied)\b",
        r"\bpolish\b",
        r"\brestructur(e|ing)\b",
        r"\bchore\b",
        r"\b(test|tests|testing)\b",
        r"\bbuild\b",
        r"\b(ci|pipeline|workflow|github\s*actions?)\b",
    ],
    "P4": [
        r"\b(typo|typos)\b",
        r"\b(style|styling|format(ting)?|lint(ing)?)\b",
        r"\bgrammar\b",
        r"\bcomment(s)?\b",
        r"\b(docs?|documentation|readme|changelog)\b",
        r"\b(bump|bumps|bumped)\b",
        r"\b(dependency|dependencies|deps)\b",
        r"\b(version|versions|semver)\b",
        
        
    ],
}

SEVERITY_PRIORITY = ["P0", "P1", "P2", "P3", "P4"]

COMPONENT_PATTERNS = {
    "documentation": [
        r"\b(docs?|documentation|readme|guide|manual|tutorial|examples?|changelog)\b",
    ],
    "testing": [
        r"\b(tests?|testing|pytest|unittest|fixture|mock(s|ed|ing)?|spec|coverage|flaky)\b",
    ],
    "build & ci": [
        r"\b(build|ci|pipeline|workflow|github\s*actions?|release|deploy(ment)?|packaging|makefile|tox|nox)\b",
    ],
    "dependencies": [
        r"\b(dependency|dependencies|deps|package|requirements?|poetry|pip|lockfile|pyproject|pip-?tools?)\b",
    ],
    "version & bump": [
        r"\b(bump(s|ed|ing)?|version(s|ing)?|semver|release\s*notes?|tag(s|ged|ging)?)\b",
    ],
    
    "configuration": [
        r"\b(config(uration)?|settings|toml|yaml|yml|ini|\.env|dotenv|pyproject\.toml)\b",
    ],
    "cli interface": [
        r"\b(cli|command\s*line|argument(s)?|flag(s)?|option(s)?|subcommand|prompt)\b",
    ],
    "git integration": [
        r"\b(git|branch(es)?|rebase|merge|hook(s)?|push|pull|cross[-\s]*reference|reference)\b",
    ],
    "api & endpoints": [
        r"\b(api|endpoint(s)?|request(s)?|response(s)?|client|server|http|rest|graphql)\b",
    ],
    "user interface": [
        r"\b(ui|frontend|view|button|page|screen|layout|css|theme)\b",
    ],
    "database & schema": [
        r"\b(database|db|sql|migration|schema|query|orm|sqlalchemy|sqlite)\b",
    ],
    "authentication": [
        r"\b(auth|login|token|permission|access|oauth|jwt|credentials?)\b",
    ],
    "runtime stability": [
        r"\b(error|exception|crash|timeout|leak|hang|panic|traceback|stacktrace)\b",
    ],
    "performance": [
        r"\b(performance|slow|latency|throughput|optimi[sz]ation|speed|memory)\b",
    ],
    "internationalization": [
        r"\b(i18n|l10n|translation|locale|language\s*support)\b",
    ],
    "logging & telemetry": [
        r"\b(log(ging)?|telemetry|metrics?|monitoring|trace(s)?)\b",
    ],
    "templates & rendering": [
        r"\b(template(s)?|render(ing)?|jinja|markup|markdown|mkdocs)\b",
    ],
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "when", "week",
    "issue", "issues", "closed", "close", "make", "made", "via", "use", "using",
    "add", "adds", "added", "adding", "update", "updates", "updated",
    "support", "supports", "supported", "allow", "allows", "remove", "removes",
    "removed", "change", "changes", "changed", 
    "request", "merge", "merged", "open", "opened", "init", "main",
}


def _count_pattern_hits(text, pattern_groups):
    lowered = text.lower()
    scores = {}
    for label, patterns in pattern_groups.items():
        total = 0
        for pattern in patterns:
            total += len(re.findall(pattern, lowered))
        if total:
            scores[label] = total
    return scores


def _top_terms(text, limit=4):
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    counts = Counter(t for t in tokens if t not in STOPWORDS and len(t) > 2)
    return [term for term, _ in counts.most_common(limit)]


def _limit_component_words(component, max_words=4):
    words = str(component).strip().split()
    return " ".join(words[:max_words]) if words else "unknown area"


def _humanize_score(score):
    score = float(score or 0)
    if score >= 3.0:
        return "well beyond"
    if score >= 1.5:
        return "clearly beyond"
    if score >= 0.5:
        return "slightly beyond"
    return "near"


def _pick_severity(severity_scores, anomaly_score, direction, title_count):
    if severity_scores:
        ranked = sorted(
            severity_scores.items(),
            key=lambda item: (item[1], -SEVERITY_PRIORITY.index(item[0])),
            reverse=True,
        )
        return ranked[0][0], True

    if anomaly_score >= 3.0:
        return "P1", False
    if anomaly_score >= 1.5:
        return "P2", False
    if anomaly_score >= 0.5:
        return "P3", False
    if direction == "low" and title_count == 0:
        return "P4", False
    return "P3", False


def _pick_component(component_scores):
    if not component_scores:
        return "unknown area", 0.0
    ranked = sorted(component_scores.items(), key=lambda item: item[1], reverse=True)
    label, hits = ranked[0]
    return _limit_component_words(label), float(hits)


def _compute_lexicon_confidence(severity, severity_scores, component_scores, title_count, severity_from_text):
    sev_hits = severity_scores.get(severity, 0)
    total_sev = sum(severity_scores.values())
    sev_share = sev_hits / total_sev if total_sev else 0.0

    comp_hits = max(component_scores.values(), default=0)
    total_comp = sum(component_scores.values())
    comp_share = comp_hits / total_comp if total_comp else 0.0

    if total_sev and total_comp:
        dominance = 0.7 * sev_share + 0.3 * comp_share
    elif total_sev:
        dominance = sev_share
    elif total_comp:
        dominance = comp_share
    else:
        dominance = 0.0

    confidence = 0.30 + 0.65 * dominance
    if title_count:
        confidence = min(confidence + 0.05, 0.95)
    if not severity_from_text:
        confidence = max(confidence - 0.10, 0.30)
    return max(0.30, min(confidence, 0.95))


def _build_reasoning(direction, value, lower_bound, upper_bound, anomaly_score,
                     component, component_scores, severity_scores, top_terms,
                     title_count, event_count):
    band_text = ""
    try:
        if direction == "high" and pd.notna(upper_bound):
            band_text = f" ({int(value)} vs upper bound {upper_bound:.0f})"
        elif direction == "low" and pd.notna(lower_bound):
            band_text = f" ({int(value)} vs lower bound {lower_bound:.0f})"
    except Exception:
        band_text = ""

    movement = "spike" if direction == "high" else ("drop" if direction == "low" else "shift")
    magnitude = _humanize_score(anomaly_score)
    top_components = [c for c, _ in sorted(component_scores.items(), key=lambda kv: kv[1], reverse=True)[:2]]
    components_phrase = component if not top_components else ", ".join(top_components[:2])
    severity_signals = sorted(severity_scores.keys(), key=SEVERITY_PRIORITY.index)[:2]

    parts = [
        f"Weekly closures show a {magnitude}-typical {movement}{band_text}",
    ]
    if title_count:
        parts.append(f"covering {title_count} unique titles across {event_count} events")
    if components_phrase:
        parts.append(f"focused on {components_phrase}")
    if top_terms:
        parts.append(f"with recurring terms like {', '.join(top_terms)}")
    if severity_signals and (severity_signals != ["P3"]):
        parts.append(f"flagged by {'/'.join(severity_signals)} signal words")

    sentence = ", ".join(parts).rstrip(",")
    if sentence and sentence[-1] not in ".!?":
        sentence += "."
    return sentence


def extract_state_rule_based(row):
    text = str(row.get("titles_text", ""))
    severity_scores = _count_pattern_hits(text, SEVERITY_PATTERNS)
    component_scores = _count_pattern_hits(text, COMPONENT_PATTERNS)
    anomaly_score = float(row.get("anomaly_score", 0) or 0)
    direction = row.get("anomaly_direction", "normal")
    title_count = int(row.get("title_count", 0) or 0)
    event_count = int(row.get("event_count", 0) or 0)
    value = row.get("value", 0)
    lower_bound = row.get("lower_bound", float("nan"))
    upper_bound = row.get("upper_bound", float("nan"))

    severity, severity_from_text = _pick_severity(
        severity_scores, anomaly_score, direction, title_count,
    )
    component, _ = _pick_component(component_scores)
    confidence = _compute_lexicon_confidence(
        severity, severity_scores, component_scores, title_count, severity_from_text,
    )

    top_terms = _top_terms(text)

    reasoning = _build_reasoning(
        direction=direction,
        value=value,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        anomaly_score=anomaly_score,
        component=component,
        component_scores=component_scores,
        severity_scores=severity_scores,
        top_terms=top_terms,
        title_count=title_count,
        event_count=event_count,
    )

    return {
        "severity": severity,
        "component": component,
        "reasoning": reasoning,
        "extraction_method": "rule_based",
        "confidence": confidence,
    }


