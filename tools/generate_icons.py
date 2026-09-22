#!/usr/bin/env python3
"""騒音レベルラベル用の仮アイコン（白ピクトグラム）を icons/ に生成する。

128×128 の透過 PNG を白一色で描く（jet.png のみ横長。理由は jet() を参照）。白で描くことで decibel_meter.py 側の
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
    """セミ（上面図）+ 周囲に散る鳴き声のギザギザ。座標は 400×420 の下絵基準"""
    k = SS * 0.3
    ox, oy = 100, 20                              # ギザギザの分だけ下絵の外側に余白をとる
    big = pygame.Surface((round(600 * k), round(460 * k)), pygame.SRCALPHA)
    CUT = (0, 0, 0, 0)

    def P(x, y):
        return (round((x + ox) * k), round((y + oy) * k))

    def ell(x, y, rx, ry, rot=0.0, n=72):
        a = math.radians(rot)
        return [P(x + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a),
                  y + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a))
                for t in (2 * math.pi * i / n for i in range(n))]

    def line(pts, w, color=W):
        pts = [P(x, y) for x, y in pts]
        pygame.draw.lines(big, color, False, pts, round(w * k))
        for q in pts:
            pygame.draw.circle(big, color, q, round(w * k / 2))

    def both(pts, w, color=W):                    # 左右対称に描く
        line(pts, w, color)
        line([(400 - x, y) for x, y in pts], w, color)

    def blob(x, y, rx, ry, rot=0.0, gap=9):       # 周りを透明で縁取ってから白で塗る
        pygame.draw.polygon(big, CUT, ell(x, y, rx + gap, ry + gap, rot))
        pygame.draw.polygon(big, W, ell(x, y, rx, ry, rot))

    # ── 脚（6本・関節で折れ曲がる細い脚）──────────────
    both([(165, 112), (122, 96), (104, 70), (92, 64)], 12)
    both([(160, 150), (112, 146), (84, 164), (72, 164)], 12)
    both([(165, 188), (120, 214), (104, 250), (94, 258)], 12)

    # ── 胸（大きく丸い胸部 + 背中のアーチ模様）──────────
    blob(200, 140, 56, 58)
    for rx, ry, cy in ((40, 22, 142), (24, 13, 150)):
        pygame.draw.arc(big, CUT, pygame.Rect(*P(200 - rx, cy - ry), round(2 * rx * k), round(2 * ry * k)),
                        math.radians(20), math.radians(160), round(8 * k))
    line([(200, 150), (200, 186)], 8, CUT)

    # ── 翅（細長い翅を V 字に重ねる）─────────────────
    blob(172, 292, 42, 118, 9)
    blob(228, 292, 42, 118, -9)
    for sx in (-1, 1):                            # 翅脈（抜き）
        both_x = lambda x: 200 + sx * (200 - x)
        vein = [(186, 196), (180, 260), (176, 330), (182, 392)]
        line([(both_x(x), y) for x, y in vein], 7, CUT)
        for (x0, y0), (x1, y1) in (((180, 262), (156, 300)), ((178, 300), (158, 344)),
                                   ((176, 336), (160, 376))):
            line([(both_x(x0), y0), (both_x(x1), y1)], 7, CUT)

    # ── 頭・触角・複眼 ─────────────────────────────
    blob(200, 80, 40, 20)
    both([(188, 70), (180, 46), (164, 32)], 11)
    for sx in (-1, 1):
        ex = 200 + sx * 36
        pygame.draw.circle(big, CUT, P(ex, 72), round(28 * k))
        pygame.draw.circle(big, W, P(ex, 72), round(20 * k))
        pygame.draw.circle(big, CUT, P(ex, 72), round(12 * k))
        pygame.draw.circle(big, W, P(ex, 73), round(6 * k))

    # ── 鳴き声（左右に散るギザギザ）─────────────────
    for sx in (-1, 1):
        for ang in (40, 0, -40):                  # 胸の中心から見た方向（右側基準）
            t = math.radians(ang if sx > 0 else 180 - ang)
            ux, uy = math.cos(t), -math.sin(t)
            vx, vy = -uy, ux
            x0, y0 = 200 + ux * 150, 200 + uy * 150
            pts = [(x0, y0),
                   (x0 + ux * 20 + vx * 14, y0 + uy * 20 + vy * 14),
                   (x0 + ux * 24 - vx * 14, y0 + uy * 24 - vy * 14),
                   (x0 + ux * 46, y0 + uy * 46)]
            line(pts, 14)

    return _fit(big)


def _fit(big):
    """描いた範囲を切り出し、余白 6px を残して 128×128 の中央に収める"""
    crop = big.subsurface(big.get_bounding_rect())
    fit = (SIZE - 12) / max(crop.get_width(), crop.get_height())
    small = pygame.transform.smoothscale(
        crop, (round(crop.get_width() * fit), round(crop.get_height() * fit)))
    s = new_surf()
    s.blit(small, small.get_rect(center=(SIZE // 2, SIZE // 2)))
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


def _round_poly(s, pts, r, color=W):
    """角を半径 r で丸めた多角形（太い外周線と頂点の円で角を埋める）"""
    pygame.draw.polygon(s, color, pts)
    pygame.draw.lines(s, color, True, pts, r * 2)
    for p in pts:
        pygame.draw.circle(s, color, p, r)


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


PLANE_LEVEL = 10    # _airliner()（機首上げ 15°）を水平寄りに戻す角度（度）


def _airliner():
    """機首を右上に上げた旅客機の側面シルエット（840×540、座標は 420×270 基準を 2 倍）"""
    k = 2
    p = pygame.Surface((420 * k, 270 * k), pygame.SRCALPHA)

    def poly(pts, r=5, gap=0):
        """gap > 0 なら先に一回り大きく透明で抜き、下の部品との境目を見せる
        （白一色のシルエットだと胴体と翼が一体化して形が読めないため）"""
        pts = [(x * k, y * k) for x, y in pts]
        if gap:
            _round_poly(p, pts, (r + gap) * k, color=(0, 0, 0, 0))
        _round_poly(p, pts, r * k)

    poly([(175, 108), (112, 54), (122, 46), (166, 46), (214, 68), (238, 93)])   # 奥の主翼
    poly([(14, 96), (44, 88), (92, 122), (52, 152)])                            # 垂直尾翼（後傾）
    poly([(70, 150), (96, 146), (58, 204), (42, 204)])                          # 水平尾翼
    # 胴体: 太めで機首は丸く、尾部に向けて下面をすぼめる
    poly([(90, 124), (330, 64), (362, 64), (384, 77), (392, 97), (381, 113),
          (360, 121), (250, 150), (170, 174), (115, 180), (78, 168), (52, 150)], 6, gap=5)
    poly([(214, 146), (282, 128), (224, 236), (160, 246)], 6, gap=5)            # 手前の主翼
    for i in range(7):                                                          # 客室窓
        x = 150 + i * 28
        pygame.draw.circle(p, (0, 0, 0, 0), (x * k, round((131 - (x - 150) * 0.265) * k)), 4 * k)
    return p


def jet():
    """ほぼ水平に飛ぶ旅客機 + 尾部から出る爆音のギザギザ（ジェット機 / ひこうき）

    この画像だけ正方形にせず横長で出力する。はしごメーターの最上段（120〜130 dB）は
    帯が狭く、アイコンの高さが抑えられるので、横に伸ばして機体を大きく見せる
    （decibel_meter._get_icon は高さと最大幅の枠に収めて表示する）。
    """
    big = pygame.Surface((SIZE * SS * 3, SIZE * SS * 3), pygame.SRCALPHA)
    plane = pygame.transform.rotozoom(_airliner(), -PLANE_LEVEL, 1)   # 15° の機首上げを水平寄りに戻す
    pc = (900, 700)
    big.blit(plane, plane.get_rect(center=pc))

    # 尾部（420×270 基準で (40, 150)）の回転後の位置から、機軸の後方へ爆音を描く
    a = math.radians(-PLANE_LEVEL)
    lx, ly = 40 * 2 - 420, 150 * 2 - 270
    tx = pc[0] + lx * math.cos(a) + ly * math.sin(a)
    ty = pc[1] - lx * math.sin(a) + ly * math.cos(a)
    back = math.pi + math.radians(15 - PLANE_LEVEL)   # 後方の向き（y 上向きの角度）
    n = 1.3                                           # 爆音の大きさ（機体との比率）
    for kk in (-1, 0, 1):                             # 尾部から放射状に出るギザギザ（セミと同じ表現）
        t = back + kk * 0.55
        ux, uy = math.cos(t), -math.sin(t)
        vx, vy = -uy, ux
        p0 = (tx + ux * 50 * n, ty + uy * 50 * n)
        p1 = (p0[0] + (ux * 34 + vx * 22) * n, p0[1] + (uy * 34 + vy * 22) * n)
        p2 = (p1[0] + (ux * 6 - vx * 40) * n, p1[1] + (uy * 6 - vy * 40) * n)
        p3 = (p2[0] + (ux * 38 + vx * 22) * n, p2[1] + (uy * 38 + vy * 22) * n)
        _bolt(big, [p0, p1, p2, p3], round(16 * n))

    # 描いた範囲を切り出し、幅 128（左右余白 6px）の横長画像にする
    crop = big.subsurface(big.get_bounding_rect())
    fit = (SIZE - 12) / crop.get_width()
    small = pygame.transform.smoothscale(
        crop, (round(crop.get_width() * fit), round(crop.get_height() * fit)))
    s = pygame.Surface((SIZE, small.get_height() + 12), pygame.SRCALPHA)
    s.blit(small, (6, 6))
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
