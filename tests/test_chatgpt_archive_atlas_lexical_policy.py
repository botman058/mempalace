from __future__ import annotations

import dataclasses
import json

import pytest

policy = pytest.importorskip("mempalace.chatgpt_archive_atlas_lexical_policy")


def test_public_api_contract_and_lexical_evidence_shape():
    assert isinstance(policy.POLICY_VERSION, str)
    assert policy.POLICY_VERSION

    evidence = policy.extract_lexical_evidence("mempalace atlas lexical policy")
    assert isinstance(evidence, policy.LexicalEvidence)
    assert dataclasses.is_dataclass(evidence)

    expected_fields = (
        "top_terms",
        "keyphrases",
        "domains",
        "paths",
        "commands",
        "package_names",
        "model_names",
        "legal_citations",
        "capitalized_phrases",
        "noise_terms_rejected",
    )
    assert tuple(field.name for field in dataclasses.fields(policy.LexicalEvidence)) == expected_fields

    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence.top_terms = ()


def test_stopwords_rejected_and_meaningful_terms_preserved():
    text = (
        "the and you for the and you for "
        "mempalace mempalace mempalace "
        "atlas atlas atlas "
        "thread thread thread "
        "evidence evidence evidence"
    )
    evidence = policy.extract_lexical_evidence(text)

    top_term_names = {item["term"] for item in evidence.top_terms}
    assert {"the", "and", "you", "for"}.isdisjoint(top_term_names)
    assert {"the", "and", "you", "for"}.issubset(set(evidence.noise_terms_rejected))
    assert "mempalace" in top_term_names
    assert "atlas" in top_term_names


def test_extracts_commands_paths_domains_and_named_categories():
    text = (
        "Run sudo systemctl restart ssh and then tail -n 80 /var/log/auth.log. "
        "Open /etc/ssh/sshd_config and inspect /home/u4/repos/mempalace/README.md. "
        "Check https://docs.python.org/3/library/dataclasses.html and https://openai.com/research. "
        "Install pydantic and httpx. Model gpt-4.1-mini and llama-3.1-8b are compared. "
        "Reference 17 USC 512 and Brown v. Board of Education. "
        "Escalate this to Federal Rule of Civil Procedure and New York Times."
    )
    evidence = policy.extract_lexical_evidence(text)

    assert "sudo systemctl restart ssh" in evidence.commands
    assert "tail -n 80 /var/log/auth.log" in evidence.commands
    assert "/var/log/auth.log" in evidence.paths
    assert "/etc/ssh/sshd_config" in evidence.paths
    assert "docs.python.org" in evidence.domains
    assert "openai.com" in evidence.domains
    assert "pydantic" in evidence.package_names
    assert "httpx" in evidence.package_names
    assert "gpt-4.1-mini" in evidence.model_names
    assert "llama-3.1-8b" in evidence.model_names
    assert any("17 usc 512" in item.lower() for item in evidence.legal_citations)
    assert any("brown v. board of education" in item.lower() for item in evidence.legal_citations)
    assert any("federal rule of civil procedure" in item.lower() for item in evidence.capitalized_phrases)
    assert any("new york times" in item.lower() for item in evidence.capitalized_phrases)


def test_accepts_string_or_iterable_and_is_deterministic_and_bounded():
    text = " ".join(["mempalace atlas lexical evidence"] * 100)
    evidence_from_str = policy.extract_lexical_evidence(text, max_terms=5, max_items_per_kind=3)
    evidence_from_iterable = policy.extract_lexical_evidence([text], max_terms=5, max_items_per_kind=3)
    second_run = policy.extract_lexical_evidence(text, max_terms=5, max_items_per_kind=3)

    assert evidence_from_str == second_run
    assert evidence_from_str == evidence_from_iterable
    assert len(evidence_from_str.top_terms) <= 5
    assert len(evidence_from_str.keyphrases) <= 3
    assert len(evidence_from_str.domains) <= 3
    assert len(evidence_from_str.paths) <= 3
    assert len(evidence_from_str.commands) <= 3
    assert len(evidence_from_str.package_names) <= 3
    assert len(evidence_from_str.model_names) <= 3
    assert len(evidence_from_str.legal_citations) <= 3
    assert len(evidence_from_str.capitalized_phrases) <= 3
    assert len(evidence_from_str.noise_terms_rejected) <= 3


def test_dataclass_contents_are_json_safe():
    text = (
        "sudo systemctl restart ssh "
        "tail -n 80 /var/log/auth.log "
        "https://docs.python.org "
        "gpt-4.1-mini 17 USC 512 New York Times"
    )
    evidence = policy.extract_lexical_evidence(text, max_terms=10, max_items_per_kind=10)
    payload = dataclasses.asdict(evidence)
    encoded = json.dumps(payload, sort_keys=True)
    decoded = json.loads(encoded)

    assert isinstance(decoded, dict)
    assert set(decoded) == {
        "top_terms",
        "keyphrases",
        "domains",
        "paths",
        "commands",
        "package_names",
        "model_names",
        "legal_citations",
        "capitalized_phrases",
        "noise_terms_rejected",
    }
