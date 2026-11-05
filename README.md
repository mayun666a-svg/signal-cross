# signal-cross

独立记录我的信号与另一套评分的一致性，**只写 CSV，不推送、不下单**。

## 文件
- `check.py` 每 15 分钟拉数据，记录两边分数到 `cross_log.csv`
- `analyze.py` 统计 24h 后表现：单边 vs 交集

## Secrets（必填）
- `MINE_URL` 例如 https://paper.shenyue.dpdns.org
- `MINE_KEY` 接口 key

## 用法
本地：`MINE_URL=... MINE_KEY=... python check.py`
统计：`python analyze.py cross_log.csv`
