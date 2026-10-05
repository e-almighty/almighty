"""X 投稿プログラム（DRY RUN）。解析結果から「送信予定」を組み立て、output/outbox に書き出す。

送信予定 ＝ 本体（画像つき）→ 返信①（本体への返信）→ 返信②（返信①への返信）。
夜は朝の投稿を「引用」する（台帳の post_id）。DRY RUN では X に何も送らない。
本番の送信（X API v2）は SHO 確認後に足す。鍵は環境変数から読む（config/social.yaml の credentials はその名前だけ）。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

JST = ZoneInfo("Asia/Tokyo")


def load_social_config(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"dry_run": True, "outbox_dir": "output/outbox"}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _x_units(s: str) -> int:
    return sum(1 if ord(ch) < 128 else 2 for ch in s)


def alt_text(result: dict) -> str:
    """画像の代替テキスト（目の不自由な人・画像が読めない環境向け。X の ALT は 1000 文字まで）。"""
    za, zb = result["zones"]["above"], result["zones"]["below"]
    st = result.get("structure") or {}
    tr = result["trend"]
    bits = [f"{result['symbol']} {result['timeframe_label']}のチャート。相場環境は{tr.get('label_effective', tr['label'])}、現在値 {result['close']:.3f}"]
    if za:
        bits.append(f"上の注目帯 {za[0]['low']:.3f}〜{za[0]['high']:.3f}")
    if zb:
        bits.append(f"下の注目帯 {zb[0]['low']:.3f}〜{zb[0]['high']:.3f}")
    if st.get("key_level") is not None and st.get("direction") in ("up", "down"):
        bits.append(f"{'押し安値' if st['direction'] == 'up' else '戻り高値'} {st['key_level']:.3f}")
    r = result.get("rsi")
    if r:
        bits.append(f"RSI {r['value']:.0f}")
    return "。".join(bits) + "。サポートは赤、レジスタンスは緑、EMA200 は黒の線"


def scheduled_at(result: dict, scfg: dict) -> str:
    """予定時刻（JST）。解析日の朝／夜の定時。DRY RUN では表示用。"""
    sch = scfg.get("schedule") or {}
    hhmm = str(sch.get(result.get("slot", "morning"), "10:05" if result.get("slot") == "morning" else "20:05"))
    day = datetime.strptime(result["analyzed_at_jst"][:10], "%Y-%m-%d")
    h, m = (int(x) for x in hhmm.split(":"))
    return day.replace(hour=h, minute=m, tzinfo=JST).strftime("%Y-%m-%d %H:%M")


def build_plan(result: dict, scfg: dict, posting: dict | None = None) -> dict:
    """解析結果（pipeline.run の戻り値）から送信予定を組み立てる。"""
    cm = result["commentary"]
    posting = posting or {}
    files = result.get("files") or {}
    media = []
    if (scfg.get("media") or {}).get("attach_chart", True) and files.get("png"):
        media.append({"path": files["png"], "alt": alt_text(result) if (scfg.get("media") or {}).get("alt_text", True) else ""})
    posts = [{"seq": 1, "role": "body", "text": cm["post"], "units": cm.get("x_units", _x_units(cm["post"])),
              "media": media, "in_reply_to": None}]
    for i, (txt, u) in enumerate(zip(cm.get("post_replies") or [], cm.get("reply_units") or []), start=1):
        posts.append({"seq": i + 1, "role": f"reply{i}", "text": txt, "units": u, "media": [], "in_reply_to": f"seq:{i}"})
    # 夜は朝の投稿を引用（台帳の post_id）。無ければ引用なしで出す
    quote = None
    verdict = (result.get("changes") or {}).get("verdict") or {}
    if result.get("slot") == "evening" and bool(posting.get("evening_quote_morning", True)):
        pid = verdict.get("prev_post_id")
        quote = {"post_id": pid, "note": "" if pid else "朝の投稿 ID が台帳に無いため引用なし（本番では投稿後に台帳へ書き戻す）"}
        posts[0]["quote_of"] = pid
    return {
        "dry_run": bool(scfg.get("dry_run", True)),
        "created_at_jst": datetime.now(JST).strftime("%Y-%m-%d %H:%M"),
        "analyzed_at_jst": result["analyzed_at_jst"],
        "slot": result.get("slot"),
        "scheduled_at_jst": scheduled_at(result, scfg),
        "jitter_minutes": int((scfg.get("schedule") or {}).get("jitter_minutes", 0)),
        "thread_delay_seconds": int(scfg.get("thread_delay_seconds", 20)),
        "symbol": result["symbol"], "timeframe": result["timeframe"], "source": result.get("source"),
        "post_style": cm.get("post_style"),
        "posts": posts,
        "quote_morning": quote,
        "safety_hits": cm.get("safety_hits", []),
        "post_over_limit": bool(cm.get("post_over_limit")),
        "ledger_writeback": {"post_id": None, "note": "本番では本体の投稿 ID を output/state/last_result.json の post_id に書き戻す（夜の引用に使う）"},
        "credentials_env": scfg.get("credentials") or {},
    }


def plan_markdown(plan: dict) -> str:
    L = [f"# 送信予定（{'DRY RUN・X には送らない' if plan['dry_run'] else '本番'}）",
         "",
         f"- 解析時刻：{plan['analyzed_at_jst']} JST（{ '朝のプラン' if plan['slot'] == 'morning' else '夜の中間報告'}）",
         f"- 予定時刻：{plan['scheduled_at_jst']} JST（本番では 0〜{plan['jitter_minutes']} 分ずらす）",
         f"- 型：{plan['post_style']}（本体 → 返信① → 返信② を {plan['thread_delay_seconds']} 秒間隔で）",
         f"- データ源：{plan['source']}"]
    q = plan.get("quote_morning")
    if q:
        L.append(f"- 朝の投稿の引用：{q['post_id'] or 'なし'}{('（' + q['note'] + '）') if q.get('note') else ''}")
    if plan.get("safety_hits"):
        L.append(f"- 表現チェックで見つかった語：{', '.join(plan['safety_hits'])}")
    if plan.get("post_over_limit"):
        L.append("- **注意：本体が文字数上限を超えています**")
    L.append("")
    for p in plan["posts"]:
        head = {"body": "本体", "reply1": "返信①（本体への返信）", "reply2": "返信②（返信①への返信）"}.get(p["role"], p["role"])
        L.append(f"## {p['seq']}. {head}（{p['units']} 単位）")
        L.append("")
        for m in p.get("media") or []:
            L.append(f"- 画像：`{Path(m['path']).name}`")
            if m.get("alt"):
                L.append(f"- ALT：{m['alt']}")
        if p.get("quote_of"):
            L.append(f"- 引用：{p['quote_of']}")
        L.append("")
        L.append("```")
        L.append(p["text"])
        L.append("```")
        L.append("")
    L.append("※ このファイルは送信予定の下書きです。本番 ON（config/social.yaml の dry_run: false）は SHO 確認後。")
    return "\n".join(L)


def write_plan(result: dict, scfg: dict, base_dir: str | Path, posting: dict | None = None) -> dict:
    """送信予定を output/outbox に .json と .md で書く。戻り値は plan（files を含む）。"""
    plan = build_plan(result, scfg, posting)
    out = Path(base_dir) / str(scfg.get("outbox_dir", "output/outbox"))
    out.mkdir(parents=True, exist_ok=True)
    stamp = result["analyzed_at_jst"].replace("-", "").replace(" ", "_").replace(":", "")
    stem = f"{result['symbol']}_{result['timeframe']}_{stamp}_送信予定"
    (out / f"{stem}.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / f"{stem}.md").write_text(plan_markdown(plan), encoding="utf-8")
    plan["files"] = {"json": str(out / f"{stem}.json"), "md": str(out / f"{stem}.md")}
    return plan


def mark_posted_dry_run(state_dir: str | Path, plan: dict) -> str | None:
    """DRY RUN の疑似投稿 ID を台帳（last_result.json）に書き戻す。夜の「朝の投稿を引用」の流れを通しで確かめるため。
    本番では X API が返した本体の投稿 ID を同じ場所に書く。"""
    p = Path(state_dir) / "last_result.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("analyzed_at_jst") != plan["analyzed_at_jst"]:
        return None
    pid = f"dryrun-{plan['analyzed_at_jst'].replace('-', '').replace(' ', '-').replace(':', '')}"
    d["post_id"] = pid
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return pid
