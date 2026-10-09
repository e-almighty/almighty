# 少人数（1〜5名）で会員制マッチングネットワークを回し、拡大するためのデジタル運営とAI活用（えんつなぎバンク／ETB向け）

> 調査メモ（2026-10-09時点）。注意：今回の調査環境では各ベンダー公式ドメイン（kintone.cybozu.co.jp、stripe.com、cloudsign.jp、lycbiz.com 等）への直接取得が DNS エラーで失敗したため、料金の多くは ITreview・imitsu・atsoho などの比較サイトや解説記事を経由した**二次情報**である。比較サイトの一部は「2026年7月28日に公式ページを確認」と明記している。契約前に必ず公式ページで再確認すること。USD の円換算は推論で、1ドル≒150円と仮定している。

---

## Q1. 日本で使える会員CRM／コミュニティ基盤：2026年の料金と、50／300／3,000名規模での適合

### Takeaway
小さく始めるなら「Googleワークスペース＋フォーム／スプレッドシート（またはNotion）＋LINE公式アカウント」が月額数千円で済み、最も安い。会員300名を超えて紹介・成約の監査が必要になったら kintone（最低10ユーザー契約）か HubSpot Starter を正本DBにする。国産のコミュニティ専用SaaS（coorum／commune／OSIRO）はいずれも料金非公開で、企業向けの見積もり型である。海外の Circle／Mighty は月89〜199ドル程度に決済手数料が上乗せされ、日本語対応と国内決済の面で弱い。

