'use strict';
// パソコン診断ナビ（パソコン相談ナビと同じ画面構成・同じ操作）
// 文面のルール：句読点は使わず全角スペースで区切る／お客様に負担を突きつけず店側から申し出る聞き方にする
// 質問文 lead・title・help は「文節の配列」で書く（画面では文節の切れ目でだけ改行される）
// help は行ごとの配列  [[1行目の文節…],[2行目の文節…]]   強調したい所は <strong class="warn">…</strong>
// 質問の流れ：1問目「いつもの画面まで進むか」で大きく二手に分け 症状を切り分けたあと 全員に共通の4問（データ・控え・パスワード・心当たり）を聞く
//   道筋によって 7問〜10問（画面の「n / 全体」は その先いちばん長い道筋で数える）
// cat：この質問でお困りの内容が決まるとき（文字列＝どちらの答えでも／{yes,no}＝答えごと）
// note：答えによって結果ページの「ご回答から見えたこと」に足す一文
// short：集計やCSVで使う短い呼び名　summary：集計や回答一覧に出す一文（無ければ title をつなげる）
const QUESTIONS = {
 // 1 入口：いつもの画面まで進むか
 start:{label:'まず最初に',short:'いつもの画面まで進む',title:['電源を入れると','いつもの画面（デスクトップ）まで','進みますか？'],summary:'電源を入れるといつもの画面（デスクトップ）まで進みますか？',help:[['いつもの画面は','壁紙やアイコンが並ぶ','見慣れた画面のことです'],['真っ暗のまま・途中で止まる・','パスワードが通らない などは','「進まない」を選んでください']],yesLabel:'いつもの画面まで進む',noLabel:'進まない・途中で止まる',yesShort:'進む',noShort:'進まない',yes:'画面は出て いつもの操作ができる',no:'電源が入らない・止まる など',next:{yes:'alert',no:'power'}},
 // 起動しない側
 power:{label:'電源の確認',short:'電源の反応',lead:['まず 電源が入っているかを','確認します'],title:['電源ボタンを押すと','ランプが点いたり','音がしたり','しますか？'],summary:'電源ボタンを押すとランプや音などの反応がありますか？',help:[['電源ランプ・キーボードの光・','ファンの「ブーン」という音など'],['何かひとつでも反応があれば','「はい」を選んでください']],yes:'ランプや音など反応がある',no:'まったく反応がない',next:{yes:'screen',no:'powerCharge'}},
 powerCharge:{label:'電源の確認',short:'充電器でも反応なし',lead:['電源が入らないときは','充電まわりから確認します'],title:['ACアダプター（充電器）を','つないだままでも','まったく反応しませんか？'],summary:'ACアダプター（充電器）をつないだままでもまったく反応しませんか？',help:[['ノートパソコンは','バッテリーが空になると','電源が入りません'],['コンセントにつないで','しばらく待ってから','お試しいただく場合もあります']],yes:'つないでも反応しない',no:'まだ試していない・わからない',cat:'power',note:{yes:'充電器をつないでも反応がないため 本体の電源まわりの故障が考えられます',no:'まず店頭で充電器とバッテリーの状態から確認します'},next:{yes:'data',no:'data'}},
 screen:{label:'画面の確認',short:'画面に表示',lead:['電源は入るのに進まないときは','画面の様子を確認します'],title:['画面に','メーカーのロゴや文字','青い画面など','何か表示されますか？'],summary:'画面にメーカーのロゴや文字など何か表示されますか？',help:[['真っ暗のまま何も出ない場合は','「いいえ」を選んでください'],['一瞬でも何か映れば','「はい」です']],yes:'何か表示される',no:'真っ暗のまま何も出ない',cat:{no:'display'},note:{no:'電源は入るのに画面が映らないため 画面（液晶）か本体の部品の不調が考えられます'},next:{yes:'bitlocker',no:'data'}},
 bitlocker:{label:'表示の確認',short:'回復キー画面',lead:['表示される画面によって','原因が大きく変わります'],title:['「回復キーを入力してください」','という青い画面が','出ていますか？'],summary:'「回復キーを入力してください」という青い画面が出ていますか？',help:[['BitLocker（データの暗号化）が','はたらいている画面です'],['48桁の回復キーがあれば','そのまま進めます']],yes:'回復キーの画面が出る',no:'それ以外の表示',next:{yes:'bitlockerKey',no:'login'}},
 bitlockerKey:{label:'回復キーの確認',short:'回復キー用意',lead:['回復キーは','Microsoftアカウントに','保存されていることがあります'],title:['48桁の回復キーを','用意できそうですか？'],summary:'48桁の回復キーを用意できそうですか？',help:[['Microsoftアカウントの','メールアドレスとパスワードがわかれば','一緒に確認できます'],['見つからない場合は','<strong class="warn">データを残せないことがあります</strong>']],yes:'用意できる・アカウントがわかる',no:'わからない・見つからない',cat:'bitlocker',note:{yes:'回復キーが用意できれば その場で解除して確認できます',no:'回復キーが見つからないと データを残せない場合があります　Microsoftアカウントの確認から一緒に進めます'},next:{yes:'data',no:'data'}},
 login:{label:'ログインの確認',short:'パスワード不明',title:['ログイン画面は出るけれど','パスワードやPINが','わからない','ということですか？'],summary:'ログイン画面は出るがパスワードやPINがわからないということですか？',help:[['パスワードを忘れた・','何度入れても通らない など'],['ログイン画面まで進まない場合は','「いいえ」を選んでください']],yes:'パスワードやPINがわからない',no:'そこまで進まない・別の症状',next:{yes:'loginMs',no:'bootLoop'}},
 loginMs:{label:'アカウントの確認',short:'MSアカウント',lead:['Microsoftアカウントがわかれば','パスワードを','作り直せることがあります'],title:['Microsoftアカウントの','メールアドレスと','パスワードは','わかりますか？'],summary:'Microsoftアカウントのメールアドレスとパスワードはわかりますか？',help:[['パソコンを買ったときに','作ったアカウントです'],['わからない場合も','一緒に方法を考えますのでご安心ください']],yes:'どちらもわかる',no:'わからない・自信がない',cat:'password',note:{yes:'Microsoftアカウントがわかるため パスワードの再設定で入れる可能性があります',no:'アカウントの情報がわからないため お預かりして入る方法を検討します'},next:{yes:'data',no:'data'}},
 bootLoop:{label:'起動の確認',short:'再起動・自動修復',title:['再起動を繰り返したり','「自動修復」の表示で','止まったり','しますか？'],summary:'再起動を繰り返したり「自動修復」の表示で止まったりしますか？',help:[['Windowsの更新のあとや','記憶装置（SSD・HDD）の不調で','起こることがあります'],['メーカーのロゴのまま動かない場合は','「いいえ」を選んでください']],yes:'繰り返す・自動修復で止まる',no:'ロゴなどのまま動かない',cat:'boot',note:{yes:'再起動の繰り返しや自動修復の表示は Windowsの更新や記憶装置の不調で起こることがあります',no:'起動の途中で止まるため 記憶装置や本体の部品の状態も含めて調べます'},next:{yes:'data',no:'data'}},
 // 起動する側
 alert:{label:'警告画面の確認',short:'警告画面',lead:['最初に','急ぎの対応が必要なものから','確認します'],title:['「ウイルスに感染しました」','などの警告や','警告音・電話番号が','表示されましたか？'],summary:'「ウイルスに感染しました」などの警告や警告音・電話番号が表示されましたか？',help:[['画面いっぱいの警告や大きな音で','電話をかけさせる','「サポート詐欺」の画面が増えています'],['<strong class="warn">表示された番号には電話しないでください</strong>']],yes:'警告や電話番号が出た',no:'出ていない',next:{yes:'alertCalled',no:'netMail'}},
 alertCalled:{label:'警告画面の確認',short:'電話・操作した',lead:['お客様を守るための','大切な確認です'],title:['表示された番号に電話したり','案内どおりに操作したり','しましたか？'],summary:'表示された番号に電話したり案内どおりに操作したりしましたか？',help:[['電話をかけた・','遠隔操作を許した・','コンビニで支払いをした など'],['当てはまる場合は','早めの対応をご案内します']],yes:'電話や操作をした',no:'何もしていない',cat:'virus',note:{yes:'電話や操作をされているため パスワードの変更やカード会社への連絡もあわせてご案内します',no:'電話や操作をしていなければ 画面を閉じて安全を確かめるだけで済むことが多いです'},next:{yes:'data',no:'data'}},
 netMail:{label:'インターネットとメール',short:'ネット・メール',title:['インターネットや','メールのことで','お困りですか？'],summary:'インターネットやメールのことでお困りですか？',help:[['ホームページが開かない・','Wi-Fiにつながらない・'],['メールが送れない・届かない など']],yes:'ネットやメールで困っている',no:'それ以外のこと',next:{yes:'web',no:'error'}},
 web:{label:'インターネットの確認',short:'ホームページ',title:['ホームページ（インターネット）は','開けますか？'],summary:'ホームページ（インターネット）は開けますか？',help:[['YahooやGoogleなどが','ふつうに表示されるか','思い出してみてください'],['メールだけがおかしい場合は','「はい」を選んでください']],yes:'開ける',no:'開けない・つながらない',next:{yes:'mailPass',no:'netOther'}},
 netOther:{label:'インターネットの確認',short:'他の機器はつながる',lead:['パソコン側か','ご自宅の回線側かを','切り分けます'],title:['スマホなど ほかの機器は','同じWi-Fiで','インターネットにつながりますか？'],summary:'スマホなどほかの機器は同じWi-Fiでインターネットにつながりますか？',help:[['ほかの機器もつながらない場合は','ルーターや回線側の','可能性が高くなります']],yes:'ほかの機器はつながる',no:'ほかの機器もつながらない・わからない',cat:'internet',note:{yes:'ほかの機器はつながるため パソコン側の設定を確認します',no:'ほかの機器もつながらないため ご自宅のルーターや回線側の可能性があります　確認の方法をご案内します'},next:{yes:'data',no:'data'}},
 mailPass:{label:'メールの確認',short:'メールの情報',lead:['メールの不調は','パスワードや設定が','原因のことが多いです'],title:['メールのパスワードや','プロバイダーの書類は','お手元にありますか？'],summary:'メールのパスワードやプロバイダーの書類はお手元にありますか？',help:[['「パスワードを入力してください」と','表示される場合は','特に必要になります'],['わからない場合も','一緒に探しますのでご安心ください']],yes:'ある・わかる',no:'わからない・見当たらない',cat:'mail',note:{yes:'メールの情報がお手元にあるため 設定の確認で解決が見込めます',no:'メールのパスワードや書類が必要になることがあります　一緒に探しながら進めます'},next:{yes:'data',no:'data'}},
 error:{label:'動作の確認',short:'エラー・遅い',title:['エラーの表示が出たり','固まったり','極端に遅かったり','しますか？'],summary:'エラーの表示・固まる・極端に遅いなどがありますか？',help:[['「問題が発生しました」の表示・','マウスが動かなくなる・'],['起動に何分もかかる など']],yes:'エラーや遅さがある',no:'それ以外のこと',next:{yes:'slow',no:'device'}},
 slow:{label:'動作の確認',short:'遅い・固まるが主',title:['いちばん困っているのは','「遅い・固まる」','ですか？'],summary:'いちばん困っているのは「遅い・固まる」ですか？',help:[['エラーの表示が主なお困りの場合は','「いいえ」を選んでください']],yes:'遅い・固まるが主な悩み',no:'エラーの表示が主な悩み',cat:{yes:'slow'},note:{yes:'遅さや固まりは 記憶装置の空きや不調 ソフトの入りすぎなどで起こることがあります'},next:{yes:'data',no:'errorApp'}},
 errorApp:{label:'エラーの確認',short:'特定ソフトだけ',title:['そのエラーは','特定のソフト','（Officeや年賀状ソフトなど）を','使うときだけ出ますか？'],summary:'そのエラーは特定のソフトを使うときだけ出ますか？',help:[['いつ出るかわからない・','起動のたびに出る などは','「いいえ」を選んでください']],yes:'特定のソフトだけ',no:'いろいろな場面で出る',cat:'error',note:{yes:'特定のソフトだけのエラーのため ソフトの入れ直しや設定で直ることがあります',no:'いろいろな場面で出るエラーのため Windowsの更新や記憶装置の状態を含めて調べます'},next:{yes:'data',no:'data'}},
 device:{label:'機器の確認',short:'機器のこと',title:['キーボード・画面・音','プリンターなど','機器のことで','お困りですか？'],summary:'キーボード・画面・音・プリンターなど機器のことでお困りですか？',help:[['キーが効かない・','画面が割れた・','音が出ない・','印刷できない など'],['使い方やデータの移し替えのご相談は','「いいえ」を選んでください']],yes:'機器のことで困っている',no:'それ以外のこと',cat:{no:'other'},next:{yes:'deviceKind',no:'data'}},
 deviceKind:{label:'機器の確認',short:'本体の部品',title:['パソコン本体の部品','（画面・キーボード・端子・音など）','のことですか？'],summary:'パソコン本体の部品（画面・キーボード・端子・音など）のことですか？',help:[['プリンター・マウス・Wi-Fiなど','つないで使う機器のことなら','「いいえ」を選んでください']],yes:'本体の部品のこと',no:'つないで使う機器のこと',cat:{yes:'hardware',no:'peripheral'},note:{yes:'本体の部品の不調が考えられるため 部品交換や保証での修理をご案内します',no:'つないで使う機器の不調は つなぎ方や設定の確認で直ることが多いです'},next:{yes:'data',no:'data'}},
 // 全員に共通（最後の4問）
 data:{label:'データの確認',short:'残したいデータ',lead:['ここからは','受付に必要なことを','確認します'],title:['残したい','写真や書類などの','データは','入っていますか？'],summary:'残したい写真や書類などのデータは入っていますか？',help:[['作業の前に','データを守る方法を考えるための','確認です']],yes:'残したいデータがある',no:'特にない',next:{yes:'backup',no:'backup'}},
 backup:{label:'データの確認',short:'控え',title:['大切なデータの','控え（バックアップ）は','取ってありますか？'],summary:'大切なデータの控え（バックアップ）は取ってありますか？',help:[['USBメモリーや外付けの記憶装置・','クラウドなどに','写しがあれば「はい」です'],['わからない場合は','「いいえ」で大丈夫です']],yes:'控えがある',no:'ない・わからない',next:{yes:'pcpass',no:'pcpass'}},
 pcpass:{label:'パスワードの確認',short:'Windowsのパスワード',lead:['お預かりして確認するときに','必要になります'],title:['Windowsに入るときの','パスワード（PIN）は','わかりますか？'],summary:'Windowsに入るときのパスワード（PIN）はわかりますか？',help:[['受付のときに','担当者へお伝えいただきます'],['わからない場合は','別の方法をご案内します']],yes:'わかる',no:'わからない・設定していない',next:{yes:'change',no:'change'}},
 change:{label:'最後にひとつ',short:'心当たり',title:['症状が出る少し前に','心当たりは','ありますか？'],summary:'症状が出る少し前に心当たりはありますか？',help:[['落とした・水がかかった・','Windowsの更新をした・'],['新しいソフトや機器をつないだ など']],yes:'心当たりがある',no:'特にない・わからない',next:{yes:'result',no:'result'}}
};
const COMMON_IDS=['data','backup','pcpass','change'];
// 集計表での並び（枝ごと）
const BRANCHES=[['最初の質問',['start']],['起動しない側',['power','powerCharge','screen','bitlocker','bitlockerKey','login','loginMs','bootLoop']],['起動する側',['alert','alertCalled','netMail','web','netOther','mailPass','error','slow','errorApp','device','deviceKind']],['全員に共通',COMMON_IDS]];
const phr=parts=>parts.map(p=>'<span class="ph">'+p+'</span>').join('');
const plain=parts=>parts.join('').replace(/<[^>]+>/g,'');
const titleText=q=>q.summary || plain(q.title);
// その質問から結果までの いちばん長い道筋の質問数（画面の「n / 全体」に使う）
const depthMemo={};
function depth(id){if(!QUESTIONS[id])return 0;if(!depthMemo[id]){const q=QUESTIONS[id];depthMemo[id]=1+Math.max(depth(q.next.yes),depth(q.next.no));}return depthMemo[id];}
const QUESTION_MAX=depth('start');

