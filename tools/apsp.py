# -*- coding: utf-8 -*-
r"""막간 화면(AP_SP*.BIN) 글 그림 한글화(2026-10-10) — work/text/apsp_ko.tsv(파일·시작줄·줄수·들여쓰기·원문·번역)
  줄 그림 = 288×H 4비트, 파일 안 START 부터 0x1000 간격(2편 H16 @0x13D58 · 3편 H17 @0x13CD0 — VDP1 VRAM 0x10000‥ 과 바이트 대조로 확정)
  글꼴 나눔고딕 ExtraBold(한글 잉크 높이 = 원본 글자 높이) · 따옴표 뒤에선 안 끊음
  색: 0 투명 · 1 흰 글자 ‥ 12 회색(가장자리 덮임 낮을수록 큰 번호) · 13 남색 그림자(오른쪽 아래 1px) — 원본 분포 그대로
  문단 = 원래 줄 수에 «정확히» 맞춰 고르게 나눔(빈 줄 안 생기게), 부호 뒤 공백 삭제, 넘치면 글자 크기 1 줄임
  python tools/apsp.py   → work/gfx/apsp_kr.png 미리보기(원문 | 한글)
"""
import os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import scgfx

GAME = 2 if 'gundam-ao' in ROOT else 3
START, H, NFILE = {2: (0x13D58, 16, 5), 3: (0x13CD0, 17, 4)}[GAME]
W = 288; STRIDE = 0x1000
TOP = 0                      # 원본 글자 맨 윗줄
INK_H = H - 2                # 원본 글자 높이(2편 0‥14, 3편 0‥15 — 그 아래 1줄은 그림자)
X0, INDENT, XMAX = 2, 18, 284
FONT = os.path.join(scgfx.NG, 'NanumGothicExtraBold.ttf')
TSV = os.path.join(ROOT, 'work', 'text', 'apsp_ko.tsv')
PUNCT = ',.!?:;)]}\'"~、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥'
QUOTE = "\"'"               # 여는 따옴표 뒤에서 끊지 않게
SQ = re.compile('([' + re.escape(PUNCT) + '])[ 　](?![ 　])')


