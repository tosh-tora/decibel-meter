# CLAUDE.md

## プロジェクト概要

コンサートホールのスクリーン向けリアルタイム dB SPL 表示アプリ。  
単一 Python ファイル (`decibel_meter.py`) + pygame + sounddevice で構成。

## 起動・依存

```bash
pip install -r requirements.txt   # pygame, sounddevice, numpy
python decibel_meter.py
```

## アーキテクチャ

シングルウィンドウ（1024×640、リサイズ可）。  
`State` オブジェクトを `AudioEngine`（バックグラウンドスレッド）と描画ループ（メインスレッド）が `state.lock` で共有する。

```
AudioEngine._callback()  ─── state.lock ───┐
  RMS → dBFS → EMA平滑化 → dB SPL           │
  ノイズゲート判定                           │
  history deque 追記                        │
                                            ↓
main() ループ (30 fps)
  handle_key() → screen 遷移
  draw_operator() / draw_audience()
  _draw_overlay() (Tab オーバーレイ)
```

## 画面遷移

```
device_select → startup (calib読込あり)
             └→ calib_step1 → calib_step2 → calib_confirm
noise_setup → noise_measure → main
```

- `device_select`: 起動時に必ず表示。`list_input_devices()` の一覧から ↑↓/クリックで選び、ASIO なら ←→ でチャンネル選択。Enter で `AudioEngine` を開いて startup（校正あり）/ calib_step1 へ。開けなければ `status_msg` にエラーを出して留まる。F5 で再スキャン（`_rescan_devices`）

- `startup`: 保存済み calibration を表示。Enter → `noise_setup`、S → `main`、R → `calib_step1`、D → `device_select`（calib_step1/2 でも D 可）。校正時のデバイス（`calibration.json` の `device`）が現在と違えば警告
- `calib_step1/2`: 騒音計の参照値を入力。raw_buf の平均値を使って回帰
- `calib_confirm`: プレビュー確認後 `calibration.json` へ保存
- `noise_setup`: 暗騒音測定パラメータ設定（duration / percentile / margin）
- `noise_measure`: 自動タイマー計測、完了で `main` へ遷移
- `main`: 計測画面（大型 dB 表示 + 折れ線グラフ）。`SPACE` で計測開始/停止。**再開時**は履歴に切れ目マーカー `(t, None)` を挿入して折れ線を停止前とつなげず、最大/最小（`spl_max/min` とその `_t`）・`spl_sum/count` をリセットする

## 主要定数（変更が多い箇所）

| 定数 | 既定値 | 役割 |
|------|--------|------|
| `ALPHA` | 0.3 | EMA 平滑化係数（小さいほど滑らか） |
| `HISTORY_SEC` | 120 | グラフ表示秒数 |
| `UPDATE_HZ` | 12.5 | グラフ更新レート |
| `DISP_HZ` | 3.0 | 観客画面の数字更新レート（インターバル内の最大値を表示） |
| `UPDATE_FLASH_SEC` | 0.8 | kids メーターの最大/最小 更新フラッシュの表示秒数 |
| `DB_MIN/MAX` | 20/130 | グラフ Y 軸範囲 |
| `GRID_DBS` | [30,50,70,90,110,130] | グラフ水平グリッド |
| `DB_COLORS` | 70/90/110 dB | グラフ折れ線・統計値（最大/最小）の色閾値（シアングリーン/明黄/明橙/明赤） |
| `DB_GRADIENT` | 40/65/85/105/120 dB | アイコン・キャプション用の連続グラデーション基準点（青→緑→黄→橙→赤、`db_color_smooth` で線形補間） |
| `NOISE_LABELS` | 30〜120 dB の7段階 | 騒音レベルラベル（上限dB, 大人ラベル, 大人アイコン, 子どもラベル, 子どもアイコン） |

## キャリブレーション

- 2点: `dB_SPL = a * dB_raw + b`（`calib_from_two_points`）
- 1点: `a=1.0`, `b = spl_ref - raw_avg`（`calib_from_one_point`）
- 保存先: `calibration.json`（スクリプトと同階層）

## 観客画面の表示ロジック

- **レイアウトはモード依存**（`kids = state.aud_mode == "kids"`、`content_r` = 非メーター領域の右端）:
  - **adult**: `top_h = H*0.58`。左＝統計列（`stat_col_w`）、中央＝大型数字、右＝単一イラスト（`right_w = W*0.36`）、下＝全幅グラフ
  - **kids**: `top_h = H*0.62`。右にウィンドウ縦いっぱい・幅広（`lad_col_w = W*0.30`）のはしごメーター、その左に大型アクティブアイコン（`icon_zone_w = W*0.24`）、中央に大型数字、下＝メーター左側だけのグラフ（幅 `content_r`）。遠方視認性のためメーターを大きく確保
