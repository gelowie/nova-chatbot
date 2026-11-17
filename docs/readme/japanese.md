<div align="center">

![Nova banner](../img/banner.png)

<a href="../../CHANGELOG.md"><img src="../img/badges/version.svg" alt="version: 1.0"></a> <a href="../../LICENSE"><img src="../img/badges/license.svg" alt="license: MIT"></a> <a href="../../help/installing-nova.md"><img src="../img/badges/runtime.svg" alt="runtime: Python 3.10+"></a> <a href="../nova.md"><img src="../img/badges/dependencies.svg" alt="dependencies: none"></a>

</div>

# Nova — Local JSON-Powered Chatbot

> これは英語版 [README](../../README.md) の翻訳です。正本は英語版で、翻訳は遅れる場合があります。相違を見つけたら issue でお知らせください。

タイプミスに強い、親しみやすいチャットボットで、**すべて自分のコンピューター上で動作します**。
クラウド API も API キーもサードパーティのサービスも `pip install` も不要です。

<div align="center">

[English](../../README.md) | [中文](chinese.md) | [日本語](japanese.md) | [한국어](korean.md) | [Español](spanish.md)

</div>

## 目次

- [Nova とは？](#nova-とは)
- [機能](#機能)
- [制限事項](#制限事項)
- [クイックスタート](#クイックスタート)
- [Nova と話す](#nova-と話す)
- [仕組み](#仕組み)
- [リポジトリ構成](#リポジトリ構成)
- [Java 実装](#java-実装)
- [テスト](#テスト)
- [Nova を拡張する](#nova-を拡張する)
- [ドキュメント](#ドキュメント)
- [コントリビュート](#コントリビュート)
- [ライセンス](#ライセンス)

## Nova とは？

Nova は、フレンドリーで役に立つアシスタントを作るのにクラウドサービスは不要だと示す、セルフホスト型のチャットボットです。動作に必要なものはすべてこのリポジトリにあります。

- **個性**（返答、ジョーク、アドバイス）はただの JSON です：[`src/json/brain.json`](../../src/json/brain.json)
- **ロジック**（ルーティング、計算、日付）は短い Python です：[`src/py/`](../../src/py/)
- **インターフェース**は 1 つの HTML ファイルです：[`src/index.html`](../../src/index.html)
- 標準ライブラリだけの小さな**サーバー**がそれらをつなぎます：[`server.py`](../../server.py)

Nova は学習用プロジェクトであり、自分専用のローカルアシスタントを作るためのテンプレートであり、プライベートなおしゃべり相手です。メッセージがコンピューターの外に出ることはありません。できることの範囲は[制限事項](#制限事項)を参照してください。

## 機能

- **オフライン、依存ゼロ。** Python 標準ライブラリのみ。
- **正確な計算。** 「whats 5 plus 3 times 2」「144 divided by 12」「15% of 200」「2^10」「3 squared plus 4 squared」。制限付きの構文木ウォーカーで評価し、`eval()` は使いません。
- **時刻と日付。** 現在時刻、今日の日付と曜日、明日/昨日、来月/先月、「in 3 weeks」のようなオフセット（コンピューターの時計を使用）。
- **JSON の頭脳**：62 の話題（あいさつ、雑談、気持ち、アドバイス、おすすめ、ジョーク 10 件、豆知識 7 件、名言 5 件、なぞなぞ 4 件）。
- **タイプミスとスラングに強い。** 127 件のタイプミス修正と 61 件のフレーズ修正に加え、あいまい一致により「helo」「hru」「wat r u doin」「helloooo thereeee」も通じます。
- **洗練されたチャット画面。** 入力中インジケーター、クイック返信ボタン、タイムスタンプ、クリアボタン、レスポンシブ表示。
- **ローカルでプライベート。** サーバーは `127.0.0.1` だけで待ち受けます。

## 制限事項

- ルールベース：言語モデルは使っていません。Nova はパターン照合と小さなプログラムの実行を行うだけです。
- 記憶なし：メッセージはそれぞれ単独で処理されます。
- インターネットに接続しないため、天気・ニュース・株価などのライブデータはなく、ファイルや画像も読めません。
- 照合は英語のみです（他の文字やアクセント付き文字は頭脳に無視されます）。
- 内容は小規模で、範囲外の話題にはフォールバックの返答になります。
- 1 ユーザー、1 台のマシン向けです。
- [Java 実装](#java-実装)は計算と時刻のスキルのみです。

## クイックスタート

**必要なもの：** Python 3.10 以上（3.12 で開発・テスト）と Web ブラウザー。JDK は任意の Java デモにのみ必要です。

```bash
git clone https://github.com/gelowie/nova-chatbot.git
cd nova-chatbot
python server.py        # macOS/Linux では次のようにする必要がある場合があります：python3 server.py
```

ブラウザーで <http://127.0.0.1:8000> を開きます。`Ctrl+C` でサーバーを停止します。

動作確認：

```bash
curl http://127.0.0.1:8000/health
# {"ok":true}
```

詳細とトラブルシューティング：[Nova のインストール](../../help/installing-nova.md)。

## Nova と話す

| 入力 | 使われる仕組み | 返答の例 |
|---|---|---|
| `whats 5 plus 3 times 2` | 計算スキル | Solved **5 + 3 × 2** = **11** |
| `15% of 200` | 計算スキル | Solved **(15 ÷ 100) × 200** = **30** |
| `100 / 0` | 計算スキル | I can't divide by zero — that one breaks the universe. |
| `what time is it` | 時刻スキル | It's **15:03** on your system clock. |
| `what is the date in 3 weeks` | 時刻スキル | That lands on **Friday, 06 November 2026** (2026-11-06). |
| `helo` / `hru` / `sup` | JSON の頭脳 | あいさつまたは「元気？」への返答。 |
| `tell me a joke` | JSON の頭脳 | 保存されているジョークのひとつ。 |
| `i feel great today` | JSON の頭脳 | 日付ではなく、会話としての返答。 |
| `asdfghjkl` | フォールバック | 「わかりませんでした」という親切なメッセージと提案。 |

質問例の一覧と HTTP API：[Nova の使い方](../../help/how-to-use-nova.md)。

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "whats 5 plus 3 times 2"}'
# {"text": "Solved **5 + 3 × 2** = **11**", "skill": "math", "suggestions": [...]}
```

## 仕組み

```
Browser (src/index.html) ── POST /chat ──► server.py ──► NovaEngine.respond()   (src/py/engine.py)
                                                              │
                                      1. math_solver.solve       → "math"
                                      2. time_reader.handle      → "time"
                                      3. JSON brain (fuzzy match) → "brain"
                                      4. fallback                → "fallback"
```

1. 最初に答えを出したレイヤーが採用されます。
2. スキルが先に動くので、正確に答えられる質問はあいまい一致ではなく計算されます。
3. 頭脳はメッセージを正規化し（小文字化、スラングとタイプミスの修正）、各パターンと単語の重なりでスコアを付け（パターンがそのまま含まれていれば加点）、最高スコアが 0.35 以上なら答えます。
4. 返答は常に `{"text", "skill", "suggestions"}` です。

詳しくは：[アーキテクチャ](../nova.md)と [JSON の頭脳](../../help/the-json-brain.md)。

## リポジトリ構成

```
nova-chatbot/
├── server.py                  # HTTP サーバー（実行のエントリーポイント）
├── src/
│   ├── index.html             # ブラウザーのチャット画面
│   ├── json/brain.json        # 返答、パターン、タイプミス・スラング修正
│   ├── py/                    # Python エンジン（サポート対象の実装）
│   │   ├── engine.py          #   ルーティング、正規化、照合
│   │   ├── math_solver.py     #   計算スキル
│   │   └── time_reader.py     #   日付/時刻スキル
│   └── java/                  # Java の計算・時刻スキルと CLI デモ
├── tests/test_nova.py         # 自動テスト
├── docs/                      # ドキュメント、翻訳、画像
│   ├── _docs.md               #   ドキュメントの索引
│   ├── nova.md                #   アーキテクチャとコンポーネント
│   ├── compatible/            #   プラットフォーム別の互換性メモ
│   ├── readme/                #   README の翻訳
│   └── img/                   #   バナー、アイコン、バッジ
├── help/                      #   ガイド（インストール、使い方、頭脳、スキル）
├── .github/                   # Issue フォーム、PR テンプレート、CI、Dependabot
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Java 実装

[`src/java/`](../../src/java/) には**計算スキルと時刻スキル**の Java 版とコマンドラインデモがあります。これは部分的な移植です。HTTP サーバーはなく `brain.json` も読まないため会話はできず、Python エンジンと置き換えることもできません。同じ入力に対して両者のスキルは同じ出力を返しますが、Java は `double` で計算するため 2^53 を超える整数の結果は異なります。

```bash
javac -encoding UTF-8 -d out src/java/*.java
java -cp out nova.NovaEngine
```

JDK 17 以上を推奨します（OpenJDK 21 でコンパイルと実行を確認）。特殊文字が `?` と表示される場合は `-Dstdout.encoding=UTF-8`（Java 19+）を付けて実行するか、ターミナルを UTF-8 にしてください。

## テスト

```bash
python -m unittest discover -s tests -v
```

テストでは、`brain.json` が正しいこと、計算と時刻の答え、普通の会話が時刻の質問と誤認されないこと、インテントのルーティング、タイプミス処理、フォールバック、HTTP サーバー（ヘルスチェック、ページ、アイコン、チャット、不正なリクエスト）を確認します。サーバーの起動や追加パッケージは不要です。GitHub Actions も同じテストを実行し、Java ファイルをコンパイルします（[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)）。

## Nova を拡張する

- **返答・インテント・タイプミス修正の追加：** [`brain.json`](../../src/json/brain.json) を編集します。[JSON の頭脳ガイド](../../help/the-json-brain.md)を参照してください。
- **正確に答えるスキルの追加：** [自分だけのスキルを作る](../../help/_create-skill/create-your-own-skill.md)に従ってください（動作確認済みのチュートリアル）。

## ドキュメント

すべてのドキュメントの索引は [`docs/_docs.md`](../_docs.md) にあります： [Nova とは](../../help/what-is-nova.md) · [存在理由](../../help/why-nova.md) · [Nova は優れている？](../../help/is-nova-good.md) · [インストール](../../help/installing-nova.md) · [使い方](../../help/how-to-use-nova.md) · [画像](../img/_img.md)

## コントリビュート

コントリビュートを歓迎します。[コントリビューションガイド](../../.github/CONTRIBUTING.md)を読み、[バグ報告または機能リクエスト](https://github.com/gelowie/nova-chatbot/issues/new/choose)を作成するか、プルリクエストを送ってください。[変更履歴](../../CHANGELOG.md)も参照してください。

## ライセンス

Nova は [MIT ライセンス](../../LICENSE)の下で公開されています。Copyright (c) 2026 Angelo MT。
