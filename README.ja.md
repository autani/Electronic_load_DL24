# Electronic_load_DL24

![アプリケーション画面](Electronic_load_DL24kai.jpg)

Atorch DL24 電子負荷向けの Python 制御ソフトウェアです。

このリポジトリは [Jay2k1/Electronic_load_DL24](https://github.com/Jay2k1/Electronic_load_DL24) の個人フォークです。Jay2k1 版は [misdoro/Electronic_load_px100](https://github.com/misdoro/Electronic_load_px100) からのフォークです。

[English](README.md)

# バイナリプロトコル

[v2.70 バイナリプロトコルの説明](protocol_PX-100_2_70.md) を参照してください。

# 制御ソフトウェア

### 主な機能

- 負荷の電圧カットオフ、電流、タイマ、ON/OFF を制御
- 電圧・電流の時間グラフ（電力と MOSFET 温度も表示可能）
- グラフの時間窓の選択、最新追従、横スクロール
- 終了時およびデバイスリセット時に CSV へログ保存
- 指定電圧ステップでの内部抵抗測定
- 低電流放電の容量試験を速めるソフトウェア CC-CV 放電

### このフォークでの変更

[Jay2k1/Electronic_load_DL24](https://github.com/Jay2k1/Electronic_load_DL24) との差分です。

- 起動時は非接続。シリアルポートを選んで **OPEN**（最初に見つかったポートは自動で開かない）
- シリアル接続の **CLOSE** / **Refresh**
- グラフ横軸はデバイス内部時計ではなく、計測開始からの経過時間
- 時間範囲: 30 s、1 min、2 min、5 min、15 min、30 min、1 h、2 h、4 h、All（初期値は All）
- **Follow latest** とグラフ下のスクロールバーで過去データを確認
- 負荷操作は **ON**（赤）/ **OFF**（青）ボタン。見た目は機器の状態に追従
- 電圧・電流の調整単位は 0.1 V / 0.1 A
- 電力・MOSFET 温度グラフは、有効にするまで非表示
- 黒背景の容量・時間表示は白文字
- ウィンドウ配置、前回のシリアルポート、グラフ範囲などをローカルの `.settings` に保存（git 管理外）。保存したポートが一覧に無いときは未選択
- コンソールのデバッグ出力は既定でオフ。出すときは `-v` / `--verbose`
- 新しい pandas で落ちる不具合を修正（削除された `DataFrame._append` を使わない）

### Jay2k1 フォークでの変更（misdoro/Electronic_load_px100 との差分）

- サイドバーの読み値に電力 (W) と MOSFET 温度 (°C)
- 電力・MOSFET 温度グラフ（追加の Y 軸）
- それらのグラフの表示切り替え
- セルラベルをグラフタイトルに使用
- グラフの tight layout
- 凡例の統合

# 実行方法

## Windows（バッチファイル）

このフォルダで次をダブルクリックします。

1. `windows_setupenv.bat` — Python / pip / venv の有無を確認し、`.venv` を作って `requirements.txt` を入れる
2. `windows_runapp.bat` — venv の Python でアプリを起動する

セットアップは初回（または `requirements.txt` が変わったとき）だけ実行し、普段は `windows_runapp.bat` を使います。

## コマンドライン（Windows / Linux / macOS）

- Python 3 を入れる（開発は 3.12。3.8 以降を想定）
- リポジトリをクローンする
- `pip install --user -r requirements.txt`（venv でも可）
- `python main.py` で起動

```text
python main.py           # コンソール出力なし
python main.py -v        # デバッグ出力（プロトコル、サンプルなど）
python main.py --verbose
python main.py -h
```

初回起動時は `.settings` はありません。ウィンドウを閉じると `main.py` と同じ場所に `.settings` が作られます。次回起動時に、前回のポート（まだ存在するとき）、グラフ範囲、ウィンドウサイズなどの UI 状態を復元します。

# 免責

個人利用のためのフォークです。製品としての保守はしておらず、パッケージ済みインストーラもありません。
