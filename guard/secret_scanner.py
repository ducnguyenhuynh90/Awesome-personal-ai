"""Secret scanner (S5 definition).

A secret lets someone authenticate, sign or decrypt: passwords, secret keys,
private keys, access tokens, session cookies, 2FA seeds, DB URLs with a password.
NOT secrets: IDs used with a secret (client/operator/merchant/account IDs),
empty/placeholder/masked values, public keys (pk_, phc_), hashes, URLs without
credentials. Judge by what the value does, not the field name.

Runs on every tool result and every output before delivery. On a hit: redact,
never store the value, and return findings so the caller can tell David where
it sits and file the report through the configured reporter (config/limits.yaml
-> security.report_command). The reporter is configured by the operator; this
module never sends anything itself.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

REDACTED = "[REDACTED:{kind}]"

# (kind, regex). Group "v" = the secret value when only part of the match is secret.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai_style_key", re.compile(r"\bsk-(?:proj-|live-|test-)?[A-Za-z0-9_\-]{20,}")),
    ("stripe_secret", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("slack_webhook", re.compile(r"https://hooks\.slack\.com/(?:services|triggers|workflows)/[A-Za-z0-9/_\-]+")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("posthog_personal_key", re.compile(r"\bphx_[A-Za-z0-9]{30,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}")),
    ("db_url_password", re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp|mssql)://[^\s:/@]+:(?P<v>[^\s@/]{3,})@")),
    ("otp_seed", re.compile(r"otpauth://[^\s]*secret=(?P<v>[A-Z2-7]{16,})", re.I)),
    # key = value assignments where the key names a secret and the value looks real.
    ("assigned_secret", re.compile(
        r"(?i)\b(?:password|passwd|pwd|secret|secret_key|client_secret|api_key|apikey|access_token|auth_token|"
        r"refresh_token|private_key|session(?:_?id|_?cookie)?|cookie|totp_secret|2fa_seed)\b"
        r"[\"']?\s*[:=]\s*[\"']?(?P<v>[^\s\"',;]{8,})")),
]

# Values that look like secrets but are not (S5 definition).
NOT_SECRET = re.compile(
    r"^(?:\[REDACTED:[a-z_]+\]|\*+|x{4,}|X{4,}|<[^>]+>|\$\{[^}]+\}|changeme|placeholder|example|redacted|null|none|true|false|"
    r"(?:pk|phc)_[A-Za-z0-9_]+|[0-9a-f]{32}|[0-9a-f]{40}|[0-9a-f]{64}|.*\.\.\..*)$",
    re.I,
)


@dataclass
class Finding:
    kind: str
    start: int
    end: int
    preview: str  # first 4 chars + length; never the value

    def __str__(self) -> str:
        return f"{self.kind} at char {self.start} ({self.preview})"


def _preview(value: str) -> str:
    return f"{value[:4]}… len={len(value)}"


def scan(text: str) -> list[Finding]:
    findings: list[Finding] = []
    taken: list[tuple[int, int]] = []
    for kind, pattern in PATTERNS:
        for m in pattern.finditer(text):
            if "v" in pattern.groupindex and m.group("v") is not None:
                start, end, value = m.start("v"), m.end("v"), m.group("v")
            else:
                start, end, value = m.start(), m.end(), m.group(0)
            if NOT_SECRET.match(value):
                continue
            if any(s <= start < e or s < end <= e for s, e in taken):
                continue
            taken.append((start, end))
            findings.append(Finding(kind, start, end, _preview(value)))
    return sorted(findings, key=lambda f: f.start)


def redact(text: str) -> tuple[str, list[Finding]]:
    findings = scan(text)
    out = text
    for f in sorted(findings, key=lambda f: -f.start):
        out = out[: f.start] + REDACTED.format(kind=f.kind) + out[f.end :]
    return out, findings
