# wagtail-mptt-comments

**ページ用のスレッド形式コメント、ゲスト向けスパム対策、任意のモデレーション、通知、Wagtail 管理ツールを提供します。記事のコメント向けであり、フォーラムのカテゴリやプライベートメッセージ用ではありません。**

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md) · [Italiano](README.it.md) · [Português (Brasil)](README.pt-BR.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Türkçe](README.tr.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

## 主な機能

- django-mptt による入れ子の返信。
- ゲスト投稿向け honeypot、時間トークン、簡易チャレンジ。
- 任意のモデレーションと管理者/返信者への通知。
- コメントツリーと最新コメント用テンプレートタグ。現在の Site で絞り込み。

## 要件と互換性

- 宣言されている依存関係: `Wagtail >= 6.0; django-mptt >= 0.16.0; django-prose-editor >= 0.26; nh3 >= 0.2.14`.
- Python、Django、Wagtail の互換性は組み合わせて確認してください。最低依存バージョンは全バージョンのサポートを意味しません。

パッケージのメタデータでは Wagtail >= 6.0 を宣言していますが、最小依存バージョンは全バージョンでの互換性を保証しません。このアーカイブには、すべての Django/Wagtail 組み合わせを網羅する自動テストマトリクスはありません。本番環境を更新する前に、正確なバージョン、データベース、ストレージバックエンド、デプロイ設定をステージングで確認してください。

## インストール

Wagtail プロジェクトと同じ仮想環境にパッケージをインストールします。

```bash
pip install wagtail-mptt-comments
```

プロジェクトで必要な他の依存関係を維持しながら、次の順序でアプリを追加します。

```python
INSTALLED_APPS = [
    # プロジェクトで必要な他の Django/Wagtail 依存関係も維持してください。
    "mptt",
    "django_prose_editor",
    "wagtail_mptt_comments",
]
```

```python
from django.urls import include, path
urlpatterns = [
    # ...
    path("comments/", include("wagtail_mptt_comments.urls")),
]
```

`python manage.py migrate wagtail_mptt_comments` を実行してください。


## 初期設定

以下は最小の開始例です。モデル名、API フィールド、URL は実際の構成に合わせてください。

```django
{% load mptt_comment_tags %}
{% render_comments page %}
```

最近のコメントは `{% get_latest_comments 5 as latest_comments %}` で表示できます。現在の Wagtail Site が設定された request コンテキストでタグを使ってください。

`Page.get_context()` でツリー、フォーム、件数を再度準備するのではなく、このタグを使用してください。設定表、モデレーションの流れ、CSS 変数の全容は英語 README にあります。


## 重要な設定と動作

このディレクトリの英語 README が正式な基準ドキュメントで、設定表と詳細例をすべて含みます。この翻訳では実際の導入手順と重要な安全上の注意を説明します。高度な設定を変更する前に英語版を確認してください。

設定の完全な一覧は[英語 README](README.md)を参照してください。

### 重要な注意事項

テンプレートで `{% render_comments page %}` を使い、`get_context()` でフォーム/ツリーを重複して準備しないでください。最新コメントは現在の Site に限定し、信頼できるプロキシが設定されていない限りプロキシヘッダーを信頼しないでください。

## セキュリティと運用

- 依存関係を最新に保ってください。ユーザー作成 HTML には定められたサニタイズ/レンダリング経路を使い、保存済みコメントやフォーラム投稿を無条件に `|safe` で表示しないでください。
- 通常ユーザー、制限ユーザー、モデレーター、管理者でマイグレーションと権限を確認してください。
- マルチサイト環境では、設定済みのすべてのホストと未設定のホストをテストしてください。Site を特定できない場合、全サイトのレコードに検索範囲を拡張してはいけません。
- API トークン、SMTP 認証情報、非公開 URL は秘密情報として扱ってください。Git にコミットしたり、公開の不具合報告に含めたりしないでください。
- マイグレーション、大量移動、インポート、初回の一括公開の前に、データベースとメディアファイルをバックアップし、まずステージングで実行してください。

## 推奨構成

- `wagtail-simple-forum` は記事コメントに加えてトピック討論とプライベートメッセージを提供します。
- 画像ディレクトリ管理と画像選択は任意です。

## 確認チェックリスト

- [ ] ステージングに候補版を導入し、Python、Django、Wagtail、DB の各バージョンを記録する。
- [ ] `python manage.py check` とパッケージのマイグレーションを実行する。
- [ ] 通常ユーザーと制限ユーザーで主要な操作を試す。
- [ ] ログ、アクセス制御、キャッシュ、バックアップ、復元を確認する。

このアーカイブは静的な構文・パッケージチェックに合格していますが、この環境では Django/Wagtail の完全な実行時統合テストを行っていません。以下の項目は全組み合わせのテスト済みという意味ではなく、リリース前の必須確認事項です。

## トラブルシューティング

動作しない場合は、アプリ設定、マイグレーション、URL の順序、ユーザー権限、Django ログを確認してください。パッケージ版と例を英語 README と照合してください。

## ライセンスとサポート

MIT. ソースコード: [https://github.com/vovansrnd/wagtail-mptt-comments](https://github.com/vovansrnd/wagtail-mptt-comments).

