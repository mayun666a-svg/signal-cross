#!/usr/bin/env python3
"""记录模式：把我的信号和独立三级周期评分做对照，只写 CSV，不推送。
需要：requests。我的接口地址与 key 从环境变量读取，不写死在代码里。
"""
import csv, json, os, sys, time
from datetime import datetime, timezone
import requests

SYMBOLS = [x.strip().upper() for x in os.environ.get("SYMBOLS","BTCUSDT,ETHUSDT,ZECUSDT,SOLUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT,LINKUSDT").split(",") if x.strip()]
MINE = os.environ.get("MINE_URL", "").rstrip("/")
KEY = os.environ.get("MINE_KEY", "")
CSV_PATH = os.environ.get("CSV_PATH", "cross_log.csv")
FIELDS = ["ts","symbol","price","my_score","my_action","alt_score","alt_signal","both_long"]

def klines(sym, interval, limit=220):
    for host in ("https://api.binance.com","https://data-api.binance.vision"):
        try:
            r = requests.get(f"{host}/api/v3/klines",
                             params={"symbol": sym, "interval": interval, "limit": limit}, timeout=15)
            if r.ok:
                d = r.json()
                if len(d) >= 60:
                    # 丢掉未收盘的最后一根
                    return [float(x[4]) for x in d[:-1]]
        except Exception:
            pass
    return []

def ema(a, n):
    k = 2.0 / (n + 1); e = a[0]; out = [e]
    for v in a[1:]:
        e = v * k + e * (1 - k); out.append(e)
    return out

def rsi(a, n=14):
    g = l = 0.0
    for i in range(1, n + 1):
        d = a[i] - a[i-1]
        g += max(d, 0) / n; l += max(-d, 0) / n
    for i in range(n + 1, len(a)):
        d = a[i] - a[i-1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
    return 100.0 if l == 0 else 100 - 100 / (1 + g / l)

def macd_hist(a):
    e12, e26 = ema(a, 12), ema(a, 26)
    line = [x - y for x, y in zip(e12, e26)]
    sig = ema(line, 9)
    return line[-1] - sig[-1], line[-2] - sig[-2]

def score_one(closes):
    """独立评分：趋势 + 动量 + RSI，与现有系统不同源。"""
    if len(closes) < 60:
        return None
    e20, e50 = ema(closes, 20)[-1], ema(closes, 50)[-1]
    px = closes[-1]
    s = 0
    s += 30 if px > e20 > e50 else (-30 if px < e20 < e50 else 0)
    s += 20 if px > e50 else -20
    h, hp = macd_hist(closes)
    s += 20 if h > 0 and h > hp else (10 if h > 0 else (-20 if h < hp else -10))
    r = rsi(closes)
    if r > 75: s -= 15
    elif r < 30: s += 10
    elif 45 <= r <= 65: s += 10
    return max(-100, min(100, s))

def alt_score(sym):
    parts, ok = [], True
    for tf, w in (("1d", 0.5), ("4h", 0.3), ("15m", 0.2)):
        c = klines(sym, tf)
        s = score_one(c)
        if s is None:
            ok = False; break
        parts.append(s * w)
    if not ok:
        return None, None
    total = round(sum(parts))
    sig = "long" if total >= 35 else ("short" if total <= -35 else "wait")
    return total, sig

def mine():
    if not MINE or not KEY:
        return {}
    try:
        r = requests.get(f"{MINE}/signals", params={"key": KEY, "symbols": ",".join(SYMBOLS), "interval": "1d"}, timeout=25)
        if not r.ok:
            return {}
        return {x["symbol"]: x for x in r.json().get("signals", []) if "err" not in x}
    except Exception:
        return {}

def main():
    m = mine()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    rows = []
    for s in SYMBOLS:
        a, sig = alt_score(s)
        x = m.get(s, {})
        price = x.get("price")
        if price is None:
            c = klines(s, "1d", 3)
            price = c[-1] if c else None
        rows.append([ts, s, price, x.get("score"), x.get("action"), a, sig,
                     1 if (x.get("action") == "long" and sig == "long") else 0])
        time.sleep(0.25)
    new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(FIELDS)
        w.writerows(rows)
    print(f"{ts} 记录 {len(rows)} 行 -> {CSV_PATH}")

if __name__ == "__main__":
    main()
