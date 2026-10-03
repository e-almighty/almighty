"""ローソク足の読み込み。

3つの入口を同じ形（DataFrame: index=UTC の時刻, 列 open/high/low/close/volume）にそろえる。

  load_csv(path)
      TradingView MCP（mcp-tv-get-ohlcv）の書き出し: 列 t,o,h,l,c,v（t は UTC の Unix 秒）
      一般的な形: 列 time,open,high,low,close[,volume]（time は ISO か Unix 秒）
  fetch_gmo_klines(symbol, interval, dates)
      GMOコイン 外国為替 公開API（無料・キー不要）
      ※ クラウドの作業部屋からは通信できないため 2026-10-03 時点で未検証。SHO の PC で確認する。
  resample(df, rule)
      下位足から上位足を作る（例: 1h → 4h）。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

GMO_KLINES_URL = "https://forex-api.coin.z.com/public/v1/klines"
GMO_TICKER_URL = "https://forex-api.coin.z.com/public/v1/ticker"

_COLS = ["open", "high", "low", "close", "volume"]


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    rename = {"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume",
              "Time": "time", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume",
              "timestamp": "time", "datetime": "time", "date": "time"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "time" not in df.columns:
        raise ValueError("時刻の列（t または time）が見つかりません")
    t = df["time"]
    if pd.api.types.is_numeric_dtype(t):
        unit = "ms" if float(t.iloc[-1]) > 1e11 else "s"
        idx = pd.to_datetime(t, unit=unit, utc=True)
    else:
        idx = pd.to_datetime(t, utc=True)
    out = pd.DataFrame({c: pd.to_numeric(df[c], errors="coerce") for c in _COLS if c in df.columns})
    if "volume" not in out.columns:
        out["volume"] = 0.0
    out.index = pd.DatetimeIndex(idx, name="time")
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out = out.dropna(subset=["open", "high", "low", "close"])
    return out[_COLS]


def load_csv(path: str | Path) -> pd.DataFrame:
    return _normalize(pd.read_csv(path))


def load_json(path: str | Path) -> pd.DataFrame:
    """mcp-tv-get-ohlcv の生の JSON（{"candles":[{t,o,h,l,c,v}...]} または配列）を読む。"""
    import json
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        for key in ("candles", "data", "ohlcv", "bars"):
            if key in raw:
                raw = raw[key]
                break
    return _normalize(pd.DataFrame(raw))


def fetch_gmo_klines(symbol: str = "USD_JPY", interval: str = "4hour", dates: list[str] | None = None,
                     price_type: str = "BID", timeout: int = 15) -> pd.DataFrame:
    """GMOコイン公開APIからローソク足を取る。

    interval: 1min 5min 10min 15min 30min 1hour 4hour 8hour 12hour 1day 1week 1month
    dates:    1hour 以下は YYYYMMDD（1日ずつ）、4hour 以上は YYYY（1年ずつ）。省略時は今年。
    """
    import requests
    if dates is None:
        dates = [pd.Timestamp.utcnow().strftime("%Y")]
    frames = []
    for d in dates:
        r = requests.get(GMO_KLINES_URL, params={"symbol": symbol, "priceType": price_type,
                                                 "interval": interval, "date": d}, timeout=timeout)
        r.raise_for_status()
        body = r.json()
        if body.get("status") != 0:
            raise RuntimeError(f"GMO klines エラー: {body}")
        rows = body.get("data", [])
        if rows:
            df = pd.DataFrame(rows).rename(columns={"openTime": "time"})
            df["time"] = pd.to_numeric(df["time"])
            frames.append(df)
    if not frames:
        raise RuntimeError("GMO klines: データが空でした")
    return _normalize(pd.concat(frames, ignore_index=True))


def fetch_gmo_ticker(symbol: str = "USD_JPY", timeout: int = 10) -> dict:
    import requests
    r = requests.get(GMO_TICKER_URL, timeout=timeout)
    r.raise_for_status()
    for item in r.json().get("data", []):
        if item.get("symbol") == symbol:
            return item
    raise RuntimeError(f"{symbol} がティッカーに見つかりません")


def resample(df: pd.DataFrame, rule: str, origin: str = "epoch", offset: str | None = None) -> pd.DataFrame:
    """下位足から上位足を作る。TradingView の FX 4時間足は UTC 00:00 起点なので既定のまま使える。"""
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    kw = {"label": "left", "closed": "left"}
    if rule[-1:].lower() in ("h", "t", "s") or rule.lower().endswith("min"):
        kw.update({"origin": origin, "offset": offset})   # origin は時間単位の足にだけ効く
    out = df.resample(rule, **kw).agg(agg)
    return out.dropna(subset=["open"])
