from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "skills" / "helin-livestream-planning-master" / "scripts" / "live_calc.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


class RoiTests(unittest.TestCase):
    def test_break_even_and_target_roi(self) -> None:
        result = run("roi", "--margin", "60", "--sign-rate", "85", "--fee", "5", "--target-net", "10")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("= 2.14", result.stdout)
        self.assertIn("= 2.72", result.stdout)

    def test_one_means_one_percent(self) -> None:
        result = run("roi", "--margin", "40", "--sign-rate", "80", "--fee", "1")
        self.assertIn("其他变动费率 1.0%", result.stdout)
        self.assertIn("= 3.21", result.stdout)

    def test_percent_sign_accepted(self) -> None:
        result = run("roi", "--margin", "30%", "--sign-rate", "80%")
        self.assertIn("= 4.17", result.stdout)

    def test_decimal_input_warns(self) -> None:
        result = run("roi", "--margin", "0.3", "--sign-rate", "80")
        self.assertIn("请写 30", result.stderr)

    def test_loss_when_fee_exceeds_margin(self) -> None:
        result = run("roi", "--margin", "10", "--fee", "15")
        self.assertIn("任何投流都亏损", result.stdout)


class PitTests(unittest.TestCase):
    def test_gap_against_target(self) -> None:
        items = "修护精华两件装:269:320,修护全套礼盒:599:40,面膜体验装:39.9:600,氨基酸洁面:89:180"
        result = run("pit", "--items", items, "--target", "180000")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("合计预估 GMV: 150,000.00", result.stdout)
        self.assertIn("缺口 30,000.00（16.7%）", result.stdout)

    def test_tsv_file_with_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "goods.tsv"
            path.write_text("品名\t直播价\t单量\t角色\n主推A\t299\t300\t主推\n福利B\t39.9\t800\t福利\n", encoding="utf-8")
            result = run("pit", "--file", str(path))
        self.assertIn("合计预估 GMV: 121,620.00", result.stdout)


class MechTests(unittest.TestCase):
    def test_share_of_gross_profit(self) -> None:
        result = run("mech", "--items", "开场福袋小样:8:200,晒单抽免单:269:3,满赠旅行装:12:400", "--gmv", "150000", "--margin", "60")
        self.assertIn("让利总额: 7,207.00", result.stdout)
        self.assertIn("让利占毛利 8.0%", result.stdout)

    def test_zero_margin_does_not_crash(self) -> None:
        result = run("mech", "--items", "赠品:10:5", "--gmv", "1000", "--margin", "0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("无法计算让利占毛利", result.stdout)


if __name__ == "__main__":
    unittest.main()
