from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills" / "helin-analyze-livestream-commerce" / "scripts" / "transcript_ledger.py"
FIXTURE = ROOT / "evals" / "fixtures" / "synthetic-beauty-transcript.md"

SPEC = importlib.util.spec_from_file_location("transcript_ledger", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
LEDGER = importlib.util.module_from_spec(SPEC)
sys.modules["transcript_ledger"] = LEDGER
SPEC.loader.exec_module(LEDGER)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


class CountUnitsTests(unittest.TestCase):
    def test_counts_chinese_and_ignores_punctuation(self) -> None:
        self.assertEqual(LEDGER.count_units("宝宝们，来看这个！"), 7)

    def test_counts_latin_and_number_groups_as_one(self) -> None:
        self.assertEqual(LEDGER.count_units("SPF50 防晒 99.9%"), 4)


class ParseTests(unittest.TestCase):
    def write(self, text: str) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(Path(handle.name).unlink)
        return Path(handle.name)

    def test_timestamp_only_lines(self) -> None:
        segments, fmt = LEDGER.parse_transcript(FIXTURE)
        self.assertIn("时间戳独占一行", fmt)
        self.assertEqual(len(segments), 7)
        self.assertEqual(segments[1].ts, 70)

    def test_speaker_and_timestamp_header(self) -> None:
        path = self.write("主播A 00:00\n\n大家好欢迎来到直播间。\n\n助播B 01:02:03\n\n上链接。\n")
        segments, _ = LEDGER.parse_transcript(path)
        self.assertEqual([s.speaker for s in segments], ["主播A", "助播B"])
        self.assertEqual(segments[1].ts, 3723)

    def test_inline_timestamps_with_continuation(self) -> None:
        path = self.write("[00:00:05] 主播：一号链接。\n[00:01:10] 助播：最后三单了！\n续行。\n")
        segments, fmt = LEDGER.parse_transcript(path)
        self.assertEqual(fmt, "行首时间戳")
        self.assertEqual(segments[1].text, "最后三单了！续行。")

    def test_time_mentions_in_plain_text_do_not_switch_format(self) -> None:
        body = "家人们晚上好，今天给大家带来洗眼液，想要的扣1。\n\n" * 20
        path = self.write(body + "明晚 8:00\n\n下一个蒸汽眼罩。\n\n周六 20:00\n\n明天见。\n")
        segments, fmt = LEDGER.parse_transcript(path)
        self.assertIn("无可靠时间戳", fmt)
        self.assertEqual(sum(s.units for s in segments), LEDGER.count_units(body) + LEDGER.count_units("明晚8:00下一个蒸汽眼罩周六20:00明天见"))

    def test_short_preamble_is_reported_not_counted(self) -> None:
        path = self.write("# 标题\n2026年07月03日 20:41\n\n主播 00:00\n" + "欢迎" * 20 + "\n主播 01:00\n" + "上链接" * 20 + "\n")
        segments, fmt = LEDGER.parse_transcript(path)
        self.assertIn("首个时间戳前有", fmt)
        self.assertEqual(segments[0].speaker, "主播")
        self.assertTrue(segments[0].text.startswith("欢迎"))

    def test_srt_subtitles(self) -> None:
        path = self.write("1\n00:00:01,000 --> 00:00:03,000\n家人们晚上好\n\n2\n00:00:04,000 --> 00:00:09,000\n<i>只剩最后3单</i>\n")
        segments, fmt = LEDGER.parse_transcript(path)
        self.assertIn("SRT", fmt)
        self.assertEqual(segments[0].ts, 1)
        self.assertEqual(segments[0].text, "家人们晚上好只剩最后3单")

    def test_plain_text_splits_long_paragraphs(self) -> None:
        path = self.write("这是一句话。" * 200)
        segments, fmt = LEDGER.parse_transcript(path)
        self.assertIn("无可靠时间戳", fmt)
        self.assertGreater(len(segments), 1)
        self.assertTrue(all(s.units <= LEDGER.MAX_PLAIN_SEGMENT_UNITS for s in segments))


class TimelineTests(unittest.TestCase):
    def test_measured_rate_from_timestamps(self) -> None:
        segments, _ = LEDGER.parse_transcript(FIXTURE)
        tl = LEDGER.timeline(segments, None)
        self.assertEqual(tl.source, "原始时间戳实测")
        self.assertGreater(tl.total, 390)

    def test_user_duration_calibrates_rate(self) -> None:
        segments = [LEDGER.Segment("S001", "", None, "字" * 300), LEDGER.Segment("S002", "", None, "字" * 300)]
        tl = LEDGER.timeline(segments, 2)
        self.assertEqual(tl.rate, 300)
        self.assertEqual(tl.starts[1], 60)
        self.assertEqual(tl.total, 120)

    def test_default_rate_without_duration(self) -> None:
        segments = [LEDGER.Segment("S001", "", None, "字" * 250)]
        tl = LEDGER.timeline(segments, None)
        self.assertEqual(tl.rate, 250)
        self.assertIn("默认值", tl.source)

    def test_excerpt_not_starting_at_zero(self) -> None:
        segments = [LEDGER.Segment("S001", "", 5400, "字" * 300), LEDGER.Segment("S002", "", 5460, "字" * 300)]
        tl = LEDGER.timeline(segments, None)
        self.assertEqual(tl.ends[1] - tl.starts[1], 60)
        self.assertEqual(tl.total, 120)

    def test_backward_timestamps_continue_timeline(self) -> None:
        segments = [
            LEDGER.Segment("S001", "", 0, "字" * 300),
            LEDGER.Segment("S002", "", 60, "字" * 300),
            LEDGER.Segment("S003", "", 0, "字" * 300),
            LEDGER.Segment("S004", "", 60, "字" * 300),
        ]
        tl = LEDGER.timeline(segments, None)
        self.assertEqual(tl.resets, [2])
        self.assertEqual(tl.rate, 300)
        self.assertTrue(all(b > a for a, b in zip(tl.starts, tl.starts[1:])))
        self.assertEqual(tl.total, 240)


class CommandTests(unittest.TestCase):
    def test_signals_finds_scarcity_and_link_cues(self) -> None:
        result = run("signals", str(FIXTURE))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("卡:", result.stdout)
        self.assertIn("一号链接", result.stdout)

    def test_ledger_counts_returns_and_reports_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            boundaries = Path(tmp) / "b.tsv"
            boundaries.write_text(
                "P1\t洗脸巾\tS001\tS001\nP2\t保湿精华\tS002\tS004\nP3\t防晒乳\tS005\tS005\nP2\t保湿精华\tS006\tS006\n",
                encoding="utf-8",
            )
            result = run("ledger", str(FIXTURE), str(boundaries))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("P2·R2", result.stdout)
        self.assertIn("| P2 | 保湿精华 | 2 |", result.stdout)
        self.assertIn("未归属段：S007–S007", result.stdout)

    def test_ledger_rejects_unknown_segment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            boundaries = Path(tmp) / "b.tsv"
            boundaries.write_text("P1\t洗脸巾\tS001\tS999\n", encoding="utf-8")
            result = run("ledger", str(FIXTURE), str(boundaries))
        self.assertEqual(result.returncode, 2)
        self.assertIn("段号不存在", result.stderr)


if __name__ == "__main__":
    unittest.main()
