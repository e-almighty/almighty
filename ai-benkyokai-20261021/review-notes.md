# review-notes.md — 判断理由・QA結果・次回への改善

案件: AI勉強会 2026-10-21 第一部 AI「Astra を味方にする夜」（日本営業協会 勉強会）
作成日: 2026-10-20 ／ 担当: AI HTMLスライド社員（seminar-presentation-deck Bundle）／ 制作モデル: Claude Fable 5.1（Claude Code）

## 1. 成果物

| もの | 場所 | 備考 |
|---|---|---|
| HTML デッキ（40 枚） | `slides/index.html` ＋ `css07/`（deck07.css 無改変・**deck07-bright.css 追加**）＋ `js07/`（無改変）＋ `img/logos/` 3 点 | ブラウザで開き矢印キーで送る。`#n` で n 枚目 |
| 1 ファイル版 HTML | `納品/第一部AI_Astraを味方にする夜_2026-10-21.html`（0.58 MB） | CSS・JS・画像を埋め込み。どこで開いても崩れない |
| PDF（40 ページ・16:9） | `納品/第一部AI_Astraを味方にする夜_2026-10-21.pdf`（6.07 MB） | 全ページ撮影 PNG → JPEG q90 → 13.333×7.5 インチ |
| 話者ノート | `speaker-notes.md` | 各スライドの `data-notes` と同じ内容 |
| 全ページ画面写真 | `screenshots/final/slide_001〜040.png`（1920×1080）、俯瞰 `screenshots/overview/sheet_1.png` `sheet_2.png` | 目視 QA の証拠 |
| 生成スクリプト | `build_deck.py`（中身と図解の定義）、`deck_tools.py`（撮影・一覧・1 ファイル化・PDF） | 文言を直したら `python3 build_deck.py` → `python3 deck_tools.py all` |
| 設計書類 | `brief.md` `questions.md` `story-plan.md` `source-map.md` | 8 点セット |

## 2. 何を参考にしたか

| 参照元 | 使い方 |
|---|---|
| `07_AGENTS/ai-slide-employee/AGENT.md` | STEP1〜7、Skill 選択、「Skill 同士で競合したら AGENT.md の目的を優先」 |
| `05_SKILLS/seminar-presentation-deck/` SKILL・MASTER_PROMPT・RUN・knowledge/05-07-output-standard | 8 点セット、固定ブロック、二段階契約、機械 QA、見た目の正本 |
| `engine/07-seminar-style/`（css07・js07・sample-index の骨組み） | `.xop-slide / .xop-canvas / .semantic-layer`（1920×1080 固定）と `tone-*` の仕組み |
| `03_PROJECTS/AI勉強会_20260826/`（前回デッキ・review-notes） | 表紙・流れ・ワーク・まとめの構造。Windows の Chrome 撮影の落とし穴（絶対パス・--no-sandbox） |
| `05_SKILLS/seminar-presentation-deck/output/2026-08-15_elecom-router-basics/review-notes.md` | 明るい地の配色（地 #CFE6F9・文字 #0A2A55）と「黒・灰色は避ける」の確定事項 |
| `01_MEMORY/deck-delivery-preferences.md` | 1 ファイル HTML を必ず出す、短い版を想定する |
| `03_PROJECTS/AI勉強会_20261021/リサーチ_GPT-6Astra_活用と対比.md` | 全スライドの事実と数字（2026-10-19 時点・出典付き） |

## 3. 何を判断したか

### 判断① 明るい地は「上書き CSS」で実現し、正本の CSS は触らなかった

SHO の選択は「明るい地（水色×濃紺）」。07 様式は黒×黄固定で `deck07.css` は改変禁止。エレコム案件は PPTX へ逃げたが、今回は HTML → PDF の依頼なので、`deck07.css` の後に `deck07-bright.css` を読み込んで `.xop-canvas / .sem-* / .corner-stripes / .brand-watermark / .hl / .card-hard` だけ上書きした。骨組み・スケール・ナビは 07 のまま。tone は `sky`（章扉・核心 1 文）／`paper`（本文）／`white`（表）の 3 種に置き換え、黒背景は使っていない。

### 判断② 40 枚を手書きせず、生成スクリプトで組んだ

`build_deck.py` に部品（header / card / grid / rows / table / flow / timeline / kpi / stairs / ladder / two_cols / bubble）と 40 枚の定義を置いた。文言修正や次回の再利用が速く、話者ノートも同じ定義から自動生成できる。

### 判断③ 表紙の汎用カバー画像（黒×黄）は使わなかった

明るい地と衝突するため、表紙は CSS だけで「キーワード 3 カード」を置いた。外部画像はツールのロゴ 3 点のみ（07 エンジン同梱）。

### 判断④ 数字は「公式」と「第三者」を分け、各スライドの下に出典行を置いた

