from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCANNER = ROOT / "skills" / "humanizer-ua" / "scripts" / "scan.py"
SPEC = importlib.util.spec_from_file_location("humanizer_ua_scan", SCANNER)
assert SPEC and SPEC.loader
scan = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scan
SPEC.loader.exec_module(scan)


class ScannerTests(unittest.TestCase):
    def test_clean_text(self) -> None:
        report = scan.analyze(
            "Ми перевірили звіт двічі. У другій таблиці знайшли помилку, виправили її й повторили розрахунок.",
            "neutral",
        )
        self.assertEqual(report["hard_ban_count"], 0)
        self.assertGreaterEqual(report["score"]["value"], 85)

    def test_protected_markdown_is_excluded_from_rules_and_metrics(self) -> None:
        text = (
            "> Варто зазначити, що цитата містить маркер.\n"
            "```text\n"
            "У сучасному світі. — Сприяє підвищенню результату.\n"
            "```\n"
            "   ~~~text\n"
            "Необхідно підкреслити. — Дозволяє ефективно працювати.\n"
            "   ~~~\n"
            "У фрагменті `у сучасному світі` теж є захищений маркер.\n"
            "Варто зазначити, що це видима проза."
        )
        report = scan.analyze(text, "neutral")

        self.assertEqual(report["hard_ban_count"], 1)
        self.assertEqual(report["hard_bans"][0]["lines"], [9])
        self.assertIn("Варто зазначити, що це видима проза", report["hard_bans"][0]["examples"][0])
        self.assertEqual(report["metrics"]["em_dashes"], 0)
        self.assertEqual(report["word_count"], 12)

    def test_hard_markers_reduce_score(self) -> None:
        report = scan.analyze(
            "У сучасному світі сервіс є потужним інструментом і відкриває нові горизонти.",
            "marketing",
        )
        self.assertEqual(report["hard_ban_count"], 3)
        self.assertLess(report["score"]["value"], 85)

    def test_ukrainian_russisms(self) -> None:
        report = scan.analyze(
            "На протязі місяця команда приймала участь у роботі. Даний метод являється точним.",
            "neutral",
        )
        labels = {hit["label"] for hit in report["markers"]}
        self.assertIn("На протязі (про час)", labels)
        self.assertIn("Приймати участь", labels)
        self.assertIn("Даний/дана/дане", labels)
        self.assertIn("Являється у значенні «є»", labels)

    def test_genre_filter(self) -> None:
        neutral = scan.analyze("Варто зазначити, що метод відіграє важливу роль.", "neutral")
        academic = scan.analyze("Варто зазначити, що метод відіграє важливу роль.", "academic")
        self.assertEqual(neutral["hard_ban_count"], 2)
        self.assertEqual(academic["hard_ban_count"], 0)
        self.assertEqual(academic["muted_by_genre"], 2)

    def test_json_cli_and_exit_code(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCANNER), "-", "--json"],
            input="У сучасному світі це відкриває нові горизонти.",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hard_ban_count"], 2)
        self.assertIn("disclaimer", payload)

    def test_line_numbers(self) -> None:
        report = scan.analyze("Перший рядок.\nВарто зазначити, що це тест.", "neutral")
        self.assertEqual(report["hard_bans"][0]["lines"], [2])


if __name__ == "__main__":
    unittest.main()

