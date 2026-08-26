#!/usr/bin/env python3
"""Детермінований редакторський сканер для humanizer-ua.

Сканер не визначає авторство тексту. Він знаходить українські шаблонні
формули, кальки та структурні сигнали, щоб редактор знав, де дивитися вручну.
Зовнішні залежності не потрібні.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


VERSION = "1.0.0"
GENRES = ("marketing", "neutral", "academic", "legal", "fiction")
WORD_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]+(?:['’][A-Za-zА-Яа-яІіЇїЄєҐґ]+)?")


@dataclass(frozen=True)
class Rule:
    code: str
    category: str
    label: str
    pattern: str
    hard: bool = False
    muted: tuple[str, ...] = ()


@dataclass
class Hit:
    code: str
    category: str
    label: str
    count: int
    lines: list[int]
    examples: list[str]


HARD_RULES = (
    Rule("H01", "вступ", "У сучасному світі", r"\bу\s+сучасному\s+світі\b", True, ("academic", "legal", "fiction")),
    Rule("H02", "метатекст", "Варто зазначити", r"\bварто\s+зазначити(?:\s*,?\s*що)?\b", True, ("academic", "legal")),
    Rule("H03", "метатекст", "Важливо зазначити", r"\bважливо\s+зазначити(?:\s*,?\s*що)?\b", True, ("academic", "legal")),
    Rule("H04", "метатекст", "Необхідно підкреслити", r"\bнеобхідно\s+підкреслити(?:\s*,?\s*що)?\b", True, ("academic", "legal")),
    Rule("H05", "кліше", "Відіграє важливу роль", r"\bвідігра(?:є|ють)\s+(?:ключову|важливу|значну)\s+роль\b", True, ("academic", "legal")),
    Rule("H06", "кліше", "Потужний інструмент", r"\b(?:є|став|стала|стало)\s+потужним\s+інструментом\b", True),
    Rule("H07", "риторика", "Не просто X, а Y", r"\bне\s+просто\b.{0,90}\b(?:а|але)\s+(?:й|і)?\s*", True, ("fiction",)),
    Rule("H08", "кліше", "Відкриває нові горизонти", r"\bвідкрива(?:є|ють)\s+нові\s+горизонти\b", True),
    Rule("H09", "кліше", "Розкрити потенціал", r"\bрозкр(?:ити|иває|ивають)\s+(?:весь\s+|повний\s+)?потенціал\b", True),
    Rule("H10", "кліше", "Комплексний підхід", r"\bкомплексн(?:ий|ого|ому|им)\s+підх(?:ід|оду|оді|одом)\b", True, ("academic", "legal")),
    Rule("H11", "кліше", "Ключ до успіху", r"\bключ(?:ем)?\s+до\s+успіху\b", True),
    Rule("H12", "кліше", "Невід'ємна частина", r"\bневід['’]ємн(?:а|ою)\s+частин(?:а|ою)\b", True, ("academic", "legal")),
    Rule("H13", "канцелярит", "На сьогоднішній день", r"\bна\s+сьогоднішній\s+день\b", True, ("legal",)),
    Rule("H14", "невизначеність", "Широкий спектр", r"\bширок(?:ий|ого|ому|им)\s+спектр(?:у|ом)?\b", True, ("academic",)),
    Rule("H15", "канцелярит", "Дозволяє ефективно", r"\bдозволя(?:є|ють)\s+ефективно\b", True),
    Rule("H16", "канцелярит", "Сприяє підвищенню", r"\bсприя(?:є|ють)\s+підвищенню\b", True, ("academic", "legal")),
    Rule("H17", "висновок", "Підсумовуючи вищесказане", r"\bпідсумовуючи\s+вищесказане\b", True, ("academic", "legal")),
    Rule("H18", "висновок", "Таким чином, можна зробити висновок", r"\bтаким\s+чином\s*,?\s*можна\s+зробити\s+висновок\b", True, ("academic", "legal")),
    Rule("H19", "висновок", "У підсумку слід зазначити", r"\bу\s+підсумку\s+слід\s+зазначити\b", True, ("academic", "legal")),
    Rule("H20", "кліше", "Важко переоцінити", r"\bважко\s+переоцінити\b", True, ("academic", "fiction")),
)


SOFT_RULES = (
    Rule("S01", "русизм", "Являється у значенні «є»", r"\bявля(?:ється|ються|вся|лася|лося|лися)\b"),
    Rule("S02", "русизм", "Приймати участь", r"\bприйм(?:ати|ає|ають|ав|ала|али)\s+участь\b"),
    Rule("S03", "русизм", "На протязі (про час)", r"\bна\s+протязі\b"),
    Rule("S04", "русизм", "Слідуючий", r"\bслідуюч(?:ий|а|е|і|ого|ому|им|ою)\b"),
    Rule("S05", "русизм", "По питанню", r"\bпо\s+питанн(?:ю|ях)\b"),
    Rule("S06", "калька", "Має місце", r"\bма(?:є|ють|ло)\s+місце\b", muted=("legal",)),
    Rule("S07", "канцелярит", "Здійснювати діяльність", r"\bздійсн\w*\s+(?:діяльн\w*|перевір\w*|контрол\w*)\b", muted=("legal",)),
    Rule("S08", "канцелярит", "Проводити роботу", r"\bпровод\w*\s+робот\w*\b", muted=("legal",)),
    Rule("S09", "канцелярит", "Даний/дана/дане", r"\bдан(?:ий|а|е|і|ого|ому|им|ою|их|ими)\b", muted=("academic", "legal")),
    Rule("S10", "невизначеність", "Певною мірою", r"\bпевною\s+мірою\b", muted=("academic",)),
    Rule("S11", "невизначеність", "У деяких випадках", r"\bу\s+деяких\s+випадках\b", muted=("academic", "legal")),
    Rule("S12", "перехід", "Крім того", r"\bкрім\s+того\b"),
    Rule("S13", "перехід", "Водночас", r"\bводночас\b"),
    Rule("S14", "перехід", "Таким чином", r"\bтаким\s+чином\b", muted=("academic", "legal")),
    Rule("S15", "чатбот", "Ось покращена версія", r"\bось\s+(?:покращена|відредагована|оновлена)\s+версія\b"),
    Rule("S16", "чатбот", "Сподіваюся, це допоможе", r"\bсподіваюся\s*,?\s*(?:що\s+)?це\s+допоможе\b"),
    Rule("S17", "чатбот", "Можу також", r"\bможу\s+також\s+(?:підготувати|додати|зробити|переписати)\b"),
    Rule("S18", "риторика", "Чесно кажучи", r"\bчесно\s+кажучи\b"),
    Rule("S19", "риторика", "Давайте чесно", r"\bдавайте\s+чесно\b"),
    Rule("S20", "кліше", "Ефективне рішення", r"\bефективн(?:е|им|ого)\s+рішенн(?:я|ям)\b"),
)


ALL_RULES = HARD_RULES + SOFT_RULES
COMPILED = {rule.code: re.compile(rule.pattern, re.IGNORECASE | re.DOTALL) for rule in ALL_RULES}

NOMINAL_SUFFIXES = ("ння", "ття", "ізація", "ування", "ювання", "ення", "ання")
VERB_SUFFIXES = (
    "ти", "ться", "є", "ють", "емо", "имо", "ете", "ите", "ав", "ала",
    "али", "ив", "ила", "или", "ув", "ула", "ули", "атиме", "итиме",
)
UK_STOPWORDS = {
    "і", "й", "та", "але", "або", "що", "як", "це", "цей", "ця", "ці",
    "у", "в", "з", "із", "зі", "до", "для", "на", "не", "ми", "ви",
    "вони", "він", "вона", "було", "є", "тому", "після", "коли",
}


def read_text(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def compact_example(text: str, start: int, end: int) -> str:
    left = max(0, start - 28)
    right = min(len(text), end + 45)
    excerpt = re.sub(r"\s+", " ", text[left:right]).strip()
    return excerpt[:120]


def scan_rules(text: str, genre: str) -> tuple[list[Hit], int]:
    hits: list[Hit] = []
    muted_count = 0
    for rule in ALL_RULES:
        matches = list(COMPILED[rule.code].finditer(text))
        if not matches:
            continue
        if genre in rule.muted:
            muted_count += len(matches)
            continue
        hits.append(
            Hit(
                code=rule.code,
                category=rule.category,
                label=rule.label,
                count=len(matches),
                lines=sorted({line_number(text, match.start()) for match in matches}),
                examples=[compact_example(text, match.start(), match.end()) for match in matches[:2]],
            )
        )
    return hits, muted_count


def sentences(text: str) -> list[str]:
    cleaned = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    return [part.strip() for part in re.split(r"(?<=[.!?…])\s+|\n+", cleaned) if WORD_RE.search(part)]


def coefficient_of_variation(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return round(math.sqrt(variance) / mean, 3)


def structural_metrics(text: str, words: list[str]) -> dict[str, object]:
    sentence_list = sentences(text)
    lengths = [len(WORD_RE.findall(sentence)) for sentence in sentence_list]
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if WORD_RE.search(part)]
    paragraph_lengths = [len(WORD_RE.findall(part)) for part in paragraphs]
    list_items = [line.strip() for line in text.splitlines() if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line)]
    list_starts = []
    for item in list_items:
        body = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", item)
        first = WORD_RE.search(body)
        if first:
            list_starts.append(first.group(0).lower())
    repeated_starts = len(list_starts) - len(set(list_starts))
    nominalizations = sum(1 for word in words if word.lower().endswith(NOMINAL_SUFFIXES) and len(word) > 6)
    verbs = sum(1 for word in words if word.lower().endswith(VERB_SUFFIXES) and len(word) > 3)
    return {
        "sentences": len(sentence_list),
        "sentence_lengths": lengths,
        "mean_sentence_length": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
        "sentence_length_cv": coefficient_of_variation(lengths),
        "paragraphs": len(paragraphs),
        "paragraph_lengths": paragraph_lengths,
        "list_items": len(list_items),
        "repeated_list_starts": repeated_starts,
        "em_dashes": text.count("—"),
        "nominalizations_heuristic": nominalizations,
        "verbs_heuristic": verbs,
    }


def language_warning(text: str, words: list[str]) -> str | None:
    letters = re.findall(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]", text)
    cyrillic = re.findall(r"[А-Яа-яІіЇїЄєҐґ]", text)
    if letters and len(cyrillic) / len(letters) < 0.55:
        return "Текст не схожий на український: редакторські метрики можуть бути неточними."
    lowered = {word.lower() for word in words}
    ua_signal = any(ch in text.lower() for ch in "іїєґ") or len(lowered & UK_STOPWORDS) >= 2
    ru_signal = bool(re.search(r"[ыэёъ]", text.lower()))
    if len(words) >= 8 and ru_signal and not ua_signal:
        return "Текст схожий на російський; humanizer-ua призначений для української мови."
    return None


def score_report(hits: list[Hit], metrics: dict[str, object], word_count: int) -> tuple[int, str, list[dict[str, object]]]:
    penalties: list[dict[str, object]] = []
    hard_count = sum(hit.count for hit in hits if hit.code.startswith("H"))
    soft_count = sum(hit.count for hit in hits if hit.code.startswith("S"))

    if hard_count:
        points = min(42, hard_count * 8)
        penalties.append({"reason": f"сильні маркери: {hard_count}", "points": -points})
    if soft_count:
        density = soft_count * 100 / max(word_count, 1)
        points = min(24, max(2, round(density * 2.2)))
        penalties.append({"reason": f"лексичні маркери: {soft_count}", "points": -points})

    sentence_count = int(metrics["sentences"])
    sentence_cv = float(metrics["sentence_length_cv"])
    if sentence_count >= 5 and sentence_cv < 0.22:
        penalties.append({"reason": "надто рівна довжина речень", "points": -7})
    if int(metrics["list_items"]) >= 4 and int(metrics["repeated_list_starts"]) >= 2:
        penalties.append({"reason": "шаблонні початки пунктів списку", "points": -5})
    paragraph_lengths = list(metrics["paragraph_lengths"])
    if len(paragraph_lengths) >= 4 and sum(length <= 16 for length in paragraph_lengths) / len(paragraph_lengths) >= 0.75:
        penalties.append({"reason": "забагато коротких мікроабзаців", "points": -4})
    nominalizations = int(metrics["nominalizations_heuristic"])
    if word_count >= 40 and nominalizations * 100 / word_count > 5:
        penalties.append({"reason": "висока щільність віддієслівних іменників", "points": -5})
    em_dashes = int(metrics["em_dashes"])
    if word_count >= 40 and em_dashes * 100 / word_count > 3:
        penalties.append({"reason": "тире використано як універсальний зв'язок", "points": -3})

    score = max(0, 100 + sum(int(item["points"]) for item in penalties))
    band = "чисто" if score >= 85 else "точкова правка" if score >= 60 else "потрібен рерайт"
    return score, band, penalties


def analyze(text: str, genre: str) -> dict[str, object]:
    words = WORD_RE.findall(text)
    hits, muted_count = scan_rules(text, genre)
    metrics = structural_metrics(text, words)
    score, band, penalties = score_report(hits, metrics, len(words))
    hard_hits = [hit for hit in hits if hit.code.startswith("H")]
    soft_hits = [hit for hit in hits if hit.code.startswith("S")]
    return {
        "version": VERSION,
        "genre": genre,
        "word_count": len(words),
        "score": {"value": score, "band": band, "penalties": penalties},
        "hard_ban_count": sum(hit.count for hit in hard_hits),
        "marker_count": sum(hit.count for hit in soft_hits),
        "hard_bans": [asdict(hit) for hit in hard_hits],
        "markers": [asdict(hit) for hit in soft_hits],
        "muted_by_genre": muted_count,
        "metrics": metrics,
        "warning": language_warning(text, words),
        "disclaimer": "Редакторська оцінка, не визначення авторства і не ймовірність AI.",
    }


def print_report(report: dict[str, object], source: str) -> None:
    score = report["score"]
    print(f"=== humanizer-ua scan: {source} ===")
    print(f"Жанр: {report['genre']} · слів: {report['word_count']}")
    if report["warning"]:
        print(f"⚠ {report['warning']}")
    print()
    print(f"РЕДАКТОРСЬКА ЧИСТОТА: {score['value']}/100 [{score['band']}]")
    print("Це не ймовірність AI і не визначення авторства.")
    for penalty in score["penalties"]:
        print(f"  {penalty['points']:+d}  {penalty['reason']}")
    if not score["penalties"]:
        print("  без штрафів")
    print()

    print("СИЛЬНІ МАРКЕРИ:")
    if report["hard_bans"]:
        for hit in report["hard_bans"]:
            lines = ", ".join(str(line) for line in hit["lines"])
            print(f"  ⛔ [{hit['code']}] {hit['label']} ×{hit['count']} (рядки {lines})")
    else:
        print("  ✓ не знайдено")
    print()

    print("М'ЯКІ МАРКЕРИ:")
    if report["markers"]:
        for hit in report["markers"][:15]:
            lines = ", ".join(str(line) for line in hit["lines"])
            print(f"  • [{hit['category']}] {hit['label']} ×{hit['count']} (рядки {lines})")
    else:
        print("  ✓ не знайдено")
    print()

    metrics = report["metrics"]
    print("РИТМ І СТРУКТУРА:")
    print(
        f"  речень: {metrics['sentences']}, середня довжина: "
        f"{metrics['mean_sentence_length']}, CV: {metrics['sentence_length_cv']}"
    )
    print(
        f"  абзаців: {metrics['paragraphs']}, пунктів списку: {metrics['list_items']}, "
        f"довгих тире: {metrics['em_dashes']}"
    )
    print(
        f"  віддієслівних іменників (евристика): {metrics['nominalizations_heuristic']}, "
        f"дієслівних форм (евристика): {metrics['verbs_heuristic']}"
    )
    if report["muted_by_genre"]:
        print(f"  жанровим фільтром знято збігів: {report['muted_by_genre']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Редакторський сканер humanizer-ua")
    parser.add_argument("source", nargs="?", default="-", help="UTF-8 файл або - для stdin")
    parser.add_argument("--genre", choices=GENRES, default="neutral")
    parser.add_argument("--json", action="store_true", help="вивести JSON")
    parser.add_argument("--version", action="version", version=f"humanizer-ua {VERSION}")
    args = parser.parse_args()

    try:
        text = read_text(args.source)
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not text.strip():
        payload = {"empty": True, "score": {"value": 100, "band": "чисто"}}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("Текст порожній, сканувати нічого.")
        return 0

    report = analyze(text, args.genre)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report, args.source)
    return 1 if report["hard_ban_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

