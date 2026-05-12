from pathlib import Path
from unittest.mock import patch

import inspect
import json
import re
import shutil
import sys

import pytest

from mempalace import chatgpt_archive_atlas_contract as contract
from mempalace.chatgpt_archive_atlas_embedding_cache import ChatGPTAtlasEmbeddingCacheResult

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "systemd" / "start_chatgpt_archive_atlas_snow_white_iii.sh"
RUNNER_PATH = REPO_ROOT / "mempalace" / "chatgpt_archive_atlas_runner.py"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "chatgpt_archive_atlas"
CUDA_LIBRARY_PATH_SUFFIXES = (
  "nvidia/cublas/lib",
  "nvidia/cuda_cupti/lib",
  "nvidia/cuda_nvrtc/lib",
  "nvidia/cuda_runtime/lib",
  "nvidia/cudnn/lib",
)


def _script_text() -> str:
  return SCRIPT_PATH.read_text(encoding="utf-8")


def _runner_text() -> str:
  assert RUNNER_PATH.exists(), f"missing runner: {RUNNER_PATH}"
  return RUNNER_PATH.read_text(encoding="utf-8")


def _snapshot_files(root: Path) -> set[Path]:
  return {path for path in root.rglob("*") if path.is_file()}


def _seed_source_dir(tmp_path: Path) -> Path:
  source_dir = tmp_path / "source"
  copies = [
    ("single_dict_export.json", source_dir / "a" / "conversations.json"),
    ("list_export.json", source_dir / "b" / "conversations.json"),
  ]
  for fixture_name, destination in copies:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE_DIR / fixture_name, destination)
  return source_dir


def _import_runner():
  if not RUNNER_PATH.exists():
    pytest.skip("runner module is not present")
  return __import__("mempalace.chatgpt_archive_atlas_runner", fromlist=["*"])


class _FakeEmbeddingCache:
  def __init__(self) -> None:
    self.calls: list[dict[str, object]] = []

  def __call__(self, *args, **kwargs) -> ChatGPTAtlasEmbeddingCacheResult:
    lexical_rows = args[0] if args else ()
    run_dir = kwargs.get("run_dir") or kwargs.get("run_root")
    if run_dir is None and len(args) >= 2:
      run_dir = args[1]
    if run_dir is None:
      raise AssertionError("embedding cache call missing run_dir")

    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = run_dir / contract.CANONICAL_ARTIFACT_PATHS["thread_embeddings"]
    vectors_path = run_dir / "thread_embedding_vectors.jsonl"
    metadata_path.write_text("", encoding="utf-8")
    vectors_path.write_text("", encoding="utf-8")
    self.calls.append(
      {
        "run_id": kwargs.get("run_id", "run"),
        "run_dir": str(run_dir),
        "rows": len(list(lexical_rows)),
      }
    )
    return ChatGPTAtlasEmbeddingCacheResult(
      metadata_rows=(),
      vector_rows=(),
      metadata_path=metadata_path,
      vectors_path=vectors_path,
      effective_device="cpu",
      embedded_count=0,
      skipped_count=0,
      source_errors=(),
    )


def _patch_fake_embedding_cache(monkeypatch, module) -> _FakeEmbeddingCache:
  fake = _FakeEmbeddingCache()
  import mempalace.chatgpt_archive_atlas_embedding_cache as embedding_cache_module

  monkeypatch.setattr(
    embedding_cache_module,
    "materialize_chatgpt_thread_embedding_cache",
    fake,
  )
  if hasattr(module, "materialize_chatgpt_thread_embedding_cache"):
    monkeypatch.setattr(module, "materialize_chatgpt_thread_embedding_cache", fake)
  return fake


def _normalize_exit_code(value) -> int:
  if value is None:
    return 0
  if isinstance(value, bool):
    return int(value)
  if isinstance(value, int):
    return value
  return int(value)


