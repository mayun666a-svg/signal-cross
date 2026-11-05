#!/usr/bin/env python3
"""统计对照结果：交集 vs 单边，24 小时后的涨跌与胜率。用法：python analyze.py cross_log.csv"""
import csv, sys
from collections import defaultdict
from datetime import datetime

path = sys.argv[1] if len(sys.argv) > 1 else "cross_log.csv"
rows = list(csv.DictReader(open(path, encoding="utf-8")))
if not rows:
    raise SystemExit("没有数据")

def t(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")

# 同一币种按时间排序，用后续 24h 内的价格算收益
by_sym = defaultdict(list)
for r in rows:
    if r["price"]:
        by_sym[r["symbol"]].append((t(r["ts"]), float(r["price"]), r))

groups = {"我的信号": [], "独立评分": [], "两边都看多": []}
for sym, arr in by_sym.items():
    arr.sort()
    for i, (ts, px, r) in enumerate(arr):
        fwd = next((p for (t2, p, _) in arr[i:] if (t2 - ts).total_seconds() >= 24 * 3600), None)
        if fwd is None:
            continue
        ret = fwd / px - 1
        if r["my_action"] == "long":
            groups["我的信号"].append(ret)
        if r["alt_signal"] == "long":
            groups["独立评分"].append(ret)
        if r["both_long"] == "1":
            groups["两边都看多"].append(ret)

print(f"{'组':<12}{'样本':>6}{'24h涨':>9}{'胜率':>8}{'平均':>9}")
print("-" * 46)
for k, v in groups.items():
    if not v:
        print(f"{k:<12}{0:>6}{'-':>9}{'-':>8}{'-':>9}")
        continue
    win = sum(1 for x in v if x > 0) / len(v)
    print(f"{k:<12}{len(v):>6}{(sum(x > 0 for x in v) / len(v) * 100):>8.0f}%{win * 100:>8.0f}%{sum(v) / len(v) * 100:>8.2f}%")
print("\n说明：样本 < 50 笔时结论不成立，只作观察。")
