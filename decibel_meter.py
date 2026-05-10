#!/usr/bin/env python3
"""
Decibel Meter — Concert Hall Sound Level Display

2-point calibration: dB_SPL = a * dB_raw + b
Calibration is saved to calibration.json and reloaded on next startup.

Controls (Operator window):
  Space  — start / stop measurement
  R      — re-run calibration
  F      — toggle fullscreen on audience window
  Q/Esc  — quit
"""

import json
import math
import threading
import time
from collections import deque
from pathlib import Path

import numpy as np
import pygame
import sounddevice as sd

# ─────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────
SAMPLE_RATE   = 44100
BLOCK_SIZE    = 1024          # ~23 ms per callback
ALPHA         = 0.3           # EMA smoothing factor
HISTORY_SEC   = 120
UPDATE_HZ     = 12.5          # graph data rate
HISTORY_MAX   = int(HISTORY_SEC * UPDATE_HZ)
RAW_BUF_MAX   = int(3 * UPDATE_HZ)   # 3 s window for calibration snapshot

CALIB_FILE    = Path(__file__).parent / "calibration.json"

# Colors
BG         = (10, 10, 10)
C_TEXT     = (210, 210, 210)
C_DIM      = (90,  90,  90)
C_ACCENT   = (240, 192, 64)
C_OK       = (76,  219, 110)
C_WARN     = (255, 140, 0)
C_ERR      = (255,  60,  60)

DB_COLORS = [
    (70,  (76,  219, 110)),
    (90,  (240, 192, 64)),
    (110, (255, 140, 0)),
    (999, (255,  48, 48)),
]

GRID_DBS   = [30, 50, 70, 90, 110, 130]
DB_MIN, DB_MAX = 20, 130


# ─────────────────────────────────────────────────────────────
#  State  (shared between audio thread and render thread)
# ─────────────────────────────────────────────────────────────
class State:
    def __init__(self):
        self.lock = threading.Lock()

        # audio
        self._ema_raw    = -60.0       # internal EMA accumulator
        self.current_raw = -60.0       # smoothed dBFS (for calibration display)
        self.current_spl =  0.0        # calibrated dB SPL
        self.raw_buf     = deque(maxlen=40)   # last ~3 s of raw values

        # graph
        self.history          = deque(maxlen=HISTORY_MAX)
        self._last_hist_t     = 0.0
        self.running          = False

        # calibration
        self.calib  = None             # {"a": float, "b": float} or None
        self.screen = "startup"        # startup | calib_step1 | calib_step2
                                       # calib_confirm | noise_setup
                                       # noise_measure | main
        self.calib_pts  = []           # list of (raw_avg, spl_ref) tuples
        self.input_str  = ""           # text input buffer
        self.confirm_calib = None      # pending calib before save

        # noise gate
        self.nf_settings  = {"duration": 10, "percentile": 10, "margin": 5}
        self.nf_floor     = None       # measured noise floor dB SPL
        self.nf_buf       = []         # SPL samples collected during measurement
        self.nf_measuring = False      # currently measuring?
        self.nf_start_t   = 0.0        # measurement start time
        self.nf_cursor    = 0          # selected row in noise_setup (0/1/2)
        self.nf_frozen    = False      # gate is currently holding display
        self.nf_frozen_val = 0.0       # last SPL value before freeze

        # UI misc
        self.fullscreen     = False
        self.show_overlay   = False    # Tab: operator overlay on audience view
        self.status_msg     = ""       # one-line status for operator panel