def _invoke_runner(
  module,
  *,
  source_dir: Path,
  run_root: Path,
  run_id: str,
  limit: int = 0,
) -> int:
  argv = [
    "--source-dir",
    str(source_dir),
    "--run-root",
    str(run_root),
    "--run-id",
    run_id,
  ]
  if limit:
    argv.extend(["--limit", str(limit)])

  if hasattr(module, "main"):
    try:
      signature = inspect.signature(module.main)
      if len(signature.parameters) == 0:
        with patch.object(sys, "argv", ["chatgpt_archive_atlas_runner", *argv]):
          return _normalize_exit_code(module.main())
      return _normalize_exit_code(module.main(argv))
    except SystemExit as exc:
      return _normalize_exit_code(exc.code)
    except TypeError:
      with patch.object(sys, "argv", ["chatgpt_archive_atlas_runner", *argv]):
        return _normalize_exit_code(module.main())
    except ValueError:
      return 1

  if hasattr(module, "run") and hasattr(module, "parse_args"):
    args = module.parse_args(argv)
    return _normalize_exit_code(module.run(args))

  pytest.fail("runner entrypoint contract is unsupported by this test helper")


def _line_has_run_id_validation(line: str) -> bool:
  if "RUN_ID" not in line or "if" not in line:
    return False
  if "$RUN_ID" not in line:
    return False
  if "if [[" not in line and "if [" not in line:
    return False
  return (
    'if [[ -z "$RUN_ID" ]]' in line
    or "=~" in line
    or "==" in line
  )


def _line_has_run_id_path_guard(line: str) -> bool:
  if "RUN_ID" not in line or "if" not in line or "if [[" not in line and "if [" not in line:
    return False
  if "=~" in line and re.search(r"\^[A-Za-z0-9_\\.\\-]+\\$", line) is not None:
    return True
  if "==" in line and "/*/" not in line:
    return (
      ("*" in line and "/../" in line)
      or ("*" in line and "/" in line and "/\"" in line)
      or ("*" in line and "*" in line and ".." in line)
    )
  return False


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
    if stripped.startswith("--"):
      args.append(stripped)
    elif stripped.startswith("${cmd") or stripped.startswith("--unit="):
      args.append(stripped)
    else:
      break
  return args


def _first_matching_index(lines: list[str], predicate) -> int:
  for index, line in enumerate(lines):
    if predicate(line):
      return index
  return -1


def _extract_cuda_path_block(lines: list[str], start_idx: int) -> list[str]:
  if start_idx < 0:
    return []
  depth = 0
  block = []
  for line in lines[start_idx:]:
    block.append(line)
    stripped = line.strip()
    if stripped.startswith("if") and "cuda_dirs" in line:
      depth += 1
    elif stripped == "fi" and depth:
      depth -= 1
      if depth == 0:
        break
  return block


def _find_cuda_guard_line_index(lines: list[str]) -> int:
  return next(
    i
    for i, line in enumerate(lines)
    if line.strip().startswith("if")
    and "cuda_dirs" in line
    and ("${#cuda_dirs[@]}" in line or "${#cuda_dirs}" in line)
  )


def test_runner_uses_canonical_defaults_and_run_root():
  text = _script_text()
  assert "/media/u0/OneDrive_Backup/mempalace" in text
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
  assert "--limit N" in text
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
  assert text.index("while (($#)); do") < text.index('if [[ -z "$UNIT" ]]; then')


def test_systemd_wrapper_refuses_run_id_traversal_inputs():
  text = _script_text()
  lines = text.splitlines()
  run_dir_index = next(
    i for i, line in enumerate(lines) if 'RUN_DIR="$RUN_ROOT/$RUN_ID"' in line
  )
  run_id_validation_index = next(
    i for i, line in enumerate(lines) if _line_has_run_id_validation(line)
  )
  assert run_id_validation_index < run_dir_index

  has_path_guard = any(_line_has_run_id_path_guard(line) for line in lines)
  assert has_path_guard


