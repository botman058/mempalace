from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "systemd" / "start_chatgpt_archive_atlas_snow_white_iii.sh"


def _script_text() -> str:
  return SCRIPT_PATH.read_text(encoding="utf-8")


def test_runner_uses_canonical_defaults_and_run_root():
  text = _script_text()
  assert '/media/u0/OneDrive_Backup/mempalace' in text
  assert 'SOURCE_DIR="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_SOURCE_DIR:-$ROOT/sources/chatgpt}"' in text
  assert 'RUN_ROOT="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ROOT:-$ROOT/data/chatgpt_archive_atlas}"' in text
  assert '--run-root "$RUN_ROOT"' in text
  assert '--run-id "$RUN_ID"' in text


def test_runner_has_path_guard_and_service_user_with_resource_caps():
  text = _script_text()
  assert "/media/u0/Extreme\\ SSD" in text
  assert "--property=User=mempalace" in text
  assert "--property=Group=mempalace" in text
  assert "--property=CPUQuota=200%" in text
  assert "--property=MemoryMax=16G" in text
  assert "--setenv=MEMPALACE_EMBEDDING_DEVICE=cuda" in text


def test_runner_supports_limit_and_has_no_localai_mcp_publish_surface():
  text = _script_text()
  assert '--limit N' in text
  assert 'cmd+=(--limit "$LIMIT")' in text
  assert "LOCALAI_BASE_URL" not in text
  assert "LOCALAI_TOKEN_FILE" not in text
  assert "--localai" not in text
  assert "--mcp" not in text
  assert "--publish" not in text


def test_runner_computes_default_unit_after_run_id_parse():
  text = _script_text()
  assert 'UNIT="${MEMPALACE_CHATGPT_ARCHIVE_ATLAS_UNIT:-}"' in text
  assert 'if [[ -z "$UNIT" ]]; then' in text
  assert 'UNIT="${UNIT_BASE}-${RUN_ID}"' in text
  assert 'MEMPALACE_CHATGPT_ARCHIVE_ATLAS_RUN_ID="$RUN_ID"' in text
  assert 'MEMPALACE_CHATGPT_ARCHIVE_ATLAS_UNIT="$UNIT"' in text
  assert text.index('while (($#)); do') < text.index('if [[ -z "$UNIT" ]]; then')
