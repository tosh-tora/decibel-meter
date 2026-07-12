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


def jet():
    """ジェット機シルエット（ジェット機エンジンの横）"""
    s = new_surf()
    pygame.draw.polygon(s, W, [
        (120, 64),            # 機首
        (86, 54), (60, 50),   # 胴体上面
        (64, 20),  (50, 20),  # 主翼（上）
        (38, 52),
        (20, 48), (8, 30),    # 尾翼
        (14, 62), (8, 76),
        (22, 72), (38, 74),
        (50, 106), (64, 106), # 主翼（下）
        (60, 76), (86, 72),
    ])
    return s


ICONS = {
    "residential.png":  residential,
    "library.png":      library,
    "conversation.png": conversation,
    "cicada.png":       cicada,
    "construction.png": construction,
    "horn.png":         horn,
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