# ─────────────────────────────────────────────────────────────
#  Audio Engine
# ─────────────────────────────────────────────────────────────
class AudioEngine:
    def __init__(self, state: State):
        self.state  = state
        self.stream = None

    def start(self):
        if self.stream:
            return
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="float32",
            channels=1,
            callback=self._callback,
        )
        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def _callback(self, indata, frames, time_info, status):
        rms = float(np.sqrt(np.mean(indata[:, 0] ** 2)))
        if rms < 1e-9:
            return
        raw = 20.0 * math.log10(rms)
        now = time.time()

        with self.state.lock:
            s = self.state
            s._ema_raw  = ALPHA * raw + (1 - ALPHA) * s._ema_raw
            smoothed    = s._ema_raw
            s.current_raw = smoothed
            s.raw_buf.append(smoothed)

            if s.calib:
                a, b = s.calib["a"], s.calib["b"]
                s.current_spl = a * smoothed + b
            else:
                s.current_spl = smoothed

            # noise floor measurement
            if s.nf_measuring:
                s.nf_buf.append(s.current_spl)
                if now - s.nf_start_t >= s.nf_settings["duration"]:
                    arr = sorted(s.nf_buf)
                    idx = max(0, int(len(arr) * s.nf_settings["percentile"] / 100) - 1)
                    s.nf_floor = arr[idx]
                    s.nf_measuring = False
                    s.screen = "main"

            # noise gate
            if s.nf_floor is not None:
                threshold = s.nf_floor + s.nf_settings["margin"]
                if s.current_spl < threshold:
                    s.nf_frozen = True
                else:
                    s.nf_frozen = False
                    s.nf_frozen_val = s.current_spl
            else:
                s.nf_frozen = False
                s.nf_frozen_val = s.current_spl

            if s.running and (now - s._last_hist_t) >= 1.0 / UPDATE_HZ:
                val = s.nf_frozen_val if s.nf_frozen else s.current_spl
                s.history.append((now, val))
                s._last_hist_t = now


# ─────────────────────────────────────────────────────────────
#  Calibration helpers
# ─────────────────────────────────────────────────────────────
def calib_from_two_points(p1, p2):
    raw1, spl1 = p1
    raw2, spl2 = p2
    if abs(raw2 - raw1) < 1e-6:
        return None
    a = (spl2 - spl1) / (raw2 - raw1)
    b = spl1 - a * raw1
    return {"a": round(a, 4), "b": round(b, 4)}


def calib_from_one_point(raw, spl):
    return {"a": 1.0, "b": round(spl - raw, 4)}


def save_calib(calib):
    with open(CALIB_FILE, "w") as f:
        json.dump(calib, f, indent=2)


def load_calib():
    if not CALIB_FILE.exists():
        return None
    try:
        with open(CALIB_FILE) as f:
            data = json.load(f)
        if "a" in data and "b" in data:
            return data
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────
#  Drawing helpers
# ─────────────────────────────────────────────────────────────
def draw_text(surf, text, font, color, x, y, anchor="topleft"):
    img  = font.render(text, True, color)
    rect = img.get_rect(**{anchor: (x, y)})
    surf.blit(img, rect)
    return rect


def db_color(db):
    for threshold, color in DB_COLORS:
        if db < threshold:
            return color
    return DB_COLORS[-1][1]


def draw_graph(surf, history, area: pygame.Rect, font_s):
    """Draw the 120-second dB SPL history graph inside *area*."""
    PAD_L, PAD_R, PAD_T, PAD_B = 46, 14, 10, 24
    gx = area.left + PAD_L
    gy = area.top  + PAD_T
    gW = area.width  - PAD_L - PAD_R
    gH = area.height - PAD_T - PAD_B

    # y-axis grid & labels
    for g in GRID_DBS:
        y = gy + gH - int((g - DB_MIN) / (DB_MAX - DB_MIN) * gH)
        pygame.draw.line(surf, (38, 38, 38), (gx, y), (gx + gW, y))
        draw_text(surf, str(g), font_s, (100, 100, 100), gx - 4, y, anchor="midright")

    if len(history) < 2:
        return

    now  = time.time()
    span = float(HISTORY_SEC)

    def tx(t):  return gx + int(gW * max(0.0, 1.0 - (now - t) / span))
    def ty(db): return gy + gH - int((db - DB_MIN) / (DB_MAX - DB_MIN) * gH)

    pts = [(tx(t), ty(db)) for t, db in history if now - t <= span]
    if len(pts) < 2:
        return

    # x-axis time labels
    for sec in range(30, HISTORY_SEC + 1, 30):
        x = tx(now - sec)
        if gx <= x <= gx + gW:
            pygame.draw.line(surf, (38, 38, 38), (x, gy), (x, gy + gH))
            draw_text(surf, f"-{sec}s", font_s, (90, 90, 90), x, gy + gH + 3, anchor="midtop")

    # filled area (semi-transparent)
    fill = pygame.Surface((area.width, area.height), pygame.SRCALPHA)
    offset = (area.left, area.top)
    shifted = [(p[0] - offset[0], p[1] - offset[1]) for p in pts]
    floor_y = gy + gH - area.top
    fill_pts = shifted + [(shifted[-1][0], floor_y), (shifted[0][0], floor_y)]
    if len(fill_pts) >= 3:
        pygame.draw.polygon(fill, (240, 192, 64, 38), fill_pts)
    surf.blit(fill, area.topleft)

    # stroke
    pygame.draw.lines(surf, C_ACCENT, False, pts, 2)


