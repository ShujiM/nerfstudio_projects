# Nerfstudio Web UI ユーザーマニュアル

このマニュアルでは、Docker + Web UI 環境を使用して 3D Gaussian Splatting (Splatfacto) や NeRF (Nerfacto) を実行する手順を説明します。

## 1. 起動と終了

### 起動方法
PowerShell で以下のコマンドを実行します。

```powershell
# 初回またはコード更新時
.\scripts\start.bat build

# コンテナ起動（更新時も推奨）
.\scripts\start.bat up

# Web UI起動
.\scripts\start.bat web
```

起動後、ブラウザで **http://localhost:8501** にアクセスしてください。

### 終了方法
Web UIの実行を止めるには PowerShell で `Ctrl+C` を押します。
コンテナ自体を停止するには以下のコマンドを実行します。

```powershell
.\scripts\start.bat down
```

---

## 2. 操作フロー

### ステップ 1: データアップロード (Upload Data)

1. サイドバーから **"1. Upload Data"** を選択します。
2. **Project Name** にプロジェクト名（例: `my_data`）を入力します。スペースは使えません。
3. **Data Type** を選択します。
   - **Video**: `.mp4` ファイルをアップロードします。
   - **Images**: 画像フォルダの中身（jpg/png）を複数選択してアップロードします。

> **Note**: アップロードされたデータは `data/uploads/` に保存されます。

### ステップ 2: データ処理 (Process Data)

> ⚠️ **重要**: このステップをスキップすると、学習中にエラー (`transforms.json not found`) が発生します。

1. サイドバーから **"2. Process Data"** を選択します。
2. **Project Name** が正しいか確認します。
3. **Start Processing** をクリックします。
4. ログが表示され、処理が開始されます（数分かかります）。
5. **"Processing Complete! transforms.json created..."** と表示されれば成功です。

> **失敗する場合**:
> - 動画が短すぎる、または特徴点が少ない場合、COLMAPが失敗することがあります。
> - 赤いエラーメッセージが出た場合は、ログを確認してください。

### ステップ 3: モデル学習 (Train Model)

1. サイドバーから **"3. Train Model"** を選択します。
2. **Project Name** を確認します。
   - **"✅ Found processed data"** と表示されていればOKです。
   - **"❌ transforms.json not found"** と出る場合は、ステップ2に戻ってください。
3. **Model** を選択します（推奨: `splatfacto`）。
4. **Start Training** をクリックします。
5. ログが流れ始め、学習が始まります。
6. **Viewer**: 学習が初期化されると、`http://localhost:7007` で3Dビューワーが利用可能になります。

### ステップ 4: エクスポート (View & Export)

1. サイドバーから **"4. View & Export"** を選択します。
2. **Select Project** でプロジェクトを選びます。
3. **Select Checkpoint** で学習結果（config.yml）を選びます。
4. **Export Format** を選択します（例: `gaussian-splat`）。
5. **Export PLY** をクリックします。
6. 完了すると、**Download** ボタンが表示されます。

---

## トラブルシューティング

### Q. "transforms.json not found" エラーが出る
Processingステップが完了していません。"2. Process Data" を実行し、成功メッセージを確認してください。

### Q. Viewerが表示されない
学習開始直後は表示されません。ログに "Printing training status..." などが表示され始めてから数秒〜数分待ちます。また、Web UI内のiframeで表示されない場合は、ブラウザの新しいタブで `http://localhost:7007` を開いてください。

### Q. "No module named streamlit" エラー
Dockerイメージが古い可能性があります。以下のコマンドで再ビルドしてください。
`.\scripts\start.bat build`
その後、必ず `.\scripts\start.bat up` でコンテナを再作成してください。
