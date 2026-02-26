# GLOMAP統合 & プログレスバー実装プラン

## 概要

1. **GLOMAP**: COLMAPの10-100倍高速なグローバルSfMパイプラインを前処理オプションとして追加
2. **プログレスバー**: 全処理（前処理/トレーニング/エクスポート/変換）に進行状況表示を追加

---

## Proposed Changes

### 1. GLOMAP統合

GLOMAPはCOLMAPデータベースを入力として使用するため、nerfstudioコンテナに追加します。

#### [MODIFY] [containers/nerfstudio/Dockerfile](file:///c:/Users/muna1/nerfstudio_projects/containers/nerfstudio/Dockerfile)

- GLOMAP をソースからビルド（cmake 3.28+ / ninja / COLMAP依存）
- 既存COLMAPと共存

#### [MODIFY] [app.py](file:///c:/Users/muna1/nerfstudio_projects/app.py)

**前処理ページに追加:**
- SfMエンジン選択: `COLMAP (標準)` / `GLOMAP (高速)`
- GLOMAPパイプライン: `colmap feature_extractor` → `colmap exhaustive_matcher` → `glomap mapper`
- 出力はCOLMAP形式のため、既存ワークフローと完全互換

---

### 2. プログレスバー

#### [MODIFY] [app.py](file:///c:/Users/muna1/nerfstudio_projects/app.py)

[run_command](file:///c:/Users/muna1/nerfstudio_projects/app.py#76-112) 関数を `run_command_with_progress` に拡張:

| 処理 | プログレス検出方法 |
|---|---|
| **COLMAP前処理** | ステップ数（feature extraction → matching → mapping → undistortion） |
| **GLOMAP前処理** | 同上（feature → matching → glomap mapper） |  
| **Nerfstudioトレーニング** | ログからイテレーション番号をパース（`Step 1000/30000`） |
| **SuGaR** | パイプラインステップ（3DGS → coarse → refine）× 各ステップ内イテレーション |
| **2DGS** | ログからイテレーション番号をパース |
| **エクスポート** | ステップベース |
| **PLY→GLB変換** | indeterminate（処理時間短いため） |

---

## Verification Plan

1. GLOMAPビルド確認: `glomap -h` がコンテナ内で動作
2. 前処理ページでGLOMAP選択 → SfM実行 → transforms.json生成確認
3. プログレスバーが各処理で正しく進捗表示されること
