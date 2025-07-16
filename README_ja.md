# GTPlanner: AI搭載のPRD生成ツール

<p align="center">
  <img src="./assets/banner.png" width="800" alt="GTPlanner Banner"/>
</p>

<p align="center">
  <strong>自然言語の記述を、Vibeコーディングに適した構造化された技術文書に変換する、インテリジェントな製品要求仕様書（PRD）生成ツールです。</strong>
</p>

<p align="center">
  <a href="#-概要">概要</a> •
  <a href="#-web-ui-推奨">Web UI</a> •
  <a href="#-機能">機能</a> •
  <a href="#️-使用方法">使用方法</a> •
  <a href="#️-アーキテクチャ">アーキテクチャ</a> •
  <a href="#-貢献">貢献</a>
</p>

<p align="center">
  <strong>言語版:</strong>
  <a href="README.md">🇺🇸 English</a> •
  <a href="README_zh-CN.md">🇨🇳 简体中文</a> •
  <a href="README_ja.md">🇯🇵 日本語</a>
</p>

---

## 🎯 概要

GTPlannerは、「vibeコーディング」のために設計された先進的なAIツールで、高レベルのアイデアや要件を、構造が明確で内容が詳細な技術文書に効率的に変換することを目的としています。最新の**Webインターフェース**を通じて、GTPlannerの全機能を体験することをお勧めします。

