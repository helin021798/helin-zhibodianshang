#!/usr/bin/env python3
"""直播文稿台账工具：分段目录、憋卡踢促信号线索、产品出场台账与语速校准。

只用标准库。三个子命令：

  outline  FILE                 输出文稿概况与分段目录（段号、时间、说话人、字数、开头预览）
  signals  FILE                 按段列出憋单/卡单/踢单/促单/上链等关键词命中，作为定位线索
  ledger   FILE BOUNDARIES      按分段边界生成出场台账、单品汇总、覆盖缺口与重叠检查

BOUNDARIES 为 UTF-8 文本，每行一条，用 Tab 或至少两个空格分隔：

  编号    名称            起始段  结束段
  N1      开场预告        S001    S012
  P1      洗眼液组合      S013    S058
  P2      蒸汽眼罩        S059    S090
  P1      洗眼液组合      S091    S120     ← 同一编号再次出现即记为返场

编号以 P 开头表示商品，以 N 开头表示非商品段（开场预告、抽奖、互动、下场预告等）。
以 # 开头的行和空行忽略。

支持的文稿格式：时间戳独占一行（可带说话人）、行首时间戳、SRT/VTT 字幕、无时间戳纯文本。
时间戳回退（多段文稿拼接）时，回退处视为新片段接在上一段之后计算时长，显示和引用仍用原始时间戳。
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

DEFAULT_RATE = 250.0
MAX_PLAIN_SEGMENT_UNITS = 400
SUBTITLE_MERGE_UNITS = 200

UNIT_PATTERN = re.compile(
    r"[㐀-䶿一-鿿豈-﫿]|[A-Za-z0-9]+(?:[._%+-][A-Za-z0-9]+)*"
)
TS = r"\d{1,2}:\d{2}(?::\d{2})?"
# 「主播A 00:21」独占一行（飞书妙记、通义听悟等常见导出格式）
HEADER_LINE = re.compile(rf"^\s*(?P<spk>[^\d\s\[\]#][^\t]{{0,30}}?)\s+(?P<ts>{TS})\s*$")
# 「[00:21]」或「00:21 主播A」独占一行，正文在下一行
TS_ONLY_LINE = re.compile(rf"^\s*\[?(?P<ts>{TS})\]?(?:\s+(?P<spk>[^\d\s：:][^：:]{{0,19}}?))?\s*$")
# 「[00:21] 主播A：正文」或「00:21 主播A：正文」行首时间戳格式
INLINE_LINE = re.compile(
    rf"^\s*\[?(?P<ts>{TS})\]?\s*(?:(?P<spk>[^：:\s]{{1,20}})\s*[：:])?\s*(?P<text>.*)$"
)
# SRT/VTT 字幕时间轴「00:00:01,000 --> 00:00:03,000」
CUE_LINE = re.compile(rf"^\s*(?P<ts>{TS})(?:[.,]\d{{1,3}})?\s*-->\s*\S+")
SENTENCE_END = re.compile(r"(?<=[。！？!?；;…])")

N = "[0-9一二两三四五六七八九十几]+"
# 正则词表：命中只是定位线索，动作是否成立必须回到原文判断
SIGNALS: dict[str, re.Pattern[str]] = {
    "憋": re.compile(r"扣[1一个]|扣想要|想要的(扣|打)|打在公屏|公屏|先不上|还没上|等(一下|会儿)再?上|暂时不上|人多了?再|灯牌|点个?关注|点赞到|预约"),
    "卡": re.compile(rf"库存|只剩|最后{N}[单件套盒份个]|最后几单|抢完|抢光|没有了|没货|断货|名额|限量|就这么多|卖完|拍完"),
    "踢": re.compile(rf"踢|未付款|没付款|没有付款|释放|加库存|加{N}单|再加|补单|追加|回流|放{N}单"),
    "促": re.compile(rf"抽奖|福袋|截屏|截图|送你|赠品|下单就送|前{N}名|锦鲤|免单|返现|保价|多送"),
    "上链": re.compile(rf"上链接|{N}号链接|小黄车|购物车|开价|改价|上车|刷新|去拍|拍下|三二一|321|单独上"),
    "价格": re.compile(r"到手|原价|日常价|日播价|专柜价|官方的?价|官网|划线价|券后|立减|全网"),
    "售后": re.compile(rf"退货|退换|运费险|包退|售后|假一|{N}天试用|先用后|无理由|过敏"),
}


@dataclass
class Segment:
    sid: str
    speaker: str
    ts: int | None  # 原始时间戳秒数；无时间戳为 None
    text: str
    units: int = field(init=False)

    def __post_init__(self) -> None:
        self.units = count_units(self.text)


@dataclass
class Timeline:
    starts: list[float]  # 连续时间轴上每段起点秒数，用于计算时长
    ends: list[float]  # 连续时间轴上每段终点秒数
    total: float  # 全场时长秒数
    rate: float  # 语速，字/分钟
    source: str  # 语速来源说明
    resets: list[int]  # 时间戳回退的段下标（多段文稿拼接点）

    @property
    def measured(self) -> bool:
        return self.source == "原始时间戳实测"


def count_units(text: str) -> int:
    """每个中日韩文字计 1，连续英文或数字词组计 1，标点和空白不计。"""
    return len(UNIT_PATTERN.findall(text))


def parse_ts(value: str) -> int:
    parts = [int(p) for p in value.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def fmt_ts(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def split_long(text: str, limit: int = MAX_PLAIN_SEGMENT_UNITS) -> list[str]:
    """把无时间戳的超长段落按句末标点切成不超过 limit 字的块。"""
    if count_units(text) <= limit:
        return [text]
    chunks, buf = [], ""
    for sentence in SENTENCE_END.split(text):
        if buf and count_units(buf + sentence) > limit:
            chunks.append(buf)
            buf = ""
        buf += sentence
    if buf:
        chunks.append(buf)
    return chunks


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: 需要 UTF-8 文本；docx/pdf 请先转成文本") from exc


def preamble(lines: list[str]) -> str:
    """首个时间戳之前的文字（忽略 # 标题行）。"""
    return "".join(ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#"))


def layout_ok(lines: list[str], is_stamp: Callable[[str], bool]) -> bool:
    """判断时间戳行是文稿结构，还是正文里偶然出现的「明晚 8:00」。

    真实的带时间戳文稿里，时间戳行至少占非空行的一成，且首个时间戳之前的正文不超过全文两成。
    """
    first = next(i for i, ln in enumerate(lines) if is_stamp(ln))
    hits = sum(1 for ln in lines if is_stamp(ln))
    nonempty = sum(1 for ln in lines if ln.strip())
    total = sum(count_units(ln) for ln in lines)
    return hits * 10 >= nonempty and count_units(preamble(lines[:first])) <= total * 0.2


def parse_subtitles(lines: list[str]) -> list[tuple[str, int | None, str]]:
    """SRT/VTT：去掉序号行、时间轴和样式标签，相邻字幕合并到约 SUBTITLE_MERGE_UNITS 字一段。"""
    cues: list[tuple[int, str]] = []
    ts, buf = None, []
    for i, ln in enumerate(lines):
        m = CUE_LINE.match(ln)
        if m:
            if ts is not None and buf:
                cues.append((ts, "".join(buf)))
            ts, buf = parse_ts(m["ts"]), []
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if ln.strip().isdigit() and CUE_LINE.match(nxt):
            continue
        if ts is not None and ln.strip():
            buf.append(re.sub(r"<[^>]+>", "", ln.strip()))
    if ts is not None and buf:
        cues.append((ts, "".join(buf)))

    raw: list[tuple[str, int | None, str]] = []
    cur_ts, cur = None, ""
    for ts, text in cues:
        if cur and count_units(cur + text) > SUBTITLE_MERGE_UNITS:
            raw.append(("", cur_ts, cur))
            cur = ""
        if not cur:
            cur_ts = ts
        cur += text
    if cur:
        raw.append(("", cur_ts, cur))
    return raw


def parse_transcript(path: Path) -> tuple[list[Segment], str]:
    lines = read_text(path).splitlines()

    def header_match(ln: str) -> re.Match[str] | None:
        return HEADER_LINE.match(ln) or TS_ONLY_LINE.match(ln)

    def inline_match(ln: str) -> bool:
        return bool(re.match(rf"^\s*\[?{TS}\]?\s+\S", ln)) and not TS_ONLY_LINE.match(ln)

    cue_hits = sum(1 for ln in lines if CUE_LINE.match(ln))
    header_hits = sum(1 for ln in lines if header_match(ln))
    inline_hits = sum(1 for ln in lines if inline_match(ln))
    raw: list[tuple[str, int | None, str]] = []
    lead = ""

    if cue_hits >= 2:
        fmt = "SRT/VTT 字幕（相邻字幕合并为段）"
        raw = parse_subtitles(lines)
    elif header_hits >= 2 and header_hits >= inline_hits and layout_ok(lines, lambda ln: bool(header_match(ln))):
        fmt = "时间戳独占一行（可带说话人）"
        spk, ts, buf = "", None, []
        started = False
        for i, ln in enumerate(lines):
            m = header_match(ln)
            if m:
                if started:
                    raw.append((spk, ts, "".join(buf)))
                else:
                    lead = preamble(lines[:i])
                spk, ts, buf, started = (m["spk"] or "").strip(), parse_ts(m["ts"]), [], True
            elif started:
                buf.append(ln.strip())
        if started:
            raw.append((spk, ts, "".join(buf)))
    elif inline_hits >= 2 and layout_ok(lines, inline_match):
        fmt = "行首时间戳"
        for i, ln in enumerate(lines):
            m = INLINE_LINE.match(ln)
            if m and re.match(rf"^\s*\[?{TS}", ln):
                if not raw:
                    lead = preamble(lines[:i])
                raw.append(((m["spk"] or "").strip(), parse_ts(m["ts"]), m["text"].strip()))
            elif ln.strip() and raw:
                spk, ts, text = raw[-1]
                raw[-1] = (spk, ts, text + ln.strip())
    else:
        fmt = "无可靠时间戳（按段落切分）"
        for para in re.split(r"\n\s*\n|\n", "\n".join(lines)):
            para = para.strip()
            if para and not para.startswith("#"):
                for chunk in split_long(para):
                    raw.append(("", None, chunk))

    if lead:
        # 首个时间戳之前多为标题、导出时间等元信息，不计入字数，但必须提示，避免正文被悄悄丢掉
        fmt += f"；首个时间戳前有 {count_units(lead)} 字未计入（开头：{lead[:20]}），如是口播请补时间戳"

    segments = [Segment(f"S{i:03d}", spk, ts, text) for i, (spk, ts, text) in enumerate(raw, 1)]
    segments = [s for s in segments if s.units > 0]
    for i, seg in enumerate(segments, 1):
        seg.sid = f"S{i:03d}"
    return segments, fmt


def timeline(segments: list[Segment], duration_min: float | None) -> Timeline:
    """计算每段在连续时间轴上的起止、全场时长和语速。"""
    total_units = sum(s.units for s in segments)
    if segments and all(s.ts is not None for s in segments):
        # 用时间戳前进的相邻段算语速；回退处（拼接点）不计入
        span, span_units = 0, 0
        for a, b in zip(segments, segments[1:]):
            if b.ts >= a.ts:
                span += b.ts - a.ts
                span_units += a.units
        rate = span_units / (span / 60) if span > 0 and span_units > 0 else DEFAULT_RATE
        starts, resets = [float(segments[0].ts)], []
        for i, (a, b) in enumerate(zip(segments, segments[1:]), 1):
            if b.ts >= a.ts:
                step = b.ts - a.ts
            else:
                step = a.units / rate * 60  # 回退前一段没有下一个时间戳，按语速估算
                resets.append(i)
            starts.append(starts[-1] + step)
        ends = starts[1:] + [starts[-1] + segments[-1].units / rate * 60]
        return Timeline(starts, ends, ends[-1] - starts[0], rate, "原始时间戳实测", resets)
    if duration_min:
        rate = total_units / duration_min
        source = f"用户提供总时长 {duration_min:g} 分钟校准"
    else:
        rate = DEFAULT_RATE
        source = "默认值，未知总时长，估算偏差可能较大"
    starts, acc = [], 0
    for s in segments:
        starts.append(acc / rate * 60)
        acc += s.units
    total = total_units / rate * 60
    return Timeline(starts, starts[1:] + [total], total, rate, source, [])


def clock(segments: list[Segment], tl: Timeline, i: int, end: bool = False) -> str:
    """显示用时间：有原始时间戳时用原始时间戳（便于回查），否则用估算时间。"""
    if tl.measured:
        seg = segments[i]
        return fmt_ts(seg.ts + (tl.ends[i] - tl.starts[i]) if end else seg.ts)
    return "≈" + fmt_ts(tl.ends[i] if end else tl.starts[i])


def reset_note(segments: list[Segment], tl: Timeline) -> str:
    sids = "、".join(segments[i].sid for i in tl.resets[:5]) + ("等" if len(tl.resets) > 5 else "")
    return (f"时间戳回退 {len(tl.resets)} 处（{sids}），文稿可能由多段拼接；"
            "回退处已接在上一段之后计算时长，回退前一段的时长按语速估算")


def cmd_outline(args: argparse.Namespace) -> int:
    segments, fmt = parse_transcript(args.file)
    if not segments:
        print("error: 未解析到任何有效文字", file=sys.stderr)
        return 2
    tl = timeline(segments, args.duration_min)
    total_units = sum(s.units for s in segments)
    speakers: dict[str, int] = {}
    for s in segments:
        speakers[s.speaker or "（未标注）"] = speakers.get(s.speaker or "（未标注）", 0) + s.units

    print(f"# 文稿概况：{args.file.name}")
    print(f"- 格式：{fmt}；分段 {len(segments)} 段；有效字数 {total_units}")
    est = "" if tl.measured else "（估算）"
    minutes = f"约 {tl.total / 60:.0f} 分钟" if tl.total >= 60 else "<1 分钟"
    print(f"- 时长：{minutes}{est}；语速 {tl.rate:.0f} 字/分钟（{tl.source}）")
    if tl.resets:
        print(f"- 警告：{reset_note(segments, tl)}")
    print("- 说话人字数：" + "；".join(f"{k} {v}" for k, v in sorted(speakers.items(), key=lambda kv: -kv[1])))
    print()
    for i, seg in enumerate(segments):
        preview = re.sub(r"\s+", "", seg.text)[: args.preview]
        spk = f" | {seg.speaker}" if seg.speaker else ""
        print(f"{seg.sid} | {clock(segments, tl, i)}{spk} | {seg.units}字 | {preview}")
    return 0


def cmd_signals(args: argparse.Namespace) -> int:
    segments, _ = parse_transcript(args.file)
    if not segments:
        print("error: 未解析到任何有效文字", file=sys.stderr)
        return 2
    tl = timeline(segments, args.duration_min)
    wanted = args.only.split(",") if args.only else list(SIGNALS)
    print("# 信号线索（关键词命中≠动作成立，必须回到原文确认）")
    print("段号 | 时间 | 命中（类别:词×次）")
    for i, seg in enumerate(segments):
        hits = []
        for cat in wanted:
            pattern = SIGNALS.get(cat)
            if not pattern:
                continue
            found: dict[str, int] = {}
            for m in pattern.finditer(seg.text):
                found[m.group(0)] = found.get(m.group(0), 0) + 1
            if found:
                hits.append(cat + ":" + "、".join(k if v == 1 else f"{k}×{v}" for k, v in found.items()))
        if hits:
            print(f"{seg.sid} | {clock(segments, tl, i)} | " + "  ".join(hits))
    return 0


def parse_boundaries(path: Path, valid: dict[str, int]) -> list[tuple[str, str, int, int]]:
    rows = []
    for no, ln in enumerate(read_text(path).splitlines(), 1):
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in re.split(r"\t+|\s{2,}", ln.strip()) if p.strip()]
        if len(parts) != 4:
            raise ValueError(f"边界文件第 {no} 行需要 4 列（编号 名称 起始段 结束段）：{ln}")
        pid, name, a, b = parts
        if a not in valid or b not in valid:
            raise ValueError(f"边界文件第 {no} 行段号不存在：{a} / {b}")
        if valid[a] > valid[b]:
            raise ValueError(f"边界文件第 {no} 行起始段晚于结束段：{a} > {b}")
        rows.append((pid, name, valid[a], valid[b]))
    return rows


