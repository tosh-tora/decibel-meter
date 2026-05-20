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
startup (calib読込あり)
calib_step1 → calib_step2 → calib_confirm
noise_setup → noise_measure → main
```

- `startup`: 保存済み calibration を表示。Enter → `noise_setup`、S → `main`、R → `calib_step1`
- `calib_step1/2`: 騒音計の参照値を入力。raw_buf の平均値を使って回帰
- `calib_confirm`: プレビュー確認後 `calibration.json` へ保存
- `noise_setup`: 暗騒音測定パラメータ設定（duration / percentile / margin）
- `noise_measure`: 自動タイマー計測、完了で `main` へ遷移
- `main`: 計測画面（大型 dB 表示 + 折れ線グラフ）

## 主要定数（変更が多い箇所）

| 定数 | 既定値 | 役割 |
|------|--------|------|
| `ALPHA` | 0.3 | EMA 平滑化係数（小さいほど滑らか） |
| `HISTORY_SEC` | 120 | グラフ表示秒数 |
| `UPDATE_HZ` | 12.5 | グラフ更新レート |
| `DB_MIN/MAX` | 20/130 | グラフ Y 軸範囲 |
| `GRID_DBS` | [30,50,70,90,110,130] | グラフ水平グリッド |
| `DB_COLORS` | 70/90/110 dB | 色閾値（緑/黄/橙/赤） |

## キャリブレーション

- 2点: `dB_SPL = a * dB_raw + b`（`calib_from_two_points`）
- 1点: `a=1.0`, `b = spl_ref - raw_avg`（`calib_from_one_point`）
- 保存先: `calibration.json`（スクリプトと同階層）

## ノイズゲート

`nf_floor`（パーセンタイル計算）+ `nf_settings["margin"]` dB が閾値。  
`current_spl < threshold` のとき `nf_frozen = True`、観客画面の数字が暗くなり `nf_frozen_val`（直前値）を表示・記録する。

## WASAPI

`AudioEngine._open_stream()` で排他モード（`WasapiSettings(exclusive=True)`）を先に試みる。  
失敗（他アプリが占有など）は黙って共有モードにフォールバック。  
`state.wasapi_exclusive` で現在のモードを保持し、オーバーレイに表示。

## フォント

`meiryo,yu gothic,ms gothic` を優先して日本語表示。  
観客画面の数字は 260pt ボールド（`aud_num`）、単位は 80pt（`aud_unit`）。

## ファイル構成

```
decibel_meter.py   # アプリ本体（全ロジック）
requirements.txt   # 依存パッケージ
calibration.json   # キャリブレーション保存（自動生成）
specification.md   # 企画仕様書
```
