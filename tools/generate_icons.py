#!/usr/bin/env python3
"""騒音レベルラベル用の仮アイコン（白ピクトグラム）を icons/ に生成する。

128×128 の透過 PNG を白一色で描く。白で描くことで decibel_meter.py 側の
BLEND_RGBA_MULT ティントがそのまま表示色になる。
本番用イラストに差し替える場合は icons/ 内の同名ファイルを上書きすればよい。

実行:  python tools/generate_icons.py
"""

import math
from pathlib import Path

import pygame

SIZE = 128
W = (255, 255, 255, 255)
ICON_DIR = Path(__file__).parent.parent / "icons"


def new_surf():
    return pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)


def residential():
    """家 + 月（深夜の住宅地）"""
    s = new_surf()
    # 月（三日月: 白円から透明円をくり抜く）
    moon = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.circle(moon, W, (24, 24), 18)
    pygame.draw.circle(moon, (0, 0, 0, 0), (34, 18), 15)
    s.blit(moon, (76, 4))
    # 家
    pygame.draw.polygon(s, W, [(14, 66), (52, 34), (90, 66)])          # 屋根
    pygame.draw.rect(s, W, pygame.Rect(24, 66, 56, 52))                # 本体
    pygame.draw.rect(s, (0, 0, 0, 0), pygame.Rect(42, 84, 20, 34))    # ドア
    return s


def library():
    """開いた本（静かな図書館）"""
    s = new_surf()
    pygame.draw.polygon(s, W, [(64, 34), (14, 24), (14, 92), (64, 102)])
    pygame.draw.polygon(s, W, [(64, 34), (114, 24), (114, 92), (64, 102)])
    pygame.draw.line(s, (0, 0, 0, 0), (64, 34), (64, 102), 5)          # 中央の谷
    for i in range(3):                                                  # 行のライン
        y = 44 + i * 16
        pygame.draw.line(s, (0, 0, 0, 0), (22, y - 2), (56, y + 3), 4)
        pygame.draw.line(s, (0, 0, 0, 0), (72, y + 3), (106, y - 2), 4)
    return s


def conversation():
    """吹き出し ×2（普通の会話）"""
    s = new_surf()
    pygame.draw.rect(s, W, pygame.Rect(8, 20, 68, 44), border_radius=12)
    pygame.draw.polygon(s, W, [(20, 60), (20, 78), (38, 62)])
    pygame.draw.rect(s, W, pygame.Rect(52, 66, 68, 44), border_radius=12)
    pygame.draw.polygon(s, W, [(108, 106), (108, 124), (90, 108)])
    return s


