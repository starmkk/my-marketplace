#!/usr/bin/env python3
"""port-metrics 리포트 생성기 CLI(파일 I/O 전담).

종료 코드: 0 = 판정 대상 ≥ 1 건 ∧ 전부 pass 또는 사전 등록 예상 fail /
1 = 예상 밖 fail·invalid·not_established 또는 판정 대상 0 건 / 2 = 형식 오류 / 3 = 예외.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

from port_metrics import render, schema
from port_metrics.catalog import Catalog, load_catalog
from port_metrics.report import ReportModel, build_report
from port_metrics.schema import FormatError

SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = SKILL_ROOT / "assets" / "catalog.json"
CATALOG_MD_PATH = SKILL_ROOT / "references" / "metric-catalog.md"
# 동결 파일 기본 위치(프로젝트 루트 = 실행 cwd 기준). 이 위치를 쓰면 프로젝트별 포인터가 필요 없음
DEFAULT_THRESHOLDS = Path("experiments") / "port-metrics" / "thresholds.json"

Obj = dict[str, Any]


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise FormatError(f"{path}: 입력 파일을 읽지 못함({exc})") from exc


def _decode(raw: bytes, path: Path) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FormatError(f"{path}: UTF-8 이 아님({exc})") from exc


def _catalog() -> Catalog:
    try:
        return load_catalog(CATALOG_PATH)
    except (OSError, ValueError) as exc:
        raise FormatError(f"{CATALOG_PATH}: {exc}") from exc


def _fail_if(problems: list[str], path: Path) -> None:
    if problems:
        shown = "\n  ".join(problems[:50])
        raise FormatError(f"{path}: 형식 오류 {len(problems)} 건\n  {shown}")


def load_thresholds(path: Path, catalog: Catalog) -> tuple[Obj, str]:
    """thresholds.json 적재·검증. (객체, 파일 바이트 sha256) 반환."""
    raw = _read_bytes(path)
    obj = schema.parse_json(_decode(raw, path))
    _fail_if(schema.validate_thresholds(obj, catalog), path)
    assert isinstance(obj, dict)
    return obj, hashlib.sha256(raw).hexdigest()


def load_rows(path: Path) -> list[Obj]:
    """jsonl 원자료 행 적재(빈 줄 무시, NaN 거부)."""
    rows: list[Obj] = []
    text = _decode(_read_bytes(path), path)
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = schema.parse_json(line)
        except FormatError as exc:
            raise FormatError(f"{path}:{number}: {exc}") from exc
        if not isinstance(row, dict):
            raise FormatError(f"{path}:{number}: 행은 객체여야 함")
        rows.append(row)
    return rows


def load_model(
    results_path: Path, thresholds_path: Path, partial: list[str] | None
) -> ReportModel:
    """results·thresholds 를 읽어 리포트 모델 생성(형식 오류는 FormatError)."""
    catalog = _catalog()
    thresholds, sha = load_thresholds(thresholds_path, catalog)
    results = schema.parse_json(_decode(_read_bytes(results_path), results_path))
    problems = schema.validate_results(results, catalog, thresholds["scope"], partial)
    _fail_if(problems, results_path)
    assert isinstance(results, dict)
    base = results_path.parent

    def rows_of(relative: str) -> list[Obj]:
        return load_rows(base / relative)

    model = build_report(results, thresholds, sha, catalog, rows_of, partial)
    return dataclasses.replace(model, thresholds_path=str(thresholds_path.resolve()))


def _emit(text: str, output: str | None) -> None:
    if output is None or output == "-":
        sys.stdout.write(text)
    else:
        Path(output).write_text(text, encoding="utf-8")


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _git_ignored(path: Path) -> bool:
    """path 가 git 저장소 안에서 .gitignore 대상인지(저장소 밖·git 없음 = False)."""
    target = path.resolve()
    try:
        done = subprocess.run(
            ["git", "check-ignore", "-q", str(target)],
            cwd=target.parent,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return done.returncode == 0


def _thresholds_path(arg: str | None) -> Path:
    """--thresholds 인자 또는 기본 위치."""
    path = DEFAULT_THRESHOLDS if arg is None else Path(arg)
    if arg is None and not path.is_file():
        raise FormatError(
            f"{path.resolve()}: 기본 위치에 동결 파일 없음 — 프로젝트 루트에서 실행하거나 "
            "init-thresholds 로 만들거나 --thresholds 로 지정"
        )
    return path


def _note_thresholds(path: Path, sha: str) -> None:
    """사용한 동결 파일(절대 경로·sha)을 stderr 에 알림 — 엉뚱한 파일 사용을 드러냄."""
    sys.stderr.write(f"임계 파일: {path.resolve()} (sha256 {sha[:12]})\n")


def cmd_init_thresholds(args: argparse.Namespace) -> int:
    """scope 로 카탈로그 기본 규칙을 펼친 미동결 thresholds.json 생성.

    기본 출력 = DEFAULT_THRESHOLDS, `-o -` = stdout. 기존 파일은 --force 없이 덮어쓰지 않음.
    """
    catalog = _catalog()
    scope: Obj = {
        "stages": _split(args.stages),
        "purposes": _split(args.purposes),
        "model_types": _split(args.model_types),
        "input_kind": args.input_kind,
    }
    probe: Obj = dict(schema.default_thresholds(catalog, scope), scope=scope)
    _fail_if(schema.validate_thresholds(probe, catalog), Path("<scope 인자>"))
    thresholds = schema.default_thresholds(catalog, scope)
    text = json.dumps(thresholds, ensure_ascii=False, indent=2) + "\n"
    if args.output == "-":
        sys.stdout.write(text)
        return 0
    out = DEFAULT_THRESHOLDS if args.output is None else Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.force and out.exists():
        # 번호를 늘려 보관 — 재동결을 반복해도 이전 판본을 덮어쓰지 않음
        number = 1
        while out.with_name(f"{out.name}.{number}.bak").exists():
            number += 1
        backup = out.with_name(f"{out.name}.{number}.bak")
        out.replace(backup)
        sys.stderr.write(f"이전 동결 파일 보관: {backup.resolve()}\n")
    try:
        with out.open("x", encoding="utf-8") as handle:
            handle.write(text)
    except FileExistsError as exc:
        raise FormatError(
            f"{out.resolve()}: 동결 파일이 이미 있어 덮어쓰지 않음 — 기존 파일을 쓰거나, "
            "재동결이면 사용자 승인 후 --force(이전 회차는 sha 불일치로 invalid, "
            "이전 판본은 .bak·git 이력에 남음)"
        ) from exc
    sys.stderr.write(
        f"생성: {out.resolve()} — limit null 채우기·frozen_at 기록 후 커밋\n"
    )
    if _git_ignored(out):
        sys.stderr.write(
            f"경고: {out.resolve()} 는 .gitignore 대상 — 커밋되지 않으면 동결 근거가 남지 않음"
            "(.gitignore 예외 추가 또는 -o 로 추적 경로 지정)\n"
        )
    return 0


def cmd_checklist(args: argparse.Namespace) -> int:
    """thresholds scope 기준 측정 체크리스트 출력."""
    catalog = _catalog()
    path = _thresholds_path(args.thresholds)
    thresholds, sha = load_thresholds(path, catalog)
    _note_thresholds(path, sha)
    _emit(render.render_checklist(catalog, thresholds), args.output)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """리포트 생성. 종료 코드 = 판정 결과."""
    partial = None if args.partial is None else _split(args.partial)
    thresholds_path = _thresholds_path(args.thresholds)
    model = load_model(Path(args.results), thresholds_path, partial)
    _note_thresholds(thresholds_path, model.thresholds_sha)
    _emit(render.render_report(model), args.output)
    return model.exit_code


def cmd_catalog_md(args: argparse.Namespace) -> int:
    """metric-catalog.md 생성 구간 출력(--write 면 문서 갱신)."""
    table = render.render_catalog_table(_catalog())
    if not args.write:
        sys.stdout.write(table)
        return 0
    text = _decode(_read_bytes(CATALOG_MD_PATH), CATALOG_MD_PATH)
    try:
        updated = render.replace_generated(text, table)
    except ValueError as exc:
        raise FormatError(f"{CATALOG_MD_PATH}: {exc}") from exc
    if updated != text:
        CATALOG_MD_PATH.write_text(updated, encoding="utf-8")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """CLI 인자 정의."""
    parser = argparse.ArgumentParser(description="port-metrics 리포트 생성기")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-thresholds", help="미동결 thresholds.json 생성")
    init.add_argument("--stages", required=True, help="예: S1,S2,S3,S4,S5")
    init.add_argument("--purposes", default="", help="convert,regress,optimize,ship")
    init.add_argument("--model-types", default="", help="streaming,llm,classifier")
    init.add_argument("--input-kind", required=True, choices=("audio", "other"))
    init.add_argument(
        "-o", "--output", default=None, help=f"기본 {DEFAULT_THRESHOLDS}, '-' = stdout"
    )
    init.add_argument(
        "--force",
        action="store_true",
        help="기존 동결 파일 덮어쓰기(재동결, 사용자 승인 후)",
    )
    init.set_defaults(func=cmd_init_thresholds)

    thresholds_help = f"동결 파일(기본 {DEFAULT_THRESHOLDS})"
    checklist = sub.add_parser("checklist", help="측정 전 체크리스트")
    checklist.add_argument("--thresholds", default=None, help=thresholds_help)
    checklist.add_argument("-o", "--output", default=None)
    checklist.set_defaults(func=cmd_checklist)

    report = sub.add_parser("report", help="리포트 생성")
    report.add_argument("results")
    report.add_argument("--thresholds", default=None, help=thresholds_help)
    report.add_argument("--partial", default=None, help="필수 검사 축소: S1,S2")
    report.add_argument("-o", "--output", default=None)
    report.set_defaults(func=cmd_report)

    catalog_md = sub.add_parser("catalog-md", help="카탈로그 생성 표")
    catalog_md.add_argument("--write", action="store_true")
    catalog_md.set_defaults(func=cmd_catalog_md)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점. 종료 코드 반환."""
    args = build_parser().parse_args(argv)
    try:
        code: int = args.func(args)
        return code
    except FormatError as exc:
        sys.stderr.write(f"형식 오류: {exc}\n")
        return 2
    except Exception:  # 예상 밖 예외는 종료 코드 3 으로 구분
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
