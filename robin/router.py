"""Find the best role agent and skills for a request.

Deterministic BM25 over the registry: no API call, no embeddings, runs on the VM.
The orchestrator injects the shortlist into the chief-of-staff prompt, so the
model chooses among 3 agents / 5 skills instead of the whole catalogue. This is
the same idea as tool search: keep the catalogue out of context, retrieve on demand.

Below `min_confidence` the router says so and the chief of staff asks one
clarifying question instead of guessing.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from robin.registry import Agent, Skill, load_agents, load_skills

STOP = set(
    "a an and are as at be by can do does for from get give how i in is it me my of on or our please "
    "should so that the their this to us we what when where which who why will with you your".split()
)

# Light synonym map: business words people use vs. words in descriptions.
SYNONYMS = {
    "ftd": ["deposit", "conversion"],
    "kpi": ["metric"],
    "kpis": ["metric"],
    "okr": ["goal", "strategy"],
    "okrs": ["goal", "strategy"],
    "board": ["executive", "strategy"],
    "investor": ["executive", "strategy", "finance"],
    "churn": ["retention", "metric"],
    "retention": ["metric", "cohort"],
    "ads": ["campaign", "marketing"],
    "seo": ["content", "marketing"],
    "copy": ["content", "marketing"],
    "hire": ["hiring", "people"],
    "hiring": ["people", "recruit"],
    "candidate": ["hiring", "interview"],
    "contract": ["legal"],
    "license": ["regulation", "compliance"],
    "licence": ["regulation", "compliance"],
    "kyc": ["regulation", "compliance"],
    "aml": ["regulation", "compliance"],
    "bug": ["engineering", "incident"],
    "outage": ["incident", "engineering"],
    "budget": ["finance", "spend"],
    "cost": ["finance", "spend"],
    "pricing": ["price", "market"],
    "prd": ["spec", "product"],
    "feature": ["product", "spec"],
    "complaint": ["support", "ticket"],
    "complaints": ["support", "ticket"],
    "reviews": ["review", "customer", "voice"],
    "rival": ["competitor"],
    "rivals": ["competitor"],
    "deck": ["presentation", "executive"],
    "objectives": ["okr", "goal"],
    "objective": ["okr", "goal"],
    "fell": ["drop"],
    "fall": ["drop"],
    "falling": ["drop"],
    "declined": ["decline"],
    "canned": ["macro"],
    "shut": ["decision", "decide"],
    "kill": ["decision", "decide"],
    "funding": ["invest", "decision"],
    "country": ["market"],
    "countries": ["market"],
    "expand": ["market", "strategy"],
    "expansion": ["market", "strategy"],
}


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    out: list[str] = []
    for w in words:
        if w in STOP or len(w) < 2:
            continue
        stem = w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w
        out.append(stem)
        out.extend(SYNONYMS.get(w, []))
    return out


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.4, b: float = 0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.avgdl = sum(map(len, docs)) / max(len(docs), 1)
        df: Counter = Counter()
        for d in docs:
            df.update(set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in docs]

    def score(self, query: list[str]) -> list[float]:
        scores = []
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = 0.0
            for t in query:
                f = tf.get(t)
                if not f:
                    continue
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            scores.append(s)
        return scores


@dataclass
class Match:
    name: str
    score: float
    confidence: float


@dataclass
class Route:
    request: str
    agents: list[Match]
    skills: list[Match]
    confident: bool

    @property
    def agent(self) -> str:
        return self.agents[0].name if self.confident and self.agents else "chief-of-staff"

    def as_prompt(self) -> str:
        """Short block for the orchestrator prompt (dynamic part, after the cached prefix)."""
        lines = ["<routing_shortlist>"]
        lines.append("agents: " + ", ".join(f"{m.name} ({m.confidence:.2f})" for m in self.agents))
        lines.append("skills: " + ", ".join(f"{m.name} ({m.confidence:.2f})" for m in self.skills))
        if not self.confident:
            lines.append("low confidence: ask David one clarifying question or handle as chief-of-staff")
        lines.append("</routing_shortlist>")
        return "\n".join(lines)


class Router:
    def __init__(self, agents: dict[str, Agent] | None = None, skills: dict[str, Skill] | None = None,
                 min_confidence: float = 0.35):
        self.agents = load_agents() if agents is None else agents
        self.skills = load_skills() if skills is None else skills
        # Staff roles (chief-of-staff, reviewer) are never routed to by keywords.
        self._agent_names = [n for n, a in self.agents.items() if a.kind == "department"]
        self._skill_names = list(self.skills)
        self._skill_index = BM25([tokenize(self.skills[n].search_text()) for n in self._skill_names])
        # An agent's document = its own text + the text of the department skills it owns.
        docs = []
        for n in self._agent_names:
            a = self.agents[n]
            own = [self.skills[k].search_text() for k in a.skills
                   if k in self.skills and self.skills[k].department == a.department]
            docs.append(tokenize(" ".join([a.search_text(), *own])))
        self._agent_index = BM25(docs)
        self._owner = {k: n for n in self._agent_names for k in self.agents[n].skills
                       if k in self.skills and self.skills[k].department == self.agents[n].department}
        self.min_confidence = min_confidence

    @staticmethod
    def _rank(names: list[str], scores: list[float], k: int) -> list[Match]:
        ranked = sorted(zip(names, scores), key=lambda x: -x[1])[:k]
        total = sum(max(s, 0) for _, s in ranked) or 1.0
        return [Match(n, round(s, 3), round(max(s, 0) / total, 3)) for n, s in ranked if s > 0]

    def route(self, request: str, k_agents: int = 3, k_skills: int = 5) -> Route:
        q = tokenize(request)
        skill_scores = self._skill_index.score(q)
        # Two-level vote: agent score + the best score among the department skills it owns.
        best_owned: dict[str, float] = {}
        for name, sc in zip(self._skill_names, skill_scores):
            owner = self._owner.get(name)
            if owner:
                best_owned[owner] = max(best_owned.get(owner, 0.0), sc)
        agent_scores = [s + best_owned.get(n, 0.0) for n, s in zip(self._agent_names, self._agent_index.score(q))]
        agents = self._rank(self._agent_names, agent_scores, k_agents)
        # Boost skills owned by the top agent so the shortlist is coherent.
        if agents:
            owned = set(self.agents[agents[0].name].skills)
            skill_scores = [s * 1.3 if n in owned else s for n, s in zip(self._skill_names, skill_scores)]
        skills = self._rank(self._skill_names, skill_scores, k_skills)
        confident = bool(agents) and agents[0].confidence >= self.min_confidence and agents[0].score >= 1.0
        return Route(request, agents, skills, confident)
