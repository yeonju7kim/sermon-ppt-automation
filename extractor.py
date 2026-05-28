"""원고 텍스트에서 성구 인용 추출."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

from bible_books import all_aliases_regex, lookup


@dataclass(frozen=True)
class Reference:
    book_en: str
    book_ko: str
    chapter: int
    verse_start: int
    verse_end: int

    @property
    def header_en(self) -> str:
        if self.verse_start == self.verse_end:
            return f"{self.book_en} {self.chapter}:{self.verse_start}"
        return f"{self.book_en} {self.chapter}:{self.verse_start}-{self.verse_end}"

    @property
    def header_ko(self) -> str:
        if self.verse_start == self.verse_end:
            return f"{self.book_ko} {self.chapter}:{self.verse_start}"
        return f"{self.book_ko} {self.chapter}:{self.verse_start}-{self.verse_end}"

    def verse_numbers(self) -> list[int]:
        return list(range(self.verse_start, self.verse_end + 1))


_BOOK_PATTERN = all_aliases_regex()

# 책 이름 뒤 마침표 허용 (예: "롬. 8:28", "Hab. 3:17"). 한글 '장' 대신 시편의 '편'도 인정.
# 패턴 1: "<책>[.] <장>:<절>[-<절>]"  (콜론 사용)
_PAT_COLON = re.compile(
    rf"(?P<book>{_BOOK_PATTERN})\.?\s*"
    rf"(?P<chap>\d+)\s*[:：]\s*"
    rf"(?P<vs>\d+)(?:\s*[-–~]\s*(?P<ve>\d+))?",
    re.IGNORECASE,
)

# 패턴 2: "<책>[.] <장>장|편 <절>[-<절>]절"  (한글 표기)
_PAT_KOREAN = re.compile(
    rf"(?P<book>{_BOOK_PATTERN})\.?\s*"
    rf"(?P<chap>\d+)\s*[장편]\s*"
    rf"(?P<vs>\d+)(?:\s*[-–~]\s*(?P<ve>\d+))?\s*절",
    re.IGNORECASE,
)


def _read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        try:
            import docx
        except ImportError as e:
            raise SystemExit("docx 파일을 읽으려면 python-docx 설치 필요: pip install python-docx") from e
        d = docx.Document(str(path))
        return "\n".join(p.text for p in d.paragraphs)
    raise SystemExit(f"지원하지 않는 형식: {suffix}")


def extract_from_text(text: str) -> list[Reference]:
    """등장 순서대로 중복 제거한 Reference 리스트 반환."""
    found: list[Reference] = []
    seen: set[tuple] = set()

    matches: list[tuple[int, re.Match]] = []
    for pat in (_PAT_COLON, _PAT_KOREAN):
        for m in pat.finditer(text):
            matches.append((m.start(), m))
    matches.sort(key=lambda x: x[0])

    for _, m in matches:
        canon = lookup(m.group("book"))
        if not canon:
            continue
        en, ko = canon
        chap = int(m.group("chap"))
        vs = int(m.group("vs"))
        ve = int(m.group("ve")) if m.group("ve") else vs
        key = (en, chap, vs, ve)
        if key in seen:
            continue
        seen.add(key)
        found.append(Reference(en, ko, chap, vs, ve))
    return found


def extract_from_file(path: str | Path) -> list[Reference]:
    return extract_from_text(_read_text(Path(path)))


if __name__ == "__main__":
    import sys
    refs = extract_from_file(sys.argv[1])
    for r in refs:
        print(f"{r.header_en}  |  {r.header_ko}")
