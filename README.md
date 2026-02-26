# 🎨 3DGS Studio — Nerfstudio + SuGaR + 2DGS + GLOMAP

マルチフレームワーク対応の3Dガウシアンスプラッティング／NeRFスタジオ。
Docker Composeによるマルチコンテナ構成で、Web UIから全操作が可能です。

## ✨ 主な機能

| 機能 | 説明 |
|---|---|
| **Nerfstudio** | splatfacto, nerfacto, instant-ngp等 多数のモデル |
| **SuGaR** | 3DGSからテクスチャ付きメッシュを抽出 |
| **2DGS** | 2Dガウシアンスプラッティング（高品質レンダリング） |
| **GLOMAP** | COLMAPの10-100倍高速なグローバルSfM |
| **プログレスバー** | 全処理の進行状況をリアルタイム表示 |
| **PLY→GLB変換** | ブラウザ/PlayCanvas用に変換 |
| **外部エディタ連携** | SuperSplat / PlayCanvas への直接リンク |

## 🔧 必要環境

- Docker Desktop (NVIDIA GPU対応)
- NVIDIA GPU (RTX 3060以上推奨 / VRAM 8GB+)
- NVIDIA Container Toolkit

## 🚀 セットアップ

```bash
# 1. ビルド（初回のみ / 各コンテナ個別にビルド可能）
scripts\start.bat build-ns    # Nerfstudio + GLOMAP
scripts\start.bat build-sugar # SuGaR (メッシュ抽出)
scripts\start.bat build-2dgs  # 2DGS (2Dガウシアン)

# 2. コンテナ起動
scripts\start.bat up          # 全コンテナ起動

# 3. Web UI起動
scripts\start.bat web         # http://localhost:8501
```

## 📁 ディレクトリ構成

```
nerfstudio_projects/
├── app.py                          # Web UI (Streamlit)
├── docker-compose.yml              # 3サービス定義
├── containers/
│   ├── nerfstudio/Dockerfile       # Nerfstudio + GLOMAP + Docker CLI
│   ├── sugar/Dockerfile            # SuGaR + PyTorch3D
│   └── 2dgs/Dockerfile             # 2DGS + diff-surfel-rasterization
├── scripts/
│   ├── start.bat                   # Windows用コマンドヘルパー
│   ├── sugar_train.py              # SuGaRパイプライン
│   ├── 2dgs_train.py               # 2DGSパイプライン
│   └── convert_ply_to_glb.py       # PLY→GLB変換
├── data/                           # 📂 入力データ (Git管理外)
│   ├── uploads/                    # アップロード動画/画像
│   └── nerfstudio/                 # COLMAP/GLOMAP前処理済み
├── outputs/                        # 📂 トレーニング出力 (Git管理外)
│   └── my_project/
│       ├── splatfacto/
│       ├── nerfacto/
│       ├── sugar/
│       └── 2dgs/
└── exports/                        # 📂 エクスポート結果 (Git管理外)
```

> **Note**: `data/`, `outputs/`, `exports/` はGit管理対象外です。

## 📋 コマンド一覧

```bash
# ビルド
scripts\start.bat build-ns      # Nerfstudioビルド
scripts\start.bat build-sugar   # SuGaRビルド
scripts\start.bat build-2dgs    # 2DGSビルド

# 起動・停止
scripts\start.bat up            # 全コンテナ起動
scripts\start.bat up-ns         # Nerfstudioのみ
scripts\start.bat up-sugar      # SuGaRのみ
scripts\start.bat up-2dgs       # 2DGSのみ
scripts\start.bat down          # 全停止
scripts\start.bat status        # 状態確認

# ユーティリティ
scripts\start.bat web           # Web UI起動
scripts\start.bat shell         # nerfstudioシェル
scripts\start.bat gpu           # GPU確認
scripts\start.bat logs          # ログ表示
```

## 🌐 Web UIワークフロー

1. **📂 データアップロード** — 動画(mp4) または 画像(jpg/png)
2. **⚙️ データ前処理** — SfMエンジン選択:
   - `COLMAP (標準)` — 従来通りの信頼性
   - `GLOMAP (高速 ⚡)` — 10-100倍高速
3. **🏋️ トレーニング** — フレームワーク選択:
   - Nerfstudio (splatfacto, nerfacto等)
   - SuGaR (メッシュ抽出)
   - 2DGS (2Dガウシアン)
4. **📦 エクスポート** — PLY/OBJ/GLBダウンロード + 外部エディタリンク

## 🐳 Dockerボリューム

| コンテナパス | ホストパス | 用途 |
|---|---|---|
| `/workspace` | `.` (プロジェクトルート) | ソースコード |
| `/workspace/data` | `./data` | 入力データ |
| `/workspace/outputs` | `./outputs` | トレーニング出力 |
| `/workspace/exports` | `./exports` | エクスポート結果 |

## 🔗 ポート

| ポート | サービス |
|---|---|
| `8501` | Streamlit Web UI |
| `7007` | Nerfstudio Viewer |

## 📝 技術メモ

- **GLOMAP**: cmake 3.30 + FetchContent で COLMAP/PoseLib をソースビルド
- **PyTorch3D**: `--no-build-isolation` が必須（SuGaR/diff-gaussian-rasterization共通）
- **Docker Socket**: nerfstudioコンテナからSuGaR/2DGSコンテナを制御
- **共有ボリューム**: data/outputs/exportsは全コンテナで共有