深い統合やカスタム開発を希望する開発者向けに、[PocketFlow](https://github.com/The-Pocket/PocketFlow)をベースに構築された強力なバックエンドエンジンも提供しています。これは非同期・ノードベースのアーキテクチャを採用し、インタラクティブなCLI、REST API、MCPサービスなど、複数の利用方法をサポートしています。

このプロジェクトは、2つの主要な部分から構成されています：
- **💻 [GTPlanner-frontend (Web UI)](https://github.com/The-Agent-Builder/GTPlanner-frontend)**：機能豊富でインタラクティブなオンラインプランニング体験を提供します。（推奨）[🚀 ライブデモを今すぐ体験！](https://the-agent-builder.com/)
- **⚙️ GTPlanner (Backend)**：CLIやAPIなど、多様な統合方法を提供する強力なバックエンドエンジン。

## 💻 Web UI (推奨)

最高かつ最も便利な体験を得るために、当社のWeb UIの使用を強くお勧めします。現代の開発者向けにカスタマイズされた、スムーズなAIプランニングワークフローを提供します。

![GTPlanner Web UI](assets/web.gif)

**主な利点:**
- **インテリジェントプランニングアシスタント**: AIの支援により、複雑なシステムアーキテクチャやプロジェクト計画を迅速に生成します。
- **即時ドキュメント生成**: プランニングセッションから包括的な技術文書を自動的に作成します。
- **Vibeコーディングのための設計**: Cursor、Windsurf、GitHub Copilotなどの最新のAI開発ツールに完璧に適合するよう出力を最適化します。
- **チームコラボレーション**: 複数のフォーマットでのエクスポートをサポートし、チームとの共有や協力を容易にします。

## MCP統合
GTPlannerが生成した計画は、お気に入りのAIプログラミングツールで直接使用でき、開発フローにシームレスに連携します：

- Cherry Studioでの使用:
  - ![Cherry StudioでのMCP使用例](assets/Cherry_Studio_2025-06-24_01-05-49.png)
- Cursorでの使用:
  - ![CursorでのMCP使用例](assets/Cursor_2025-06-24_01-12-05.png)


---

## ✨ 機能

- **🗣️ 自然言語処理**: あなたの要件記述を構造化されたPRDに変換します。
- **🌍 多言語サポート**: 英語、中国語、スペイン語、フランス語、日本語を完全にサポートし、自動言語検出機能を備えています。詳細は[多言語ガイド](docs/multilingual-guide.md)をご覧ください。
- **📝 Markdownサポート**: 既存のMarkdownドキュメントを処理し、統合します。
- **⚡ 非同期処理**: 完全非同期のパイプラインにより、迅速な応答性能を保証します。
- **🔄 反復的な最適化**: インタラクティブなフィードバックループを通じて、ドキュメントを反復的に最適化します。
- **📊 構造化された出力**: 標準化され、カスタマイズ可能な技術文書を生成します。
- **🧩 拡張可能なアーキテクチャ**: モジュール化されたノード設計により、カスタマイズと拡張が容易です。
- **🌐 多様なインターフェース**: CLI、FastAPI、MCPプロトコルを完全にサポートします。
- **🔧 LLM非依存**: 設定可能なエンドポイントにより、さまざまな大規模言語モデル（LLM）と互換性があります。
- **📁 自動ファイル管理**: ファイル名と出力ディレクトリを自動的に生成します。
- **🎯 スマート言語検出**: ユーザーの言語を自動検出し、適切な応答を提供します。

---

## 📋 環境要件 (バックエンドとCLI)

- **Python**: 3.10以降
- **パッケージマネージャー**: [uv](https://github.com/astral-sh/uv) (推奨) または pip
- **LLM APIアクセス**: OpenAI互換のAPIエンドポイント (例：OpenAI, Anthropic, またはローカルモデル)

## 🚀 インストール (バックエンドとCLI)

1. このリポジトリをクローンします

```bash
git clone https://github.com/OpenSQZ/GTPlanner.git
cd GTPlanner
```

2. 依存関係をインストールします

uvを使用 (推奨):
```bash
uv sync
```

pipを使用:
```bash
pip install -r requirements.txt
```

3. 設定

GTPlannerは、OpenAI互換のAPIをサポートしています。`settings.toml`ファイルでLLM、APIキー、環境変数、言語を設定できます。デフォルト言語は英語です。

```bash
export LLM_API_KEY="your-api-key-here"
```

## 🛠️ 使用方法

### 🖥️ CLIモード

コマンドラインを好む開発者向けに、GTPlannerは**インタラクティブモード**と**直接実行モード**をサポートする強力なコマンドラインインターフェースを提供します。

![GTPlanner CLI](assets/cil.png)

#### インタラクティブモード

CLIを初めて使用するユーザーに推奨される方法で、プロセス全体をガイドします。

インタラクティブCLIを起動:
```bash
uv run python main.py --interactive
```
または、Windowsではバッチスクリプト`start_cli.bat`を使用します。

**ワークフロー例:**
1.  起動後、言語を選択します。
2.  自然言語でプロジェクトの要件を入力します。
3.  (オプション) 出力ディレクトリを指定します。
4.  ツールがステップバイステップのプロセスを生成し、反復的な最適化のためにあなたのフィードバックを待ちます。
5.  'q'を入力して保存し、終了します。

#### 直接実行モード (非インタラクティブモード)

自動化スクリプトや迅速な生成タスクのために、コマンドライン引数で直接入力を提供し、ワンステップで完了できます。

**使用例:**
```bash
uv run python main.py --input "WeChatグループチャットを要約し、メンバーのユーザープロファイルを作成する" --output-dir "wechat_analyzer" --lang "ja"
```

**主なパラメータ:**
-   `--interactive`: インタラクティブモードを起動します。
-   `--input "..."`: 要件文字列を直接入力します。
-   `--output-dir "..."`: ドキュメントを保存するディレクトリを指定します（デフォルトは`PRD`）。
-   `--output "..."`: 具体的な出力ファイル名を指定します（`--output-dir`の設定を上書きします）。
-   `--lang <en|ja>`: 言語を設定します（デフォルトは`en`）。

### 🌐 FastAPIバックエンド

REST APIサービスを起動します:

```bash
uv run fastapi_main.py
```

サービスはデフォルトで`http://0.0.0.0:11211`で実行されます。`http://0.0.0.0:11211/docs`にアクセスして、インタラクティブなAPIドキュメントを表示できます。

**利用可能なエンドポイント:**

当社のAPIは、最大限の柔軟性を実現するために、標準、ストリーミング、統合対話など、複数のエンドポイントを提供します。

*   **統合対話エンドポイント (推奨)**
    *   `POST /chat/unified`: 強力なストリーミングファーストのエンドポイントです。意図認識、コンテキスト対話、計画生成、ドキュメント生成機能を統合しています。GTPlanner Web UIのようなインタラクティブなアプリケーションを構築するための推奨インターフェースです。

*   **ストリーミング計画エンドポイント**
    *   `POST /planning/short/stream`: ストリーミング応答を通じて、高レベルの計画を段階的に生成します。
    *   `POST /planning/long/stream`: ストリーミング応答を通じて、詳細な設計書を生成します。長時間のタスクでリアルタイムに進捗を表示するのに最適です。

*   **標準計画エンドポイント**
    *   `POST /planning/short`: 単一の応答で、完全な高レベルの計画を生成します。
    *   `POST /planning/long`: 単一の応答で、完全な詳細設計書を生成します。

### 🔌 MCPサービス (AI統合に推奨)

MCPサービスはAIアシスタントとシームレスに統合し、直接関数呼び出しをサポートします。

1. MCPサービスを起動します。

```bash
cd mcp
uv sync
uv run python mcp_service.py
```

2. MCPクライアントを設定します。

```json
{
  "mcpServers": {
    "GT-planner": {
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

**利用可能なMCPツール:**
- `generate_flow`: 要件から計画フローを生成します。
- `generate_design_doc`: 詳細なPRDを作成します。

---

## 🏗️ アーキテクチャ

GTPlannerは、PocketFlow上に構築された非同期ノードベースのアーキテクチャを使用しています：

### 主要コンポーネント

1.  **Short Planner Flow** (`short_planner_flow.py`)
    -   高レベルの計画ステップを生成
    -   反復的な最適化をサポート
    -   レビューおよび最終化ノードを含む

2.  **Main Requirement Engine** (`cli_flow.py`)
    -   完全なドキュメント生成パイプライン
    -   多段階処理とフィードバックループを備える

3.  **Node Implementations** (`nodes.py`)
    -   `AsyncInputProcessingNode`: ユーザー入力を処理
    -   `AsyncRequirementsAnalysisNode`: 要件を抽出し分類
    -   `AsyncDesignOptimizationNode`: 改善と最適化案を提示
    -   `AsyncDocumentationGenerationNode`: 構造化されたドキュメントを作成
    -   `AsyncFeedbackProcessingNode`: 反復的な最適化プロセスを管理

### フローチャート

```mermaid
flowchart TD
    inputNode[非同期入力処理] --> analysisNode[非同期要件分析]
    analysisNode --> optimizationNode[非同期設計最適化]
    optimizationNode --> docGenNode[非同期ドキュメント生成]
    docGenNode --> feedbackNode[非同期フィードバック処理]
    feedbackNode -->|新しいイテレーション| analysisNode
    feedbackNode -->|完了| endNode[プロセス終了]
```

### ユーティリティ関数 (`utils/`)

- **`call_llm.py`**: JSON修復機能を備えた非同期/同期のLLM通信
- **`parse_markdown.py`**: Markdownドキュメントを処理し、その構造を抽出
- **`format_documentation.py`**: 標準化されたドキュメントフォーマット
- **`store_conversation.py`**: 対話履歴を管理

---

## 📦 プロジェクト構造

```
GTPlanner/
├── main.py                    # フル機能のCLIメインエントリポイント
├── cli.py                     # シンプルなCLIエントリポイント
├── cli_flow.py                # 主要な要件エンジンのフロー定義
├── short_planner_flow.py      # 短期計画フローの実装
├── filename_flow.py           # 自動ファイル名生成
├── nodes.py                   # 主要な非同期ノードの実装
├── fastapi_main.py            # FastAPIバックエンドサービス
├── settings.toml              # 設定ファイル
├── pyproject.toml             # プロジェクトメタデータと依存関係
├── requirements.txt           # Pythonの依存関係
├── start_cli.bat              # Windows CLI起動スクリプト
├── api/                       # API実装
│   └── v1/
│       └── planning.py        # 計画関連のエンドポイント
├── mcp/                       # MCPサービス
│   ├── mcp_service.py         # MCPサーバーの実装
│   └── pyproject.toml         # MCP関連の依存関係
├── utils/                     # ユーティリティ関数
│   ├── call_llm.py            # LLM通信
│   ├── parse_markdown.py      # Markdown処理
│   ├── format_documentation.py  # ドキュメントフォーマット
│   └── store_conversation.py    # 対話管理
├── docs/                      # 設計書
│   ├── design.md              # 主要なアーキテクチャ設計
│   └── design-longplan.md     # 長期計画APIの設計
├── output/                    # 生成されたドキュメントの出力ディレクトリ
└── assets/                    # プロジェクトアセット
    └── banner.png             # プロジェクトバナー
```

---

## 📚 依存関係

### 主要な依存関係
- **Python** >= 3.10
- **openai** >= 1.0.0 - LLM API通信
- **pocketflow** == 0.0.1 - 非同期ワークフローエンジン
- **dynaconf** >= 3.1.12 - 設定管理
- **aiohttp** >= 3.8.0 - 非同期HTTPクライアント
- **json-repair** >= 0.45.0 - JSONレスポンスの修復
- **python-dotenv** >= 1.0.0 - 環境変数の読み込み

### APIの依存関係
- **fastapi** == 0.115.9 - REST APIフレームワーク
- **uvicorn** == 0.23.1 - ASGIサーバー
- **pydantic** - データ検証

### MCPの依存関係
- **fastmcp** - モデルコンテキストプロトコル（MCP）の実装

---

## 🤝 貢献

あらゆる形での貢献と協力を心から歓迎します。[貢献ガイドライン](CONTRIBUTING.md)をご覧になり、ぜひご参加ください。

## 📄 ライセンス

このプロジェクトはMITライセンスに基づいています。詳細は[LICENSE](LICENSE.md)ファイルをご覧ください。

## 🙏 謝辞

- [PocketFlow](https://github.com/The-Pocket/PocketFlow)非同期ワークフローエンジンをベースに構築
- 設定管理は[Dynaconf](https://www.dynaconf.com/)によって提供
- MCPプロトコルを介してAIアシスタントとシームレスに統合することを目指して設計