def cicada():
    """セミ（上面図・騒音をまき散らすセミの鳴き声）"""
    s = new_surf()

    # ── 騒音（周囲に散らす稲妻）────────────────────────────
    bolt = pygame.Surface((26, 34), pygame.SRCALPHA)
    pygame.draw.polygon(bolt, W, [(16, 0), (4, 20), (13, 20), (6, 34),
                                  (24, 13), (14, 13), (20, 0)])
    for bx, by, ang in [(20, 24, 40), (13, 62, 90), (20, 100, -40),
                        (108, 24, -40), (115, 62, -90), (108, 100, 40)]:
        rb = pygame.transform.rotate(bolt, ang)
        s.blit(rb, rb.get_rect(center=(bx, by)))

    # ── 脚（6本・先に描いて翅で根元を隠す）───────────────
    for x0, y0, x1, y1, x2, y2 in [(54, 34, 42, 26, 34, 28),
                                   (54, 42, 40, 42, 32, 46),
                                   (55, 50, 43, 56, 36, 62)]:
        pygame.draw.lines(s, W, False, [(x0, y0), (x1, y1), (x2, y2)], 3)
        pygame.draw.lines(s, W, False,
                          [(128 - x0, y0), (128 - x1, y1), (128 - x2, y2)], 3)

    # ── 翅（左右の大きな翅）──────────────────────────────
    wingL = [(60, 36), (48, 44), (38, 66), (40, 92), (52, 110), (61, 84), (62, 54)]
    wingR = [(128 - x, y) for x, y in wingL]
    pygame.draw.polygon(s, W, wingL)
    pygame.draw.polygon(s, W, wingR)
    # 翅脈（控えめなクロスハッチ・抜き。白い翅部分だけが切り取られる）
    for k in range(5):
        x = 34 + k * 10
        pygame.draw.line(s, (0, 0, 0, 0), (x, 44), (x + 22, 108), 1)
        pygame.draw.line(s, (0, 0, 0, 0), (x + 22, 44), (x, 108), 1)
        pygame.draw.line(s, (0, 0, 0, 0), (128 - x, 44), (106 - x, 108), 1)
        pygame.draw.line(s, (0, 0, 0, 0), (106 - x, 44), (128 - x, 108), 1)

    # ── 胴体（胸部＋節のある腹部）────────────────────────
    pygame.draw.polygon(s, W, [(58, 44), (70, 44), (67, 96), (64, 106), (61, 96)])
    for y in (54, 66, 78, 90):
        pygame.draw.line(s, (0, 0, 0, 0), (59, y), (69, y), 2)
    pygame.draw.ellipse(s, W, pygame.Rect(52, 28, 24, 18))

    # ── 頭部・触角・複眼（大きなつぶらな目）──────────────
    pygame.draw.ellipse(s, W, pygame.Rect(50, 14, 28, 18))
    pygame.draw.lines(s, W, False, [(58, 16), (52, 6), (45, 4)], 2)
    pygame.draw.lines(s, W, False, [(70, 16), (76, 6), (83, 4)], 2)
    for ex in (51, 77):
        pygame.draw.circle(s, W, (ex, 18), 10)
        pygame.draw.circle(s, (0, 0, 0, 0), (ex, 18), 5)               # 瞳（抜き）
        pygame.draw.circle(s, W, (ex - 2, 15), 2)                      # ハイライト
    return s


def construction():
    """ブルドーザー（工事現場）"""
    s = new_surf()
    # クローラー（履帯）
    pygame.draw.rect(s, W, pygame.Rect(26, 94, 82, 24), border_radius=12)
    for cx in (42, 60, 78, 96):                                       # 転輪（穴）
        pygame.draw.circle(s, (0, 0, 0, 0), (cx, 108), 6)
    # 車体（エンジンフード）
    pygame.draw.polygon(s, W, [(40, 80), (48, 62), (90, 62), (90, 94), (40, 94)])
    # 運転席（キャブ）
    pygame.draw.rect(s, W, pygame.Rect(64, 44, 28, 20), border_radius=3)
    pygame.draw.rect(s, (0, 0, 0, 0), pygame.Rect(70, 50, 14, 12))    # 窓（抜き）
    # 排気筒
    pygame.draw.rect(s, W, pygame.Rect(54, 46, 7, 18))
    pygame.draw.rect(s, W, pygame.Rect(52, 42, 11, 6), border_radius=2)  # キャップ
    # 排土板（ブレード）
    pygame.draw.polygon(s, W, [(20, 58), (32, 62), (32, 104), (26, 112), (14, 108), (12, 64)])
    pygame.draw.line(s, W, (32, 90), (50, 80), 7)                     # プッシュアーム
    return s


def horn():
    """車 + 音波（自動車のクラクション）"""
    s = new_surf()
    pygame.draw.rect(s, W, pygame.Rect(8, 66, 84, 28), border_radius=8)   # 車体
    pygame.draw.polygon(s, W, [(22, 66), (34, 46), (66, 46), (76, 66)])   # キャビン
    pygame.draw.circle(s, W, (28, 96), 12)                                # 車輪
    pygame.draw.circle(s, W, (72, 96), 12)
    pygame.draw.circle(s, (0, 0, 0, 0), (28, 96), 5)
    pygame.draw.circle(s, (0, 0, 0, 0), (72, 96), 5)
    for r in (12, 22, 32):                                                # 音波
        pygame.draw.arc(s, W, pygame.Rect(92 - r, 58 - r, r * 2, r * 2),
                        -math.pi / 4, math.pi / 4, 5)
    return s