def load():
    out = []
    for ln in open(TSV, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip(): continue
        f, s, n, ind, ja, ko = ln.rstrip('\n').split('\t')
        out.append((f, int(s), int(n), ind == '1', ja, SQ.sub(r'\1', ko.strip())))
    return out


def font_for(size):
    return ImageFont.truetype(FONT, size)


def pick_size():
    """한글 잉크 높이가 원본 글자 높이(INK_H)에 맞는 가장 큰 크기"""
    best = 10
    for s in range(10, 24):
        b = font_for(s).getbbox('한글')
        if b[3] - b[1] <= INK_H: best = s
    return best


def tokens(t):
    """줄바꿈 자리: 공백(먹음) · 부호 뒤(안 먹음)"""
    out, cur = [], ''
    for i, c in enumerate(t):
        if c == ' ':
            if cur: out.append(cur); cur = ''
            continue
        cur += c
        if c in PUNCT and c not in QUOTE and i + 1 < len(t) and t[i + 1] not in PUNCT and t[i + 1] != ' ':
            out.append(cur + '\0'); cur = ''        # \0 = 부호 뒤 이음(공백 없이 붙음)
    if cur: out.append(cur)
    return out


def join(toks):
    s = ''
    for k, w in enumerate(toks):
        if k and not toks[k - 1].endswith('\0'): s += ' '
        s += w.rstrip('\0')
    return s


# 줄바꿈 금지·감점(하스피 2026-10-10 «기회라는 / 듯» — 꾸밈말과 의존 명사가 갈라짐)
BOUND = re.compile(r'^(듯|것|수|때|중|뿐|만큼|만한|자(?=이고|인가|이다|였다)|데|바|줄|척|채|대로|적|터|바람)'
                   r'(이고|이|은|는|을|를|이다|이었다|이었던|인가|에|에서|까지|인|이던|이었다|한|이|도|뿐이었다|이라|이니)?[.,…!?"]*$')
def AUX(l, r):
    """본용언 + 보조 용언(«발견되지 / 않아» «이루려 / 했던» «덮쳐 / 오는» «이뤄 / 낸»)"""
    return ((l.endswith('지') and r.startswith('않')) or
            (l.endswith('려') and r[:1] in '하했한할') or
            (l.endswith('고') and r[:1] in '있말') or
            (l[-1:] in '어아여쳐해워져뤄라' and r[:1] in '오와온가간갔주준줬보봤버두둔놓놔내낸있'))


MODIF = {'어느', '두', '세', '그', '이', '저', '큰', '새', '온', '각', '몇', '단', '더', '또'}
PAIRS = {('캘리포니아', '베이스'), ('님바스', '슈타젠'), ('알프', '카무라'), ('클루스트', '모제스'), ('모제스', '박사'), ('클루스트', '박사가'),
         ('루나', '투'), ('EXAM', '시스템'), ('EXAM', '연구의'), ('유우', '일행'), ('유우', '일행은'), ('유우', '일행의'),
         ('유우', '일행에게'), ('유우', '일행이'), ('푸른', '사신이'), ('푸른', '짐')}
PAIR_HEAD = ('블루', '2호기'), ('블루', '3호기')


def break_cost(tk, b):
    """tk[b-1] 뒤에서 줄을 끊는 값(클수록 나쁨)"""
    if b <= 0 or b >= len(tk): return 0
    left, right = tk[b - 1], tk[b]
    lr = left.rstrip('\0'); l = lr.rstrip(',.…'); r = right.rstrip('\0')
    if left.endswith('\0') and lr[-1:] not in ',.…!?': return 90000   # ) " 뒤 조사(«EXAM(이그잼) / 을»)
    if lr[-1:] in ',.…!?': return -1500                         # 쉼표·마침표 뒤에서 끊기 = 좋음
    if BOUND.match(r): return 60000
    if l in MODIF: return 30000
    if AUX(l, r): return 40000
    if (l, r.rstrip(',.…')) in PAIRS or any(l == a and r.startswith(h) for a, h in PAIR_HEAD): return 30000
    return 0


def wrap_exact(text, n, indent, F):
    """n 줄로 정확히 — 줄마다 남는 폭 제곱합 + 끊는 자리 값(break_cost) 최소(DP)"""
    tk = tokens(text); m = len(tk)
    lim = lambda i: XMAX - X0 - (INDENT if (i == 0 and indent) else 0)
    INF = float('inf')
    def wid(a, b): return F.getlength(join(tk[a:b]))
    best = [[INF] * (m + 1) for _ in range(n + 1)]; prev = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0
    for i in range(n):
        for a in range(m + 1):
            if best[i][a] == INF: continue
            for b in range(a + 1, m + 1):
                w = wid(a, b)
                if w > lim(i): break
                slack = lim(i) - w
                c = best[i][a] + slack ** 2 + break_cost(tk, b)
                if c < best[i + 1][b]: best[i + 1][b] = c; prev[i + 1][b] = a
    if best[n][m] == INF: return None
    lines, b = [], m
    for i in range(n, 0, -1):
        a = prev[i][b]; lines.append(join(tk[a:b])); b = a
    return lines[::-1]


def render(line, first_indent, F, size):
    S = 4
    big = Image.new('L', (W * S, (H + 2) * S), 0); d = ImageDraw.Draw(big)
    F4 = font_for(size * S)
    asc = F4.getbbox('한글')[1]
    d.text(((X0 + (INDENT if first_indent else 0)) * S, (TOP * S) - asc), line, font=F4, fill=255)
    cov = np.asarray(big.resize((W, H + 2), Image.LANCZOS), np.float32)[:H] / 255
    px = np.zeros((H, W), np.uint8)
    on = cov > 0.12
    px[on] = np.clip(np.round(1 + (0.85 - cov[on]) / 0.73 * 11), 1, 12).astype(np.uint8)
    sh = np.zeros_like(cov); sh[1:, 1:] = cov[:-1, :-1]
    px[(~on) & (sh > 0.35)] = 13
    return px


def build_rows():
    """{'AP_SP1': {줄번호: 그림}} + 보고"""
    size = pick_size(); res = {}; log = []
    for f, s, n, ind, ja, ko in load():
        for sz in range(size, size - 4, -1):
            F = font_for(sz); lines = wrap_exact(ko, n, ind, F)
            if lines: break
        assert lines, ('줄 수 안에 안 들어감', f, s, ko)
        if sz != size: log.append('%s %d: 크기 %d→%d' % (f, s, size, sz))
        for i, t in enumerate(lines):
            res.setdefault(f, {})[s + i] = render(t, ind and i == 0, F, sz)
    return res, size, log


def patch(name, data):
    rows = build_rows()[0].get(name.strip('/').split('.')[0])
    if not rows: return data
    d = bytearray(data)
    for r, px in rows.items():
        o = START + r * STRIDE
        assert any(d[o:o + W * H // 2]), ('원본 빈 줄에 쓰려 함', name, r)
        scgfx.put4(d, o, px)
    assert len(d) == len(data)
    return bytes(d)


def preview():
    import disc
    res, size, log = build_rows()
    pal = [(40, 40, 60)] + [(248 - 8 * i,) * 3 for i in range(12)] + [(0, 24, 56), (0, 0, 0), (0, 0, 0)]
    blocks = []
    for k in range(1, NFILE + 1):
        nm = 'AP_SP%d' % k; d = disc.read('/%s.BIN' % nm); r = 0
        while START + r * STRIDE + W * H // 2 <= len(d) and any(d[START + r * STRIDE:START + r * STRIDE + W * H // 2]):
            a = scgfx.get4(d, START + r * STRIDE, W, H); b = res[nm][r]
            blocks.append(np.hstack([a, np.full((H, 8), 0, np.uint8), b])); r += 1
        assert r == len(res[nm]), (nm, r, len(res[nm]))
        blocks.append(np.zeros((6, W * 2 + 8), np.uint8))
    img = np.vstack(blocks)
    rgb = np.array(pal, np.uint8)[img]
    Image.fromarray(rgb).resize((rgb.shape[1] * 2, rgb.shape[0] * 2), Image.NEAREST).save(os.path.join(ROOT, 'work', 'gfx', 'apsp_kr.png'))
    print('크기', size, '·', '; '.join(log) or '줄임 없음')


if __name__ == '__main__':
    preview()
