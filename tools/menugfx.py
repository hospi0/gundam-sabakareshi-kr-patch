# -*- coding: utf-8 -*-
r"""STAGE SELECT 화면 글 그림 한글화(2026-10-10, 하스피 «큰일났어» — 第1話·제목·戦術得点·被弾率·総合戦績·評価·点 이 일본어 그대로)
  그림 = 3.BIN 안 SGL 텍스처 표(폭·높이·CG·HV 8 B, 3.BIN 0x06020000 적재) + 그림 자료(파일 오프셋 = CG×8 + DELTA)
  표·DELTA 는 3.BIN 에서 자동으로 찾음(가장 긴 텍스처 표 · PRESS START BUTTON 그림 위치) — 1·2·3편 공통 도구, 편별 번호는 ITEMS
  색: 0 투명 · 1‥14 회색 단계(14 가장 밝음, 팔레트 colr 0x0E20 = 0x620 회색 사다리) — 원본처럼 그림자 없이 덮임만큼 밝기
  python tools/menugfx.py   → work/gfx/menu_kr.png 미리보기(원본 | 한글)
"""
import os, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import scgfx

GAME = 1 if 'gundam-blue' in ROOT else 2 if 'gundam-ao' in ROOT else 3
FONT = os.path.join(scgfx.NG, 'NanumGothicBold.ttf')
_T = scgfx.TITLES
# 번호 → (한국어, 정렬) — 번호는 각 편 3.BIN 텍스처 표 차례(work/gfx/menu3bin.png 로 확인)
ITEMS = {
    1: {65: ('평가', 'l'), **{66 + i: ('제%d화' % (i + 1), 'c') for i in range(5)},
        **{71 + i: (_T[i], 'c') for i in range(5)}, 76: ('전술득점', 'l'), 77: ('피탄율', 'l'), 78: ('종합전적', 'l'), 91: ('점', 'c')},
    2: {72: ('평가', 'l'), **{73 + i: ('제%d화' % (i + 1), 'c') for i in range(5)},
        **{78 + i: (_T[i], 'c') for i in range(5)}, 83: ('전술득점', 'l'), 84: ('피탄율', 'l'), 85: ('종합전적', 'l'), 98: ('점', 'c')},
    3: {74: ('평가', 'l'), **{75 + i: ('제%d화' % (i + 1), 'c') for i in range(5)},
        80: (_T[0], 'c'), 81: (_T[1], 'c'), 82: (_T[2], 'c'), 84: ('의 진실', 'l'), 85: (_T[4], 'c'),   # 83 = «EXAM» 그림 그대로 + 84 «の真実»
        86: ('전술득점', 'l'), 87: ('피탄율', 'l'), 88: ('종합전적', 'l'), 101: ('점', 'c')},
}[GAME]


def ok(d, a):
    w, h, cg, hv = struct.unpack_from('>4H', d, a)
    return 8 <= w <= 504 and w % 8 == 0 and 1 <= h <= 255 and hv == ((w // 8) << 8 | h)


def table(d):
    """가장 긴 텍스처 표 → (시작, [(w,h,cg)…], DELTA)"""
    best, a = (0, 0), 0
    while a < len(d) - 8:
        if ok(d, a):
            b = a
            while ok(d, b): b += 8
            if (b - a) // 8 > best[1]: best = (a, (b - a) // 8)
            a = b
        else: a += 2
    ents = [struct.unpack_from('>3H', d, best[0] + i * 8) for i in range(best[1])]
    w, h, cg = ents[36]                                       # PRESS START BUTTON(세 편 같은 그림, 144×16)
    i = d.find(PRESS) - PRESS_AT; assert i > 0 and (w, h) == (144, 16), ('PRESS START 못 찾음', w, h)
    return best[0], ents, i - cg * 8


PRESS_AT = 72 * 5                                              # PRESS START BUTTON 그림 5‥6째 줄(144 B) — 세 편 같은 그림
PRESS = bytes.fromhex('7f5222afad4223ca4f933332eb333344eb33334400000000eb333344233cd43302f9af30ad4223ca233cd433000000009d8445bffa0004d7233cd433233cd433ad3333daad5334cc7f5334bfae5335da5f833341fb333300fb33330000000000fb333300000cd00007f77f80ae5335da000cd000000000009e6124aefa0004d7000cd000000cd000bc0000cbbc2000bd')


def render(text, w, h, align):
    for size in range(16, 9, -1):
        F = ImageFont.truetype(FONT, size * 4)
        b = F.getbbox(text)
        if (b[2] - b[0]) / 4 <= w - 1 and (F.getbbox('한')[3] - F.getbbox('한')[1]) / 4 <= h - 2: break
    big = Image.new('L', (w * 4, h * 4), 0); dr = ImageDraw.Draw(big)
    tw = b[2] - b[0]; gh = F.getbbox('한'); top = (h * 4 - (gh[3] - gh[1])) // 2 - gh[1]
    x = {'l': 0, 'c': (w * 4 - tw) // 2}[align] - b[0]
    dr.text((x, top), text, font=F, fill=255)
    cov = np.asarray(big.resize((w, h), Image.LANCZOS), np.float32) / 255
    px = np.where(cov > 0.06, np.clip(np.round(cov * 14), 1, 14), 0).astype(np.uint8)
    return px, size


def patch(d3):
    d = bytearray(d3); _, ents, delta = table(bytes(d3))
    for k, (text, al) in ITEMS.items():
        w, h, cg = ents[k]; o = cg * 8 + delta
        px, _ = render(text, w, h, al)
        scgfx.put4(d, o, px)
    assert len(d) == len(d3)
    return bytes(d)


def preview():
    import disc
    d = disc.read('/3.BIN'); _, ents, delta = table(d); rows = []
    for k, (text, al) in ITEMS.items():
        w, h, cg = ents[k]; a = scgfx.get4(d, cg * 8 + delta, w, h); b, sz = render(text, w, h, al)
        rows.append(np.hstack([a, np.zeros((h, 6), np.uint8), b, np.zeros((h, 260 - 2 * w), np.uint8)]))
        print('%3d %3d×%d %-12s 크기 %d' % (k, w, h, text, sz))
    img = np.vstack([np.vstack([r, np.zeros((3, r.shape[1]), np.uint8)]) for r in rows])
    g = (img * 17).astype(np.uint8); g[img == 0] = 40
    Image.fromarray(g).resize((g.shape[1] * 3, g.shape[0] * 3), Image.NEAREST).save(os.path.join(ROOT, 'work', 'gfx', 'menu_kr.png'))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    preview()