def whisper():
    """口元に人差し指（ひそひそごえ）"""
    s = new_surf()
    # 顔
    pygame.draw.circle(s, W, (64, 64), 46)
    # 目（閉じた目・抜き）
    for ex in (46, 82):
        pygame.draw.arc(s, (0, 0, 0, 0), pygame.Rect(ex - 9, 46, 18, 14),
                        math.pi, 2 * math.pi, 4)
        pygame.draw.circle(s, (0, 0, 0, 0), (ex, 52), 6)
    # 人差し指（抜きの縁取りの中に白い指）
    pygame.draw.rect(s, (0, 0, 0, 0), pygame.Rect(53, 64, 22, 60), border_radius=11)
    pygame.draw.rect(s, W, pygame.Rect(58, 69, 12, 52), border_radius=6)
    return s


def ambulance():
    """救急車 + サイレン音波（きゅうきゅうしゃのサイレン）"""
    s = new_surf()
    # 荷室（箱）
    pygame.draw.rect(s, W, pygame.Rect(8, 52, 74, 46), border_radius=4)
    # キャブ（前部）
    pygame.draw.polygon(s, W, [(82, 62), (104, 62), (116, 78), (116, 98), (82, 98)])
    pygame.draw.rect(s, (0, 0, 0, 0), pygame.Rect(88, 68, 16, 12))     # 窓（抜き）
    # 十字マーク（抜き）
    pygame.draw.rect(s, (0, 0, 0, 0), pygame.Rect(39, 60, 10, 30))
    pygame.draw.rect(s, (0, 0, 0, 0), pygame.Rect(29, 70, 30, 10))
    # 車輪
    for cx in (30, 98):
        pygame.draw.circle(s, W, (cx, 102), 11)
        pygame.draw.circle(s, (0, 0, 0, 0), (cx, 102), 5)
    # 回転灯 + サイレン音波
    pygame.draw.rect(s, W, pygame.Rect(38, 40, 12, 12), border_radius=3)
    for r in (12, 20, 28):
        pygame.draw.arc(s, W, pygame.Rect(44 - r, 38 - r, r * 2, r * 2),
                        math.pi / 6, 5 * math.pi / 6, 4)
    return s


SS = 4   # jet() は 4 倍の解像度で描いて縮小する（斜めの輪郭をなめらかにするため）


def _round_poly(s, pts, r):
    """角を半径 r で丸めた多角形（太い外周線と頂点の円で角を埋める）"""
    pygame.draw.polygon(s, W, pts)
    pygame.draw.lines(s, W, True, pts, r * 2)
    for p in pts:
        pygame.draw.circle(s, W, p, r)