def test_systemd_wrapper_uses_narrow_readwrite_paths():
  text = _script_text()
  assert '--property=ReadWritePaths="$RUN_ROOT"' in text or '--property=ReadWritePaths="$RUN_DIR"' in text
  assert '--property=ReadWritePaths="$ROOT"' not in text


def test_systemd_wrapper_invokes_runner_as_module_not_file():
  text = _script_text()
  cmd_block = _script_cmd_block(text)
  assert any(part == "-m" for part in cmd_block)
  assert any("mempalace.chatgpt_archive_atlas_runner" in part for part in cmd_block)
  assert not any(part == '$SCRIPT' for part in cmd_block)
  assert not any(part == "$SCRIPT" for part in cmd_block)
  assert not any(part == '"$SCRIPT"' for part in cmd_block)


def test_systemd_wrapper_sets_cuda_library_paths_for_transient_run():
  text = _script_text()
  lines = text.splitlines()
  assert "site.getsitepackages()" in text
  assert "site_lib=" in text
  assert "cuda_dirs=()" in text
  assert "$VENV/bin/python" in text
  assert any("for dir in" in line for line in lines)

  systemd_args = _systemd_run_args(text)
  assert any(
    part.startswith("--setenv=LD_LIBRARY_PATH=") or "LD_LIBRARY_PATH" in part
    for part in systemd_args
  )
  for required in CUDA_LIBRARY_PATH_SUFFIXES:
    assert any(required in line for line in lines)
  assert any(
    line.strip().startswith("if")
    and "cuda_dirs" in line
    and ("${#cuda_dirs[@]}" in line or "${#cuda_dirs}" in line)
    for line in lines
  )
  assert any(
    'export LD_LIBRARY_PATH="${cuda_dirs[*]}"' in line
    or "LD_LIBRARY_PATH" in line and "cuda_dirs" in line
    for line in lines
  )


def test_systemd_wrapper_fails_closed_when_cuda_dirs_not_present_or_empty():
  text = _script_text()
  lines = text.splitlines()
  start = _find_cuda_guard_line_index(lines)
  cuda_block = _extract_cuda_path_block(lines, start)
  assert any(line.strip().startswith("else") for line in cuda_block), "missing else guard for empty cuda dir set"
  end_idx = next(i for i, line in enumerate(cuda_block) if line.strip() == "else")
  guard_block = cuda_block[end_idx + 1:]
  guard_text = "\n".join(guard_block).lower()
  assert "echo" in guard_text, "missing clear guard/telemetry when no cuda dirs found"
  assert ("exit" in guard_text or "unset ld_library_path" in guard_text), (
    "missing non-ambiguous fail-closed behavior when no cuda dirs are found"
  )


def test_systemd_wrapper_sudo_reexec_precedes_privileged_checks_and_cuda_discovery():
  text = _script_text()
  lines = text.splitlines()

  reexec_index = _first_matching_index(
    lines,
    lambda line: line.strip().startswith('if [[ "$EUID" -ne 0 ]]'),
  )
  assert reexec_index >= 0

  live_checks = [
    'if [[ ! -f "$SCRIPT" ]]',
    'if [[ ! -x "$VENV/bin/python" ]]',
    'if [[ ! -d "$SOURCE_DIR" ]]',
    'site_lib="$("$VENV/bin/python"',
    'if [[ -z "$ATLAS_LD_LIBRARY_PATH" ]]; then',
    "for dir in \\",
    'if ((${#cuda_dirs[@]})); then',
  ]

  first_privileged_or_cuda_index = min(
    idx
    for idx in (
      _first_matching_index(lines, lambda line, needle=needle: needle in line) for needle in live_checks
    )
    if idx >= 0
  )
  assert first_privileged_or_cuda_index > reexec_index

  cuda_guard_index = _find_cuda_guard_line_index(lines)
  assert cuda_guard_index > reexec_index