リサーチ要約の「要確認リスト」にある食い違いは、両論併記（OSWorld の Fable 値）か、数字を出さない（Pro の週上限）か、出典を添える（Pro 500）で処理した。WSJ 報道の挙動と OpenAI の説明は別カードに分けた（28 枚目）。

### 判断⑤ アンケート QR は載せなかった

前回の QR（8/26 の Artifact）が今も有効か未確認。40 枚目は「アンケートはこのあとご案内」にとどめた。有効なら `app/参加者アンケートQR.png` を右カードに差し込める。

### 判断⑥ 実績は SHO の実体験だけ

「40〜60 枚を約 2 時間」「勉強会 第 8 回」「Obsidian の頭脳を 2 社の AI で共有」は 9/25 の EvenG2 会話と 04_KNOWLEDGE のノートから。USB 販売の数字は本題ではないので入れていない。架空の数字は入れていない。

### 判断⑦ 枚数は上限側の 40 枚、10 分版の抜き出しを brief に記載

第一部の持ち時間が未確認のため、60 分前後を仮定して 40 枚。短い場合の 13 枚（1・5・6・11・13・16・17・21・22・28・29・34・39）を `brief.md` に書いた。

## 4. 機械 QA 結果

| 検証 | 方法 | 結果 |
|---|---|---|
| 素材リンク欠落 | `scripts/validate_deck_assets.py slides/index.html` | ✅ OK: all local assets exist（欠落 0） |
| 全ページ撮影 | `deck_tools.py shoot`（headless Chrome 1920×1080・絶対パス・--no-sandbox） | ✅ 40/40 枚（初回 1 分 19 秒） |
| 1 ファイル化 | `deck_tools.py standalone` | ✅ 埋め込み画像 6 枚、残った外部参照なし。単体で撮影した 1 枚目が元デッキと同一サイズ（796,896 bytes） |
| PDF | `deck_tools.py pdf`（img2pdf） | ✅ 40 ページ、MediaBox 959.976×540 pt（16:9） |

## 5. 目視 QA で直したもの（俯瞰シート → 原寸 10 枚で確認）

| 枚 | 見つけた崩れ | 直し方 |
|---|---|---|
| 2 | 流れの 7 項目が左 4・右 3 で間隔が不揃い | 2 列グリッド固定の行間に変更、文字 36px |
| 3 | 自己紹介の左カードの文字が小さく余白が多い | 見出し 38px・本文 28px、事業を 3 行に |
| 16・33 | 表の枠が固定高さで、最終行の下に白い空白 | 表を自動高さに（`table()` の bottom を外した） |
| 23 | コピペ用プロンプトの文字が濃紺カードに対して小さい | 31px・行間 1.95 |
| 24 | 10 例のカードが 5 段に収まらず、出典行に重なった | カードの padding を 14px に |
| 25 | 見出しが 2 行に折れてはしご図に近づく | 見出しを短く（「使い分けは三段」） |
| 37 | 見出しの「す」だけ 2 行目に落ちた | 「頭脳は会社に残す」を見出しから外し下のカードへ |
| 32・37 | Claude Code のロゴ（横長 545×312）が正方形枠で潰れた | `logo()` で claude_code だけ幅 1.75 倍 |
| 40 | 次回予告の 2 カードの文字が小さい | 38px・行間 1.5、カードを低く |

直した後の 2・3・7・13・16・18・23・24・25・28・32・33・34・37・40 を原寸で確認。文字のはみ出し・重なり・画像比率の崩れなし。同じ tone が 3 枚続く箇所なし（章扉の直後は必ず本文）。

## 6. 残った注意点・SHO の確認待ち

- デザイン（明るい地）が実際の投影でどう見えるか。会場のプロジェクターが暗いと薄い水色の章扉は白っぽく見える可能性がある
- 3 枚目の自己紹介の文言（事業内容の表現）
- 17・18 枚目は SHO の ChatGPT 画面写真（Work への切り替え・Computer Use の確認画面）を入れるとより強い。画像を `slides/img/` に置き `build_deck.py` で差し込める
- アンケート QR（判断⑤）
- 数字は 2026-10-19 時点。当日までに大きな発表があれば 5・16・33 枚目を見直す

## 7. 次回に固定できること

- `css07/deck07-bright.css`：07 様式を明るい地にする上書き CSS。他案件でもそのまま使える
- `build_deck.py` の部品：header / card / grid / rows / table / flow / timeline / kpi / stairs / ladder / two_cols / bubble / logo
- `deck_tools.py`：Windows で「撮影 → 一覧 → 1 ファイル化 → PDF」を 1 コマンドで通す道具
- 教訓：5 段グリッドのカードは padding 14〜18px にする／見出しは 56px で全角 24 文字まで（超えると折れる）／横長ロゴは枠の幅を変える
