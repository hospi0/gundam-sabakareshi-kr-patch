# -*- coding: utf-8 -*-
r"""건담 외전 III 결과 화면·시나리오 제목 그림 한글(2026-10-10, 1편 tools/scgfx.py 에서) — 무압축 4비트 그림 제자리 덮어쓰기.
  팔레트: 16단계 회색(0 = 흰색 … 15 = 검정), 그림마다 앞 0x20 B 에 팔레트. 글자 = 흰색 안티에일리어스 → 덮인 정도로 색 번호(15 − 15×덮임).
  · SC_1.BIN 한마디 288×80 21장(교관 평가 + 실패 메시지) — 틀(바깥 3 px)은 두고 안쪽 지우고 다시 씀
  · SC_1.BIN 항목 이름 240×80(16곳 같은 그림) — 글자 자리(왼쪽 이름·오른쪽 단위)만
  · SC_1.BIN 단위 열 40×80(17곳) — 点 → 점
  · S0_1.BIN 시나리오 제목 240×32 5장(TITLE_BASE + n×0xF20) — 기울인 굵은 글씨
  python tools/scgfx.py   → work/gfx/*.png 미리보기(위 원본 · 아래 한글)
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
NG = r'C:\claude\utils\font\nanum-gothic'

COMMENTS = [   # (위치, 한국어) — 3편 21장(1편 14장 + 0x4D4A8 부터 7장), 실패 5장은 1편과 같은 그림
    (0x5820, '자네에게 3호기를 맡긴 건 옳은 판단이었던 것 같군. 믿고 있겠다.'),
    (0xBD88, '그럭저럭 해내는 것 같군. 하지만 3호기의 능력은 이 정도가 아니다.'),
    (0xEAA8, '왠지 예전보다 실력이 떨어진 것 아닌가? 정신 차려 주게.'),
    (0x117C8, '그 상황을 타개하다니 그야말로 신기로군. 자네라면 이 작전을 안심하고 맡길 수 있다.'),
    (0x144E8, '잘 살아 돌아와 주었다. 하지만 승부는 지금부터다, 단단히 부탁한다.'),
    (0x17208, '일단 생환을 축하한다. 하지만 실력을 더 올리지 않으면 앞으로는 힘들 거다.'),
    (0x19F28, '드디어 적의 본거지다. 여기까지 온 이상 자네와 블루의 힘을 믿을 뿐이다.'),
    (0x1CC48, '드디어 적의 본거지다. 자네의 조종 기술이 진짜인지 보여 주게.'),
    (0x1F968, '지금 자네 실력으로는 3호기를 잃을지도 모르겠군. 좀 더 전투에 집중해라.'),
    (0x22688, '자기 파손율 높음.|전투 속행 불능입니다.'),
    (0x253A8, '작전 행동 중 전선을 이탈.|적전 도망으로 간주합니다.'),
    (0x280C8, '적의 공격으로 방어 지점이|파괴되었습니다.'),
    (0x2ADE8, '작전 시간 초과.|임무 실패입니다.'),
    (0x2DB08, 'EXAM 시스템 가동 임계점 돌파.|전투 속행 불능.'),
    (0x4D4A8, '이제 자네는 블루의 능력을 최대한 끌어내고 있는 것 같군. 아니, 그 이상일지도.'),
    (0x501C8, '자네는 우수한 파일럿이지만 아직 블루의 성능에 너무 기대고 있다. 이대로는 놈을 쓰러뜨릴 수 없다.'),
    (0x52EE8, '블루의 성능에만 기댄 싸움으로는 살아남지 못한다. 자네의 능력을 보여 주게.'),
    (0x55C08, '잘했다. 자네의 전투 능력은 우리 상상을 훨씬 뛰어넘는다. 혹시 자네는...'),
    (0x58928, '잘했다. 자네의 활약으로 어떻게든 결판이 난 것 같군. 임무 종료다.'),
    (0x5B648, '잘했다, 임무 종료다. 하지만 자네의 능력이 정말 이 정도인가...'),
    (0x5E368, '적의 공격으로 조사대 헬기가|격추되었습니다.'),
]
TITLES = ['EXAM 탈환 작전', '추격의 서곡', '스페이스 콜로니', 'EXAM의 진실', '심판받는 자']
TITLE_BASE = 0x20            # S0_1 240×32 5장(간격 0xF20) — 6번째 MS SIMULATOR(영문)는 그대로
LABELS = ['전술득점', '피탄율', '종합전적']
LABEL_POS = [0x3280]          # 대표(같은 그림 16곳은 build 에서 전부)


def get4(d, o, w, h):
    b = np.frombuffer(d[o:o + w * h // 2], np.uint8)
    return np.stack([b >> 4, b & 15], 1).ravel().reshape(h, w).copy()


def put4(d, o, px):
    f = px.ravel().astype(np.uint8)
    d[o:o + len(f) // 2] = ((f[0::2] << 4) | f[1::2]).tobytes()


def cover(lines, font, size, w, h, align='left', x0=0, y0=0, lh=None, shear=0.0, center_block=True):
    """흰 글자 덮임(0‥1) — lines 를 (x0,y0) 부터 lh 간격, 블록 가로 가운데"""
    F = ImageFont.truetype(os.path.join(NG, font), size)
    big = Image.new('L', (w * 4, h * 4), 0); d = ImageDraw.Draw(big)
    F4 = ImageFont.truetype(os.path.join(NG, font), size * 4)
    lh = lh or size + 6
    widths = [d.textlength(t, font=F4) for t in lines]; bw = max(widths)
    bx = (w * 4 - bw) / 2 if center_block else x0 * 4
    for i, t in enumerate(lines):
        x = bx + ((bw - widths[i]) / 2 if align == 'center' else 0)
        d.text((x, (y0 + i * lh) * 4), t, font=F4, fill=255)
    if shear:
        big = big.transform(big.size, Image.AFFINE, (1, shear, -shear * big.size[1] / 2, 0, 1, 0), Image.BICUBIC)
    return np.asarray(big.resize((w, h), Image.LANCZOS), np.float32) / 255


def wrap(text, font, size, maxw):
    F = ImageFont.truetype(os.path.join(NG, font), size); d = ImageDraw.Draw(Image.new('L', (1, 1)))
    out = []
    for part in text.split('|'):
        cur = ''
        for wd in part.split(' '):
            t = (cur + ' ' + wd).strip()
            if d.textlength(t, font=F) <= maxw: cur = t
            else: out.append(cur); cur = wd
        out.append(cur)
    return out


def ink(px, cov, box):
    """box(x0,y0,x1,y1) 안을 배경 15 로 지우고 덮임만큼 흰색"""
    x0, y0, x1, y1 = box
    px[y0:y1, x0:x1] = 15
    idx = np.clip(np.round(15 - 15 * cov), 0, 15).astype(np.uint8)
    m = cov > 0.03
    sub = px[y0:y1, x0:x1]; sub[m[y0:y1, x0:x1]] = idx[y0:y1, x0:x1][m[y0:y1, x0:x1]]
    return px


def comment(px, text):
    lines = wrap(text, 'NanumGothicBold.ttf', 16, 272)
    assert len(lines) <= 3, (text, lines)
    lh = 23; top = (80 - (lh * (len(lines) - 1) + 18)) // 2 - 1
    cov = cover(lines, 'NanumGothicBold.ttf', 16, 288, 80, y0=top, lh=lh)
    return ink(px, cov, (4, 4, 284, 76)), lines


def title(px, text):
    cov = cover([text], 'NanumGothicExtraBold.ttf', 24, 240, 32, align='center', y0=2, shear=0.18)
    return ink(px, cov, (0, 0, 240, 32))


ROWS = [(7, 24), (30, 47), (54, 71)]   # 원본 글자 줄 8‥22·31‥45·55‥69(구분선 26·49·74 는 안 건드림)


def label(px):
    for (y0, y1), t in zip(ROWS, LABELS):
        cov = cover([t], 'NanumGothicBold.ttf', 15, 240, 80, x0=14, y0=y0, center_block=False)
        px = ink(px, cov, (12, y0, 82, y1))
    for (y0, y1), t in zip(ROWS, ('점', None, '점')):
        if not t: continue
        cov = cover([t], 'NanumGothicBold.ttf', 15, 240, 80, x0=204, y0=y0, center_block=False)
        px = ink(px, cov, (200, y0, 224, y1))
    return px


def unit(px):
    """40×80 = «評価» 칸(위 글자만) → 평가"""
    cov = cover(['평가'], 'NanumGothicBold.ttf', 15, 40, 80, align='center', y0=7)
    return ink(px, cov, (3, 5, 37, 25))


RANKS = [(0x8540, '소위'), (0x8BA0, '중위'), (0x9200, '대위'), (0x61088, '소령')]   # ★2026-10-10 하스피 «우하단 계급 그림문자» — 40×80(위 계급장·아래 글자 50‥61행)


def rank(px, text):
    """계급 칸 아래 글자(行 48‥63)만 지우고 밝은 획(1·4·7) + 오른쪽 아래 그림자(14)로 다시 씀 — 계급장은 그대로"""
    cov = cover([text], 'NanumGothicBold.ttf', 12, 40, 80, align='center', y0=49)
    px[48:64, 1:39] = 0
    sub = px[48:64, 1:39]; c = cov[48:64, 1:39]
    core = c > 0.55; mid = (c > 0.3) & ~core; edge = (c > 0.1) & ~core & ~mid
    sh = np.zeros_like(core); sh[1:, 1:] = (core | mid)[:-1, :-1]
    sub[sh & ~(core | mid | edge)] = 14
    sub[edge] = 10; sub[mid] = 7; sub[core] = 1
    return px


def same_spots(d, o, w, h):
    """같은 그림이 있는 모든 위치(첫 줄 + 가운데 줄이 같은 곳)"""
    img = d[o:o + w * h // 2]; out = []; i = d.find(img)
    while i >= 0: out.append(i); i = d.find(img, i + 1)
    return out


def patch_sc1(sc1):
    d = bytearray(sc1); log = []
    for o, t in COMMENTS:
        px, lines = comment(get4(d, o, 288, 80), t); put4(d, o, px); log.append((hex(o), lines))
    lab = get4(sc1, 0x3280, 240, 80); new = label(lab.copy())
    spots = same_spots(sc1, 0x3280, 240, 80)
    for o in spots: put4(d, o, new)
    for o, t in RANKS:
        put4(d, o, rank(get4(d, o, 40, 80), t))
    un = get4(sc1, 0x20, 40, 80); nu = unit(un.copy())
    uspots = same_spots(sc1, 0x20, 40, 80)
    for o in uspots: put4(d, o, nu)
    return bytes(d), log, len(spots), len(uspots)


def patch_s01(s01):
    d = bytearray(s01)
    for n, t in enumerate(TITLES):
        o = TITLE_BASE + n * 0xF20; put4(d, o, title(get4(d, o, 240, 32), t))
    return bytes(d)


def preview():
    import disc
    sc1 = disc.read('/SC_1.BIN'); s01 = disc.read('/S0_1.BIN')
    n1, log, ns, nu = patch_sc1(sc1); n0 = patch_s01(s01)
    gray = lambda a: (255 - a.astype(np.int32) * 17).astype(np.uint8)
    os.makedirs(os.path.join(ROOT, 'work', 'gfx'), exist_ok=True)
    rows = []
    for o, _ in COMMENTS:
        rows += [np.hstack([gray(get4(sc1, o, 288, 80)), np.full((80, 6), 128, np.uint8), gray(get4(n1, o, 288, 80))]), np.full((6, 582), 128, np.uint8)]
    Image.fromarray(np.vstack(rows)).resize((582 * 2, len(rows) // 2 * 86 * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'gfx', 'comments.png'))
    rows = []
    for n in range(5):
        o = TITLE_BASE + n * 0xF20
        rows += [np.hstack([gray(get4(s01, o, 240, 32)), np.full((32, 6), 128, np.uint8), gray(get4(n0, o, 240, 32))]), np.full((6, 486), 128, np.uint8)]
    rows += [np.hstack([gray(get4(sc1, 0x3280, 240, 80)), np.full((80, 6), 128, np.uint8), gray(get4(n1, 0x3280, 240, 80))])]
    rows += [np.full((6, 486), 128, np.uint8), np.hstack([gray(get4(sc1, 0x20, 40, 80)), np.full((80, 6), 128, np.uint8), gray(get4(n1, 0x20, 40, 80)), np.full((80, 400), 128, np.uint8)])]
    a = np.vstack(rows); Image.fromarray(a).resize((a.shape[1] * 2, a.shape[0] * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'gfx', 'titles_labels.png'))
    for l in log: print(l)
    print('항목 이름 그림 %d곳 · 단위 열 %d곳' % (ns, nu))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    preview()
