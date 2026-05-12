from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator
from urllib.parse import urlsplit

POLICY_VERSION = "chatgpt_archive_atlas.lexical_policy.v1"

_STOPWORDS = frozenset(
    {
        "a",
        "about",
        "above",
        "after",
        "again",
        "against",
        "all",
        "also",
        "am",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "because",
        "been",
        "before",
        "being",
        "below",
        "between",
        "both",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "done",
        "down",
        "during",
        "each",
        "either",
        "else",
        "etc",
        "even",
        "few",
        "for",
        "from",
        "further",
        "get",
        "got",
        "had",
        "has",
        "have",
        "having",
        "he",
        "her",
        "here",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "itself",
        "just",
        "let",
        "lets",
        "make",
        "many",
        "may",
        "me",
        "might",
        "more",
        "most",
        "much",
        "my",
        "myself",
        "need",
        "no",
        "nor",
        "not",
        "now",
        "of",
        "off",
        "on",
        "once",
        "only",
        "or",
        "other",
        "our",
        "ours",
        "ourselves",
        "out",
        "over",
        "own",
        "please",
        "same",
        "she",
        "should",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "themselves",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "too",
        "under",
        "until",
        "up",
        "us",
        "use",
        "using",
        "very",
        "want",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
    }
)

_GENERIC_NOISE = frozenset(
    {
        "ai",
        "assistant",
        "bin",
        "chat",
        "conversation",
        "data",
        "docs",
        "example",
        "file",
        "files",
        "help",
        "message",
        "messages",
        "question",
        "reply",
        "run",
        "response",
        "see",
        "section",
        "string",
        "test",
        "tests",
        "text",
        "thing",
        "things",
        "topic",
        "user",
        "via",
        "work",
    }
)

