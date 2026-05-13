from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT / "scripts" / "systemd" / "start_chatgpt_atlas_guided_extraction_snow_white_iii.sh"
)


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def _script_cmd_block(text: str) -> list[str]:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "cmd=(")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == ")")
    return [line.strip() for line in lines[start + 1 : end]]


def _systemd_run_args(text: str) -> list[str]:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "systemd-run \\")
    args: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            break
        if stripped.startswith("--") or stripped.startswith('"${cmd[@]}"'):
            args.append(stripped)
        else:
            break
    return args


def test_wrapper_uses_canonical_defaults() -> None:
    text = _script_text()
    assert 'CANONICAL_ROOT="/media/u0/OneDrive_Backup/mempalace"' in text
    assert 'CANONICAL_LOCALAI_BASE_URL="http://snow-white-iii:8080/v1"' in text
    assert (
        'CANONICAL_ATLAS_RUN_DIR="$CANONICAL_ROOT/data/chatgpt_archive_atlas/atlas_full2_20260512T0412Z_2fc8ac5"'
        in text
    )
    assert 'SOURCE_DIR="${MEMPALACE_CHATGPT_ATLAS_GUIDED_SOURCE_DIR:-$ROOT/sources/chatgpt}"' in text
    assert 'RUN_ROOT="${MEMPALACE_CHATGPT_ATLAS_GUIDED_RUN_ROOT:-$ROOT/data/atlas_guided_chatgpt_signals}"' in text
    assert 'LOCALAI_TOKEN_FILE="${MEMPALACE_CHATGPT_ATLAS_GUIDED_LOCALAI_TOKEN_FILE:-$ROOT/secrets/localai_token}"' in text


def test_wrapper_has_expected_cli_surface_and_never_passes_publish() -> None:
    text = _script_text()
    cmd_block = _script_cmd_block(text)
    systemd_args = _systemd_run_args(text)
    assert "--atlas-guided" in text
    assert "--atlas-run-dir PATH" in text
    assert "--candidate-records PATH" in text
    assert "--run-id ID" in text
    assert "--run-dir PATH" in text
    assert "--limit N" in text
    assert "--retry-errors" in text
    assert "--provider-max-attempts N" in text
    assert any(part == "--atlas-guided" for part in cmd_block)
    assert any(part == '--atlas-run-dir "$ATLAS_RUN_DIR"' for part in cmd_block)
    assert any(part == '--candidate-records "$CANDIDATE_RECORDS"' for part in cmd_block)
    assert any(part == '--localai-base-url "$LOCALAI_BASE_URL"' for part in cmd_block)
    assert any(part == '--localai-token-file "$LOCALAI_TOKEN_FILE"' for part in cmd_block)
    assert any(part == '--provider-max-attempts "$PROVIDER_MAX_ATTEMPTS"' for part in cmd_block)
    assert not any("--publish" in part for part in cmd_block)
    assert not any("--publish" in part for part in systemd_args)
    assert "--mempalace-url" not in text
    assert "--mempalace-token" not in text


def test_wrapper_has_host_path_and_run_id_guards() -> None:
    text = _script_text()
    assert "MEMPALACE_INSTALL_ALLOW_OTHER_HOST" in text
    assert "/media/u0/Extreme\\ SSD" in text
    assert 'if [[ -n "$RUN_DIR_ARG" && -n "$RUN_ID" ]]; then' in text
    assert 'if [[ "$RUN_ID" == "." || "$RUN_ID" == ".." || "$RUN_ID" == *"/"* || "$RUN_ID" == *"\\\\"* ]]; then' in text
    assert 'if [[ ! "$RUN_ID" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$ ]]; then' in text
    assert 'RUN_DIR="$RUN_ROOT/$RUN_ID"' in text
    assert 'require_within "guided run directory" "$RUN_ROOT" "$RUN_DIR"' in text
    assert 'require_within "atlas run directory" "$ATLAS_RUN_ROOT" "$ATLAS_RUN_DIR"' in text
    assert 'require_within "candidate records" "$ATLAS_RUN_DIR" "$CANDIDATE_RECORDS"' in text


def test_wrapper_enforces_localai_and_canonical_token_path() -> None:
    text = _script_text()
    for blocked in (
        "api.openai.com",
        "anthropic.com",
        "openrouter.ai",
        "together.xyz",
        "groq.com",
        "generativelanguage.googleapis.com",
        "vertexai.googleapis.com",
    ):
        assert blocked in text
    assert 'if [[ "$normalized" != "$CANONICAL_LOCALAI_BASE_URL" ]]; then' in text
    assert 'CANONICAL_LOCALAI_TOKEN_FILE="$(realpath -m "$ROOT/secrets/localai_token")"' in text
    assert 'if [[ "$LOCALAI_TOKEN_FILE_RESOLVED" != "$CANONICAL_LOCALAI_TOKEN_FILE" ]]; then' in text


def test_wrapper_uses_transient_service_user_resource_caps_and_narrow_write_path() -> None:
    text = _script_text()
    assert "--property=User=mempalace" in text
    assert "--property=Group=mempalace" in text
    assert "--property=MemoryMax=16G" in text
    assert "--property=CPUQuota=200%" in text
    assert '--property=ReadWritePaths="$RUN_DIR"' in text
    assert '--property=ReadWritePaths="$ROOT"' not in text
    assert '--setenv=LOCALAI_THREAD_SIGNAL_ATLAS_GUIDED=1' in text


def test_wrapper_checks_expected_atlas_input_artifacts_before_start() -> None:
    text = _script_text()
    assert 'ATLAS_THREAD_CANDIDATES="$ATLAS_RUN_DIR/atlas_thread_candidates.jsonl"' in text
    assert 'ATLAS_COVERAGE_REPORT="$ATLAS_RUN_DIR/atlas_candidate_coverage.json"' in text
    assert 'ATLAS_THREAD_INDEX="$ATLAS_RUN_DIR/thread_index.jsonl"' in text
    assert 'if [[ ! -f "$CANDIDATE_RECORDS" ]]; then' in text
    assert 'if [[ ! -f "$ATLAS_THREAD_CANDIDATES" ]]; then' in text
    assert 'if [[ ! -f "$ATLAS_COVERAGE_REPORT" ]]; then' in text
    assert 'if [[ ! -f "$ATLAS_THREAD_INDEX" ]]; then' in text