def cmd_ledger(args: argparse.Namespace) -> int:
    segments, _ = parse_transcript(args.file)
    if not segments:
        print("error: 未解析到任何有效文字", file=sys.stderr)
        return 2
    tl = timeline(segments, args.duration_min)
    index = {s.sid: i for i, s in enumerate(segments)}
    rows = parse_boundaries(args.boundaries, index)
    tag = "原始时间戳" if tl.measured else "估算"

    print(f"# 出场台账（时间口径：{tag}；语速 {tl.rate:.0f} 字/分钟，{tl.source}）")
    if tl.resets:
        print(f"\n> 警告：{reset_note(segments, tl)}。跨拼接点的出场，起止时间分属两段文稿。")
    print()
    print("| 出场编号 | 名称 | 起止段 | 起止时间 | 时长(分) | 字数 |")
    print("|---|---|---|---|---:|---:|")
    seen: dict[str, int] = {}
    totals: dict[str, dict[str, float]] = {}
    covered = [0] * len(segments)
    for pid, name, a, b in sorted(rows, key=lambda r: r[2]):
        seen[pid] = seen.get(pid, 0) + 1
        label = pid if seen[pid] == 1 else f"{pid}·R{seen[pid]}"
        units = sum(s.units for s in segments[a : b + 1])
        minutes = (tl.ends[b] - tl.starts[a]) / 60
        for i in range(a, b + 1):
            covered[i] += 1
        t = totals.setdefault(pid, {"name": name, "count": 0, "units": 0, "min": 0.0})
        t["count"] += 1
        t["units"] += units
        t["min"] += minutes
        spans_reset = any(a < r <= b for r in tl.resets)
        when = f"{clock(segments, tl, a)}–{clock(segments, tl, b, end=True)}" + ("（跨拼接点）" if spans_reset else "")
        print(f"| {label} | {name} | {segments[a].sid}–{segments[b].sid} | {when} | {minutes:.1f} | {units} |")

    print()
    print("| 编号 | 名称 | 出场次数 | 累计时长(分) | 占全场 | 累计字数 |")
    print("|---|---|---:|---:|---:|---:|")
    for pid, t in sorted(totals.items(), key=lambda kv: -kv[1]["min"]):
        share = t["min"] * 60 / tl.total * 100 if tl.total else 0
        print(f"| {pid} | {t['name']} | {int(t['count'])} | {t['min']:.1f} | {share:.0f}% | {int(t['units'])} |")

    prod = [t for pid, t in totals.items() if pid.upper().startswith("P")]
    non = [t for pid, t in totals.items() if not pid.upper().startswith("P")]
    print()
    print(f"- 全场：{tl.total / 60:.1f} 分钟，{sum(s.units for s in segments)} 字")
    print(f"- 商品段合计：{len(prod)} 个商品，{sum(t['min'] for t in prod):.1f} 分钟，{int(sum(t['units'] for t in prod))} 字")
    print(f"- 非商品段合计：{len(non)} 类，{sum(t['min'] for t in non):.1f} 分钟，{int(sum(t['units'] for t in non))} 字")
    if tl.measured:
        print(f"- 注：末段 {segments[-1].sid} 没有下一个时间戳，其结束时间按实测语速估算")

    gaps, overlaps = [], []
    i = 0
    while i < len(segments):
        if covered[i] == 0:
            j = i
            while j + 1 < len(segments) and covered[j + 1] == 0:
                j += 1
            gaps.append(f"{segments[i].sid}–{segments[j].sid}（{sum(s.units for s in segments[i:j + 1])}字）")
            i = j + 1
        else:
            if covered[i] > 1:
                overlaps.append(segments[i].sid)
            i += 1
    print()
    print("- 未归属段：" + ("；".join(gaps) if gaps else "无"))
    print("- 重叠段：" + ("、".join(overlaps) if overlaps else "无"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="直播文稿台账工具")
    parser.add_argument("--duration-min", type=float, help="用户提供的实际直播总时长（分钟），无时间戳时用于校准语速")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("outline", help="文稿概况与分段目录")
    p.add_argument("file", type=Path)
    p.add_argument("--preview", type=int, default=24, help="每段预览字数，默认 24")
    p.set_defaults(func=cmd_outline)
    p = sub.add_parser("signals", help="憋卡踢促等信号线索")
    p.add_argument("file", type=Path)
    p.add_argument("--only", help="只看指定类别，逗号分隔，如 憋,卡,踢,促")
    p.set_defaults(func=cmd_signals)
    p = sub.add_parser("ledger", help="按边界生成出场台账")
    p.add_argument("file", type=Path)
    p.add_argument("boundaries", type=Path)
    p.set_defaults(func=cmd_ledger)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
