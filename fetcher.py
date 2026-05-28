"""성구 텍스트 조회. NIV(Bible Gateway) + 개역개정(대한성서공회) + SQLite 캐시.

저작권: NIV는 Biblica, 개역개정은 대한성서공회 저작권. 본 도구는 사용자의 개인
설교 준비 용도로 사용자 본인 머신에서 텍스트를 가져와 로컬에 캐시할 뿐, 어떤
성경 본문도 코드에 임베드하지 않는다.
"""
from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from extractor import Reference


# 대한성서공회 책 코드 (URL용 영문 약어)
BSKOREA_BOOK_CODES = {
    "Genesis": "gen", "Exodus": "exo", "Leviticus": "lev", "Numbers": "num",
    "Deuteronomy": "deu", "Joshua": "jos", "Judges": "jdg", "Ruth": "rut",
    "1 Samuel": "1sa", "2 Samuel": "2sa", "1 Kings": "1ki", "2 Kings": "2ki",
    "1 Chronicles": "1ch", "2 Chronicles": "2ch", "Ezra": "ezr",
    "Nehemiah": "neh", "Esther": "est", "Job": "job", "Psalms": "psa",
    "Proverbs": "pro", "Ecclesiastes": "ecc", "Song of Songs": "sng",
    "Isaiah": "isa", "Jeremiah": "jer", "Lamentations": "lam",
    "Ezekiel": "ezk", "Daniel": "dan", "Hosea": "hos", "Joel": "jol",
    "Amos": "amo", "Obadiah": "oba", "Jonah": "jon", "Micah": "mic",
    "Nahum": "nam", "Habakkuk": "hab", "Zephaniah": "zep", "Haggai": "hag",
    "Zechariah": "zec", "Malachi": "mal",
    "Matthew": "mat", "Mark": "mrk", "Luke": "luk", "John": "jhn",
    "Acts": "act", "Romans": "rom", "1 Corinthians": "1co",
    "2 Corinthians": "2co", "Galatians": "gal", "Ephesians": "eph",
    "Philippians": "php", "Colossians": "col",
    "1 Thessalonians": "1th", "2 Thessalonians": "2th",
    "1 Timothy": "1ti", "2 Timothy": "2ti", "Titus": "tit",
    "Philemon": "phm", "Hebrews": "heb", "James": "jas",
    "1 Peter": "1pe", "2 Peter": "2pe", "1 John": "1jn", "2 John": "2jn",
    "3 John": "3jn", "Jude": "jud", "Revelation": "rev",
}


@dataclass
class Verse:
    number: int
    text: str


# ---------- 캐시 ----------

class VerseCache:
    """SQLite로 (translation, book_en, chapter, verse) → text 캐시."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS verses (
        translation TEXT NOT NULL,
        book_en TEXT NOT NULL,
        chapter INTEGER NOT NULL,
        verse INTEGER NOT NULL,
        text TEXT NOT NULL,
        PRIMARY KEY (translation, book_en, chapter, verse)
    )
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.execute(self.SCHEMA)
        self.conn.commit()

    def get(self, translation: str, ref: Reference) -> list[Verse] | None:
        cur = self.conn.execute(
            "SELECT verse, text FROM verses WHERE translation=? AND book_en=? AND chapter=? "
            "AND verse BETWEEN ? AND ? ORDER BY verse",
            (translation, ref.book_en, ref.chapter, ref.verse_start, ref.verse_end),
        )
        rows = cur.fetchall()
        expected = ref.verse_end - ref.verse_start + 1
        if len(rows) != expected:
            return None
        return [Verse(n, t) for n, t in rows]

    def put(self, translation: str, book_en: str, chapter: int, verses: list[Verse]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO verses(translation, book_en, chapter, verse, text) "
            "VALUES (?, ?, ?, ?, ?)",
            [(translation, book_en, chapter, v.number, v.text) for v in verses],
        )
        self.conn.commit()


# ---------- 네트워크 fetcher ----------

class BibleGatewayFetcher:
    """NIV(영문) 조회용. https://www.biblegateway.com 스크래핑."""

    URL = "https://www.biblegateway.com/passage/"
    HEADERS = {"User-Agent": "Mozilla/5.0 (sermon-ppt-tool)"}

    def fetch(self, ref: Reference, version: str = "NIV") -> list[Verse]:
        q = {"search": ref.header_en, "version": version}
        r = requests.get(self.URL + "?" + urlencode(q), headers=self.HEADERS, timeout=20)
        r.raise_for_status()
        return self._parse(r.text, ref, version)

    @staticmethod
    def _parse(html: str, ref: Reference, version: str) -> list[Verse]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one(".passage-text")
        if container is None:
            raise RuntimeError(f"Bible Gateway: passage-text 없음 ({ref.header_en} {version})")

        # 각주/대체본문 제거
        for sel in [
            "sup.crossreference", "sup.footnote", "div.footnotes",
            "div.crossrefs", "h3", "h4", "span.chapternum",
        ]:
            for tag in container.select(sel):
                tag.decompose()

        # 구절은 .text와 versenum 으로 식별 — Bible Gateway는
        # <span class="text [book]-[chap]-[verse]">…</span> 구조 사용
        verses: dict[int, str] = {}
        for span in container.select("span.text"):
            classes = span.get("class", [])
            verse_num = None
            for c in classes:
                m = re.match(r"^[\w]+-(\d+)-(\d+)$", c)
                if m and int(m.group(1)) == ref.chapter:
                    verse_num = int(m.group(2))
                    break
            if verse_num is None:
                continue
            if not (ref.verse_start <= verse_num <= ref.verse_end):
                continue

            # 절번호 sup 제거
            for sup in span.select("sup.versenum"):
                sup.decompose()
            text = span.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            # 같은 절 여러 span은 이어붙임
            verses[verse_num] = (verses.get(verse_num, "") + " " + text).strip()

        result = [Verse(n, verses[n]) for n in sorted(verses.keys())]
        missing = [n for n in ref.verse_numbers() if n not in verses]
        if missing:
            raise RuntimeError(f"Bible Gateway 누락 절 {missing} ({ref.header_en} {version})")
        return result