# ─────────────────────────────────────────────────────────────
#  Screen: Operator window
# ─────────────────────────────────────────────────────────────
def draw_operator(surf, state: State, fonts):
    W, H = surf.get_size()
    surf.fill((14, 14, 14))

    f_title  = fonts["title"]
    f_body   = fonts["body"]
    f_small  = fonts["small"]
    f_mono   = fonts["mono"]

    def line(text, x, y, color=C_TEXT, font=None):
        return draw_text(surf, text, font or f_body, color, x, y)

    scr = state.screen

    # ── Header ──────────────────────────────────────────────
    draw_text(surf, "DECIBEL METER", f_title, C_ACCENT, W // 2, 20, anchor="midtop")
    pygame.draw.line(surf, (40, 40, 40), (20, 56), (W - 20, 56), 1)

    y = 70

    # ── Calibration screens ──────────────────────────────────
    if scr == "startup":
        calib = state.calib
        draw_text(surf, "前回のキャリブレーションを読み込みました", f_body, C_OK, W // 2, y, anchor="midtop")
        y += 32
        draw_text(surf, f"  a = {calib['a']:.4f}   b = {calib['b']:.4f}", f_mono, C_DIM, W // 2, y, anchor="midtop")
        y += 48

        raw  = state.current_raw
        spl  = state.current_spl
        draw_text(surf, f"現在の入力:  {raw:+.1f} dBFS  →  {spl:.1f} dB SPL", f_mono, C_TEXT, W // 2, y, anchor="midtop")
        y += 60

        line("[Enter] 暗騒音測定へ進む", 40, y, C_OK)
        y += 26
        line("[S]  スキップしてスタート", 40, y, C_DIM)
        y += 26
        line("[R]  再キャリブレーション", 40, y, C_DIM)

    elif scr in ("calib_step1", "calib_step2"):
        step = 1 if scr == "calib_step1" else 2
        draw_text(surf, f"STEP {step} / 2", f_title, C_ACCENT, 40, y)
        y += 38

        if step == 1:
            desc = "静かな音を出してください（pp の弱音、呼吸音など）"
        else:
            desc = "大きな音を出してください（ff の強奏、手拍子など）"
            if state.calib_pts:
                r0, s0 = state.calib_pts[0]
                draw_text(surf, f"STEP1完了: raw={r0:+.1f}  →  {s0} dB SPL  ✓",
                          f_small, C_OK, 40, y)
                y += 26

        line(desc, 40, y, C_TEXT)
        y += 36

        raw = state.current_raw
        color_raw = C_OK if abs(raw - (state.raw_buf[-1] if state.raw_buf else raw)) < 1.0 else C_WARN
        draw_text(surf, f"マイク入力:  {raw:+.1f} dBFS", f_mono, color_raw, 40, y)
        y += 36

        line("騒音計の値を入力して Enter:", 40, y, C_DIM)
        y += 28

        # input box
        box_rect = pygame.Rect(40, y, 200, 44)
        pygame.draw.rect(surf, (28, 28, 28), box_rect, border_radius=6)
        pygame.draw.rect(surf, C_ACCENT, box_rect, 1, border_radius=6)
        disp = state.input_str + "_"
        draw_text(surf, disp, f_mono, C_TEXT, box_rect.left + 12, box_rect.centery, anchor="midleft")
        draw_text(surf, "dB SPL", f_body, C_DIM, box_rect.right + 10, box_rect.centery, anchor="midleft")
        y += 64

        line("[Enter] 確定", 40, y, C_OK)
        y += 26
        if step == 2:
            line("[S] 1点のみで確定（精度低）", 40, y, C_DIM)
            y += 26
        line("[R] 最初からやり直し", 40, y, C_DIM)

    elif scr == "calib_confirm":
        c = state.confirm_calib
        draw_text(surf, "キャリブレーション完了", f_title, C_OK, 40, y)
        y += 40
        draw_text(surf, f"a = {c['a']:.4f}   b = {c['b']:.4f}", f_mono, C_TEXT, 40, y)
        y += 30
        for i, (r, s) in enumerate(state.calib_pts, 1):
            draw_text(surf, f"  点{i}: raw={r:+.1f} dBFS  →  {s} dB SPL", f_small, C_DIM, 40, y)
            y += 22
        y += 16

        raw = state.current_raw
        spl_preview = c["a"] * raw + c["b"]
        draw_text(surf, f"現在のプレビュー:  {spl_preview:.1f} dB SPL", f_mono, C_ACCENT, 40, y)
        y += 42

        line("[Enter / S] 保存して次へ（暗騒音測定）", 40, y, C_OK)
        y += 26
        line("[R] やり直し", 40, y, C_DIM)

    elif scr == "noise_setup":
        draw_text(surf, "暗騒音 測定設定", f_title, C_ACCENT, 40, y)
        y += 10
        draw_text(surf, "ホールが静かな状態で実施してください", f_small, C_DIM, 40, y + 30)
        y += 60

        ROWS = [
            ("計測時間",   "duration",   "秒",   3, 60,  1),
            ("パーセンタイル", "percentile", "",  5, 50,  5),
            ("マージン",   "margin",     "dB",  0, 20,  1),
        ]

        for i, (label, key, unit, lo, hi, step) in enumerate(ROWS):
            val  = state.nf_settings[key]
            sel  = (i == state.nf_cursor)
            fg   = C_ACCENT if sel else C_TEXT
            bg_r = pygame.Rect(36, y - 4, W - 72, 36)
            if sel:
                pygame.draw.rect(surf, (28, 28, 28), bg_r, border_radius=6)
                pygame.draw.rect(surf, C_ACCENT, bg_r, 1, border_radius=6)
            cursor_mark = "▶ " if sel else "  "
            draw_text(surf, f"{cursor_mark}{label}", f_body, fg, 48, y + 4)
            draw_text(surf, f"{val} {unit}", f_mono, fg, W - 80, y + 4, anchor="midright")
            draw_text(surf, f"← →", f_small, C_DIM if not sel else C_ACCENT,
                      W - 60, y + 4, anchor="midleft")
            y += 42

        y += 16
        line("[Enter] 測定開始", 40, y, C_OK);   y += 26
        line("[S] スキップ（ノイズゲートなし）", 40, y, C_DIM); y += 26
        line("[R] キャリブレーションからやり直し", 40, y, C_DIM)

    elif scr == "noise_measure":
        draw_text(surf, "暗騒音 計測中", f_title, C_ACCENT, 40, y)
        y += 50

        dur     = state.nf_settings["duration"]
        elapsed = min(time.time() - state.nf_start_t, dur) if state.nf_measuring else dur
        remain  = max(0.0, dur - elapsed)

        # progress bar
        bar_rect = pygame.Rect(40, y, W - 80, 28)
        pygame.draw.rect(surf, (28, 28, 28), bar_rect, border_radius=6)
        fill_w = int(bar_rect.width * elapsed / dur)
        if fill_w > 0:
            pygame.draw.rect(surf, C_ACCENT,
                             pygame.Rect(bar_rect.left, bar_rect.top, fill_w, bar_rect.height),
                             border_radius=6)
        draw_text(surf, f"{remain:.1f} 秒", f_body, C_TEXT,
                  bar_rect.centerx, bar_rect.centery, anchor="center")
        y += 48

        draw_text(surf, f"現在: {state.current_spl:.1f} dB SPL", f_mono, C_TEXT, 40, y)
        y += 28
        draw_text(surf, f"サンプル数: {len(state.nf_buf)}", f_small, C_DIM, 40, y)
        y += 42

        line("[S] キャンセル（ノイズゲートなし）", 40, y, C_DIM)

    # ── Main screen ──────────────────────────────────────────
    elif scr == "main":
        spl = state.current_spl
        db_str = f"{max(0, min(140, round(spl)))}"
        color = db_color(spl)

        # big number
        draw_text(surf, db_str + " dB SPL", fonts["large"], color, W // 2, y, anchor="midtop")
        y += fonts["large"].get_height() + 10

        c = state.calib
        if c:
            draw_text(surf, f"calib: a={c['a']:.3f}  b={c['b']:.3f}", f_mono, (50, 50, 50),
                      W // 2, y, anchor="midtop")
        y += 28

        # status
        if state.running:
            status, sc = "● 計測中", C_OK
        else:
            status, sc = "⏸ 停止中", C_ERR
        draw_text(surf, status, f_body, sc, W // 2, y, anchor="midtop")
        y += 50

        pygame.draw.line(surf, (35, 35, 35), (20, y), (W - 20, y), 1)
        y += 12

        keys = [
            ("[SPACE] 開始 / 停止", C_TEXT),
            ("[N]  暗騒音再測定", C_DIM),
            ("[R]  再キャリブレーション", C_DIM),
            ("[F]  観客画面フルスクリーン切替", C_DIM),
            ("[Q / Esc]  終了", C_DIM),
        ]
        for k, kc in keys:
            draw_text(surf, k, f_small, kc, 40, y)
            y += 22


# ─────────────────────────────────────────────────────────────
#  Screen: Audience window
# ─────────────────────────────────────────────────────────────
def draw_audience(surf, state: State, fonts):
    W, H = surf.get_size()
    surf.fill(BG)

    scr = state.screen
    if scr != "main":
        msg = "準備中..." if scr != "startup" else "キャリブレーション中..."
        draw_text(surf, msg, fonts["body"], C_DIM, W // 2, H // 2, anchor="center")
        return

    # ── dB number (top 58%) ──────────────────────────────────
    top_h = int(H * 0.58)

    spl     = state.current_spl
    db_val  = max(0, min(140, round(spl)))
    db_str  = str(db_val)
    color   = db_color(spl)

    # Dynamically choose font size to fit width
    f_num   = fonts["aud_num"]
    f_unit  = fonts["aud_unit"]

    # noise gate: freeze & dim when below threshold
    if state.nf_frozen:
        color = tuple(max(0, c - 80) for c in color)

    num_surf  = f_num.render(db_str,  True, color)
    unit_surf = f_unit.render(" dB",  True, (60, 60, 60) if state.nf_frozen else (120, 120, 120))

    total_w = num_surf.get_width() + unit_surf.get_width()
    cx = (W - total_w) // 2
    cy = (top_h - num_surf.get_height()) // 2 + 10

    surf.blit(num_surf,  (cx, cy))
    surf.blit(unit_surf, (cx + num_surf.get_width(),
                          cy + num_surf.get_height() - unit_surf.get_height()))

    # ── status / start hint ──────────────────────────────────
    if not state.running:
        hint = fonts["body"].render("SPACE で計測開始", True, (80, 80, 80))
        surf.blit(hint, hint.get_rect(center=(W // 2, top_h - 22)))
    else:
        dot = fonts["small"].render("● REC", True, C_OK)
        surf.blit(dot, dot.get_rect(midright=(W - 20, top_h - 18)))

    # ── divider ──────────────────────────────────────────────
    pygame.draw.line(surf, (40, 40, 40), (30, top_h), (W - 30, top_h), 1)

    # ── Graph (bottom 42%) ───────────────────────────────────
    graph_rect = pygame.Rect(0, top_h + 4, W, H - top_h - 4)
    draw_graph(surf, state.history, graph_rect, fonts["small"])


# ─────────────────────────────────────────────────────────────
#  Key handling
# ─────────────────────────────────────────────────────────────
def handle_key(event, state: State, audio: AudioEngine):
    key = event.key
    scr = state.screen

    # ── Global keys ──────────────────────────────────────────
    if key in (pygame.K_q, pygame.K_ESCAPE):
        return False   # signal quit

    # ── Calibration text input ───────────────────────────────
    if scr in ("calib_step1", "calib_step2", "startup"):
        if scr in ("calib_step1", "calib_step2"):
            if key == pygame.K_BACKSPACE:
                state.input_str = state.input_str[:-1]
                return True
            if event.unicode.isdigit():
                if len(state.input_str) < 3:
                    state.input_str += event.unicode
                return True

        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if scr == "startup":
                state.screen = "noise_setup"
                audio.start()
                return True

            # parse input
            try:
                spl_ref = float(state.input_str)
            except ValueError:
                state.status_msg = "数値を入力してください"
                return True

            if not (20.0 <= spl_ref <= 140.0):
                state.status_msg = "20〜140 の範囲で入力してください"
                return True

            raw_avg = float(np.mean(list(state.raw_buf))) if state.raw_buf else state.current_raw
            state.input_str = ""

            if scr == "calib_step1":
                state.calib_pts = [(raw_avg, spl_ref)]
                state.screen = "calib_step2"

            elif scr == "calib_step2":
                state.calib_pts.append((raw_avg, spl_ref))
                c = calib_from_two_points(state.calib_pts[0], state.calib_pts[1])
                if c is None:
                    state.status_msg = "2点の音量差が小さすぎます。異なる音量で測り直してください"
                    state.screen = "calib_step1"
                    state.calib_pts = []
                else:
                    state.confirm_calib = c
                    state.screen = "calib_confirm"
            return True

        if key == pygame.K_r:
            _reset_calib(state)
            return True

        # S = skip (1-point or direct jump)
        if key == pygame.K_s:
            if scr == "startup":
                state.screen = "main"
                audio.start()
                return True
            if scr == "calib_step2" and state.calib_pts:
                raw_avg = float(np.mean(list(state.raw_buf))) if state.raw_buf else state.current_raw
                try:
                    spl_ref = float(state.input_str) if state.input_str else None
                except ValueError:
                    spl_ref = None
                if spl_ref is None:
                    spl_ref = state.calib_pts[0][1]   # re-use step1 ref as fallback
                c = calib_from_one_point(state.calib_pts[0][0], state.calib_pts[0][1])
                state.confirm_calib = c
                state.calib_pts.append((raw_avg, spl_ref))
                state.screen = "calib_confirm"
            return True

    elif scr == "calib_confirm":
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_s):
            state.calib = state.confirm_calib
            save_calib(state.calib)
            state.screen = "noise_setup"
            audio.start()
        elif key == pygame.K_r:
            _reset_calib(state)
        return True

    elif scr == "noise_setup":
        ROWS = ["duration", "percentile", "margin"]
        LIMITS = {"duration": (3, 60, 1), "percentile": (5, 50, 5), "margin": (0, 20, 1)}
        if key == pygame.K_UP:
            state.nf_cursor = (state.nf_cursor - 1) % 3
        elif key == pygame.K_DOWN:
            state.nf_cursor = (state.nf_cursor + 1) % 3
        elif key in (pygame.K_RIGHT, pygame.K_EQUALS, pygame.K_PLUS):
            k = ROWS[state.nf_cursor]
            lo, hi, step = LIMITS[k]
            state.nf_settings[k] = min(hi, state.nf_settings[k] + step)
        elif key in (pygame.K_LEFT, pygame.K_MINUS):
            k = ROWS[state.nf_cursor]
            lo, hi, step = LIMITS[k]
            state.nf_settings[k] = max(lo, state.nf_settings[k] - step)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            _start_nf_measure(state)
        elif key == pygame.K_s:
            state.nf_floor = None
            state.screen = "main"
        elif key == pygame.K_r:
            _reset_calib(state)
        return True

    elif scr == "noise_measure":
        if key == pygame.K_s:
            state.nf_measuring = False
            state.nf_floor = None
            state.screen = "main"
        return True

    elif scr == "main":
        if key == pygame.K_SPACE:
            state.running = not state.running

        elif key == pygame.K_n:
            state.screen = "noise_setup"

        elif key == pygame.K_r:
            state.running = False
            state.history.clear()
            audio.stop()
            _reset_calib(state)

        elif key == pygame.K_f:
            pygame.display.toggle_fullscreen()
            state.fullscreen = not state.fullscreen

        elif key == pygame.K_TAB:
            state.show_overlay = not state.show_overlay

    return True


def _reset_calib(state: State):
    state.screen      = "calib_step1"
    state.calib_pts   = []
    state.confirm_calib = None
    state.input_str   = ""
    state.calib       = None
    state.nf_floor    = None
    state.nf_frozen   = False


def _start_nf_measure(state: State):
    state.nf_buf      = []
    state.nf_measuring = True
    state.nf_start_t  = time.time()
    state.screen      = "noise_measure"


# ─────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────
def main():
    pygame.init()

    # ── Fonts ────────────────────────────────────────────────
    def sf(names, size, bold=False):
        return pygame.font.SysFont(names, size, bold=bold)

    FONT_NAMES = "meiryo,yu gothic,ms gothic,segoe ui,arial"
    MONO_NAMES = "meiryo,ms gothic,consolas,courier new"

    fonts = {
        "title":    sf(FONT_NAMES, 22, bold=True),
        "large":    sf(FONT_NAMES, 72, bold=True),
        "body":     sf(FONT_NAMES, 18),
        "small":    sf(FONT_NAMES, 14),
        "mono":     sf(MONO_NAMES, 16),
        "aud_num":  sf(FONT_NAMES, 260, bold=True),
        "aud_unit": sf(FONT_NAMES, 80),
    }

    # ── Single window ────────────────────────────────────────
    screen = pygame.display.set_mode((1024, 640), pygame.RESIZABLE)
    pygame.display.set_caption("Decibel Meter")

    # ── State & Audio ─────────────────────────────────────────
    state = State()
    audio = AudioEngine(state)

    # Start audio immediately for live calibration display
    audio.start()

    # Startup: load existing calibration?
    saved = load_calib()
    if saved:
        state.calib  = saved
        state.screen = "startup"
    else:
        state.screen = "calib_step1"

    # ── Main loop ─────────────────────────────────────────────
    clock = pygame.time.Clock()
    running = True

    while running:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if not handle_key(event, state, audio):
                    running = False
                    break

        if not running:
            break

        # Render
        with state.lock:
            if state.screen == "main":
                draw_audience(screen, state, fonts)
                if state.show_overlay:
                    _draw_overlay(screen, state, fonts)
            else:
                draw_operator(screen, state, fonts)

        pygame.display.flip()
        clock.tick(30)

    # Cleanup
    audio.stop()
    pygame.quit()


def _draw_overlay(surf, state: State, fonts):
    """Semi-transparent operator info panel (Tab to toggle)."""
    W, H = surf.get_size()
    panel_w, panel_h = 360, 210
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((10, 10, 10, 210))

    f = fonts["small"]
    fm = fonts["mono"]
    nf = state.nf_floor
    threshold = f"{nf + state.nf_settings['margin']:.1f}" if nf is not None else "---"
    gate_str  = f"GATE {threshold} dB {'🔇' if state.nf_frozen else '  '}" if nf is not None else "GATE  off"

    lines = [
        ("OPERATOR",                              (240, 192, 64)),
        (f"RAW  {state.current_raw:+.1f} dBFS",  (160, 160, 160)),
        (f"SPL  {state.current_spl:.1f} dB",      (210, 210, 210)),
        (gate_str,                                (100, 180, 100) if not state.nf_frozen else (180, 100, 100)),
        ("",                                      (0, 0, 0)),
        ("[SPACE] 開始/停止  [N] 暗騒音測定",      (100, 100, 100)),
        ("[F] フルスクリーン  [Tab] この画面",      (100, 100, 100)),
    ]
    if state.calib:
        c = state.calib
        lines.insert(4, (f"calib a={c['a']:.3f}  b={c['b']:.3f}", (70, 70, 70)))

    y = 10
    for text, color in lines:
        img = fm.render(text, True, color) if text else None
        if img:
            panel.blit(img, (12, y))
        y += 22

    pygame.draw.rect(panel, (60, 60, 60), panel.get_rect(), 1)
    surf.blit(panel, (W - panel_w - 16, 16))


if __name__ == "__main__":
    main()
