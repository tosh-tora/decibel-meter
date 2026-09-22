#!/usr/bin/env python3
"""騒音レベルラベル用の仮アイコン（白ピクトグラム）を icons/ に生成する。

128×128 の透過 PNG を白一色で描く（jet.png のみ横長。理由は jet() を参照）。白で描くことで decibel_meter.py 側の
BLEND_RGBA_MULT ティントがそのまま表示色になる。
一部のアイコン（セミ・ショベルカー・耳打ち・救急車）は tools/*_src.png の下絵
（白地に黒のシルエット）を白抜きにして作る。絵を変えるときは下絵を差し替えて再実行する。

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


CICADA_SRC = Path(__file__).parent / "cicada_src.png"   # セミの下絵（白地に黒のシルエット、右に鳴き声）
CICADA_AXIS_X = 201.5   # セミの左右対称軸（下絵基準、両目の中点）
CICADA_BOLT_X = 300     # これより右にある黒い塊を鳴き声のギザギザとみなす（下絵基準）


def cicada():
    """セミ + 左右に出る鳴き声のギザギザ（下絵は右側だけなので、左右反転して左にも付ける）"""
    art = _from_src(CICADA_SRC)
    src = pygame.image.load(str(CICADA_SRC))
    dark = pygame.mask.from_threshold(src, (0, 0, 0), (128, 128, 128, 255))
    bolts = [r for c in dark.connected_components() for r in c.get_bounding_rects()
             if r.left >= CICADA_BOLT_X]

    pad = 80                                                   # 左のギザギザを置く余白
    big = pygame.Surface((art.get_width() + pad, art.get_height()), pygame.SRCALPHA)
    big.blit(art, (pad, 0))
    for r in bolts:
        r = r.inflate(6, 6)                                    # 縁のアンチエイリアスも含める
        piece = pygame.transform.flip(art.subsurface(r.clip(art.get_rect())), True, False)
        big.blit(piece, (pad + round(2 * CICADA_AXIS_X) - r.right, r.top))
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


CONSTRUCTION_SRC = Path(__file__).parent / "construction_src.png"   # ショベルカーの下絵（白地に黒のシルエット）


def _from_src(path, min_area=0):
    """白地に黒の下絵を白抜きにする（黒いほど不透明）。min_area 未満の黒い塊（px、下絵基準）は消す"""
    src = pygame.image.load(str(path))
    ink = 255 - pygame.surfarray.array3d(src).mean(axis=2)
    ink = (ink - 40) * 255 / (215 - 40)                   # 地のわずかな灰色（圧縮ノイズ）を透明にする
    if min_area:
        dark = pygame.mask.from_threshold(src, (0, 0, 0), (128, 128, 128, 255))
        for comp in dark.connected_components():
            if comp.count() < min_area:
                grown = pygame.mask.Mask(comp.get_size())
                grown.draw(comp, (0, 0))
                for dx in range(-4, 5):                     # 縁のアンチエイリアスも消す
                    for dy in range(-4, 5):
                        grown.draw(comp, (dx, dy))
                hit = pygame.surfarray.array3d(grown.to_surface())[..., 0] > 0
                ink[hit] = 0
    big = pygame.Surface(src.get_size(), pygame.SRCALPHA)
    big.fill(W)
    pygame.surfarray.pixels_alpha(big)[:] = ink.clip(0, 255).astype("uint8")
    return big


def construction():
    """ショベルカー + 砕ける岩 + 衝撃のギザギザ（下絵のシルエットを白抜きにしたもの）"""
    return _fit(_from_src(CONSTRUCTION_SRC))


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


WHISPER_SRC = Path(__file__).parent / "whisper_src.png"   # 耳打ちの下絵（白地に黒のシルエット）


def whisper():
    """耳打ちする人と聞く人（ひそひそ話）。下絵にある声の三本線は小さい塊として取り除く"""
    return _fit(_from_src(WHISPER_SRC, min_area=2000))


AMBULANCE_SRC = Path(__file__).parent / "ambulance_src.png"   # 救急車の下絵（白地に黒のシルエット）


def ambulance():
    """救急車 + 回転灯の光 + サイレン音波（下絵のシルエットを白抜きにしたもの）"""
    return _fit(_from_src(AMBULANCE_SRC))


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
