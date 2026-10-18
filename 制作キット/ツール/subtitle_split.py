#!/usr/bin/env python3
"""ナレーション1文を、字幕の「めくり」単位に分ける（第15章）

## なぜ分けるのか

ナレーション1文をそのまま1枚の字幕にすると、**4〜6秒ものあいだ画面が動きません。**
視聴者には「字幕が止まっている」ように見えます。

そこで、1文を短く割って、**話の進みに合わせてめくります。**

## 守っている3つのきまり

  ① **字幕は必ず1行**にする（2行にしない）
  ② **単語の途中で切らない**
  ③ 1枚は 1.4〜3.0秒 のあいだに収める

②が難しいところです。日本語は単語のあいだに空白がないので、
「どこで切ってよいか」を自分で決める必要があります。

### 切ってよい場所

  ・句読点のうしろ（。、！？・）
  ・助詞のうしろ（を・が・に・で・と・は・も・へ・や・の・から・まで…）
  ・文末表現のうしろ（です・ます・ました・ません・ない…）

### 切ってはいけない場所

  ・漢字と漢字のあいだ（「基礎/控除」のように熟語が割れる）
  ・カタカナの途中（「エレ/ベンラボ」になる）
  ・英数字の途中（「3,0/00万円」になる）
  ・小さい字や長音が行頭に来る（「ま/っすぐ」「デー/ター」）
  ・閉じカッコや句読点が行頭に来る

切ってよい場所が見つからないときは、**上限より長くなっても切りません。**
単語を割るくらいなら、少しはみ出すほうがましだからです。
"""
import re

MAX_LINE = 28          # 1行に入れる最大文字数
#   ★実測で決めています。フォント83のとき28字＝1,672px（使える幅1,760px）。
#     フォントや余白を変えたら、測り直してください。
MIN_SEC = 1.4          # 1枚あたりの最低表示時間（秒）
#   ★短すぎる枚は「表示時間を伸ばす」のではなく「作らない」ようにします。
#     伸ばすと、その後ろの枚が全部うしろへずれて、音声と合わなくなります。
MAX_SEC = 3.0          # 1枚あたりの最長表示時間（秒）
#   ★字数だけで決めると、ゆっくり読む声のときに1枚が5〜6秒出っぱなしになり、
#     「字幕が進まない」と感じられます。
SNAP_SEC = 0.35        # 息つぎに合わせるのは、狙いからこの秒数以内のときだけ

_CUT = set("。、！？!?,・")             # ここで切ってよい（句読点）

# ── 切ってよい場所を決めるための材料 ──────────────────
_PARTICLE1 = set("をがにでとはもへやのかね")          # 助詞1文字
_PARTICLE2 = ["から", "まで", "より", "には", "にも", "では", "でも", "とは",
              "って", "など", "ため", "ので", "のに", "けど", "たり"]
_TAIL = ["です", "ます", "ました", "ません", "でした", "ない", "した", "する",
         "いる", "ある", "なる", "れる", "られる", "ください", "しょう"]

_SMALL = set("ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮーヽヾ々")   # これが行頭に来ないように
_CLOSE = set("」』）)】＞>、。！？!?,.・")                        # 同上
# 助詞の直前がこれなら「言葉に付いた助詞」とみなす（＝そこで切ってよい）
#   「全員に」の「に」は 員(漢字) に付いている → 助詞
#   「かかる」の「か」は か(ひらがな) に続いている → 助詞ではない（動詞の途中）
_CONTENT = re.compile(r"[一-龥ァ-ヴ0-9０-９A-Za-z]")

# これが後ろに続くときは切らない（動詞や決まり文句が割れるため）
#   ★長いものを先に置くこと（「きない」を「きた」より先に当てる）
_NO_START = [
    # 補助動詞・形式名詞
    "いう", "いる", "いれ", "いた", "いき", "いく", "くる", "きた",
    "しまう", "おく", "みる", "ゆく", "こと", "もの", "ため",
    # 「〜できる」が割れるのを防ぐ（申請で/きない → NG）
    "きない", "きます", "きなけれ", "きれば", "きる", "きれ", "きよ",
    # 「〜ではなく」が割れるのを防ぐ（消印では/なく → NG）
    "なければ", "なけれ", "なかっ", "なく", "ない",
    # 「〜として」「〜しました」が割れるのを防ぐ
    "しまし", "しない", "して", "した", "しま", "しな",
]

_KANJI = re.compile(r"[一-龥]")
_KATA = re.compile(r"[ァ-ヴー]")
_ALNUM = re.compile(r"[0-9０-９A-Za-z,.，．]")