def test_runner_target_path_exists():
  assert RUNNER_PATH.exists(), f"missing runner target: {RUNNER_PATH}"


def test_runner_module_static_scan_has_no_external_service_or_chroma_writes():
  source = _runner_text().lower()
  assert re.search(r"\blocalai\b", source) is None
  assert re.search(r"\bopenai\b", source) is None
  assert re.search(r"\bmcp\b", source) is None
  assert re.search(r"\bchroma\b", source) is None
  assert re.search(r"\bchromadb\b", source) is None
  assert re.search(r"\brequests\b", source) is None
  assert re.search(r"\bhttpx\b", source) is None
  assert re.search(r"\bpalace_path\b", source) is None


def test_runner_unit_writes_expected_artifacts_under_requested_run_dir(tmp_path, monkeypatch):
  module = _import_runner()
  fake_cache = _patch_fake_embedding_cache(monkeypatch, module)
  source_dir = _seed_source_dir(tmp_path)
  run_root = tmp_path / "run_root"
  run_id = "safe-run-01"
  run_dir = run_root / run_id

  pre = _snapshot_files(tmp_path)
  rc = _invoke_runner(module, source_dir=source_dir, run_root=run_root, run_id=run_id, limit=3)
  post = _snapshot_files(tmp_path)
  assert rc == 0

  new_files = post - pre
  assert run_dir.exists()
  assert new_files
  assert all(str(path).startswith(str(run_dir)) for path in new_files)
  assert (run_dir / contract.CANONICAL_ARTIFACT_PATHS["progress"]).exists()
  assert (run_dir / contract.CANONICAL_ARTIFACT_PATHS["artifacts_index"]).exists()
  assert fake_cache.calls


def test_runner_writes_phase_artifacts_under_requested_run_dir(tmp_path, monkeypatch):
  module = _import_runner()
  fake_cache = _patch_fake_embedding_cache(monkeypatch, module)
  source_dir = _seed_source_dir(tmp_path)
  run_root = tmp_path / "run_root"
  run_id = "progressive"
  run_dir = run_root / run_id

  phase_events: list[tuple[str, str]] = []
  phase_file_snapshots: list[tuple[str, list[str]]] = []

  _orig_write_progress = module._write_progress

  def _spy_write_progress(**kwargs):
    phase = kwargs["phase"]
    status = kwargs["status"]
    phase_events.append((phase, status))
    result = _orig_write_progress(**kwargs)
    phase_file_snapshots.append((phase, sorted(path.name for path in _snapshot_files(kwargs["run_dir"]))))
    return result

  artifact_writes: list[Path] = []
  _orig_write_jsonl = module._write_jsonl
  _orig_write_text_atomic = module._write_text_atomic
  _orig_write_json_atomic = module._write_json_atomic

  def _spy_write_jsonl(path: Path, rows, validate_schema=None):
    artifact_writes.append(path)
    return _orig_write_jsonl(path, rows, validate_schema=validate_schema)

  def _spy_write_text_atomic(path: Path, content: str):
    artifact_writes.append(path)
    return _orig_write_text_atomic(path, content)

  def _spy_write_json_atomic(path: Path, payload):
    artifact_writes.append(path)
    return _orig_write_json_atomic(path, payload)

  monkeypatch.setattr(module, "_write_progress", _spy_write_progress)
  monkeypatch.setattr(module, "_write_jsonl", _spy_write_jsonl)
  monkeypatch.setattr(module, "_write_text_atomic", _spy_write_text_atomic)
  monkeypatch.setattr(module, "_write_json_atomic", _spy_write_json_atomic)

  pre = _snapshot_files(tmp_path)
  rc = _invoke_runner(module, source_dir=source_dir, run_root=run_root, run_id=run_id)
  post = _snapshot_files(tmp_path)
  assert rc == 0
  assert fake_cache.calls
  assert phase_events[0] == ("source_inventory", "running")
  assert phase_events[-1] == ("complete", "complete")

  run_dir_files = [path for path in post - pre if str(path).startswith(str(run_dir))]
  assert run_dir_files
  assert all(str(path).startswith(str(run_dir)) for path in run_dir_files)
  assert artifact_writes and all(str(path).startswith(str(run_dir)) for path in artifact_writes)
  assert any(path.name == contract.CANONICAL_ARTIFACT_PATHS["progress"] for path in run_dir_files)
  assert all(str(path).startswith(str(run_dir)) for path in (run_dir / contract.CANONICAL_ARTIFACT_PATHS["progress"], run_dir / contract.CANONICAL_ARTIFACT_PATHS["artifacts_index"]))
  assert any(phase == "source_inventory" for phase, _ in phase_events)
  assert any(phase == "complete" for phase, _ in phase_events)
  assert contract.CANONICAL_ARTIFACT_PATHS["progress"] in phase_file_snapshots[0][1]
  assert contract.CANONICAL_ARTIFACT_PATHS["artifacts_index"] in phase_file_snapshots[-1][1]


