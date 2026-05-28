"""66권 정규명 / 한글-영문 별칭 매핑."""

BOOKS = [
    ("Genesis", "창세기", ["Gen", "Ge", "Gn"], ["창"]),
    ("Exodus", "출애굽기", ["Exod", "Exo", "Ex"], ["출"]),
    ("Leviticus", "레위기", ["Lev", "Lv"], ["레"]),
    ("Numbers", "민수기", ["Num", "Nu", "Nm"], ["민"]),
    ("Deuteronomy", "신명기", ["Deut", "Dt"], ["신"]),
    ("Joshua", "여호수아", ["Josh", "Jos"], ["수"]),
    ("Judges", "사사기", ["Judg", "Jdg"], ["삿"]),
    ("Ruth", "룻기", ["Ru"], ["룻"]),
    ("1 Samuel", "사무엘상", ["1 Sam", "1Sam", "1 Sa", "1Sa"], ["삼상"]),
    ("2 Samuel", "사무엘하", ["2 Sam", "2Sam", "2 Sa", "2Sa"], ["삼하"]),
    ("1 Kings", "열왕기상", ["1 Kgs", "1Kgs", "1 Ki", "1Ki"], ["왕상"]),
    ("2 Kings", "열왕기하", ["2 Kgs", "2Kgs", "2 Ki", "2Ki"], ["왕하"]),
    ("1 Chronicles", "역대상", ["1 Chr", "1Chr", "1 Ch", "1Ch"], ["대상"]),
    ("2 Chronicles", "역대하", ["2 Chr", "2Chr", "2 Ch", "2Ch"], ["대하"]),
    ("Ezra", "에스라", ["Ezr"], ["스"]),
    ("Nehemiah", "느헤미야", ["Neh", "Ne"], ["느"]),
    ("Esther", "에스더", ["Esth", "Est"], ["에"]),
    ("Job", "욥기", ["Jb"], ["욥"]),
    ("Psalms", "시편", ["Psalm", "Ps", "Psa", "Pss"], ["시"]),
    ("Proverbs", "잠언", ["Prov", "Pro", "Pr"], ["잠"]),
    ("Ecclesiastes", "전도서", ["Eccl", "Ecc", "Ec", "Qoh"], ["전"]),
    ("Song of Songs", "아가", ["Song", "SOS", "Sng", "Song of Solomon"], ["아"]),
    ("Isaiah", "이사야", ["Isa", "Is"], ["사"]),
    ("Jeremiah", "예레미야", ["Jer", "Je"], ["렘"]),
    ("Lamentations", "예레미야애가", ["Lam", "La"], ["애"]),
    ("Ezekiel", "에스겔", ["Ezek", "Eze", "Ezk"], ["겔"]),
    ("Daniel", "다니엘", ["Dan", "Dn"], ["단"]),
    ("Hosea", "호세아", ["Hos", "Ho"], ["호"]),
    ("Joel", "요엘", ["Jl"], ["욜"]),
    ("Amos", "아모스", ["Am"], ["암"]),
    ("Obadiah", "오바댜", ["Obad", "Ob"], ["옵"]),
    ("Jonah", "요나", ["Jnh", "Jon"], ["욘"]),
    ("Micah", "미가", ["Mic", "Mc"], ["미"]),
    ("Nahum", "나훔", ["Nah", "Na"], ["나"]),
    ("Habakkuk", "하박국", ["Hab", "Hb"], ["합"]),
    ("Zephaniah", "스바냐", ["Zeph", "Zep", "Zph"], ["습"]),
    ("Haggai", "학개", ["Hag", "Hg"], ["학"]),
    ("Zechariah", "스가랴", ["Zech", "Zec", "Zch"], ["슥"]),
    ("Malachi", "말라기", ["Mal", "Ml"], ["말"]),
    ("Matthew", "마태복음", ["Matt", "Mat", "Mt"], ["마"]),
    ("Mark", "마가복음", ["Mrk", "Mk", "Mr"], ["막"]),
    ("Luke", "누가복음", ["Luk", "Lk"], ["눅"]),
    ("John", "요한복음", ["Jn", "Jhn"], ["요"]),
    ("Acts", "사도행전", ["Ac"], ["행"]),
    ("Romans", "로마서", ["Rom", "Ro", "Rm"], ["롬"]),
    ("1 Corinthians", "고린도전서", ["1 Cor", "1Cor", "1 Co", "1Co"], ["고전"]),
    ("2 Corinthians", "고린도후서", ["2 Cor", "2Cor", "2 Co", "2Co"], ["고후"]),
    ("Galatians", "갈라디아서", ["Gal", "Ga"], ["갈"]),
    ("Ephesians", "에베소서", ["Eph", "Ephes"], ["엡"]),
    ("Philippians", "빌립보서", ["Phil", "Php", "Pp"], ["빌"]),
    ("Colossians", "골로새서", ["Col"], ["골"]),
    ("1 Thessalonians", "데살로니가전서", ["1 Thess", "1Thess", "1 Th", "1Th"], ["살전"]),
    ("2 Thessalonians", "데살로니가후서", ["2 Thess", "2Thess", "2 Th", "2Th"], ["살후"]),
    ("1 Timothy", "디모데전서", ["1 Tim", "1Tim", "1 Ti", "1Ti"], ["딤전"]),
    ("2 Timothy", "디모데후서", ["2 Tim", "2Tim", "2 Ti", "2Ti"], ["딤후"]),
    ("Titus", "디도서", ["Tit"], ["딛"]),
    ("Philemon", "빌레몬서", ["Phlm", "Phm", "Pm"], ["몬"]),
    ("Hebrews", "히브리서", ["Heb"], ["히"]),
    ("James", "야고보서", ["Jas", "Jm"], ["약"]),
    ("1 Peter", "베드로전서", ["1 Pet", "1Pet", "1 Pe", "1Pe"], ["벧전"]),
    ("2 Peter", "베드로후서", ["2 Pet", "2Pet", "2 Pe", "2Pe"], ["벧후"]),
    ("1 John", "요한일서", ["1 Jn", "1Jn", "1 Jo", "1Jo"], ["요일"]),
    ("2 John", "요한이서", ["2 Jn", "2Jn", "2 Jo", "2Jo"], ["요이"]),
    ("3 John", "요한삼서", ["3 Jn", "3Jn", "3 Jo", "3Jo"], ["요삼"]),
    ("Jude", "유다서", [], ["유"]),
    ("Revelation", "요한계시록", ["Rev", "Re", "Apoc"], ["계"]),
]


def _norm(s: str) -> str:
    return s.replace(" ", "").lower()


_ALIAS_TO_CANONICAL: dict[str, tuple[str, str]] = {}
for en, ko, en_aliases, ko_aliases in BOOKS:
    canonical = (en, ko)
    for name in [en, ko, *en_aliases, *ko_aliases]:
        _ALIAS_TO_CANONICAL[_norm(name)] = canonical


def lookup(name: str) -> tuple[str, str] | None:
    """책 이름(한/영/약어)을 입력받아 (영문 정규명, 한글 정규명) 반환."""
    return _ALIAS_TO_CANONICAL.get(_norm(name))


def all_aliases_regex() -> str:
    """모든 책 이름/약어를 길이 내림차순으로 OR 결합 (긴 매치 우선)."""
    import re
    names = sorted(set(_ALIAS_TO_CANONICAL.keys()), key=lambda x: -len(x))
    parts = []
    for en, ko, en_aliases, ko_aliases in BOOKS:
        for name in [en, ko, *en_aliases, *ko_aliases]:
            parts.append(name)
    parts.sort(key=lambda x: -len(x))
    return "|".join(re.escape(p) for p in parts)