// お困りの内容（切り分けの結果）　check：当店で確認すること（結果ページの先頭に出す）
const CATS = {
 power:{name:'電源が入らない',headline:['お困りの内容は','「電源が入らない」','トラブルのようです'],check:'ACアダプターとバッテリー 本体の電源まわりを確認します'},
 display:{name:'画面が映らない',headline:['お困りの内容は','「電源は入るが画面が映らない」','トラブルのようです'],check:'画面（液晶）と本体の部品のどちらに原因があるかを確認します'},
 bitlocker:{name:'回復キーの画面が出る',headline:['お困りの内容は','「BitLockerの回復キー」の','画面のようです'],check:'回復キーの保管先を一緒に確認し 解除できるかを見ます'},
 password:{name:'パスワードがわからない',headline:['お困りの内容は','「パスワードがわからず入れない」','トラブルのようです'],check:'アカウントの種類を確認し パスワードを作り直す方法を探します'},
 boot:{name:'Windowsが起動しない',headline:['お困りの内容は','「Windowsが起動しない」','トラブルのようです'],check:'Windowsの修復と 記憶装置（SSD・HDD）の状態を確認します'},
 virus:{name:'ウイルス感染・警告画面',headline:['お困りの内容は','「ウイルス感染・警告画面」の','トラブルのようです'],check:'警告の正体を確かめ 不審なソフトが残っていないかを確認します'},
 internet:{name:'インターネットにつながらない',headline:['お困りの内容は','「インターネットにつながらない」','トラブルのようです'],check:'Wi-Fiの設定とつなぎ方 ルーターや回線側の状態を確認します'},
 mail:{name:'メールができない',headline:['お困りの内容は','「メールができない」','トラブルのようです'],check:'メールの設定とパスワード 容量やプロバイダー側の状態を確認します'},
 slow:{name:'動作が遅い・固まる',headline:['お困りの内容は','「動作が遅い・固まる」','トラブルのようです'],check:'記憶装置とメモリーの状態 ソフトの入りすぎや更新の状況を確認します'},
 error:{name:'エラーが出る',headline:['お困りの内容は','「エラーが出る」','トラブルのようです'],check:'エラーの内容を確かめ Windowsやソフトの修復が必要かを確認します'},
 hardware:{name:'本体の部品の不調',headline:['お困りの内容は','「本体の部品の不調」の','トラブルのようです'],check:'不調の部品を特定し 部品交換や保証での修理ができるかを確認します'},
 peripheral:{name:'つないで使う機器の不調',headline:['お困りの内容は','「つないで使う機器」の','トラブルのようです'],check:'つなぎ方と設定を確認し 機器側の不調かパソコン側かを切り分けます'},
 other:{name:'その他のご相談',headline:['お困りの内容を','担当者が','直接お伺いします'],check:'使い方やデータの移し替えなど ご相談の内容を担当者が直接お伺いします'}
};
// 次のステップ（3つのうち必ずどれかを提案する）　名前や説明はお店の受付メニューに合わせて直す
const NEXT = {
 counter:{name:'店頭チェック',parts:['店頭','チェック'],badge:'その場で確認',desc:'その場でパソコンを見せていただき 設定やつなぎ方を確認します　短い時間で解決が見込めるときにご案内します'},
 takein:{name:'お預かり診断',parts:['お預かり','診断'],badge:'詳しく調べる',desc:'パソコンをお預かりして 起動やエラーの原因を詳しく調べます　結果とお見積りをご連絡してから作業に進みます'},
 repair:{name:'修理・メーカー相談',parts:['修理・','メーカー相談'],badge:'部品や保証の確認',desc:'部品の交換が必要なときや メーカー保証で直せる可能性があるときにご案内します　修理の方法とお見積りをご説明します'}
};
const NEXT_ORDER=['counter','takein','repair'];
const answerOf=id=>history.find(h=>h.id===id)?.answer;
function catKey(){let c='other';for(const h of history){const v=QUESTIONS[h.id].cat,k=typeof v==='string'?v:v&&v[h.answer];if(k)c=k;}return c;}
function nextKey(){
 const c=catKey();
 // 電源が入らない：充電器をつないでも反応なし → 修理　まだ試していない → まず店頭で電源まわりを確認
 if(c==='power')return answerOf('powerCharge')==='yes'?'repair':'counter';
 if(c==='hardware')return 'repair';
 // 警告画面：電話や操作をした → お預かりして不審なソフトを取り除く　何もしていない → 店頭で確認
 if(c==='virus')return answerOf('alertCalled')==='yes'?'takein':'counter';
 // 回復キー・パスワード：手がかりがあれば店頭で　なければお預かりして方法を検討
 if(c==='bitlocker')return answerOf('bitlockerKey')==='yes'?'counter':'takein';
 if(c==='password')return answerOf('loginMs')==='yes'?'counter':'takein';
 if(['display','boot','slow','error'].includes(c))return 'takein';
 // インターネット・メール・つないで使う機器・その他 → 店頭で確認
 return 'counter';
}
function recommendation(){
 const key=nextKey(),ck=catKey(),cat=CATS[ck],step=NEXT[key],reasons=[cat.check];
 for(const h of history){const n=QUESTIONS[h.id].note;if(n&&n[h.answer])reasons.push(n[h.answer]);}
 if(['power','display','hardware'].includes(ck))reasons.push('ご購入から1年以内であれば メーカー保証で修理できる場合があります');
 if(answerOf('data')==='yes')reasons.push(answerOf('backup')==='yes'?'残したいデータの控えがあるため 安心して作業を進められます':'残したいデータがあり 控え（バックアップ）がありません　作業の前にデータを守る方法をご案内します');
 else reasons.push('残したいデータは特にないとのことです');
 if(answerOf('pcpass')==='no')reasons.push('Windowsのパスワードがわからないため 作業の前に確認が必要です');
 if(answerOf('change')==='yes')reasons.push('症状が出る前に心当たりがあるとのことです　担当者に詳しくお聞かせください');
 return {key,step,ck,cat,reasons};
}