def test_runner_does_not_rewrite_embedding_artifacts_after_cache_materialization(tmp_path, monkeypatch):
  module = _import_runner()
  source_dir = _seed_source_dir(tmp_path)
  run_root = tmp_path / "run_root"
  run_id = "cached-materialized"
  run_dir = run_root / run_id

  class _MaterializedCacheNoRewrite:
    def __init__(self) -> None:
      self.calls: list[dict[str, object]] = []

    def __call__(self, rows, run_dir_arg, **kwargs) -> ChatGPTAtlasEmbeddingCacheResult:
      run_dir_path = Path(run_dir_arg)
      metadata_path = run_dir_path / contract.CANONICAL_ARTIFACT_PATHS["thread_embeddings"]
      vectors_path = run_dir_path / "thread_embedding_vectors.jsonl"
      metadata_path.parent.mkdir(parents=True, exist_ok=True)
      metadata_path.write_text("materialized metadata\n", encoding="utf-8")
      vectors_path.write_text("materialized vectors\n", encoding="utf-8")
      self.calls.append(
        {"run_dir": str(run_dir_path), "rows": len(rows), "run_id": kwargs.get("run_id")}
      )
      return ChatGPTAtlasEmbeddingCacheResult(
        metadata_rows=(),
        vector_rows=(),
        metadata_path=metadata_path,
        vectors_path=vectors_path,
        effective_device="cpu",
        embedded_count=len(rows),
        skipped_count=0,
        source_errors=(),
      )

  materialized_cache = _MaterializedCacheNoRewrite()
  import mempalace.chatgpt_archive_atlas_embedding_cache as embedding_cache_module

  monkeypatch.setattr(
    embedding_cache_module,
    "materialize_chatgpt_thread_embedding_cache",
    materialized_cache,
  )
  if hasattr(module, "materialize_chatgpt_thread_embedding_cache"):
    monkeypatch.setattr(module, "materialize_chatgpt_thread_embedding_cache", materialized_cache)

  write_calls: list[Path] = []
  _orig_write_jsonl = module._write_jsonl
  _orig_write_text_atomic = module._write_text_atomic
  _orig_write_json_atomic = module._write_json_atomic

  def _spy_write_jsonl(path: Path, rows, validate_schema=None):
    write_calls.append(path)
    return _orig_write_jsonl(path, rows, validate_schema=validate_schema)

  def _spy_write_text_atomic(path: Path, content: str):
    write_calls.append(path)
    return _orig_write_text_atomic(path, content)

  def _spy_write_json_atomic(path: Path, payload):
    write_calls.append(path)
    return _orig_write_json_atomic(path, payload)

  monkeypatch.setattr(module, "_write_jsonl", _spy_write_jsonl)
  monkeypatch.setattr(module, "_write_text_atomic", _spy_write_text_atomic)
  monkeypatch.setattr(module, "_write_json_atomic", _spy_write_json_atomic)

  rc = _invoke_runner(module, source_dir=source_dir, run_root=run_root, run_id=run_id, limit=2)

  assert rc == 0
  assert materialized_cache.calls
  assert (run_dir / contract.CANONICAL_ARTIFACT_PATHS["thread_embeddings"]).exists()
  assert (run_dir / "thread_embedding_vectors.jsonl").exists()
  assert (run_dir / contract.CANONICAL_ARTIFACT_PATHS["thread_embeddings"]).read_text(encoding="utf-8") == "materialized metadata\n"
  assert (run_dir / "thread_embedding_vectors.jsonl").read_text(encoding="utf-8") == "materialized vectors\n"
  assert contract.CANONICAL_ARTIFACT_PATHS["thread_embeddings"] not in {path.name for path in write_calls}
  assert "thread_embedding_vectors.jsonl" not in {path.name for path in write_calls}


