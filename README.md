# PoliInfo3-FormalRun-QuestionAnswering

## 更新情報

- (2022/5/15) リポジトリを公開しました。

## 目的

Question Answering は、会議録の質問の要約が与えられたときに、会議録から質問に対応する答弁を見つけだし、要約した結果を返すことを目的としています。

PoliInfo-3 では、2001 年以降の東京都議会（定例会）を対象としました。

- 入力
    - 都議会だよりに含まれる、議員の質問の要約（JSON フォーマット）
    - 本会議の会議録に含まれる、議員・答弁者（説明員）の発言（JSON フォーマット）
- 出力
    - 各質問に対応する答弁（説明）の簡潔な要約（JSON フォーマット）

## 配布ファイル

- 出題ファイル
    - `PoliInfo3_QuestionAnswering_v20211120-Train.json`
        - Question Answering で使用する学習データ（2001 年 9 月から 2019 年 12 月）。都議会だよりに含まれる、議員の質問の要約
    - `PoliInfo3_QuestionAnswering_v20211120-Test.json`
        - Question Answering で使用するテストデータ（2020 年 2 月から 2020 年 12 月）。このデータの `AnswerSummary` の値を埋めたものをリーダーボードへ提出してください
    - `PoliInfo3_QuestionAnswering_v20211120-Gold.json`
        - `PoliInfo3_QuestionAnswering_v20211120-Test.json` のラベル付き正解データ。都議会だよりに含まれる、議員の質問の要約
- 会議録ファイル
    - `PoliInfo3_Utterances_v20211120.json`
        - 本会議の会議録に含まれる、議員・答弁者（説明員）の発言
- 評価スクリプト
    - `eval_script/eval.py`
        - 本タスクで用いる ROUGE 自動評価スクリプト
- サンプルスクリプト
    - `qa_sample.py`
        - 発言の末尾 40 文字を抽出するサンプルスクリプト。Formal Run でのベースライン（ID=166）として使用
        - 入出力のデータ定義や処理方法の参考にしてください

## 評価スクリプト

### 使い方

python 3.8 にて動作確認をしています。

```
usage: eval.py [-h] -f INPUT_FILE -g GS_DATA [-d UNIDIC_PATH]

NTCIR-16 QA Lab PoliInfo-3 Question Answering タスクの ROUGE 自動評価スクリプトです．

optional arguments:
  -h, --help            show this help message and exit
  -f INPUT_FILE, --input-file INPUT_FILE
                        入力データを指定します
  -g GS_DATA, --gs-data GS_DATA
                        GSデータを指定します
  -d UNIDIC_PATH, --unidic-path UNIDIC_PATH
                        MeCabで用いるUnidicのパスを指定します
```

### 評価結果について

- 出力は標準出力に JSON 文字列として表示されます。書式は以下の通りです
    - `status`: 採点が完了した場合は `success`
    - `score`: リーダーボードに掲載される代表スコア。内容語の ROUGE-1-F のマクロ平均
    - `macro_ave`: ROUGE スコアのマクロ平均
    - `ins`: 1 要約ごとの ROUGE スコア

## 参考文献

- https://poliinfo3.github.io/question-answering/
- Yasutomo Kimura, Hideyuki Shibuki, Hokuto Ototake, Yuzu Uchida, Keiichi Takamaru, Madoka Ishioroshi, Masaharu Yoshioka, Tomoyoshi Akiba, Yasuhiro Ogawa, Minoru Sasaki, Ken-ichi Yokote, Kazuma Kadowaki, Tatsunori Mori, Kenji Araki, Teruko Mitamura and Satoshi Sekine. Overview of the NTCIR-16 QA Lab-PoliInfo-3 Task. In Proceedings of the 16th NTCIR Conference on Evaluation of Information Access Technologies, June 2022.