def _can_break(s, i):
    """s の i の直前で切ってよいか（i は 1〜len(s)-1）"""
    if i <= 0 or i >= len(s):
        return False
    a, b = s[i - 1], s[i]

    # ── 切ってはいけない ──
    if b in _SMALL or b in _CLOSE:
        return False                      # 小さい字・長音・閉じ記号が行頭に来る
    if _KANJI.match(a) and _KANJI.match(b):
        return False                      # 熟語が割れる（基礎/控除）
    if _KATA.match(a) and _KATA.match(b):
        return False                      # カタカナ語が割れる
    if _ALNUM.match(a) and _ALNUM.match(b):
        return False                      # 数字・英字が割れる
    if a in "「『（(【＜<":
        return False                      # 開きカッコの直後
    # 「では」「には」「とは」「ては」「でも」「にも」が割れるのを防ぐ
    #   （消印で／はなく のように、複合助詞の途中で切れてしまうため）
    if b in "はも" and a in "でにとてやかもの":
        return False
    # 2文字の助詞（から・まで・より・など…）の途中で切らない
    #   （少額か／ら のように割れてしまうため）
    if s[i - 1:i + 1] in _PARTICLE2:
        return False

    # そのうしろに動詞や決まり文句が続くなら切らない（という／できない／ではなく…）
    #   ★2文字固定ではなく前方一致で見る（「きない」「なけれ」のような3文字も拾うため）
    if any(s.startswith(w, i) for w in _NO_START):
        return False

    # ── 切ってよい ──
    if a in _CUT:
        return True                       # 句読点のうしろ

    def attached(word_len):
        """その助詞が『言葉に付いている』か（＝動詞の途中ではないか）"""
        j = i - word_len - 1
        return j >= 0 and bool(_CONTENT.match(s[j]))

    for w in _TAIL:
        if s[max(0, i - len(w)):i] == w:
            # 「なる方」「下がる制度」のように、うしろに名詞が続くときは切らない
            #   （文の終わりではなく、次の言葉を修飾しているため）
            if _KANJI.match(b) or _KATA.match(b):
                return False
            return True                   # 「です」「ます」などのうしろ
    for w in _PARTICLE2:
        if s[max(0, i - len(w)):i] == w and attached(len(w)):
            return True                   # 「から」「まで」などのうしろ
    if a in _PARTICLE1 and attached(1):
        return True                       # 助詞のうしろ
    return False


def _breakpoints(s):
    """その文の中で、切ってよい場所を全部返す"""
    return [i for i in range(1, len(s)) if _can_break(s, i)]


def split_caption(text, max_line=MAX_LINE, sec_per_char=None):
    """1文 → 字幕1枚ぶん（＝1行）の文字列のリスト

    sec_per_char … その行の「1文字あたり何秒か」。渡すと、
                   1枚が MAX_SEC を超えないところでも切ります。
    """
    s = (text or "").strip()
    if not s:
        return []

    # ★ゆっくり読む声のときは、字数の上限も下げます
    limit = max_line
    if sec_per_char and sec_per_char > 0:
        limit = max(6, min(max_line, int(MAX_SEC / sec_per_char)))
    min_chars = int(MIN_SEC / sec_per_char) if sec_per_char else 0

    pts = _breakpoints(s)
    out, start = [], 0
    while len(s) - start > limit:
        # 上限までの中で、いちばん後ろの「切ってよい場所」を探す
        #   ★句読点のうしろだけは、短くなっても切ってよいことにします。
        #     文が終わっているので、短くても意味が通るためです。
        cand = [p for p in pts
                if start < p <= start + limit          # ★必ず前に進むこと
                and (p >= start + min_chars or s[p - 1] in _CUT)]
        if cand:
            cut = cand[-1]
        else:
            # 上限を超えてでも、切ってよい場所まで待つ（単語を割らない）
            after = [p for p in pts if p > max(start, start + limit)]
            if not after:
                break                      # もう切れる場所がない → 残りを1枚に
            cut = after[0]
        out.append(s[start:cut])
        start = cut
    if start < len(s):
        rest = s[start:]
        # 最後が短すぎるときは、前の1枚とつなげる（一瞬で消えるのを防ぐ）
        if out and min_chars and len(rest) < min_chars:
            out[-1] += rest
        else:
            out.append(rest)
    return out or [s]


def share_time(entries, start, end, pauses=None):
    """1文の音声の長さを、字幕1枚ずつに割り振る

    pauses … その音声の中で実際に息をついだ時刻のリスト（あれば使う）
             無ければ、文字数の比で割ります。
    """
    n = len(entries)
    if n == 0:
        return []
    if n == 1:
        return [(start, end)]

    lens = [max(1, len(e)) for e in entries]
    total = sum(lens)
    want, acc = [], 0
    for L in lens[:-1]:
        acc += L
        want.append(start + (end - start) * acc / total)

    # ① 実際の息つぎが「狙いのすぐ近く」にあるときだけ、それに合わせる
    #    ★離れた息つぎに吸い寄せると、かえって音声とずれます
    if pauses:
        used, bounds = set(), []
        for w in want:
            cand = [p for p in pauses if start < p < end and p not in used]
            best = min(cand, key=lambda p: abs(p - w)) if cand else None
            if best is not None and abs(best - w) <= SNAP_SEC:
                used.add(best); bounds.append(best)
            else:
                bounds.append(w)
        bounds = sorted(bounds)
    else:
        bounds = want

    # ② 前後がぶつからないようにだけ整える
    #    ★ここで時間を引き伸ばしません。伸ばすと、以降が全部うしろへずれます。
    times, prev = [], start
    for i, b in enumerate(bounds + [end]):
        b = end if i >= len(bounds) else min(max(b, prev + 0.05), end)
        times.append((prev, b))
        prev = b
    times[-1] = (times[-1][0], end)
    return times


if __name__ == "__main__":
    tests = [
        "財産の合計がこの枠の中に収まっていれば、相続税はかかりません。",
        "ですが、相続税は全員にかかるわけではありません。",
        "お住まいの土地には、評価額が大きく下がる制度もあります。",
        "基礎控除は3,000万円です。",
        "エレベンラボという音声合成サービスを使います。",
        # ↓ 単語の途中で切れていた実例（修正の確認用）
        "期限の判定は、消印ではなく到着日です。",
        "過ぎてしまうと、さかのぼって申請できない場合があります。",
        "この制度は、誰でも利用できるわけではありません。",
        "証券会社の口座を開設して、少額から始めてみるのも一つの方法です。",
    ]
    for t in tests:
        print(f"『{t}』")
        for e in split_caption(t, sec_per_char=0.18):
            print(f"    {e}   （{len(e)}字）")
        print()
