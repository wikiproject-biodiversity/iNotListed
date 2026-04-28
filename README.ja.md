[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · **日本語** · [മലയാളം](README.ml.md) · [Igbo](README.ig.md) · [Dagbanli](README.dag.md)

# iNotWiki — Wikipedia 未作成記事を探すツール

> 🌍 *この日本語訳はAIによる下訳です。コミュニティの皆さまの修正・改善を歓迎します。
> [Codeberg で issue を開く](https://codeberg.org/wikiproject-biodiversity/iNotListed/issues)
> か、このファイルを直接編集してください。*

**iNaturalist** と **Wikidata** を使って、生物分類群について Wikipedia に
**まだ存在しない記事**を見つけるためのコマンドラインツールです。

> **冗長ホスティング。** 本プロジェクトは、片方が停止したり利用規約が変わっても
> 利用できるよう、独立した二つの Git ホスティングサービスで意図的に公開しています。
>
> - **メイン:** [codeberg.org/wikiproject-biodiversity/iNotListed](https://codeberg.org/wikiproject-biodiversity/iNotListed) — issue・PR・CI はこちら。
> - **ミラー:** [github.com/wikiproject-biodiversity/iNotListed](https://github.com/wikiproject-biodiversity/iNotListed) — 同期されたリードオンリーミラー。

## 機能
- **iNaturalist** から観察記録を取得します。`id_above` によるページネーションで、
  10,000 件を超えるプロジェクトでも動作します。
- **Wikidata** で各分類群を検索し、指定した言語版の Wikipedia 記事の有無を確認します。
- 分類群ごとの一覧表と、観察数の多い種・観察者の上位 10 件を示す PNG グラフを含む
  Markdown レポートを生成します。
- `iNotListed/<version>` として識別され、一時的な HTTP エラー (429 / 5xx) には
  指数バックオフで自動再試行します。

---

## インストール
**Python 3.9 以降**が必要です。

```sh
pip install requests matplotlib
```

---

## 使い方
```sh
python iNotWiki.py [オプション]
```

`--project_id`、`--username`、`--country_id` のうち**ちょうど一つ**を指定します。
何も指定しない場合は `biohackathon-2025` プロジェクトが使われます。

| オプション         | 説明                                                              |
|------------------|-----------------------------------------------------------------|
| `--project_id`    | iNaturalist のプロジェクト ID または slug (例: `biohackathon-2025`)     |
| `--username`      | iNaturalist のユーザー名                                            |
| `--country_id`    | iNaturalist の地点 ID                                              |
| `--languages`     | 確認する Wikipedia の言語コード (カンマ区切り、デフォルト: `en,es,ja,ar,nl,pt,fr`) |
| `--output-folder` | Markdown レポートと PNG の出力先フォルダー (デフォルト: `reports`)         |

スクリプトは生成した Markdown レポートのパスを標準出力に出すので、
シェルでそのまま受け取れます。

```sh
REPORT_PATH=$(python iNotWiki.py --project_id biohackathon-2025)
```

Forgejo Actions の中で実行された場合は、`report_path=…` を `$GITHUB_OUTPUT` にも
書き出します。

---

## 例

```sh
# プロジェクト (slug または数値 ID)
python iNotWiki.py --project_id biohackathon-2025

# ユーザー、言語を限定
python iNotWiki.py --username johndoe --languages en,nl,de

# 地点 / 国
python iNotWiki.py --country_id 7088 --output-folder reports/colombia
```

---

## issue ベースのインターフェース (Codeberg / Forgejo Actions)
`.forgejo/workflows/` にある二つのワークフローを、二種類の issue テンプレートが起動します。

- **`[Wikiblitz]: …`** — プロジェクトのみのワークフローを実行します。
- **`[Missing Wikipedia]: …`** — フォーム全体 (プロジェクト / ユーザー / 国 +
  言語チェックボックス) を使うワークフローです。

どちらも生成したレポートを `reports/issue-<n>/` に commit し、(切り詰めた)
Markdown を issue のコメントとして投稿します。

---

## 開発
本ツールは現在、`iNotWiki.py` 一つのファイルにまとまっています。
これをラップする小さな Telegram Bot を開発中です — issue 一覧を参照してください。

## ライセンス
MIT。
