ユーザーが「スキル作って」「〇〇をスキルにして」と言ったら、次の手順で進める。必ず日本語。

1. 足りないことだけまとめて聞く：使う場面（何と言ったら動くか）／手順／できあがるもの／守る決まり
2. スキル名を半角英小文字とハイフンで決め、3つのファイルを作る
 - SKILL.md：先頭は「---」で囲んだ name と description の2項目だけ。description には使う場面と、ユーザーが言いそうな言葉を3つ以上入れる。本文は日本語で 目的／使う場面／手順／できあがるもの／確認／禁止事項。会話を知らなくても読めるように書き、AI固有の道具名や絶対パスは書かない
 - agents/openai.yaml：display_name・short_description・default_prompt と allow_implicit_invocation: true
 - CHATGPT.md：SKILL.md を1,500文字以内に縮めた指示文
3. Dropbox につながっていれば /HIRATA/Obsidian/Almighty-AI-Brain/ の中に保存する
 - 05_SKILLS/<名前>/ に3つ全部
 - .claude/skills/<名前>/SKILL.md
 - .agents/skills/<名前>/ に SKILL.md と agents/openai.yaml
 - 05_SKILLS/00_SYSTEM/universal-skill-builder/目次待ち/<日付>_<名前>.md に目次1件分の文と「Git未反映」
 同名があれば作らず確認。保存できなければ中身をパス付きで表示
4. 報告：スキル名、保存した場所、保存できなかったところ、使い始め方
