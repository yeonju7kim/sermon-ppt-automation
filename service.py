"""CLI/GUI 공용 파이프라인 서비스 함수."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

__version__ = "1.0.0"

from extractor import Reference, extract_from_file, extract_from_text
from fetcher import default_fetcher
from ppt_builder import PassageVerses, build_presentation


@dataclass
class PipelineResult:
    refs: list[Reference]
    main_ref: Reference | None
    output_path: Path


def app_base_dir() -> Path:
    """런타임 리소스 기준 경로. PyInstaller 번들 / 일반 실행 모두 대응."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).parent


def default_cache_path() -> Path:
    """사용자 머신 로컬에 캐시 저장. Windows는 LOCALAPPDATA, 그 외는 ~/.cache."""
    if os.name == "nt":
        root = Path(os.getenv("LOCALAPPDATA") or Path.home())
    else:
        root = Path(os.getenv("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    d = root / "SermonPPT"
    d.mkdir(parents=True, exist_ok=True)
    return d / "bible_cache.db"


def default_template_path() -> Path:
    return app_base_dir() / "sermon_template.pptx"


def resolve_main_ref(main_passage: str | None, refs: list[Reference]) -> Reference | None:
    if not refs:
        return None
    if not main_passage or not main_passage.strip():
        return refs[0]
    parsed = extract_from_text(main_passage)
    if not parsed:
        raise ValueError(f"--main-passage 파싱 실패: {main_passage!r}")
    return parsed[0]


def build_ppt(
    manuscript_path: str | Path,
    output_path: str | Path,
    template_path: str | Path | None = None,
    title_en: str | None = None,
    title_ko: str | None = None,
    main_passage: str | None = None,
    cache_path: str | Path | None = None,
    log: Callable[[str], None] = print,
    progress: Callable[[int, int], None] | None = None,
) -> PipelineResult:
    """원고에서 인용 추출 → NIV+개역개정 조회 → PPT 생성. 전체 파이프라인."""
    manuscript_path = Path(manuscript_path)
    output_path = Path(output_path)
    template_path = Path(template_path) if template_path else default_template_path()
    cache_path = Path(cache_path) if cache_path else default_cache_path()

    if not manuscript_path.exists():
        raise FileNotFoundError(f"원고 파일을 찾을 수 없음: {manuscript_path}")
    if not template_path.exists():
        raise FileNotFoundError(f"템플릿 PPT를 찾을 수 없음: {template_path}")

    log(f"[추출] 원고: {manuscript_path.name}")
    refs = extract_from_file(manuscript_path)
    if not refs:
        raise RuntimeError("원고에서 성구 인용을 찾지 못했습니다.")
    log(f"[추출] {len(refs)}개 인용:")
    for r in refs:
        log(f"  - {r.header_en}  |  {r.header_ko}")

    has_title = bool((title_en or "").strip() or (title_ko or "").strip())
    main_ref = resolve_main_ref(main_passage, refs) if has_title else None
    if has_title and main_ref is not None:
        log(f"[본문] 타이틀 슬라이드 본문: {main_ref.header_en} ({main_ref.header_ko})")
    else:
        log("[본문] 타이틀 슬라이드 생략")

    fetcher = default_fetcher(cache_path)
    passages: list[PassageVerses] = []
    total = len(refs)
    for i, ref in enumerate(refs, 1):
        if progress is not None:
            progress(i - 1, total)
        log(f"[조회 {i}/{total}] {ref.header_en} ...")
        en = fetcher.get_niv(ref)
        ko = fetcher.get_korean(ref)
        log(f"           NIV {len(en)}절 / 개역개정 {len(ko)}절")
        passages.append(PassageVerses(ref=ref, en=en, ko=ko))
    if progress is not None:
        progress(total, total)

    log(f"[빌드] {output_path.name}")
    build_presentation(
        template_path=template_path,
        output_path=output_path,
        title_en=title_en if has_title else None,
        title_ko=title_ko if has_title else None,
        main_ref=main_ref,
        passages=passages,
    )
    log(f"[완료] {output_path}")
    return PipelineResult(refs=refs, main_ref=main_ref, output_path=output_path)