// 集計（裏メニュー）
// 回答はこのiPadの中だけに保存する（外部には送らない）　個人を特定する情報は記録しない
// 開き方：右上の「約3分・最大10問」を続けて5回タップ
const STORE_KEY='pcshindan.records.v1';
const SETTINGS_KEY='pcshindan.settings.v1';
let sessionId=null,syncing=false,syncNote='';
const loadRecords=()=>{try{return JSON.parse(localStorage.getItem(STORE_KEY))||[];}catch(e){return [];}};
const saveRecords=list=>{try{localStorage.setItem(STORE_KEY,JSON.stringify(list));return true;}catch(e){return false;}};
// 送信先（Googleスプレッドシートの受付窓口）　診断ナビ用の窓口（gas/Code.gs）を用意したら ここに入れておくと iPadごとの入力がいらない
// 合言葉はプログラムの中には書かない　iPadごとに裏メニューで入力する　合言葉が合わない送信は受付窓口がすべて断る
const DEFAULT_URL='';
const loadSettings=()=>{let s={};try{s=JSON.parse(localStorage.getItem(SETTINGS_KEY))||{};}catch(e){}return {device:s.device||'',url:s.url||DEFAULT_URL,pass:s.pass||''};};
const saveSettings=s=>{try{localStorage.setItem(SETTINGS_KEY,JSON.stringify(s));}catch(e){}};
function recordSession(consult){
 if(!sessionId)sessionId=Date.now().toString(36)+Math.random().toString(36).slice(2,6);
 const list=loadRecords(),i=list.findIndex(r=>r.id===sessionId);
 const rec={id:sessionId,at:i>=0?list[i].at:new Date().toISOString(),device:loadSettings().device,answers:history.map(h=>({q:h.id,a:h.answer})),cat:catKey(),next:nextKey(),consult:consult || (i>=0?list[i].consult:null),outcome:i>=0?(list[i].outcome||null):null,sent:false};
 if(i>=0)list[i]=rec;else list.push(rec);
 saveRecords(list);
 syncRecords();
}
// 受付の結果（スタッフが記録する）　値は counter / takein / repair（そのステップで受付）・lost（見送り）・null（未記入）
function setOutcome(id,value){
 const list=loadRecords(),i=list.findIndex(r=>r.id===id);
 if(i<0)return;
 list[i].outcome=value || null;
 list[i].sent=false;
 saveRecords(list);
 syncRecords();
}
const outcomeLabel=v=>v==='lost'?'見送り':NEXT[v]?'受付':'未記入';
const outcomeNext=v=>NEXT[v]?NEXT[v].name:'';
const answerLabel=(q,a)=>{const s=QUESTIONS[q]||{};return a==='yes'?(s.yesShort||s.yesLabel||'はい'):(s.noShort||s.noLabel||'いいえ');};
const ansOf=(r,id)=>{const x=r.answers.find(v=>v.q===id);return x?answerLabel(id,x.a):'';};
const answersText=r=>r.answers.map(v=>(QUESTIONS[v.q]?QUESTIONS[v.q].short:v.q)+'：'+answerLabel(v.q,v.a)).join('／');
const consultLabel=c=>c==='yes'?'受付を進める':c==='no'?'保留':'未選択';
const when=iso=>{const d=new Date(iso),p=n=>String(n).padStart(2,'0');return d.getFullYear()+'/'+p(d.getMonth()+1)+'/'+p(d.getDate())+' '+p(d.getHours())+':'+p(d.getMinutes());};
// 未送信の記録を1件ずつ受付窓口へ送る　同じお客様の記録は上書きされる　電波がないときは次の機会に送る
function toRow(r){
 return {id:r.id,at:when(r.at),device:r.device || loadSettings().device,cat:CATS[r.cat]?CATS[r.cat].name:'',next:NEXT[r.next]?NEXT[r.next].name:'',data:ansOf(r,'data'),backup:ansOf(r,'backup'),pcpass:ansOf(r,'pcpass'),change:ansOf(r,'change'),answers:answersText(r),consult:consultLabel(r.consult),outcome:outcomeLabel(r.outcome),outcomeNext:outcomeNext(r.outcome)};
}
async function syncRecords(){
 const s=loadSettings();
 if(!s.url||!s.pass||syncing)return;
 syncing=true;
 try{
  for(const r of loadRecords().filter(v=>!v.sent)){
   const res=await fetch(s.url,{method:'POST',body:JSON.stringify({pass:s.pass,record:toRow(r)})});
   const out=await res.json();
   if(!out.ok)throw new Error(out.error || '受付窓口がエラーを返しました');
   const list=loadRecords(),i=list.findIndex(v=>v.id===r.id);
   // 送信中にお客様が最後の選択を変えた場合は未送信のままにして次に送り直す
   if(i>=0&&JSON.stringify(list[i].answers)===JSON.stringify(r.answers)&&list[i].consult===r.consult&&(list[i].outcome||null)===(r.outcome||null)){list[i].sent=true;saveRecords(list);}
  }
  syncNote='送信できました（'+when(new Date().toISOString())+'）';
 }catch(e){syncNote='送信できませんでした：'+e.message;}
 syncing=false;
 if(screen==='admin'&&!(document.activeElement&&document.activeElement.matches('input')))render(false);
}
window.addEventListener('online',syncRecords);
function adminView(){
 const list=loadRecords(),total=list.length,set=loadSettings(),unsent=list.filter(r=>!r.sent).length;
 const esc=t=>String(t).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
 const pct=(n,d)=>d?Math.round(n/d*100):0;
 const rows=BRANCHES.map(([name,ids])=>`<tr><th colspan="6" class="group">${name}</th></tr>`+ids.map(id=>{
  let yes=0,no=0;
  for(const r of list)for(const x of r.answers)if(x.q===id){if(x.a==='yes')yes++;else no++;}
  const q=QUESTIONS[id],n=yes+no;
  return `<tr><th>${q.short}</th><td class="q">${titleText(q)}<small>${q.label}</small></td><td class="num">${n}</td><td class="num yes">${answerLabel(id,'yes')} ${yes}<small>${pct(yes,n)}%</small></td><td class="num no">${answerLabel(id,'no')} ${no}<small>${pct(no,n)}%</small></td><td class="bar"><span style="width:${pct(yes,n)}%"></span></td></tr>`;
 }).join('')).join('');
 const cats=Object.keys(CATS).map(k=>[k,list.filter(r=>r.cat===k).length]).sort((a,b)=>b[1]-a[1]).map(([k,n])=>`<tr><td class="q">${CATS[k].name}</td><td class="num">${n}<small>${pct(n,total)}%</small></td></tr>`).join('');
 const steps=NEXT_ORDER.map(k=>{const n=list.filter(r=>r.next===k).length;return `<tr><td class="q">${NEXT[k].name}</td><td class="num">${n}<small>${pct(n,total)}%</small></td></tr>`;}).join('');
 const consults=['yes','no',null].map(c=>{const n=list.filter(r=>(r.consult||null)===c).length;return `<tr><td class="q">${consultLabel(c)}</td><td class="num">${n}<small>${pct(n,total)}%</small></td></tr>`;}).join('');
 const won=list.filter(r=>NEXT[r.outcome]).length,lost=list.filter(r=>r.outcome==='lost').length,blank=total-won-lost;
 const outcomes=[['受付',won],['見送り',lost],['未記入',blank]].map(v=>`<tr><td class="q">${v[0]}</td><td class="num">${v[1]}<small>${pct(v[1],total)}%</small></td></tr>`).join('')+`<tr><td class="q"><b>受付率</b>（受付 ÷ 受付と見送りの合計）</td><td class="num">${won+lost?pct(won,won+lost)+'%':'-'}</td></tr>`;
 const wonSteps=NEXT_ORDER.map(k=>{const n=list.filter(r=>r.outcome===k).length;return `<tr><td class="q">${NEXT[k].name}</td><td class="num">${n}<small>${pct(n,won)}%</small></td></tr>`;}).join('');
 const people=list.slice().reverse().slice(0,300).map(r=>{
  const cells=COMMON_IDS.map(id=>{const x=r.answers.find(v=>v.q===id);return x?`<td class="${x.a}">${answerLabel(id,x.a)}</td>`:'<td>-</td>';}).join('');
  return `<tr><td class="when">${when(r.at)}</td><td class="q">${CATS[r.cat]?CATS[r.cat].name:'-'}</td><td class="q">${NEXT[r.next]?NEXT[r.next].name:'-'}</td>${cells}<td class="num">${r.answers.length}</td><td>${consultLabel(r.consult)}</td><td><select class="admin-outcome" data-id="${r.id}"><option value="">未記入</option>${NEXT_ORDER.map(k=>`<option value="${k}" ${r.outcome===k?'selected':''}>受付 ${NEXT[k].name}</option>`).join('')}<option value="lost" ${r.outcome==='lost'?'selected':''}>見送り</option></select></td></tr>`;
 }).join('');
 return `<section class="admin"><div class="admin-head"><div><span class="tag">スタッフ専用</span><h1>回答の集計</h1><p>このiPadで記録されたお客様 <b>${total}</b> 人　${set.url&&set.pass?`未送信 <b>${unsent}</b> 件`:'送信先か合言葉が未設定のためこのiPadの中だけに保存しています'}</p></div><div class="admin-actions"><button class="admin-button" data-action="admin-csv" ${total?'':'disabled'}>CSVで書き出す</button><button class="admin-button danger" data-action="admin-clear" ${total?'':'disabled'}>記録をすべて消す</button><button class="admin-button primary" data-action="admin-close">お客様の画面に戻る</button></div></div>
 <h2>このiPadの設定</h2><div class="admin-settings"><label>iPadの名前<input id="set-device" value="${esc(set.device)}" placeholder="例 iPad 1号機"></label><label>送信先URL（診断ナビ用の受付窓口を用意したら入力）<input id="set-url" value="${esc(set.url)}" placeholder="https://script.google.com/macros/s/…/exec" inputmode="url" autocapitalize="off" autocorrect="off"></label><label>合言葉<span class="pass-row"><input id="set-pass" type="password" value="${esc(set.pass)}" autocomplete="off" autocapitalize="off" autocorrect="off"><button type="button" class="admin-button small" data-action="admin-peek">見る</button></span></label><div class="admin-actions"><button class="admin-button primary" data-action="admin-save">設定を保存</button><button class="admin-button" data-action="admin-sync" ${set.url&&set.pass&&unsent?'':'disabled'}>未送信を今すぐ送る</button></div><p class="admin-note">${syncNote || 'すべてのiPadの集計はGoogleスプレッドシートに集まります　この画面の集計はこのiPadの分だけです'}</p></div>
 <div class="admin-two"><div><h2>受付の結果</h2><table class="admin-table"><tbody>${outcomes}</tbody></table></div><div><h2>受付した次のステップ</h2><table class="admin-table"><tbody>${wonSteps}</tbody></table></div></div>
 <div class="admin-two"><div><h2>お困りの内容（多い順）</h2><table class="admin-table"><tbody>${cats}</tbody></table></div><div><h2>おすすめした次のステップ</h2><table class="admin-table"><tbody>${steps}</tbody></table><h2>最後の選択</h2><table class="admin-table"><tbody>${consults}</tbody></table></div></div>
 <h2>質問ごとの集計（このiPadの分）</h2><div class="admin-scroll"><table class="admin-table"><thead><tr><th>質問</th><th>内容</th><th>回答数</th><th>はい</th><th>いいえ</th><th>はいの割合</th></tr></thead><tbody>${rows}</tbody></table></div>
 <h2>お客様ごとの回答（新しい順）</h2><div class="admin-scroll"><table class="admin-table people"><thead><tr><th>日時</th><th>お困りの内容</th><th>次のステップ</th>${COMMON_IDS.map(id=>`<th>${QUESTIONS[id].short}</th>`).join('')}<th>質問数</th><th>最後の選択</th><th>受付の結果（ここで記録・修正できます）</th></tr></thead><tbody>${people || `<tr><td colspan="${COMMON_IDS.length+6}">まだ記録がありません</td></tr>`}</tbody></table></div></section>`;
}
function exportCsv(){
 const head=['日時','iPad','お困りの内容','次のステップ',...COMMON_IDS.map(id=>QUESTIONS[id].short),'回答の記録','最後の選択','受付','受付した次のステップ'];
 const lines=loadRecords().map(r=>[when(r.at),r.device||'',CATS[r.cat]?CATS[r.cat].name:'',NEXT[r.next]?NEXT[r.next].name:'',...COMMON_IDS.map(id=>ansOf(r,id)),answersText(r),consultLabel(r.consult),outcomeLabel(r.outcome),outcomeNext(r.outcome)]);
 const csv='﻿'+[head,...lines].map(row=>row.map(c=>'"'+String(c).replace(/"/g,'""')+'"').join(',')).join('\r\n');
 const d=new Date(),p=n=>String(n).padStart(2,'0'),name='pc-shindan-navi-'+d.getFullYear()+p(d.getMonth()+1)+p(d.getDate())+'.csv';
 const file=new File([csv],name,{type:'text/csv'});
 if(navigator.canShare&&navigator.canShare({files:[file]})){navigator.share({files:[file],title:name}).catch(()=>{});return;}
 const a=document.createElement('a');a.href=URL.createObjectURL(file);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}

const main=document.getElementById('main');
let history=[],screen='start';
const tick='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="m5 12 4 4L19 6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const cross='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" stroke-linecap="round"/></svg>';
function aside(stage){return `<aside class="sidebar"><div class="eyebrow">PC TROUBLE CHECK</div><h2>お困りの症状を<br>いっしょに<br>確かめる　</h2><div class="steps">${['質問に答える','診断の結果を見る','受付につなぐ'].map((t,i)=>`<div class="step ${stage===i?'current':stage>i?'complete':''}" ${stage===i?'aria-current="step"':''}><span class="step-index">${stage>i?'✓':i+1}</span><span>${t}</span></div>`).join('')}</div><div class="side-bottom"><strong class="reassurance"><span>わからないときは</span><span>だいたいで大丈夫</span></strong><br>近いと思うほうを<br>選んでください　</div></aside>`;}
function choice(answer,label,sub){return `<button class="choice ${answer==='no'?'no':''}" data-answer="${answer}"><span class="choice-label">${answer==='yes'?tick:cross}${label}</span><small>${sub}</small></button>`;}
function stepCards(key){return `<div class="pack-cards">${NEXT_ORDER.map(k=>`<div class="pack-card ${k===key?'is-recommended':''}">${k===key?'<span class="pack-flag">おすすめの次のステップ</span>':''}<span class="pack-badge">${NEXT[k].badge}</span><h3>${phr(NEXT[k].parts)}</h3><p>${NEXT[k].desc}</p></div>`).join('')}</div>`;}
function staffBox(){
 const rec=loadRecords().find(r=>r.id===sessionId);
 if(!rec)return '';
 const cur=rec.outcome || '';
 const btn=(v,label)=>`<button class="staff-button ${cur===v?'is-on':''}" data-action="outcome" data-value="${v}">${label}</button>`;
 return `<div class="staff-box"><span class="staff-tag">スタッフ記入欄</span><p>${cur?'記録しました　押し直すと変更できます':'受付の結果を押してください'}</p><div class="staff-buttons">${NEXT_ORDER.map(k=>btn(k,'受付　'+NEXT[k].name)).join('')}${btn('lost','見送り')}</div></div>`;
}
function render(focus=true){
 let html,stage=0;
 if(screen==='admin'){main.innerHTML=`<div class="stage admin-stage">${adminView()}</div>`;window.scrollTo({top:0,behavior:'instant'});return;}
 if(QUESTIONS[screen]){
  const q=QUESTIONS[screen],n=history.length+1,total=history.length+depth(screen);
  html=`<section class="content fade-in ${screen==='start'?'welcome':''}"><div class="topline"><span class="tag">${q.label}</span><span class="count"><b>${String(n).padStart(2,'0')}</b> / ${total}</span></div><div class="progress" aria-label="全${total}問中${n}問目">${Array.from({length:total},(_,i)=>i+1).map(i=>`<span class="${i<=n?'on':''}"></span>`).join('')}</div><div class="question-area">${screen==='start'?'<p class="welcome-thanks">お困りのパソコン<br>いっしょに確認します　</p>':''}${q.lead?`<p class="question-lead">${phr(q.lead)}</p>`:''}<h1>${phr(q.title)}</h1><p class="helper">${q.help.map(phr).join('<br>')}</p></div><div class="choices">${choice('yes',q.yesLabel || 'はい',q.yes)}${choice('no',q.noLabel || 'いいえ',q.no)}</div><div class="navrow"><button class="text-button" data-action="back" ${history.length?'':'disabled'}>← ひとつ戻る</button><span class="navhint">どちらかをタップしてください</span></div></section>`;
 }else if(screen==='result'){
  stage=1;const r=recommendation();
  html=`<section class="content result fade-in"><div class="topline"><span class="tag">${history.length}問のご回答から</span><span class="count">診断の結果</span></div><h1 class="support-catchphrase">${phr(r.cat.headline)}</h1>${stepCards(r.key)}<div class="recommendation is-pack"><span class="eyebrow">ご回答から見えたこと</span><ul>${r.reasons.map(t=>`<li>${t}</li>`).join('')}</ul></div><p class="micro">診断の内容と料金は担当者がご案内します　お預かりの場合は 作業の前にデータの扱いを一緒に確認します</p><p class="prompt">この内容で受付を進めますか？</p><div class="choices">${choice('yes','はい受付を進める','受付の内容を確認する')}${choice('no','いいえいったん保留','今回の回答を確認する')}</div><div class="navrow"><button class="text-button" data-action="back">← 回答を見直す</button><button class="text-button" data-action="restart">最初からやり直す</button></div></section>`;
 }else{
  stage=2;const r=recommendation(),interested=screen==='handoff';
  html=`<section class="content handoff fade-in"><span class="tag">${interested?'受付内容の確認':'今回の回答まとめ'}</span><h1>${interested?'この画面を担当者にお見せください　':'必要になったときにご相談ください　'}</h1><p class="helper">${interested?'お困りの内容と次のステップを確認し 担当者がご案内するための画面です　':'今回の回答から次のステップをご提案しました　今すぐ決めなくても大丈夫です　'}</p><div class="recommendation is-pack"><span class="eyebrow">${interested?'お困りの内容':'今回の診断'}</span><span class="pack-badge">${r.step.name}</span><h2>${r.cat.name}</h2></div>${staffBox()}<ul class="answer-list">${history.map(h=>`<li><span>${titleText(QUESTIONS[h.id])}</span><b>${answerLabel(h.id,h.answer)}</b></li>`).join('')}</ul><p class="micro">この画面では申込や予約は行われません　お預かりの手続きは担当者がご案内します　</p><div class="navrow"><button class="text-button" data-action="result">← 診断の結果に戻る</button><button class="text-button" data-action="restart">最初の質問へ</button></div></section>`;
 }
 const photo=screen==='start'?'support-consultation':['power','powerCharge','screen','bitlocker','bitlockerKey','login','loginMs','bootLoop'].includes(screen)?'new-laptop':QUESTIONS[screen]?'laptop-setup':'support-consultation';
 main.innerHTML=`<div class="stage photo-${photo}">${aside(stage)}${html}</div>`;
 if(focus){main.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});}
}
main.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b||b.disabled)return;
 if(b.dataset.answer){
  const a=b.dataset.answer;
  if(QUESTIONS[screen]){const target=QUESTIONS[screen].next[a];history.push({id:screen,answer:a});screen=target;if(screen==='result')recordSession();}
  else if(screen==='result'){recordSession(a);screen=a==='yes'?'handoff':'summary';}
 }else if(b.dataset.action==='back'){const prev=history.pop();if(prev)screen=prev.id;}
 else if(b.dataset.action==='restart'){history=[];screen='start';sessionId=null;}
 else if(b.dataset.action==='admin-close'){history=[];screen='start';sessionId=null;}
 else if(b.dataset.action==='outcome'){const rec=loadRecords().find(r=>r.id===sessionId);const v=b.dataset.value;setOutcome(sessionId,rec&&rec.outcome===v?null:v);const y=window.scrollY;render(false);window.scrollTo({top:y,behavior:'instant'});return;}
 else if(b.dataset.action==='admin-csv'){exportCsv();return;}
 else if(b.dataset.action==='admin-peek'){const i=document.getElementById('set-pass');i.type=i.type==='password'?'text':'password';b.textContent=i.type==='password'?'見る':'隠す';return;}
 else if(b.dataset.action==='admin-save'){const v=id=>document.getElementById(id).value.trim();saveSettings({device:v('set-device'),url:v('set-url'),pass:v('set-pass')});syncNote='設定を保存しました';syncRecords();}
 else if(b.dataset.action==='admin-sync'){syncNote='送信しています';syncRecords();}
 else if(b.dataset.action==='admin-clear'){if(!window.confirm('記録をすべて消します　元に戻せません　よろしいですか？'))return;saveRecords([]);}
 else if(b.dataset.action==='result')screen='result';
 render();
});
main.addEventListener('change',e=>{const s=e.target.closest('select.admin-outcome');if(!s)return;setOutcome(s.dataset.id,s.value);const y=window.scrollY;render(false);window.scrollTo({top:y,behavior:'instant'});});
for(const file of ['new-laptop','laptop-setup','support-consultation']){const img=new Image();img.src='photos/'+file+'.png';}
document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();history=[];screen='start';sessionId=null;render();});
// 裏メニュー：右上の「約3分・最大10問」を3秒以内に5回タップ
let secretTaps=[];
document.querySelector('.header-note').addEventListener('click',()=>{const now=Date.now();secretTaps=secretTaps.filter(t=>now-t<3000);secretTaps.push(now);if(secretTaps.length>=5){secretTaps=[];screen='admin';syncNote='';render();syncRecords();}});
// アプリ化：オフラインでも動くようにする（https または localhost のときだけ）
if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'))navigator.serviceWorker.register('sw.js').catch(()=>{});
render(false);