### Cited Findings
**汎用CRM・業務DB**
- kintone：ライトコース 1,000円/ユーザー/月、スタンダード 1,800円/ユーザー/月で、どちらも**最低10ユーザー**。スタンダードには外部連携とプラグインが含まれる。1人で使ってもスタンダードは月18,000円になる — [ITreview kintone価格](https://www.itreview.jp/products/kintone/price)、[atsoho kintone](https://atsoho.com/apps/p/kintone)。旧体系「5ユーザー〜／追加1,200円」と書く比較サイトもあり、2024年11月の価格改定以前の情報が混じっている — [hatenabase 2026年版kintone料金](https://hatenabase.jp/blog/%E3%80%902026%E5%B9%B4%E5%AE%8C%E5%85%A8%E7%89%88%E3%80%91kintone%E3%81%AE%E6%96%99%E9%87%91%E3%81%AF%E9%AB%98%E3%81%84%EF%BC%9F%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9%E8%B2%BB%E3%81%8B%E3%82%89/)
- HubSpot：Starter は年払いで 1シート月840円、月払いなら2,400円（2026年8月時点の表示） — [issoh](https://www.issoh.co.jp/column/details/17100/)、[atsoho HubSpot CRM](https://atsoho.com/apps/p/hubspot-crm)。Marketing Hub Starter は 6,000円/月（コンタクト1,000件込み）とする掲載もある — [ITreview HubSpot Marketing Hub](https://www.itreview.jp/products/hubspot-marketing-hub/price)。Starter Customer Platform（5つのHubの基本機能をまとめたもの）は「月額2万円台」とする導入支援会社の記事があるが、内訳の根拠は示されていない — [start-link](https://start-link.jp/hubspot-ai/adoption/starter-customer-platform)
- Salesforce：Power of Us Program で、適格な非営利団体は Nonprofit Cloud または Sales/Service Cloud を**10ライセンス無償**で受けられる（APACの料金ページ） — [Salesforce AP Nonprofit Pricing](https://www.salesforce.com/ap/nonprofit/pricing/)。日本語ページは「非営利団体向けの価格」とだけ書き、10本無償の記載は確認できなかった — [Salesforce JP Nonprofit](https://www.salesforce.com/jp/nonprofit/)。無償ライセンスは出発点にすぎず、業務に合わせて構築する費用は別に必要という指摘がある — [magicfuse](https://magicfuse.co/blog/salesforce-power-of-us-program)
- Notion：Plus は年払いで約10ドル/メンバー/月（月払い12ドル）、Business は約20ドル（月払い24ドル）。フル機能のNotion AI（エージェント、AI会議メモ、エンタープライズ検索）は Business 以上に同梱で、Free と Plus は回数限定の試用のみ — [Breeze](https://www.breeze.pm/articles/notion-ai-pricing)、[automationatlas](https://automationatlas.io/answers/notion-pricing-explained-2026/)。Business を18ドルとする古い記事も残っている — [tinycommand](https://tinycommand.com/blogs/notion-pricing-explained)
- Google Workspace（2025年3月17日改定、年契約・税抜）：Business Starter 800円、Standard 1,600円、Plus 2,500円/ユーザー/月。Gemini はアドオン販売が終わり、各プランに標準搭載。Meet の録画は Standard 以上。Business 系プランは最大300ユーザーまで — [PC Watch](https://pc.watch.impress.co.jp/docs/news/1654889.html)、[SHIFT AI](https://ai-keiei.shift-ai.co.jp/google-workspace-ryoukin/)、[imitsu](https://saas.imitsu.jp/cate-groupware/service/813/price)。フレキシブル契約は Starter 950円、Standard 1,900円とする比較表もある — 同上

**LINE**
- LINE公式アカウント：コミュニケーションプランは0円で月200通（2023年6月改定で1,000通から減った）、ライトプランは5,000円（税別）で月5,000通、スタンダードプランは15,000円（税別）で月30,000通。追加配信ができるのはスタンダードのみで、1通〜3円 — [ligla](https://ligla.jp/blog/line-official/plan/)、[サングローブ](https://www.sungrove.co.jp/line-official-account-plan/)。2026年10月1日に追加メッセージ料金の改定予定とする記述があるが、未確認 — [ligla](https://ligla.jp/blog/line-official/cost/)
- Lステップ：プランはフリー、スタート、スタンダード、プロの4種で、初期費用0円。LINE公式アカウントの利用料は別にかかる — [Lステップ公式プラン](https://linestep.jp/lp/01/plan.html)。スタートは5,000円（月5,000通）、スタンダードは21,780円（税込、月30,000通）とする掲載がある — [imitsu Lステップ](https://saas.imitsu.jp/cate-line-marketing-tool/service/3175/price)。2026年に値上げしたとする記事もあるが、プラン名が公式と一致しないため信頼性は低い — [app-tatsujin](https://app-tatsujin.com/l-step-2026-pricing-plans-changes/)

**コミュニティ専用プラットフォーム**
- coorum（Asobica）：Standard、Premium、Enterprise の3プランで、料金は非公開 — [ITreview coorum](https://www.itreview.jp/products/coorum/price)。タグ管理機能を追加済み — [commercepick](https://www.commercepick.com/archives/56180)
- commmune：Light、Standard、Professional、Enterprise の4プランで、すべて要問い合わせ。Enterprise は数万人規模向け — [BOXIL](https://boxil.jp/service/5460/)、[strate](https://strate.biz/web-cs/commmune/)
- OSIRO：会員管理、月額・スポット課金、コンテンツ配信をまとめたクローズドSNS型のプラットフォーム。本体の料金は検索で見つからなかった。利用例として、読書コミュニティ「ほんのもり」はレギュラープラン月額1,980円（税込）で運営している — [OSIRO news](https://osiro.it/news/14324)、[THE BRIDGE](https://thebridge.jp/2020/02/osiro/)
- Circle：Professional は年払いで約89ドル/月（月払い129ドル、ページのコードには99ドルとの記載もある）、Business は199ドル、最上位の Circle Plus は個別見積もり。取引手数料は Professional 2%、Business 1%、Plus 0.5% で、Stripe の手数料とは別にかかる。無料プランはなく、14日間の試用がある — [cartmango](https://cartmango.com/circle-so-pricing/)、[schoolmaker](https://schoolmaker.com/blog/circle-so-pricing)。2026年4月に上位プランを値上げしたとする記録もある — [costbench](https://costbench.com/changelog/circle-price-increase-2026-04/)
- Mighty Networks：情報源によってプラン構成が違う。Launch は95ドル（年払い79ドル）で手数料2%、Scale は215ドル（年払い179ドル）で手数料1% — [kourses](https://kourses.com/?p=11768)。2026年4月と7月にプランが削除され、79〜179ドルの3プランになったという記録がある — [costbench](https://costbench.com/changelog/mighty-networks-plan-removed-2026-07/)。旧プラン名を載せた記事もある — [schoolmaker](https://www.schoolmaker.com/blog/mighty-networks-pricing)

**イベント**
- Peatix：無料イベントは手数料0円。有料イベントは販売額の4.9%＋チケット1枚あたり99円で、初期費用と月額は0円。売上の振込に210円かかるとする情報もある — [ITreview Peatix](https://www.itreview.jp/products/peatix/price)、[サングローブ](https://www.sungrove.co.jp/peatix/)

### Inferences
- **50名規模**：Google Workspace Business Standard（1,600円×運営者1〜2名）＋Googleフォーム／スプレッドシート（またはNotion Plus）＋LINE公式（無料〜ライト5,000円）で十分に回る。会員200名に月1通配信すると無料枠200通を使い切るため、早めにライトプランが必要になる。
- **300名規模**：会員・紹介・成約・報酬の台帳を、変更履歴とアクセス権を持つDBに移す。kintone スタンダードは10ユーザー×1,800円＝月18,000円。運営者が数名でも10ユーザー分の課金になるが、ゲスト機能や外部フォーム連携で会員自身に入力させる運用が組める。HubSpot Starter を数シートだけ使う構成も安い。LINE はスタンダード（15,000円）か、Lステップでセグメント配信と予約を自動化する。
- **3,000名規模**：ETB の価値が会員同士の交流と相互紹介にあるなら、coorum／commune（見積もり型、月額は数十万円規模と推測されるが未確認）や Circle Business（約3万円＋手数料1%）といったコミュニティ専用基盤を検討する段階になる。ただし国内決済と日本語のサポートを考えると、「LINE＋kintone／HubSpot＋会員ページ（WordPressや会員サイトSaaS）」の組み合わせを続けるほうが総コストは低い可能性がある。
- Salesforce の無償10ライセンスは、ETB が非営利法人でなければ対象外になる可能性が高い。営利の株式会社なら選択肢から外してよい。

### Gaps
- kintone、Stripe、LINE、クラウドサインの公式ページを直接確認できなかった（DNSエラー）。
- OSIRO、coorum、commune の実際の見積もり額と最低契約期間。
- Lステップの2026年時点の公式料金（公式ページの検索結果に金額が出なかった）。
- 2026年10月のLINE追加メッセージ料金改定の内容。

---

## Q2. マッチングの仕組み化（「できること」「探していること」のプロフィール設計、タグ、AIによる提案）と、紹介→成約→報酬を透明・監査可能に追跡する方法

### Takeaway
プロフィールは「できること（Offer）」「探していること（Need）」を構造化タグと自由記述の2層で持たせ、AIには候補を出させるだけにする。紹介を成立させる判断は人が行う。紹介→成約→報酬は「紹介ID」を軸に1レコードで状態遷移を記録し、変更履歴、成約の証憑（契約書・請求書）、双方の確認を残すと監査に耐える。報酬設計は特商法の連鎖販売取引、職業安定法、弁護士法72条、景表法（ステマ規制）に抵触しない形にすることが前提になる。

### Cited Findings
- 連鎖販売取引の定義：物品販売やサービス提供の事業で、再販売・受託販売・販売のあっせんをする人を「特定の利益」が得られると勧誘し、取引の条件として**1円以上の負担**をさせるもの。入会金など、名目を問わず負担があれば該当しうる。紹介料・マージン・ボーナスは「特定利益」にあたる — [money-lifehack](https://money-lifehack.com/article/8452)、[MC法律事務所](https://www.mc-law.jp/kigyohomu/17281)
- 連鎖販売取引の禁止行為：勧誘前に氏名や事業者名などを告げる義務がある。重要事項（特定利益・特定負担・解除条件）を告げない、または事実と違うことを告げると罰則がある（6月以下の拘禁刑、100万円以下の罰金、またはその併科） — [MC法律事務所](https://www.mc-law.jp/kigyohomu/17281)
- 職業安定法：求人者・求職者が提供した情報を運営者がそのまま掲載し、仲介しなければ有料職業紹介の許可は不要。運営者が情報にコメントや宣伝文句を加える、日程調整や連絡を代行する、といった関与をすると職業紹介に当たる可能性が高まる — [モノリス法律事務所](https://monolith.law/corporate/paid-site-job-permission)
- 弁護士法72条：弁護士でない者が報酬目的で法律事務の周旋を業として行うことは禁止されている。士業を紹介して紹介料を得る設計には注意が要る — [MC法律事務所](https://www.mc-law.jp/?p=17179)。法務省は2026年8月に、AI等を使った法務業務支援と72条の関係に関するガイドラインを補完・拡充した — [法務省](https://www.moj.go.jp/housei/shihouseido/housei10_00134.html)
- ステマ規制：2023年10月1日から景品表示法の規制対象になり、2024年6月に初の措置命令が出た。報酬を払って口コミや紹介投稿を依頼する場合は、広告であることを明示する必要がある — [NTT東日本 BizDrive](https://business.ntt-east.co.jp/column/bizdrive/stealth-marketing-rules-2023.html)
- coorum にはタグ管理機能があり、会員の属性や関心をタグで管理する方式が国産コミュニティSaaSでも標準になっている — [commercepick](https://www.commercepick.com/archives/56180)

### Inferences（設計案）
- **プロフィール項目の例**：基本情報／地域（オンライン可かどうか）／できること（大分類タグ＋具体的な提供内容＋提供形態［有償・無償・応相談］＋実績URL）／探していること（大分類タグ＋背景＋期限＋予算感）／紹介してよい範囲（公開・会員限定・運営経由のみ）／同意フラグ（AI処理への同意、第三者提供への同意）。タグは 業種×スキル×目的 の3軸、各20〜40語の統制語彙にとどめ、自由記述は AI でタグ候補に変換してから人が承認する。
- **AIマッチングの流れ**：Need レコードが登録されると、Offer 側のタグ一致と自由記述の類似度で上位5件を抽出する（Gemini や Claude を API、または Notion AI／kintone 連携で利用）。AIは推薦理由の文案も出す。運営者が週1回のマッチング会議で承認し、両者に「おつなぎ提案」を送る。AIは提案だけを担い、紹介を成立させる判断は人が行う。
- **紹介台帳（監査用）の最小項目**：紹介ID／紹介者ID／被紹介者ID／相手方ID／紹介日／ステータス（提案→面談→見積→成約→入金確認→報酬確定→報酬支払）／成約金額／証憑（契約書PDF・請求書番号）／双方の成約確認日時／報酬率と報酬額／支払日／変更履歴。kintone ならレコードの変更履歴とプロセス管理機能で、ステータスの変更者と日時が自動で残る（機能そのものは kintone の標準機能として知られるが、本調査では一次ソースを確認していない）。
- **透明性の担保**：紹介者本人が会員ページで自分の紹介の進捗と報酬額を閲覧できるようにする。報酬規程（成約の定義、対象期間、報酬率、上限、税・源泉の扱い）を会員規約の一部として公開する。報酬は「成約の実額に対する一律の率」とし、**多段階の報酬（紹介者の紹介者にも報酬が出る仕組み）は採用しない**。入会金や会費の負担と、紹介報酬による勧誘を組み合わせない。この2点が連鎖販売取引の該当リスクを下げる要点になる（推論。最終判断は弁護士に確認すること）。
- 運営者が求人や業務委託の文面を加筆したり日程調整を代行したりすると職業紹介に該当しうるため、雇用目的のマッチングは除外するか、会員同士が直接やり取りする設計にする。

### Gaps
- 「通常の紹介料」と「連鎖販売取引の特定利益」の境界を判断した具体例は見つからなかった。
- AIマッチングを国内の会員コミュニティで実装し、成果を数値で示した事例は見つからなかった。

---

## Q3. 説明会・オンボーディング・課金・請求書・電子契約の自動化

### Takeaway
説明会は「申込フォーム→カレンダー登録→LINE／メールでリマインド→Zoom（有料プランで録画とAI要約）→AIで要約・FAQ化→参加者への個別フォロー（入会フォームのリンク付き）」をノーコード連携（Make が安価）で組む。課金はカード払いを Stripe（国内カード3.6%）か PAY.JP、銀行払いは口座振替代行（1件100円前後）で補う。請求書は Misoca や freee請求書、契約はクラウドサイン Light（月11,000円＋送信1件220円）が目安になる。

### Cited Findings
- Zoom：無料のベーシックでは AI Companion を使えない。Pro プランから AI Companion が付き、グループミーティングは最大30時間、参加者上限は100名 — [Zoom Workplace プロ（公式）](https://www.zoom.com/ja/products/collaboration-tools/zoom-workplace-pro/)。有料プランの最低価格は月13.33ドルから（年払い） — [Zoom中小企業向け（公式）](https://www.zoom.com/ja/small-business/solutions/entrepreneurs/)、[eesel](https://www.eesel.ai/ja/blog/zoom-pricing)。Webinar アドオンの料金は確認できなかった。
- Google Meet の録画は Workspace Business Standard 以上で使え、Standard 以上では Docs、Meet、Chat などで Gemini を使える — [SHIFT AI](https://ai-keiei.shift-ai.co.jp/google-workspace-ryoukin/)
- Make の Core プランは年払いで約9ドル/月（月払い10.59ドル）。操作数の上限は月1万とする情報と30万とする情報がある。Zapier は無料プランで100タスク、有料の入門プランは約29.99ドルで750タスク。Zapier はステップごとに1タスクを数える — [costbench](https://costbench.com/compare/zapier-vs-make/)、[toolradar](https://toolradar.com/blog/zapier-pricing-2026)、[automationatlas](https://automationatlas.io/answers/zapier-pricing-changes-2025-2026/)
- Stripe：国内カードの決済手数料は成功した決済1件あたり3.6%で、初期費用・月額は0円 — [issoh](https://www.issoh.co.jp/tech/details/15416/)、[atsoho Stripe](https://atsoho.com/apps/p/stripe)。銀行振込1.5%、海外カード＋2%、チャージバック1件1,500円とする記事もある — [issoh](https://www.issoh.co.jp/tech/details/15416/)。Billing（サブスク）の上乗せ手数料が日本で何%かは未確認（米国基準の0.5%と0.7%が混在している）。定額課金の手数料と消費税の扱いは解説記事がある — [Classmethod](https://dev.classmethod.jp/articles/stripe-billing-fee-and-tax/)。Stripe は適格請求書発行事業者として登録済み — [issoh](https://www.issoh.co.jp/tech/details/15416/)
- PAY.JP：ベーシックは月額0円、プロは月額1万円 — [ITreview PAY.JP](https://www.itreview.jp/products/pay-jp/price)。手数料は情報源によって2.59%〜または3.3%と食い違う — [issoh](https://www.issoh.co.jp/tech/details/15722/)、[imitsu](https://saas.imitsu.jp/cate-payment/service/1810/price)。定期課金機能があり、Slack やメールで通知できる — [PAY.JP magazine](https://magazine.pay.jp/article/tabisuke)。口座振替への対応は確認できなかった。
- 口座振替代行の相場：初期費用は3万円程度から（無料のサービスも多い）、月額3,000円前後、1件100円前後 — [お名前.com ビジネス](https://www.onamae.com/business/article/232660/)。例として後払い.comは開設契約金30,000円、月額3,000円、1件130円で、振替不能の場合も処理料がかかる — [imitsu](https://saas.imitsu.jp/cate-payment/service/2634/price)。りそな決済サービスは口座確認1件55円、引落1件165円、基本手数料年4,400円（税込） — [りそな銀行](https://www.resonabank.co.jp/hojin/service/eb/resona_net/?loc=6)。ROBOT PAYMENT の「月謝ペイ」は初期費用・月額0円で、決済手数料のみ — [imitsu](https://saas.imitsu.jp/cate-payment/service/5489/price)
- 請求書：freee請求書はスタンダード1,980円、アドバンス10,000円（年払い・税抜の月額換算）で、2024年7月以降は発行枚数に応じた従量課金がある — [freee請求書 新プラン](https://www.freee.co.jp/invoice/pricing/revised_plan_2024/)、[atsoho](https://atsoho.com/apps/p/freee-seikyusho)。Misoca は無料プランで月10通まで、有料はプラン15が年8,800円、プラン100が年33,500円 — [ITreview Misoca](https://www.itreview.jp/products/misoca/price)、[atsoho Misoca](https://atsoho.com/apps/p/misoca)
- クラウドサイン：Light は固定費11,000円（税込12,100円）/月＋送信1件220円（税込242円）、アカウント数は無制限。マイナンバーカード署名は送信ごとに＋200円 — [NTTコミュニケーションズ](https://www.ntt.com/business/services/cloudsign/charge.html)、[ITreview](https://www.itreview.jp/products/cloudsign/price)。無料プランはユーザー1名、送信は月2件まで — [imitsu](https://saas.imitsu.jp/cate-electronic-contract/service/1088/price)

### Inferences（自動化レシピ）
- **説明会フロー**：Googleフォーム（またはLステップの予約機能）で申込を受ける → Make で Googleカレンダー招待と Zoom URL を自動送信 → 前日と1時間前に LINE でリマインド → Zoom Pro で録画し、AI Companion で要約 → 運営者が要約を確認・修正（誇大表現と個人名の削除） → 参加者に「録画リンク、FAQ、入会フォーム、個別相談の予約リンク」を送る → 3日後と7日後に未入会者へフォロー → CRM のステータスを「説明会参加」から「入会」へ更新。
- **入会後30日のオンボーディング**：Day0 ウェルカム（規約・心得のPDF、プロフィール入力依頼）→ Day3 プロフィール未完了ならリマインド → Day7 運営者との15分面談（AIでプロフィールから「できること／探していること」を下書きし、本人が確認）→ Day14 つながりの場（月例会）に招待し、マッチング候補を3件提示 → Day30 アンケート（NPS）と初回紹介の有無を確認。LINE のステップ配信（Lステップ）でほぼ自動化できる。
- **課金設計**：月会費はカード（Stripe Billing または PAY.JP の定期課金）を基本とし、高齢層向けに口座振替を用意する。300名以下なら口座振替は初期費用無料の代行（月謝ペイ型など）でよい。報酬の支払いは振込で行い、紹介者が適格請求書発行事業者かどうかと源泉徴収の要否を台帳に記録する。
- **会員規約への同意**：個人会員はフォーム上のチェックとタイムスタンプで足りる。法人会員や報酬の授受を伴うパートナー契約はクラウドサインで締結する（年間数十件なら Light で月1.2〜2万円程度）。

### Gaps
- Stripe Billing の日本での上乗せ料率、Zoom Webinar の円建て料金、PAY.JP の最新料率と口座振替への対応状況。
- Lステップ予約機能の利用可能プラン。

---

## Q4. 生成AIの活用例とガードレール（個人情報保護法、誇大表現の防止、人によるチェック）

### Takeaway
個人情報保護委員会の注意喚起（2023年6月）が実務の基準になる。個人データを含むプロンプトの入力は「利用目的の範囲内」に限り、入力データを学習に使わないサービスを選ぶ。紹介報酬を伴う告知文は、景表法（ステマ規制、有利誤認・優良誤認）と特商法の観点で人がチェックしてから出す。

### Cited Findings
- 個人情報保護委員会「生成AIサービスの利用に関する注意喚起等」（2023年6月2日）：個人情報取扱事業者が個人情報を含むプロンプトを入力する場合は、特定した利用目的を達成するために必要な範囲内であることを十分に確認する。本人の同意なく個人データを入力し、それが応答結果の出力以外の目的（機械学習など）で扱われると、法違反となるおそれがある。提供事業者が個人データを機械学習に利用しないことを十分に確認する — [ScanNetSecurity](https://scan.netsecurity.ne.jp/article/2023/06/13/49506.html)、[モノリス法律事務所](https://monolith.law/corporate/ppc-ai-service-alert)、[原文PDF（mlex転載）](https://content.mlex.com/Attachments/2023-06-02_O42QLHNS4K18KVCJ%2FPPC%20Generative%20AI%20230602%20J.pdf)
- 同委員会は OpenAI に、本人の同意なく要配慮個人情報を取得しないよう求めた — [モノリス法律事務所](https://monolith.law/corporate/ppc-ai-service-alert)
- 生成AIの応答には不正確な内容が含まれることがあると、同委員会は利用者向けにも注意喚起している — [内閣府 資料](https://www8.cao.go.jp/cstp/ai/ai_team/6kai/shiryouchuuikanki.pdf)
- Google Workspace の Business 系プランには Gemini が標準搭載されている（業務データと同じ環境で使える） — [PC Watch](https://pc.watch.impress.co.jp/docs/news/1654889.html)。Notion Business には AI が同梱されている — [automationatlas](https://automationatlas.io/answers/notion-pricing-explained-2026/)
- ステマ規制では、報酬を払って依頼した紹介投稿は広告である旨の表示が必要 — [NTT東日本](https://business.ntt-east.co.jp/column/bizdrive/stealth-marketing-rules-2023.html)

### Inferences（活用例と運用ルール案）
- **活用例**：①説明会の録画を要約し、FAQに整理する ②プロフィールの自由記述をタグ化し、「できること／探していること」の文案を作る ③マッチング候補の抽出と推薦文の下書き ④月例会の議事メモと次のアクションの抽出 ⑤問い合わせへの一次回答の下書き ⑥週次KPIのコメント草案 ⑦規約の改定箇所の差分要約。
- **ガードレール**：
  1. 法人契約版（Workspace の Gemini、Notion Business、Claude や ChatGPT の業務向けプランなど、学習に使わない設定のもの）だけを使い、個人アカウントの無料AIに会員データを入れない。
  2. プライバシーポリシーの利用目的に「マッチング提案のためのAIを含むシステム処理」を明記し、入会時に同意を得る。
  3. 要配慮個人情報（病歴など）はプロフィールの項目に作らない。
  4. 外部に出す文面（紹介報酬の告知、成功事例）は必ず人が確認する。「必ず稼げる」「確実に成約」などの断定、根拠のない数字、報酬を受け取った紹介者の投稿で【PR】表記がないもの、を禁止語チェックリストで確認する。
  5. AIが提案したマッチングは、運営者が承認するまで本人に通知しない。
  6. プロンプトと出力のログを保存し、四半期ごとに見直す。

### Gaps
- 2023年以降に個人情報保護委員会が生成AIについて出した更新版の指針（2025〜2026年）があるかどうかは確認できなかった。
- 個人情報保護法の3年ごと見直し（改正案）の最新状況。

---

## Q5. KPIダッシュボードの設計と週次の運営リズム（コミュニティ主導の組織の例）

### Takeaway
KPIは目的から逆算し、「獲得（説明会→入会）」「活性（アクティブ率、プロフィール完成率）」「価値創出（紹介→成約→報酬）」「継続（解約率）」の4層で数本に絞る。一般的なオンラインコミュニティのアクティブ率（月1回以上投稿する会員の割合）は10〜20%という目安がある。ただし ETB の北極星指標は「月間成約件数」または「成約につながったつなぎ数」にするのが妥当（推論）。

### Cited Findings
- アクティブ率を「月に1回以上投稿するメンバーの割合」と定義すると、一般的なオンラインコミュニティでは10〜20%程度が多い — [TIMEWELL](https://timewell.jp/en/columns/howto-increase-community-engagement)
- アクティブ率と非アクティブ率を週次または月次で両方見る。KPIは目的と結びつける — [Khoros](https://khoros.com/blog/community-kpis)
- 一般的なKPIはベースラインとして扱い、自分のコミュニティに合うか評価してから選ぶ。事業価値とつながっていることを示せないと、予算を確保しにくい。再訪セッション数や1セッションあたりの投稿数を見る — [Higher Logic](https://www.higherlogic.com/blog/common-kpis-for-online-community-forums/)
- 新規会員数は単独では評価しにくい。定期的に戻ってくる会員になって初めて価値が生まれる — [coapp](https://en.coapp.io/blog-entries/community-kpis-diese-kennzahlen-solltest-du-messen)
- 指標の用語集として Common Room の資料がある — [Common Room](https://www.commonroom.io/resources/community-metrics-glossary)

### Inferences（ダッシュボード案と週次リズム）
- **ダッシュボード（Googleスプレッドシート＋Looker Studio は無料で作れる。kintone 移行後はそのグラフ機能を使う）**
  - 獲得：説明会の申込数／参加率／参加から入会への転換率（説明会後14日以内）／入会経路（紹介・SNS・LINE）
  - 活性：プロフィール完成率（Day14時点）／30日以内に初回のつながりが生まれた率／月間アクティブ率（ログイン・投稿・つながりの場への参加のいずれか）
  - 価値創出（北極星指標）：おつなぎ提案数 → 面談実施数 → 成約数 → 成約金額 → 確定報酬額。段階ごとの転換率と、提案から成約までのリードタイム
  - 継続・収益：会員数の純増、月次解約率、MRR、未収金
  - 健全性・コンプライアンス：苦情件数、規約違反の対応件数、AI出力の修正率
- **週次リズム（1〜5名体制）**：月曜30分でKPIを確認（AIが前週差分のコメントを下書き）／火曜は説明会／水曜はマッチング会議（AI候補を人が承認）／木曜は新規会員の面談／金曜は紹介台帳の締めと報酬確認。月1回つながりの場（オンラインか対面）を開き、四半期ごとに規約・報酬規程・KPI定義を見直す。

### Gaps
- 日本の会員制紹介ネットワーク（BNIなどのリファーラル型組織を含む）で、運営KPIの具体的な数値（成約率、継続率）を公開している一次情報は見つからなかった。

---

## Q6. フェーズ別の推奨ツール構成と月額コストの目安

### Takeaway
0〜50名は月額およそ5千〜2万円、50〜300名は約3〜6万円、300名以上は約8〜20万円以上（コミュニティSaaSの見積もり次第）が目安。決済手数料（カード3.6%）と紹介報酬は変動費として別に見る。以下の金額は上記の二次情報から組み立てた**推論の試算**である。

### Cited Findings（積算の元データ）
- Google Workspace Business Standard 1,600円/ユーザー — [PC Watch](https://pc.watch.impress.co.jp/docs/news/1654889.html)
- LINE公式 ライト5,000円、スタンダード15,000円 — [ligla](https://ligla.jp/blog/line-official/plan/)
- Lステップ スタート5,000円、スタンダード21,780円（税込） — [imitsu](https://saas.imitsu.jp/cate-line-marketing-tool/service/3175/price)
- kintone スタンダード 1,800円×最低10ユーザー — [ITreview](https://www.itreview.jp/products/kintone/price)
- Zoom Pro 13.33ドル/月から — [Zoom](https://www.zoom.com/ja/small-business/solutions/entrepreneurs/)
- Make Core 約9〜10.59ドル — [costbench](https://costbench.com/compare/zapier-vs-make/)
- クラウドサイン Light 11,000円＋220円/件 — [NTT](https://www.ntt.com/business/services/cloudsign/charge.html)
- Misoca 無料（月10通）、freee請求書 1,980円〜 — [ITreview Misoca](https://www.itreview.jp/products/misoca/price)、[freee](https://www.freee.co.jp/invoice/pricing/revised_plan_2024/)
- Stripe 国内カード3.6% — [issoh](https://www.issoh.co.jp/tech/details/15416/)
- Peatix 無料イベントは0円 — [ITreview Peatix](https://www.itreview.jp/products/peatix/price)
- Circle Business 199ドル＋手数料1% — [cartmango](https://cartmango.com/circle-so-pricing/)
- coorum／commune は要見積もり — [ITreview coorum](https://www.itreview.jp/products/coorum/price)、[BOXIL commune](https://boxil.jp/service/5460/)

### Inferences（試算。税抜、1ドル≒150円）
| フェーズ | 構成 | 月額目安 |
|---|---|---|
| 0〜50名（立ち上げ） | Google Workspace Standard×1〜2（1,600〜3,200円）／Googleフォーム＋スプレッドシートで会員・紹介台帳／LINE公式 ライト（5,000円）／Zoom Pro（約2,000円）／Make Core（約1,500円）／Stripe（変動費）／Misoca 無料／契約はフォームでの同意で代替／AIは Workspace の Gemini | **約1〜1.3万円**（Lステップなしの場合） |
| 50〜300名（仕組み化） | 上記に加え、kintone スタンダード（18,000円）を会員・紹介・報酬の正本DBにする（または HubSpot Starter 数シートで数千円）／Lステップ スタンダード（約2万円）＋LINE公式 スタンダード（15,000円）／freee請求書（1,980円〜）／クラウドサイン Light（11,000円＋件数）／口座振替代行（初期0〜3万円、月3,000円＋1件100円前後）／Looker Studio（無料） | **約5〜8万円**（＋決済手数料。Lステップを使わず LINE ライトで済ませれば約3〜4万円） |
| 300名以上（拡大） | kintone の利用者を増やす／会員ポータル（コミュニティSaaSを導入する場合、Circle Business で約3万円＋1%、coorum／commune は見積もり）／Lステップ プロまたは Liny／運営者が増えた分の Workspace／Zoom Webinar（料金未確認）／AIのAPI利用料 | **約8〜20万円以上**（コミュニティSaaSの見積もり次第） |

- 移行の目安（推論）：①紹介台帳が月20件を超えたとき、または報酬の照会・異議申し立てが出始めたときに、スプレッドシートから kintone 等へ移す。②LINE の無料・ライト枠の通数に達したらプランを上げる。③運営者が3名を超え、会員間の直接交流を増やしたくなったらコミュニティSaaSを検討する。
- 最初から Circle や Mighty を使うと、USD建ての月額に加えて取引手数料1〜2%が Stripe 手数料に上乗せされ、日本語サポートの面でも少人数運営には負担が大きい（推論）。

### Gaps
- 公式の価格ページを直接確認できなかったため、各数値は二次情報に依存している。税込か税抜か、年払いか月払いかの区別も、一部の情報源ではあいまいだった。
- 国産コミュニティSaaS（OSIRO、coorum、commune）の実際の見積もり額。
- 日本の小規模な会員制紹介ネットワークが実際に使っているツール構成と費用を公開した事例は見つからなかった。
