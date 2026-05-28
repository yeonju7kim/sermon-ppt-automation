"""CLI 진입점. 코어 로직은 service.build_ppt()."""
from __future__ import annotations

import argparse

from service import build_ppt, default_template_path, default_cache_path


def parse_args():
    p = argparse.ArgumentParser(description="설교 PPT 자동 생성")
    p.add_argument("--manuscript", "-m", required=True, help="설교 원고 (.txt / .docx)")
    p.add_argument("--template", "-t", default=None,
                   help=f"템플릿 PPT (기본: {default_template_path()})")
    p.add_argument("--output", "-o", required=True, help="결과 PPT 출력 경로")
    p.add_argument("--title-en", default=None,
                   help="영문 제목. --title-en/--title-ko 둘 다 생략하면 타이틀 슬라이드 자체를 빼고 verse 슬라이드부터 시작")
    p.add_argument("--title-ko", default=None, help="한글 제목")
    p.add_argument("--main-passage", default=None,
                   help="타이틀 슬라이드에 표시할 본문 (예: 'Habakkuk 3:17-18'). 생략 시 원고에서 추출된 첫 인용")
    p.add_argument("--cache", default=None,
                   help=f"SQLite 캐시 경로 (기본: {default_cache_path()})")
    return p.parse_args()


def main():
    args = parse_args()
    build_ppt(
        manuscript_path=args.manuscript,
        output_path=args.output,
        template_path=args.template,
        title_en=args.title_en,
        title_ko=args.title_ko,
        main_passage=args.main_passage,
        cache_path=args.cache,
    )


if __name__ == "__main__":
    main()