def _arc_band(s, c, r, w, a0, a1, n=24):
    """太い円弧を塗りつぶし多角形で描く（draw.arc を太くすると隙間が出るため）"""
    ts = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    outer = [(c[0] + (r + w / 2) * math.cos(t), c[1] - (r + w / 2) * math.sin(t)) for t in ts]
    inner = [(c[0] + (r - w / 2) * math.cos(t), c[1] - (r - w / 2) * math.sin(t))
             for t in reversed(ts)]
    pygame.draw.polygon(s, W, outer + inner)
    for t in (a0, a1):
        pygame.draw.circle(s, W, (round(c[0] + r * math.cos(t)), round(c[1] - r * math.sin(t))), w // 2)


def _bolt(s, pts, w):
    pygame.draw.lines(s, W, False, pts, w)
    for q in pts:
        pygame.draw.circle(s, W, (round(q[0]), round(q[1])), w // 2)


def _airliner():
    """機首を右に向けた旅客機の側面シルエット（600×300、中心 (300, 150)）"""
    p = pygame.Surface((600, 300), pygame.SRCALPHA)
    T = (0, 0, 0, 0)
    _round_poly(p, [(312, 126), (366, 126), (262, 52), (240, 52)], 4)      # 奥の主翼（後退翼）
    _round_poly(p, [(64, 124), (26, 34), (56, 34), (156, 124)], 4)          # 垂直尾翼
    # 胴体: 細長く、機首は丸くすぼめ、尾部は上へ跳ね上げる
    pygame.draw.polygon(p, W, [
        (36, 118), (150, 121), (480, 121), (528, 126), (556, 136), (574, 150),
        (568, 162), (544, 172), (486, 178), (176, 178), (90, 160), (40, 132),
    ])
    _round_poly(p, [(78, 146), (18, 188), (44, 190), (136, 156)], 4)        # 水平尾翼
    _round_poly(p, [(296, 170), (392, 170), (246, 284), (214, 284)], 4)     # 手前の主翼（後退翼）
    # エンジン: 主翼と同じ白で重なるため、周囲を細く抜いて輪郭を見せる
    pygame.draw.rect(p, T, pygame.Rect(274, 180, 108, 42), border_radius=20)
    pygame.draw.rect(p, W, pygame.Rect(318, 172, 20, 14))                   # パイロン
    pygame.draw.rect(p, W, pygame.Rect(282, 186, 92, 30), border_radius=14)
    pygame.draw.ellipse(p, T, pygame.Rect(362, 191, 10, 20))                # 吸気口
    for i in range(15):                                                     # 客室窓
        pygame.draw.circle(p, T, (184 + i * 20, 140), 5)
    pygame.draw.polygon(p, T, [(520, 136), (548, 138), (556, 146), (522, 146)])  # 操縦席窓
    return p


def jet():
    """上昇中の旅客機 + 尾部から出る爆音（音波とギザギザ）（ジェット機 / ひこうき）"""
    big = pygame.Surface((SIZE * SS * 2, SIZE * SS * 2), pygame.SRCALPHA)
    angle, scale, cx, cy = 30, 0.9, 600, 500
    body = pygame.transform.rotozoom(_airliner(), angle, scale)
    big.blit(body, body.get_rect(center=(cx, cy)))

    # 尾部の位置（機体ローカル (50, 140) を回転・縮小した点）から後方へ爆音を描く
    a = math.radians(angle)
    lx, ly = 50 - 300, 140 - 150
    tx = cx + scale * (lx * math.cos(a) + ly * math.sin(a))
    ty = cy + scale * (-lx * math.sin(a) + ly * math.cos(a))
    back = math.pi + a                           # 後方の向き（y 上向きの角度）
    for r in (58, 94):                           # 音波
        _arc_band(big, (tx, ty), r, 16, back - 0.6, back + 0.6)
    for k in (-1, 0, 1):                         # 音波の外側に放射状のギザギザ（セミと同じ表現）
        t = back + k * 0.55
        ux, uy = math.cos(t), -math.sin(t)
        vx, vy = -uy, ux
        p0 = (tx + ux * 124, ty + uy * 124)
        p1 = (p0[0] + ux * 34 + vx * 22, p0[1] + uy * 34 + vy * 22)
        p2 = (p1[0] + ux * 6 - vx * 40, p1[1] + uy * 6 - vy * 40)
        p3 = (p2[0] + ux * 38 + vx * 22, p2[1] + uy * 38 + vy * 22)
        _bolt(big, [p0, p1, p2, p3], 16)

    # 描いた範囲を切り出し、余白 6px を残して 128×128 の中央に収める
    crop = big.subsurface(big.get_bounding_rect())
    fit = (SIZE - 12) / max(crop.get_width(), crop.get_height())
    small = pygame.transform.smoothscale(
        crop, (round(crop.get_width() * fit), round(crop.get_height() * fit)))
    s = new_surf()
    s.blit(small, small.get_rect(center=(SIZE // 2, SIZE // 2)))
    return s


ICONS = {
    "residential.png":  residential,
    "library.png":      library,
    "conversation.png": conversation,
    "cicada.png":       cicada,
    "construction.png": construction,
    "horn.png":         horn,
    "whisper.png":      whisper,
    "ambulance.png":    ambulance,
    "jet.png":          jet,
}


def main():
    pygame.init()
    ICON_DIR.mkdir(exist_ok=True)
    for name, fn in ICONS.items():
        path = ICON_DIR / name
        pygame.image.save(fn(), str(path))
        print(f"wrote {path}")
    pygame.quit()


if __name__ == "__main__":
    main()
