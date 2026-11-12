# 会話と広告の回　YouTube 一式（確認用の通し v2 の時刻：全体 15:28）

このファイルは make_youtube_kit.py で作っています（元は template.md）。長さが変わったら、走らせ直すと時刻と字幕がそろいます。

## タイトル（案）
1. **さっき話した物が、なぜ広告に出る？ スマホの中で犯人さがし**（おすすめ。台本の題）
2. スマホは会話を聞いている？ 広告の「犯人」を探偵ロボが追いかけた
3. 話しただけなのに広告が出る……スマホの中に入って確かめてみた
4. 「会話を聞かれてる？」の正体は？ 3人の容疑者を調べたら意外な結末に

- 1 は「よくある体験」がそのまま題になっていて、検索でも探されやすい言葉（話した・広告・スマホ）が入っている。
- 2〜4 は「探偵」「容疑者」で、話の形を前に出した案。

## 概要欄（そのまま貼る）
```
友だちとキャンプの話をしただけなのに、その夜、スマホにテントの広告が……。
「スマホに会話を聞かれている？」と感じたこと、ありませんか？
探偵になったまるロボと一緒に、スマホの中に入って、3人の容疑者を一人ずつ調べてみました。

▼もくじ
0:00 冒頭　さっき話しただけなのに、テントの広告が？
1:19 容疑者は3人
1:57 容疑者①　マイク　スマホの中に入って確かめる
6:36 容疑者②　スマホから出ていく手がかり
10:40 容疑者③　わたしたちの記憶
12:20 どんでん返し「会話を聞ける」と言った会社
13:19 事件のまとめ
14:30 オチ　犯人は……

▼参考にしたページ
・Apple Machine Learning Research「Voice Trigger System for Siri」 https://machinelearning.apple.com/research/voice-trigger
・Google アシスタント ヘルプ https://support.google.com/assistant/answer/11091714
・Apple サポート（画面のオレンジ・緑の点） https://support.apple.com/108331
・Pan ほか（ノースイースタン大学）, Panoptispy: Characterizing Audio and Video Exfiltration from Android Applications, PETS 2018 https://petsymposium.org/2018/files/slides/Panoptispy%20-%20Characterizing%20Audio%20and%20Video%20Exfiltration%20from%20Android%20Applications.pdf
・米国連邦取引委員会（FTC）発表 2026年5月 https://www.ftc.gov/news-events/news/press-releases/2026/05/ftc-require-cox-media-group-two-other-firms-pay-nearly-1-million-settle-charges-they-deceived
・同 2026年8月（確定） https://www.ftc.gov/news-events/news/press-releases/2026/08/ftc-finalizes-orders-cox-media-group-two-other-firms-settling-charges-they-deceived-customers-about
・FTC「A Look Behind the Screens」2024年 https://www.ftc.gov/system/files/ftc_gov/pdf/Social-Media-6b-Report-9-11-2024.pdf
・日本オートキャンプ協会「オートキャンプ白書2024」 https://autocamp.or.jp/2020/wp-content/uploads/2024/07/1cfc39047310103ceb3219e341dfa3d2.pdf
・Google マイ アド センター ヘルプ https://support.google.com/My-Ad-Center-Help/answer/12155154?hl=ja

※動画の中の合言葉は、見ている方のスマホが反応しないよう、音を消して字だけでお見せしています。
※「今わかっている調べでは」マイクが会話を広告に使っている証拠は見つかっていない、という内容です。すべてのアプリやスマホについて言い切るものではありません。
※広告の設定の場所や名前は、スマホの機種や OS の版で変わることがあります。
Siri・iPhone は Apple Inc. の商標です。Google アシスタント・Android は Google LLC の商標です。

#スマホ #広告 #しくみ #まるロボ
```

## 固定コメント（公開したら最初に書いて、固定する）
```
【まとめ】テント広告事件の犯人は、一人ではありませんでした。
①マイク：合言葉を待つ間は、スマホの中だけで聞き分けていて、外へは出さない。今わかっている調べでは、会話を広告に使った証拠はなし。
②出ていく手がかり：いた場所・見たページ・一緒にいた人（同じ Wi-Fi など）や季節から、好きそうな物を予想している。
③わたしたちの記憶：予想が当たったときだけ「聞かれていた！」と強く覚えている。

みなさんは「話しただけなのに広告が出た！」という体験、ありますか？ どんな物だったか、ぜひコメントで教えてください！
```

## 字幕ファイル
- ad_ep03_ja.srt（215 行・日本語）。YouTube Studio →「字幕」→「ファイルをアップロード」→「タイミングあり」で入れる。
- 動画に字幕が焼き込んであるので、検索・翻訳・音を消して見る人のために入れる。

## 公開前に確かめること
- もくじの時刻：本番の動画で、それぞれの章の頭に合っているか（このファイルの時刻は確認用の通しのもの）。
- 合言葉（「Hey Siri」「OK Google」など）を、概要欄・タイトル・固定コメントにも書かない（読み上げで反応するのを避ける）。
- 参考のページが開けるか。
- サムネ：本番の絵は PC の 3D のコマに差し替え。