def test_runner_failure_after_run_dir_creation_records_failure_progress(tmp_path, monkeypatch):
  module = _import_runner()
  fake_cache = _patch_fake_embedding_cache(monkeypatch, module)
  source_dir = _seed_source_dir(tmp_path)
  run_root = tmp_path / "run_root"
  run_id = "fail-after-run-dir"
  run_dir = run_root / run_id

  def _fail_topic_clusters(*_args, **_kwargs):
    raise RuntimeError("forced topic failure for failure-path coverage")

  monkeypatch.setattr(module, "build_chatgpt_topic_clusters", _fail_topic_clusters)

  progress_events: list[tuple[str, str]] = []
  _orig_write_progress = module._write_progress

  def _spy_write_progress(**kwargs):
    progress_events.append((kwargs["phase"], kwargs["status"]))
    return _orig_write_progress(**kwargs)

  monkeypatch.setattr(module, "_write_progress", _spy_write_progress)

  pre = _snapshot_files(tmp_path)
  try:
    rc = _invoke_runner(module, source_dir=source_dir, run_root=run_root, run_id=run_id, limit=1)
  except RuntimeError:
    rc = 1
  assert rc != 0

  post = _snapshot_files(tmp_path)
  new_files = post - pre
  assert new_files
  assert all(str(path).startswith(str(run_root.resolve())) for path in new_files)
  assert run_dir.exists()
  assert fake_cache.calls
  assert progress_events
  progress_path = run_dir / contract.CANONICAL_ARTIFACT_PATHS["progress"]
  assert progress_path.exists()
  progress_row = json.loads(progress_path.read_text(encoding="utf-8"))
  assert progress_row["status"] == "failed"
  assert progress_row["phase"] in {"source_inventory", "topic_clustering", "summary", "artifacts_index", "complete", "failed"}


def test_runner_rejects_path_traversal_run_id(tmp_path, monkeypatch):
  module = _import_runner()
  fake_cache = _patch_fake_embedding_cache(monkeypatch, module)
  source_dir = _seed_source_dir(tmp_path)
  run_root = tmp_path / "run_root"
  run_id = "../outside"
  run_dir = (run_root / run_id).resolve()
  pre = _snapshot_files(tmp_path)

  rc = _invoke_runner(module, source_dir=source_dir, run_root=run_root, run_id=run_id, limit=1)
  assert rc != 0

  post = _snapshot_files(tmp_path)
  new_files = post - pre
  run_root_prefix = str(run_root.resolve())
  run_root_files = [path for path in new_files if str(path).startswith(run_root_prefix)]
  outside_run_root = [path for path in new_files if not str(path).startswith(run_root_prefix)]
  assert not outside_run_root
  assert not run_dir.exists()
  assert not run_root_files
  assert not fake_cache.calls
