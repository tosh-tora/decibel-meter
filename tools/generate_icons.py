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


def vacuum():
    """掃除機（キャニスター型）"""
    s = new_surf()
    pygame.draw.ellipse(s, W, pygame.Rect(48, 70, 66, 44))             # 本体
    pygame.draw.circle(s, (0, 0, 0, 0), (81, 92), 10)                  # 車輪穴
    # ホース + 持ち手 + ノズル
    pygame.draw.lines(s, W, False, [(56, 76), (34, 36), (18, 44)], 8)
    pygame.draw.rect(s, W, pygame.Rect(6, 96, 40, 10))                 # 床ノズル
    pygame.draw.line(s, W, (18, 48), (22, 96), 8)                      # パイプ
    return s


def construction():
    """ヘルメット（工事現場）"""
    s = new_surf()
    # ドーム
    pygame.draw.ellipse(s, W, pygame.Rect(24, 34, 80, 62))
    pygame.draw.rect(s, (0, 0, 0, 0), pygame.Rect(0, 66, SIZE, 62))    # 下半分カット
    pygame.draw.rect(s, W, pygame.Rect(56, 24, 16, 18), border_radius=4)  # 頂部リブ
    pygame.draw.rect(s, W, pygame.Rect(10, 64, 108, 14), border_radius=7)  # つば
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
    "vacuum.png":       vacuum,
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