_PATH_SUFFIXES = frozenset({"json", "jsonl", "md", "py", "sh", "toml", "yaml", "yml", "txt"})
_DOMAIN_SUFFIXES = frozenset(
    {
        "ai",
        "app",
        "ca",
        "co",
        "com",
        "dev",
        "edu",
        "gov",
        "info",
        "io",
        "local",
        "me",
        "net",
        "org",
        "sh",
        "uk",
        "us",
    }
)
_COMMAND_NAMES = frozenset(
    {
        "apt",
        "apt-get",
        "awk",
        "bash",
        "black",
        "brew",
        "cargo",
        "cat",
        "cd",
        "chmod",
        "chown",
        "cmake",
        "cp",
        "curl",
        "deno",
        "docker",
        "docker-compose",
        "echo",
        "find",
        "flask",
        "gh",
        "git",
        "go",
        "gradle",
        "grep",
        "gunicorn",
        "helm",
        "java",
        "javac",
        "journalctl",
        "kubectl",
        "ls",
        "make",
        "mkdir",
        "mvn",
        "mv",
        "mysql",
        "node",
        "npm",
        "npx",
        "pip",
        "pip3",
        "pnpm",
        "poetry",
        "psql",
        "pytest",
        "python",
        "python3",
        "rg",
        "rm",
        "rsync",
        "ruff",
        "scp",
        "sed",
        "sh",
        "source",
        "sqlite3",
        "ssh",
        "sudo",
        "systemctl",
        "tail",
        "touch",
        "uv",
        "uvicorn",
        "wget",
        "xargs",
        "yarn",
    }
)
_COMMAND_BREAK_TOKENS = frozenset({"and", "but", "or", "then"})
_COMMAND_SENTENCE_WORDS = frozenset(
    {"check", "escalate", "inspect", "install", "model", "open", "reference", "run"}
)
_MODEL_PREFIXES = (
    "all-minilm",
    "bge",
    "chatgpt",
    "claude",
    "deepseek",
    "e5",
    "gemini",
    "gpt",
    "llama",
    "mixtral",
    "mistral",
    "o1",
    "o3",
    "o4",
    "qwen",
    "text-embedding",
    "text-moderation",
    "whisper",
)
_PACKAGE_CUES = frozenset(
    {
        "add",
        "crate",
        "crates",
        "dependencies",
        "dependency",
        "gem",
        "gems",
        "import",
        "imports",
        "install",
        "installed",
        "library",
        "libraries",
        "module",
        "modules",
        "package",
        "packages",
        "plugin",
        "plugins",
        "using",
        "with",
    }
)
_PACKAGE_EXCLUDES = frozenset(
    {
        "bash",
        "linux",
        "macos",
        "python",
        "python3",
        "shell",
        "ubuntu",
        "windows",
    }
)

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_URL_RE = re.compile(r"https?://[^\s<>()\]\"']+", re.IGNORECASE)
_BARE_DOMAIN_RE = re.compile(
    r"\b(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"(?:ai|app|ca|co|com|dev|edu|gov|info|io|local|me|net|org|sh|uk|us)\b(?::\d+)?",
    re.IGNORECASE,
)
_UNIX_PATH_RE = re.compile(
    r"(?<![\w~])(?:~|\.{1,2}|/)(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+/?"
)
_RELATIVE_PATH_RE = re.compile(
    r"(?<![\w/])(?:[A-Za-z0-9._-]+/)+[A-Za-z0-9._-]+(?:\.[A-Za-z0-9._-]+)?/?"
)
_WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:\\(?:[^\\\s]+\\)*[^\\\s]+\b")
_IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
_FROM_IMPORT_RE = re.compile(r"^\s*from\s+([A-Za-z_][A-Za-z0-9_.]*)\s+import\b", re.MULTILINE)
_COMMAND_INSTALL_RE = re.compile(
    r"\b(?:pip|pip3|poetry|uv|npm|pnpm|yarn|cargo|go|brew|apt|apt-get|dnf|yum)"
    r"\s+(?:install|add|get)\s+([^\n`]+)",
    re.IGNORECASE,
)
_CASE_CITATION_RE = re.compile(
    r"\b[A-Z][A-Za-z.&'/-]+(?:\s+(?:[A-Z][A-Za-z.&'/-]+|and|for|in|of|on|the))*\s+v\.\s+"
    r"[A-Z][A-Za-z.&'/-]+(?:\s+(?:[A-Z][A-Za-z.&'/-]+|and|for|in|of|on|the))*"
    r"(?:,\s*\d+\s+[A-Za-z][A-Za-z.\d ]+\s+\d+(?:\s*\(\d{4}\))?)?"
)
_STATUTE_RE = re.compile(
    r"\b\d+\s+(?:U\.?S\.?C\.?|C\.?F\.?R\.?|Stat\.)\s*"
    r"(?:§+\s*[\w().-]+|[\w().-]+)?",
    re.IGNORECASE,
)
_RULE_RE = re.compile(
    r"\b(?:Fed\.\s+R\.\s+[A-Za-z. ]+|Rule)\s+\d+(?:\([a-z0-9]+\))*",
    re.IGNORECASE,
)
_CAPITALIZED_PHRASE_RE = re.compile(
    r"\b(?:[A-Z][a-zA-Z0-9]+|[A-Z]{2,}[A-Z0-9-]*|[A-Z][a-z]+[A-Z][A-Za-z0-9]*)"
    r"(?:\s+(?:[A-Z][a-zA-Z0-9]+|[A-Z]{2,}[A-Z0-9-]*|"
    r"of|for|to|and|in|on|the)){0,4}"
)
_MODEL_RE = re.compile(
    r"\b(?:all-minilm|bge|chatgpt|claude|deepseek|e5|gemini|gpt|llama|mixtral|"
    r"mistral|o1|o3|o4|qwen|text-embedding|text-moderation|whisper)"
    r"[A-Za-z0-9._-]*\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LexicalEvidence:
    top_terms: list[dict[str, int]] = field(default_factory=list)
    keyphrases: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    package_names: list[str] = field(default_factory=list)
    model_names: list[str] = field(default_factory=list)
    legal_citations: list[str] = field(default_factory=list)
    capitalized_phrases: list[str] = field(default_factory=list)
    noise_terms_rejected: list[str] = field(default_factory=list)


def extract_lexical_evidence(
    texts,
    *,
    max_terms: int = 20,
    max_items_per_kind: int = 20,
) -> LexicalEvidence:
    term_limit = _validate_limit("max_terms", max_terms)
    item_limit = _validate_limit("max_items_per_kind", max_items_per_kind)
    normalized_texts = tuple(_iter_texts(texts))
    if not normalized_texts:
        return LexicalEvidence()

    joined_text = "\n".join(normalized_texts)
    text_without_urls = _URL_RE.sub(" ", joined_text)
    token_counts, rejected_noise = _count_terms(normalized_texts)
    capitalized_counts = _extract_capitalized_phrase_counts(joined_text)

    keyphrase_counts = _extract_keyphrase_counts(normalized_texts)
    for phrase, count in capitalized_counts.items():
        normalized_phrase = _normalize_keyphrase(phrase)
        if normalized_phrase is not None:
            keyphrase_counts[normalized_phrase] += count

    return LexicalEvidence(
        top_terms=_rank_term_counts(token_counts, term_limit),
        keyphrases=_rank_counter(keyphrase_counts, item_limit),
        domains=_rank_counter(_extract_domain_counts(joined_text), item_limit),
        paths=_rank_counter(_extract_path_counts(text_without_urls), item_limit),
        commands=_rank_counter(_extract_command_counts(joined_text), item_limit),
        package_names=_rank_counter(_extract_package_counts(joined_text), item_limit),
        model_names=_rank_counter(_extract_model_counts(joined_text), item_limit),
        legal_citations=_rank_counter(_extract_legal_citation_counts(joined_text), item_limit),
        capitalized_phrases=_rank_counter(capitalized_counts, item_limit),
        noise_terms_rejected=_rank_counter(rejected_noise, item_limit),
    )


def _validate_limit(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if value < 0:
        raise ValueError(f"{name} must be >= 0")
    return value


def _iter_texts(texts) -> Iterator[str]:
    if isinstance(texts, str):
        if texts:
            yield texts
        return

    if not isinstance(texts, Iterable):
        raise TypeError("texts must be a string or an iterable of strings")

    for item in texts:
        if not isinstance(item, str):
            raise TypeError("texts must contain only strings")
        if item:
            yield item


def _count_terms(texts: Iterable[str]) -> tuple[Counter[str], Counter[str]]:
    accepted: Counter[str] = Counter()
    rejected: Counter[str] = Counter()
    for text in texts:
        for match in _WORD_RE.finditer(text):
            raw = match.group(0)
            term = _normalize_term(raw)
            if term is None:
                continue
            if _is_noise_term(term):
                rejected[term] += 1
                continue
            accepted[term] += 1
    return accepted, rejected


def _normalize_term(value: str) -> str | None:
    term = value.strip("._+-:/\\'\"()[]{}<>;,!?").lower()
    if not term:
        return None
    if term.startswith("http") or "@" in term:
        return None
    if _normalize_domain(term) is not None:
        return None
    if term.isdigit():
        return None
    if len(term) == 1 and not any(char.isdigit() for char in term):
        return None
    if term in {"com", "org", "net", "www"}:
        return None
    if "." in term:
        suffix = term.rsplit(".", 1)[-1]
        if suffix in _PATH_SUFFIXES:
            return None
        if term.count(".") > 1 and not term.startswith(_MODEL_PREFIXES):
            return None
        if re.fullmatch(r"[a-z](?:\.[a-z0-9]+)+", term):
            return None
    if term.count(".") > 2:
        return None
    return term


def _is_noise_term(term: str) -> bool:
    if term in _STOPWORDS or term in _GENERIC_NOISE:
        return True
    if term.endswith("'s"):
        return True
    if len(term) <= 2 and term not in {"ai", "ui", "db", "os"}:
        return True
    if all(char in "._-+" for char in term):
        return True
    return False


def _extract_keyphrase_counts(texts: Iterable[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        tokens = [term for term in (_normalize_term(match.group(0)) for match in _WORD_RE.finditer(text))]
        filtered = [token for token in tokens if token and not _is_noise_term(token)]
        for size in (2, 3):
            if len(filtered) < size:
                continue
            for index in range(len(filtered) - size + 1):
                phrase = " ".join(filtered[index : index + size])
                if _is_generic_phrase(phrase):
                    continue
                counts[phrase] += 1
    for phrase in list(counts):
        if counts[phrase] < 2:
            del counts[phrase]
    return counts


def _normalize_keyphrase(value: str) -> str | None:
    words = [_normalize_term(part) for part in value.split()]
    cleaned = [word for word in words if word and not _is_noise_term(word)]
    if len(cleaned) < 2:
        return None
    phrase = " ".join(cleaned)
    if _is_generic_phrase(phrase):
        return None
    return phrase


def _is_generic_phrase(phrase: str) -> bool:
    parts = phrase.split()
    if len(parts) < 2:
        return True
    if len(set(parts)) == 1:
        return True
    return False


def _extract_domain_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for match in _URL_RE.finditer(text):
        domain = _normalize_domain(match.group(0))
        if domain is not None:
            counts[domain] += 1
    for match in _BARE_DOMAIN_RE.finditer(text):
        domain = _normalize_domain(match.group(0))
        if domain is not None:
            counts[domain] += 1
    return counts


def _normalize_domain(value: str) -> str | None:
    candidate = value.strip(".,);]}>\"'")
    if not candidate:
        return None
    try:
        parsed = urlsplit(candidate if "://" in candidate else f"https://{candidate}")
    except ValueError:
        return None
    host = parsed.netloc or parsed.path
    if not host or "[" in host or "]" in host:
        return None
    host = host.split("@", 1)[-1].split(":", 1)[0].strip(".").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host or "[" in host or "]" in host:
        return None
    if "." not in host:
        return None
    suffix = host.rsplit(".", 1)[-1]
    if suffix not in _DOMAIN_SUFFIXES:
        return None
    return host


def _extract_path_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for pattern in (_WINDOWS_PATH_RE, _UNIX_PATH_RE, _RELATIVE_PATH_RE):
        for match in pattern.finditer(text):
            path = _normalize_path(match.group(0))
            if path is not None:
                counts[path] += 1
    return counts


def _normalize_path(value: str) -> str | None:
    path = value.rstrip(".,);]}>\"'")
    if not path or "://" in path:
        return None
    if path in {".", "..", "/"}:
        return None
    if "/" not in path and "\\" not in path:
        return None
    if path.lower().split(".")[-1] in _DOMAIN_SUFFIXES and path.count("/") == 0:
        return None
    if path.endswith(":"):
        return None
    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if suffix and suffix in _DOMAIN_SUFFIXES and "/" not in path and "\\" not in path:
        return None
    if path.startswith("//"):
        return None
    if path.endswith("/") and "/" not in path[:-1]:
        return None
    if "." not in path and path.count("/") == 1 and not path.startswith(("/", "./", "../", "~/")):
        return None
    return path


def _extract_command_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    segments = list(text.splitlines())
    segments.extend(match.group(1) for match in _INLINE_CODE_RE.finditer(text))
    for segment in segments:
        command = _normalize_command(segment)
        if command is not None:
            counts[command] += 1
    for command in _iter_inline_commands(text):
        counts[command] += 1
    return counts


def _iter_inline_commands(text: str) -> Iterator[str]:
    tokens = text.split()
    index = 0
    while index < len(tokens):
        start = _command_token_start(tokens[index])
        if start is None:
            index += 1
            continue
        end = index + 1
        while end < len(tokens):
            current = tokens[end].strip(".,);]}>\"'")
            lowered = current.lower()
            if lowered in _COMMAND_SENTENCE_WORDS:
                break
            if lowered in _COMMAND_BREAK_TOKENS:
                next_start = _command_token_start(tokens[end + 1]) if end + 1 < len(tokens) else None
                if next_start is not None or lowered in {"and", "then"}:
                    break
            end += 1
        command = " ".join(
            token.strip(".,);]}>\"'")
            for token in tokens[index:end]
            if token.strip(".,);]}>\"'")
        )
        normalized = _normalize_command(command)
        if normalized is not None:
            yield normalized
        index = max(end, index + 1)


def _command_token_start(token: str) -> str | None:
    cleaned = token.lstrip("$#> ").strip(".,);]}>\"'")
    if not cleaned:
        return None
    if cleaned.lower() == "sudo":
        return cleaned
    executable = cleaned.lower().rsplit("/", 1)[-1]
    if executable in _COMMAND_NAMES:
        return cleaned
    return None


def _normalize_command(value: str) -> str | None:
    line = " ".join(value.strip().split())
    if not line:
        return None
    line = line.lstrip("$#> ")
    if not line:
        return None
    tokens = line.split()
    if not tokens:
        return None
    command_name = tokens[0].lower()
    if command_name == "sudo" and len(tokens) > 1:
        command_name = tokens[1].lower()
    executable = command_name.rsplit("/", 1)[-1]
    if executable not in _COMMAND_NAMES and not command_name.startswith(("./", "../", "/", ".venv/")):
        return None
    if len(tokens) == 1 and executable not in {"python", "python3", "pytest", "pip", "pip3", "uv"}:
        return None
    return line[:160]


def _extract_package_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for match in _COMMAND_INSTALL_RE.finditer(text):
        for token in match.group(1).split():
            package = _normalize_package_name(token)
            if package is not None:
                counts[package] += 1
    for match in _IMPORT_RE.finditer(text):
        package = _normalize_package_name(match.group(1))
        if package is not None:
            counts[package] += 1
    for match in _FROM_IMPORT_RE.finditer(text):
        root = match.group(1).split(".", 1)[0]
        package = _normalize_package_name(root)
        if package is not None:
            counts[package] += 1
    raw_tokens = [match.group(0) for match in _WORD_RE.finditer(text)]
    for index, raw_token in enumerate(raw_tokens):
        if raw_token.lower() not in _PACKAGE_CUES:
            continue
        for candidate in raw_tokens[index + 1 : index + 5]:
            package = _normalize_package_name(candidate)
            if package is None or package in {"and", "or"}:
                continue
            if not candidate[:1].islower():
                continue
            if _looks_like_package_name(package):
                counts[package] += 1
    return counts


def _normalize_package_name(value: str) -> str | None:
    package = value.strip("`'\"()[]{}<>,.;:")
    if not package or package.startswith("-"):
        return None
    if package in {"install", "add", "get"}:
        return None
    package = re.split(r"[<>=!~]", package, maxsplit=1)[0]
    package = re.sub(r"\[.*\]$", "", package)
    package = package.rstrip(",;")
    if not package:
        return None
    if package.startswith("@"):
        package = package[1:]
    if "/" in package and "." not in package and package.count("/") > 1:
        return package.lower()
    if not re.fullmatch(r"[A-Za-z0-9_.+/-]+", package):
        return None
    return package.lower()


def _looks_like_package_name(value: str) -> bool:
    if value in _STOPWORDS or value in _GENERIC_NOISE or value in _PACKAGE_EXCLUDES:
        return False
    if value in _COMMAND_NAMES:
        return False
    if len(value) < 4:
        return False
    if "." in value and value.rsplit(".", 1)[-1] in _PATH_SUFFIXES:
        return False
    if _normalize_domain(value) is not None:
        return False
    if _normalize_model_name(value) is not None:
        return False
    return True


def _extract_model_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for match in _MODEL_RE.finditer(text):
        model = _normalize_model_name(match.group(0))
        if model is not None:
            counts[model] += 1
    return counts


def _normalize_model_name(value: str) -> str | None:
    model = value.strip(".,);]}>\"'").lower()
    if not model:
        return None
    if not model.startswith(_MODEL_PREFIXES):
        return None
    if model in {"chatgpt", "gpt"}:
        return None
    return model


def _extract_legal_citation_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for pattern in (_CASE_CITATION_RE, _STATUTE_RE, _RULE_RE):
        for match in pattern.finditer(text):
            citation = _normalize_legal_citation(match.group(0))
            if citation is not None:
                counts[citation] += 1
    return counts


def _normalize_legal_citation(value: str) -> str | None:
    citation = " ".join(value.strip().split())
    if not citation:
        return None
    return citation


def _extract_capitalized_phrase_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for match in _CAPITALIZED_PHRASE_RE.finditer(text):
        phrase = _normalize_capitalized_phrase(match.group(0))
        if phrase is not None:
            counts[phrase] += 1
    return counts


def _normalize_capitalized_phrase(value: str) -> str | None:
    phrase = " ".join(value.strip(".,);]}>\"'").split())
    if not phrase:
        return None
    words = phrase.split()
    if len(words) == 1:
        word = words[0]
        if word.lower() in _STOPWORDS:
            return None
        if not any(char.isupper() for char in word[1:]) and not word.isupper():
            return None
        return word
    meaningful = [word for word in words if word.lower() not in _STOPWORDS]
    if len(meaningful) < 2:
        return None
    return phrase


def _rank_term_counts(counter: Counter[str], limit: int) -> list[dict[str, int]]:
    if limit == 0:
        return []
    ranked: list[dict[str, int]] = []
    for term, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]:
        ranked.append({"term": term, "count": count})
    return ranked


def _rank_counter(counter: Counter[str], limit: int) -> list[str]:
    if limit == 0:
        return []
    return [item for item, _ in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]]