- **表示モード**: `State.aud_mode`。`"kids"`（大人・子ども、**デフォルト**）/ `"adult"`（大人）を main 画面の `M` キーでトグル。Tab オーバーレイに現在モードを表示。大型数字・下部グラフは両モード共通。最大/最小は adult=左端の統計列、kids=右のはしごメーターに統合
- **数字色**: 固定の暖白色 `(255, 250, 200)`。`DB_COLORS`（4段階）は グラフ折れ線・adult の統計値に、`DB_GRADIENT`（連続補間）は アイコン・キャプション・kids の最大/最小ラベルの色に使用
- **フォントスケール**: `_get_sysf(size, bold)` でキャッシュ。`num_pt = top_h * 0.66` を基準に、3桁+dB が中央帯幅（`band_w`）に収まるよう縮小クランプ。ウィンドウリサイズに追従
- **セッション統計**: `State.spl_max / spl_min / spl_sum / spl_count` に蓄積。adult モードのみ左端の列に最大（上）・最小（下）を表示（kids はメーターに統合）。`R` キーで `history.clear()` と同時にリセット。最大/最小が更新された時刻は `State.spl_max_t / spl_min_t`（`time.time()`）に記録し、kids メーターの更新フラッシュに使用
  - **サンプリング**: `spl_max/min` は表示値（`disp_spl`）と同じ `val_now` を**毎コールバック**で追跡（履歴サンプリング間隔だと隙間の瞬間ピークを取りこぼし「表示値 > max」が起きるため）。`spl_sum/count`（平均用）は履歴レート（`UPDATE_HZ`）で蓄積
- **最大/最小 更新フラッシュ（kids のみ）**: 値が更新されてから `UPDATE_FLASH_SEC` 秒間、数字の周りに値の色（`db_color_smooth`）で広がりながら消えるリング＋淡いハイライトを描画。音を出すたびに最大/最小が伸びたことが観客に伝わる
- **表示スロットル**: `DISP_HZ` ごとに `disp_spl` を更新。インターバル内の最大値を `_disp_peak` で追跡して反映
- **騒音レベルラベル**: `noise_label(disp_spl, mode)` で `NOISE_LABELS` からモード別のラベル/アイコンを選択し、`_draw_level_group()` で大型イラスト（adult: 高さ `top_h*0.5`、kids: `top_h*0.45`）+ キャプションを縦積み表示。アイコンは `icons/` の白ピクトグラム（基本 128×128、`jet.png` のみ横長）を `_get_icon(file, height, max_w)` で高さ×最大幅の枠に収めてキャッシュ読込し `BLEND_RGBA_MULT` で `db_color_smooth` にティント。キャプションは列幅を超える場合のみ縮小。画像がなければテキストのみ。`nf_frozen` 時は数字と同様に減光
- **はしご型たとえメーター（kids のみ）**: `draw_noise_ladder(surf, state, rect, spl)`。`rect` はウィンドウ縦いっぱいの幅広列。内部は左列（幅42%）＝最大/最小の数値ラベル、右側＝アイコン列＋dB目盛り。`NOISE_LABELS` 全7段の子どもアイコンを dB リニア軸（`DB_MIN`〜`DB_MAX`）上に縦積みし、アイコン・目盛り・ラベルのフォントは `rect` 高さ `h` に比例（縦を大きく取るほど大きく＝遠方視認性）。アクティブ段は `db_color_smooth` ティント+1.3倍、非アクティブ段は中明度グレー `(150,150,150)`（暗くしすぎない）。現在レベルのマーカー（`h` 比例の三角＋横線、`State.ladder_pos` で30fps平滑追従）。セッション `spl_min`〜`spl_max` を半透明レンジ帯＋上下端キャップ線＋左列の「最大／最小」数値ラベル（`db_color_smooth` 着色）で統合表示し、ダイナミクスレンジを可視化

## ノイズゲート

`nf_floor`（パーセンタイル計算）+ `nf_settings["margin"]` dB が閾値。  
`current_spl < threshold` のとき `nf_frozen = True`、観客画面の数字が暗くなり `nf_frozen_val`（直前値）を表示・記録する。

## オーディオ入力（WASAPI / ASIO）

- `SD_ENABLE_ASIO` を `import sounddevice` より前に設定する（ASIO 対応 DLL の読み込みに必要。sounddevice>=0.5.1）
- `list_input_devices()`: WASAPI / ASIO の入力デバイスだけを列挙し、WASAPI の既定入力を先頭に置く。`default_device_pos()` は ASIO の Fireface → WASAPI の既定入力の順で既定の選択を決める
- `AudioEngine._open_stream()`: device は必ず明示し、samplerate はデバイスの既定値にする
  - ASIO: `channels=1` + `AsioSettings(channel_selectors=[ch])`
  - WASAPI: ネイティブのチャンネル数で排他を試み、失敗したら共有で開く（`_callback` は先頭チャンネルだけを使う）
- 現在のモード（`state.input_mode`）とデバイス名（`state.device_label`）をオーバーレイに表示

## フォント

`meiryo,yu gothic,ms gothic` を優先して日本語表示。  
観客画面の数字は 260pt ボールド（`aud_num`）、単位は 80pt（`aud_unit`）。

## ファイル構成

```
decibel_meter.py         # アプリ本体（全ロジック）
requirements.txt         # 依存パッケージ
calibration.json         # キャリブレーション保存（自動生成、校正時のデバイス名も保存）
specification.md         # 企画仕様書
icons/                   # 騒音レベルラベル用アイコン（白ピクトグラム PNG、同名差し替え可）
tools/generate_icons.py  # 仮アイコンの生成スクリプト
```
