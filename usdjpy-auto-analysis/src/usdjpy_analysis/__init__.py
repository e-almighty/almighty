"""USDJPY 自動テクニカル分析（解析 → ライン → 画像 → 日本語解説）。

モジュール構成:
  market_data  ローソク足の読み込み（CSV / GMOコイン公開API）
  indicators   EMA・ATR など（Pine Script の ta.* と同じ定義）
  swings       スイング高値・安値（Pivot High / Low）
  levels       サポート・レジスタンス候補のクラスタリングと重要度
  trend        相場環境の判定（強い上昇〜強い下落の5分類）
  trendlines   上昇・下降トレンドライン候補
  chart        投稿用チャート画像（PNG）
  commentary   日本語の解説文
  pipeline     上のすべてをつなぐ
"""

__version__ = "0.1.0"