class BsKoreaFetcher:
    """개역개정(한글) 조회용. https://www.bskorea.or.kr 스크래핑."""

    URL = "https://www.bskorea.or.kr/bible/korbibReadpage.php"
    HEADERS = {"User-Agent": "Mozilla/5.0 (sermon-ppt-tool)"}

    def fetch(self, ref: Reference, version: str = "GAE") -> list[Verse]:
        code = BSKOREA_BOOK_CODES.get(ref.book_en)
        if code is None:
            raise RuntimeError(f"대한성서공회 책 코드 없음: {ref.book_en}")
        q = {"version": version, "book": code, "chap": str(ref.chapter)}
        r = requests.get(self.URL + "?" + urlencode(q), headers=self.HEADERS, timeout=20)
        r.encoding = r.apparent_encoding or "utf-8"
        r.raise_for_status()
        return self._parse(r.text, ref)

    @staticmethod
    def _parse(html: str, ref: Reference) -> list[Verse]:
        # 본문 영역만 잘라낸다 (id="tdBible1" 내부)
        m = re.search(r'<div id="tdBible1"[^>]*>(.*?)</div>\s*<div', html, re.DOTALL)
        inner = m.group(1) if m else html

        soup = BeautifulSoup(inner, "html.parser")

        # 본문이 아닌 보조 요소만 제거.
        # - div.D2: 각주 팝업
        # - a.comment: 각주 링크 (이 안의 작은 인디케이터 글자가 본문에 섞이지 않게)
        # - [id^="voice"]: 음성 듣기 버튼
        # - .chapNum / .smallTitle: 챕터 번호·소제목
        # 주의: .name, .area, .orgin 같은 본문 강조용 inline 태그는 텍스트가 본문이므로 절대 제거 금지
        for tag in soup.select(
            "div.D2, a.comment, [id^='voice'], "
            ".chapNum, .smallTitle"
        ):
            tag.decompose()

        # 각 절은 <span><span class="number">N</span>...본문...</span><br/> 형태
        verses: dict[int, str] = {}
        for outer in soup.find_all("span", recursive=True):
            num_tag = outer.find("span", class_="number", recursive=False)
            if num_tag is None:
                continue
            num_text = num_tag.get_text(strip=True)
            if not num_text.isdigit():
                continue
            n = int(num_text)
            if not (ref.verse_start <= n <= ref.verse_end):
                continue

            num_tag.extract()
            # separator="" 로 가져와 한국어 단어 사이에 불필요한 공백이 끼지 않게 함
            text = outer.get_text(separator="", strip=False)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                verses[n] = text

        missing = [n for n in ref.verse_numbers() if n not in verses]
        if missing:
            raise RuntimeError(f"대한성서공회 누락 절 {missing} ({ref.header_ko})")
        return [Verse(n, verses[n]) for n in sorted(verses.keys())]


# ---------- 통합 fetcher ----------

class CachedFetcher:
    """캐시 우선, 미스시 네트워크 호출 + 캐시 저장."""

    POLITE_DELAY_SEC = 0.7

    def __init__(self, cache: VerseCache, niv: BibleGatewayFetcher, kor: BsKoreaFetcher):
        self.cache = cache
        self.niv = niv
        self.kor = kor
        self._last_call = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < self.POLITE_DELAY_SEC:
            time.sleep(self.POLITE_DELAY_SEC - elapsed)
        self._last_call = time.time()

    def get_niv(self, ref: Reference) -> list[Verse]:
        return self._get(ref, "NIV", lambda: self.niv.fetch(ref, "NIV"))

    def get_korean(self, ref: Reference) -> list[Verse]:
        return self._get(ref, "GAE", lambda: self.kor.fetch(ref, "GAE"))

    def _get(self, ref: Reference, translation: str, fetcher_fn) -> list[Verse]:
        cached = self.cache.get(translation, ref)
        if cached is not None:
            return cached
        self._throttle()
        verses = fetcher_fn()
        self.cache.put(translation, ref.book_en, ref.chapter, verses)
        return verses


def default_fetcher(cache_path: Path | str = "bible_cache.db") -> CachedFetcher:
    return CachedFetcher(
        cache=VerseCache(Path(cache_path)),
        niv=BibleGatewayFetcher(),
        kor=BsKoreaFetcher(),
    )
