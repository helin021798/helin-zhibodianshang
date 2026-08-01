from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "helin-analyze-livestream-commerce"
    / "scripts"
    / "text_metrics.py"
)
SPEC = importlib.util.spec_from_file_location("text_metrics", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
TEXT_METRICS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TEXT_METRICS)


class TextMetricsTests(unittest.TestCase):
    def test_counts_chinese_and_ignores_punctuation(self) -> None:
        self.assertEqual(TEXT_METRICS.count_effective_units("宝宝们，来看这个！"), 7)

    def test_counts_contiguous_latin_and_digits_as_tokens(self) -> None:
        self.assertEqual(TEXT_METRICS.count_effective_units("SPF50 现在99元"), 5)

    def test_duration_under_one_minute(self) -> None:
        result = TEXT_METRICS.estimate_duration(100)
        self.assertEqual(result["seconds"], 24)
        self.assertEqual(result["report_display"], "<1分钟")

    def test_duration_rounds_for_report(self) -> None:
        result = TEXT_METRICS.estimate_duration(625)
        self.assertEqual(result["seconds"], 150)
        self.assertEqual(result["timecode"], "00:02:30")
        self.assertEqual(result["report_display"], "约3分钟")

    def test_rejects_invalid_speech_rate(self) -> None:
        with self.assertRaises(ValueError):
            TEXT_METRICS.estimate_duration(10, 0)


if __name__ == "__main__":
    unittest.main()
