# Nerfstudio Projects

Nerfstudioによる3D再構成プロジェクト。Docker環境で実行。

## 必要環境

- Docker Desktop (NVIDIA GPU対応)
- NVIDIA GPU + 最新ドライバ
- NVIDIA Container Toolkit

## セットアップ

```bash
# 1. リポジトリのクローン
git clone https://github.com/ShujiM/nerfstudio_projects.git
cd nerfstudio_projects

# 2. Dockerイメージのビルド
docker compose build

# 3. コンテナ起動
docker compose up -d

# 4. Webインターフェース起動
# ブラウザで http://localhost:8501 にアクセス
scripts\start.bat web
```

## ディレクトリ構成

```
nerfstudio_projects/
├── app.py                  # 🆕 Web UIコード
├── Dockerfile              # Docker設定
├── docker-compose.yml      # Compose設定 (GPU, ボリューム, ポート)
├── .gitignore              # Git除外設定
├── .dockerignore           # Docker除外設定
├── scripts/                # ヘルパースクリプト
│   ├── start.sh            # Linux/Mac用
│   └── start.bat           # Windows用
├── data/                   # 📂 入力データ (Git管理外)
│   └── nerfstudio/
│       └── poster/         # COLMAP処理済みデータ
├── outputs/                # 📂 トレーニング出力 (Git管理外)
│   └── poster/
│       ├── nerfacto/
│       └── splatfacto/
└── exports/                # 📂 エクスポート結果 (Git管理外)
    ├── poster_mesh/
    ├── poster_ply/
    └── poster_pointcloud/
```

> **Note**: `data/`, `outputs/`, `exports/` はGit管理対象外です。大容量データは別途バックアップしてください。

## 使い方

### ヘルパースクリプト

```bash
# Windows
scripts\start.bat build     # イメージビルド
scripts\start.bat up        # コンテナ起動
scripts\start.bat web       # Web UI起動 (http://localhost:8501)
scripts\start.bat shell     # シェルに入る
scripts\start.bat gpu       # GPU確認
scripts\start.bat down      # コンテナ停止
```

### Nerfstudioコマンド例

コンテナ内で実行：

```bash
# データ前処理
ns-process-data images --data /workspace/data/raw_images --output-dir /workspace/data/nerfstudio/scene

# Splatfactoトレーニング
ns-train splatfacto --data /workspace/data/nerfstudio/poster

# Nerfactoトレーニング
ns-train nerfacto --data /workspace/data/nerfstudio/poster

# ビューワー (ポート7007)
# Web UI経由または直接ブラウザで http://localhost:7007 にアクセス
```

## Dockerボリューム

| コンテナパス | ホストパス | 用途 |
|---|---|---|
| `/workspace/data` | `./data` | 入力データ |
| `/workspace/outputs` | `./outputs` | トレーニング出力 |
| `/workspace/exports` | `./exports` | エクスポート結果 |
