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
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_RATE = 250.0
MAX_PLAIN_SEGMENT_UNITS = 400

UNIT_PATTERN = re.compile(
    r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]|[A-Za-z0-9]+(?:[._%+-][A-Za-z0-9]+)*"
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


def parse_transcript(path: Path) -> tuple[list[Segment], str]:
    lines = read_text(path).splitlines()
    def header_match(ln: str) -> re.Match[str] | None:
        return HEADER_LINE.match(ln) or TS_ONLY_LINE.match(ln)

    header_hits = sum(1 for ln in lines if header_match(ln))
    inline_hits = sum(1 for ln in lines if re.match(rf"^\s*\[?{TS}\]?\s+\S", ln) and not TS_ONLY_LINE.match(ln))
    raw: list[tuple[str, int | None, str]] = []

    if header_hits >= 2 and header_hits >= inline_hits:
        fmt = "时间戳独占一行（可带说话人）"
        spk, ts, buf = "", None, []
        started = False
        for ln in lines:
            m = header_match(ln)
            if m:
                if started:
                    raw.append((spk, ts, "".join(buf)))
                spk, ts, buf, started = (m["spk"] or "").strip(), parse_ts(m["ts"]), [], True
            elif started:
                buf.append(ln.strip())
        if started:
            raw.append((spk, ts, "".join(buf)))
    elif inline_hits >= 2:
        fmt = "行首时间戳"
        for ln in lines:
            m = INLINE_LINE.match(ln)
            if m and re.match(rf"^\s*\[?{TS}", ln):
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

    segments = [Segment(f"S{i:03d}", spk, ts, text) for i, (spk, ts, text) in enumerate(raw, 1)]
    segments = [s for s in segments if s.units > 0]
    for i, seg in enumerate(segments, 1):
        seg.sid = f"S{i:03d}"
    return segments, fmt


def timeline(segments: list[Segment], duration_min: float | None) -> tuple[list[float], float, float, str]:
    """返回每段起点秒数、全场时长秒数、语速（字/分钟）和语速来源说明。"""
    total_units = sum(s.units for s in segments)
    stamped = [s for s in segments if s.ts is not None]
    if stamped and len(stamped) == len(segments):
        last = segments[-1]
        # 时间戳跨度不含最后一段，先用前面各段算语速，再补最后一段时长
        span_units = total_units - last.units
        span = last.ts - segments[0].ts
        rate = span_units / (span / 60) if span > 0 and span_units > 0 else DEFAULT_RATE
        total = span + last.units / rate * 60
        starts = [float(s.ts) for s in segments]
        return starts, total, rate, "原始时间戳实测"
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
    return starts, total_units / rate * 60, rate, source


def cmd_outline(args: argparse.Namespace) -> int:
    segments, fmt = parse_transcript(args.file)
    if not segments:
        print("error: 未解析到任何有效文字", file=sys.stderr)
        return 2
    starts, total, rate, source = timeline(segments, args.duration_min)
    total_units = sum(s.units for s in segments)
    speakers: dict[str, int] = {}
    for s in segments:
        speakers[s.speaker or "（未标注）"] = speakers.get(s.speaker or "（未标注）", 0) + s.units
    backward = sum(1 for a, b in zip(segments, segments[1:]) if a.ts is not None and b.ts is not None and b.ts < a.ts)

    print(f"# 文稿概况：{args.file.name}")
    print(f"- 格式：{fmt}；分段 {len(segments)} 段；有效字数 {total_units}")
    est = "" if source == "原始时间戳实测" else "（估算）"
    minutes = f"约 {total / 60:.0f} 分钟" if total >= 60 else "<1 分钟"
    print(f"- 时长：{minutes}{est}；语速 {rate:.0f} 字/分钟（{source}）")
    if backward:
        print(f"- 警告：时间戳回退 {backward} 处，文稿可能由多段拼接，跨段时长不可直接相减")
    print("- 说话人字数：" + "；".join(f"{k} {v}" for k, v in sorted(speakers.items(), key=lambda kv: -kv[1])))
    print()
    tag = "" if source == "原始时间戳实测" else "≈"
    for seg, st in zip(segments, starts):
        preview = re.sub(r"\s+", "", seg.text)[: args.preview]
        spk = f" | {seg.speaker}" if seg.speaker else ""
        print(f"{seg.sid} | {tag}{fmt_ts(st)}{spk} | {seg.units}字 | {preview}")
    return 0


def cmd_signals(args: argparse.Namespace) -> int:
    segments, _ = parse_transcript(args.file)
    starts, _, _, source = timeline(segments, args.duration_min)
    tag = "" if source == "原始时间戳实测" else "≈"
    wanted = args.only.split(",") if args.only else list(SIGNALS)
    print("# 信号线索（关键词命中≠动作成立，必须回到原文确认）")
    print("段号 | 时间 | 命中（类别:词×次）")
    for seg, st in zip(segments, starts):
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
            print(f"{seg.sid} | {tag}{fmt_ts(st)} | " + "  ".join(hits))
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
    starts, total, rate, source = timeline(segments, args.duration_min)
    index = {s.sid: i for i, s in enumerate(segments)}
    rows = parse_boundaries(args.boundaries, index)
    ends = starts[1:] + [total]
    measured = source == "原始时间戳实测"
    tag = "原始时间戳" if measured else "估算"

    print(f"# 出场台账（时间口径：{tag}；语速 {rate:.0f} 字/分钟，{source}）")
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
        minutes = (ends[b] - starts[a]) / 60
        for i in range(a, b + 1):
            covered[i] += 1
        t = totals.setdefault(pid, {"name": name, "count": 0, "units": 0, "min": 0.0})
        t["count"] += 1
        t["units"] += units
        t["min"] += minutes
        prefix = "" if measured else "约"
        print(f"| {label} | {name} | {segments[a].sid}–{segments[b].sid} | "
              f"{prefix}{fmt_ts(starts[a])}–{fmt_ts(ends[b])} | {minutes:.1f} | {units} |")

    print()
    print("| 编号 | 名称 | 出场次数 | 累计时长(分) | 占全场 | 累计字数 |")
    print("|---|---|---:|---:|---:|---:|")
    for pid, t in sorted(totals.items(), key=lambda kv: -kv[1]["min"]):
        share = t["min"] * 60 / total * 100 if total else 0
        print(f"| {pid} | {t['name']} | {int(t['count'])} | {t['min']:.1f} | {share:.0f}% | {int(t['units'])} |")

    prod = [t for pid, t in totals.items() if pid.upper().startswith("P")]
    non = [t for pid, t in totals.items() if not pid.upper().startswith("P")]
    print()
    print(f"- 全场：{total / 60:.1f} 分钟，{sum(s.units for s in segments)} 字")
    print(f"- 商品段合计：{len(prod)} 个商品，{sum(t['min'] for t in prod):.1f} 分钟，{int(sum(t['units'] for t in prod))} 字")
    print(f"- 非商品段合计：{len(non)} 类，{sum(t['min'] for t in non):.1f} 分钟，{int(sum(t['units'] for t in non))} 字")
    if measured:
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
