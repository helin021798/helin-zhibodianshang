#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直播策划确定性测算（零依赖）。

子命令:
  roi   保本 ROI 与目标 ROI
        python3 live_calc.py roi --margin 30 --sign-rate 80 [--fee 5] [--target-net 5]
  pit   坑产预估与目标缺口
        python3 live_calc.py pit --items "主推A:299:300,福利B:39.9:800" [--target 200000]
        python3 live_calc.py pit --file 货盘.tsv [--target 200000]
        (TSV/CSV 列: 品名, 直播价, 预估单量[, 角色]; 首行可为表头)
  mech  机制让利汇总
        python3 live_calc.py mech --items "赠品小样:12:500,免单抽奖:299:3" [--gmv 200000 --margin 40]

百分比参数一律按百分数理解：30 表示 30%，1 表示 1%，0.6 表示 0.6%；也可写成 30%。
输出只基于输入，不含平台规则或行业基准。
"""
import argparse
import csv
import sys
from pathlib import Path


def pct(v, name="", warn_below=0.0):
    """百分数转小数。30、30% 都表示 30%；不再把 ≤1 的数当小数，避免 1% 扣点被读成 100%。"""
    text = str(v).strip().rstrip("%").strip()
    try:
        value = float(text) / 100
    except ValueError:
        sys.exit(f"{name or '百分比'}格式错误: {v}（写 30 或 30% 表示 30%）")
    if warn_below and 0 < value < warn_below:
        print(f"⚠ {name} 按 {value:.2%} 计算；如果想表示 {value * 100:.0%}，请写 {value * 10000:g}", file=sys.stderr)
    return value


def money(v):
    return f"{v:,.2f}"


def cmd_roi(a):
    margin = pct(a.margin, "毛利率", warn_below=0.01)
    sign = pct(a.sign_rate, "签收率", warn_below=0.01)
    fee, net = pct(a.fee, "变动费率"), pct(a.target_net, "目标净利率")
    realized = sign * (margin - fee)
    print("== 保本 ROI 测算 ==")
    print(f"毛利率 {margin:.1%} | 签收率 {sign:.1%} | 其他变动费率 {fee:.1%}")
    print(f"每 1 元前端 GMV 实得毛利 ≈ 签收率 × (毛利率 − 变动费率) = {realized:.4f}")
    if realized <= 0:
        print("结论: 实得毛利 ≤ 0，任何投流都亏损，先调整价格、成本或退货率。")
        return
    print(f"保本 ROI（前端 GMV ÷ 投放）= 1 ÷ {realized:.4f} = {1 / realized:.2f}")
    if net > 0:
        if realized - net <= 0:
            print(f"目标净利率 {net:.1%} 高于实得毛利率，无法通过投流实现。")
        else:
            print(f"目标 ROI（留 {net:.1%} 净利）= 1 ÷ ({realized:.4f} − {net:.4f}) = {1 / (realized - net):.2f}")
    print("\n每投 100 元在不同 ROI 下的毛利与净利:")
    print("ROI\t实得毛利\t扣投放后")
    for r in (1, 2, 3, 4, 5, 6, 8, 10):
        gp = 100 * r * realized
        print(f"{r}\t{gp:.1f}\t{gp - 100:+.1f}")
    print("\n提示: 前端 ROI 不含退货；未计退货运费、人力、坑位费，需等确收后复核。")


def parse_items(spec, n):
    rows = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(":")
        if len(parts) < n:
            sys.exit(f"格式错误: {chunk}（需要 {n} 段，用冒号分隔）")
        rows.append(parts)
    return rows


def read_table(path):
    p = Path(path)
    if not p.exists():
        sys.exit(f"找不到文件: {path}")
    text = p.read_text(encoding="utf-8-sig")
    if not text.strip():
        sys.exit(f"文件为空: {path}")
    delim = "\t" if "\t" in text.splitlines()[0] else ","
    rows = [r for r in csv.reader(text.splitlines(), delimiter=delim) if r and any(c.strip() for c in r)]
    try:
        float(rows[0][1])
    except (ValueError, IndexError):
        rows = rows[1:]
    return rows


def cmd_pit(a):
    if a.file:
        rows = read_table(a.file)
    elif a.items:
        rows = parse_items(a.items, 3)
    else:
        sys.exit("请提供 --items 或 --file")
    items = []
    for r in rows:
        name, price, units = r[0].strip(), float(r[1]), float(r[2])
        role = r[3].strip() if len(r) > 3 else ""
        items.append((name, role, price, units, price * units))
    total = sum(i[4] for i in items)
    print("== 坑产预估 ==")
    print("品名\t角色\t直播价\t预估单量\t预估GMV\t占比")
    for name, role, price, units, g in sorted(items, key=lambda x: -x[4]):
        share = g / total if total else 0
        print(f"{name}\t{role or '-'}\t{money(price)}\t{units:g}\t{money(g)}\t{share:.1%}")
    print(f"合计预估 GMV: {money(total)}")
    top = sorted((i[4] for i in items), reverse=True)
    if len(top) > 5 and total:
        print(f"前 5 个品占比: {sum(top[:5]) / total:.1%}")
    if total:
        print(f"第一名占比: {top[0] / total:.1%}（主推应明显领先）")
    if a.target:
        gap = a.target - total
        if gap > 0:
            print(f"目标 {money(a.target)}，缺口 {money(gap)}（{gap / a.target:.1%}）。补法: 加品 / 拉高单品单量 / 延长时长 / 加预算或预约。")
            best = max(items, key=lambda x: x[2])
            print(f"参考: 仅靠最高价品「{best[0]}」补缺口需再卖约 {gap / best[2]:.0f} 单。")
        else:
            print(f"目标 {money(a.target)}，预估已覆盖，余量 {money(abs(gap))}。")
    print("提示: 单量是假设，请在方案中标注来源（历史数据/预约推算/待确认）。")


def cmd_mech(a):
    if not a.items:
        sys.exit("请提供 --items")
    rows = parse_items(a.items, 3)
    total = 0.0
    print("== 机制让利汇总 ==")
    print("机制\t单份成本\t份数\t小计")
    for name, cost, qty in (r[:3] for r in rows):
        sub = float(cost) * float(qty)
        total += sub
        print(f"{name.strip()}\t{money(float(cost))}\t{float(qty):g}\t{money(sub)}")
    print(f"让利总额: {money(total)}")
    if a.margin and not a.gmv:
        print("提示: 只给了 --margin 没给 --gmv，无法计算让利占毛利。")
    if a.gmv:
        print(f"占预估 GMV: {total / a.gmv:.2%}")
        if a.margin:
            gp = a.gmv * pct(a.margin, "毛利率", warn_below=0.01)
            if gp <= 0:
                print("预估毛利 ≤ 0，无法计算让利占毛利；先核对毛利率。")
                return
            print(f"预估毛利 {money(gp)}，让利占毛利 {total / gp:.1%}")
            if total / gp > 0.3:
                print("⚠ 让利超过毛利三成，建议改为确认收货后兑现、抽奖或换低成本高感知赠品。")


def main():
    ap = argparse.ArgumentParser(description="直播策划确定性测算")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("roi")
    r.add_argument("--margin", required=True, help="毛利率（百分数），30 或 30%% 表示 30%%")
    r.add_argument("--sign-rate", default="100", help="签收率（百分数，1−退货率），默认 100")
    r.add_argument("--fee", default="0", help="其他按 GMV 计的变动费率（百分数），如佣金、平台扣点；1 表示 1%%")
    r.add_argument("--target-net", default="0", help="希望保留的净利率（百分数）")
    p = sub.add_parser("pit")
    p.add_argument("--items", help='"品名:直播价:单量[:角色],..."')
    p.add_argument("--file", help="TSV/CSV 货盘文件")
    p.add_argument("--target", type=float, help="本场 GMV 目标")
    m = sub.add_parser("mech")
    m.add_argument("--items", help='"机制:单份成本:份数,..."')
    m.add_argument("--gmv", type=float, help="预估 GMV")
    m.add_argument("--margin", help="平均毛利率（百分数）")
    a = ap.parse_args()
    {"roi": cmd_roi, "pit": cmd_pit, "mech": cmd_mech}[a.cmd](a)


if __name__ == "__main__":
    main()
