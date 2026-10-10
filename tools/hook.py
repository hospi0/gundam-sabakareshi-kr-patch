# -*- coding: utf-8 -*-
r"""건담 외전 III 음성 자막 훅(2026-10-10, 1편 tools/hook.py 에서 — 주소는 port.py, 표 NT 칸, 글꼴 한 벌 공유) — 다이노 hook.py(VDP1 스프라이트판) 를 옮김.
  · 자리: 하위 워크 RAM RES = 0x00244800(S0_1.BIN 을 0x44800 까지 0 으로 채우고 뒤에 붙임 → S0_1 적재 0x00200000 에 같이 실림).
          S0_0 시작 코드가 S0_1 을 먼저 불러온 뒤(0x06020102) 화면 초기화(0x06031B74 → 0x06044B38)에서 VBI 를 등록하므로 등록 때 이미 있음.
  · VBI: S0_0 의 VBlank-OUT 등록 리터럴 0x06044BE8(원래 0x060449D6) → 우리 감싸개(원래 처리기 먼저 부르고 sub). ★IN 이 아니라 OUT — 명령표 DMA(IN) 뒤·다음 프레임 그리기(IN 의 프레임 전환) 전.
  · 시계: 스트림 구조 0x06014220(1.BIN 상주) — +0x0C 상태 3 = 재생 중 · +0x04 스트림 번호 · +0x18 소리 칩에 넘긴 바이트(0x2000 단위).
          t(1/60초) = 넘긴 바이트 ÷ 1470(스테레오) − LEAD + 바뀐 뒤 센 프레임(최대 STEP). 표 RES+TAB[번호] → 묶음(없으면 자막 없음).
  · 그림: 1비트 버퍼에 찍기(버닝 레인저 stamp) → 16비트 RGB 선형 그림(0 투명 · 0x8000 검정 테두리 · 0xFFFF 흰 글자)을 VDP1 VRAM 0x70800
          (0x70400‥0x7FF00 = 스테이트 14장 모두 채움 0x8000 그대로 = 안 씀 · 0x7FF00 은 게임이 씀).
  · 명령: 보통 스프라이트(종류 0) PMOD 0x00A8(RGB·끝 코드 끔) · 좌표는 게임 지역 좌표(160,112) 기준 → XA = −w8·4, YA = 104 − nrow·8.
          매 VBI 뒤 명령표(0x25C00000)를 END 까지 훑어 그 칸만 «건너뛰고 점프(0x5000) → 우리 칸 0x7F000(명령+END)». 꺼지면 END 로.
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sh2asm import A
import port

mov = lambda m, n: 0x6003 | n << 8 | m << 4
ldb = lambda m, n: 0x6000 | n << 8 | m << 4
ldbp = lambda m, n: 0x6004 | n << 8 | m << 4
stb = lambda m, n: 0x2000 | n << 8 | m << 4
ldb0 = lambda m, d: 0x8400 | m << 4 | d
stb0 = lambda n, d: 0x8000 | n << 4 | d
exb = lambda m, n: 0x600C | n << 8 | m << 4
exw = lambda m, n: 0x600D | n << 8 | m << 4
OR = lambda m, n: 0x200B | n << 8 | m << 4
AND = lambda m, n: 0x2009 | n << 8 | m << 4
ADD = lambda m, n: 0x300C | n << 8 | m << 4
addi = lambda n, i: 0x7000 | n << 8 | (i & 0xFF)
movi = lambda n, i: 0xE000 | n << 8 | (i & 0xFF)
shll = lambda n: 0x4000 | n << 8; shlr = lambda n: 0x4001 | n << 8
shll2 = lambda n: 0x4008 | n << 8; shlr2 = lambda n: 0x4009 | n << 8
shll8 = lambda n: 0x4018 | n << 8; shlr8 = lambda n: 0x4019 | n << 8
shll16 = lambda n: 0x4028 | n << 8; shlr16 = lambda n: 0x4029 | n << 8
dt = lambda n: 0x4010 | n << 8
push = lambda m: 0x2F06 | m << 4; pop = lambda n: 0x60F6 | n << 8

RES = port.RES                       # 코드(★2·3편: port.py — S0_1 끝 뒤)
DATA = RES + 0x800                   # 변수·명령
BUF = RES + 0x900; BSTR = 52         # 1비트 쪽 버퍼 52 B × 34행
TAB = RES + 0x1000                   # 스트림 번호 → 묶음 표 + 묶음들(subs.blob)
END = port.END                       # 가장 이른 Sn_1 적재 — 넘으면 안 됨
VBI = port.VBI; VBI_LIT = port.VBI_LIT           # ★VBlank-OUT(2026-10-10 PoC 1차 VBlank-IN 은 안 보임: IN 처리기가 명령표를 SCU DMA 로 보내고 PTMR=2 라 프레임 전환 때 바로 그림 → IN 뒤에 넣으면 늦고 다음 DMA 에 지워짐)
STREAM = port.STREAM
NT = port.NT                         # 스트림 표 칸 수(1편 32 → 2·3편 64·72)
VIN = port.VIN; VIN_LIT = port.VIN_LIT          # VBlank-IN — 처리기 안에서 VDP2 레지스터를 RAM 사본에서 DMA(동기) → 끝난 뒤 S3=7 다시(★반짝임 2: 본체가 사본을 5 로 되돌리는 프레임)
DMAE = port.DMAE; DMAE_LIT = port.DMAE_LIT
# ★반짝임 근본(2026-10-10 PoC 5차): SGL 이 VBlank-IN 에 SCU 간접 DMA 표(0x060C0000/0x060F0000 두 벌)로 명령표를 보내는데 마지막 항목 =
#   «END 견본»(원래 S0_0 리터럴 풀의 0x8000 @0x0604845A) 30 B → 명령표 끝 칸. VDP1 그리기와 경쟁해 우리 점프가 프레임마다 있다 없다 함.
#   → 그 원본 리터럴(0x06048474 = 0x8604845A, 비트 31 = 표 끝)을 우리 견본 TPL 로: 평소 END, 자막 켜지면 «건너뛰고 점프 → 우리 칸».
#   TPL = S0_0 안 0x0603BAC0‥0x0603BD40(파일 0·스테이트 16장 모두 0·가리키는 리터럴 없음) — SCU DMA 가 읽으려면 상위 RAM 이어야 함.
TPL = port.TPL; TPL_LIT = port.TPL_LIT; TPL_OLD = port.TPL_OLD       # SCU 2단계 DMA 끝(벡터 0x49) — 명령표 DMA 가 끝나면 깃발만 세움
TEX = 0x25C70800; TEXA = (TEX & 0x7FFFF) // 8
LIST = 0x25C00000
OWN = 0x25C7F000; OWNL = (OWN & 0x7FFFF) // 8
# ★우선순위(2026-10-10 PoC 2차 안 보임): 조종석 계기판·컷신 띠 = NBG0 우선순위 7, 스프라이트 PRISA‥D 모두 5 → 자막이 밑에 깔림.
#   게임 스프라이트는 RGB 화소(S0)만 씀(스테이트 14장, 팔레트 우선순위 번호 1‥3 안 씀) → 자막은 팔레트 화소 «우선순위 번호 3»(종류 3: 비트 14‥13)으로,
#   S3(PRISB 위 바이트)를 7 로 — SGL 이 VBlank-IN 에 RAM 사본 0x060FFCC0 을 VDP2 레지스터로 DMA 하므로 사본과 레지스터 둘 다 씀. 같은 7 이면 스프라이트가 위.
PIX = 0x6000 | 0x7FD                 # 흰 글자 = CRAM 0x7FD · 테두리 = PIX−1 = CRAM 0x7FC(CRAOFB 스프라이트 0, 스테이트 모두 빈 칸)
#   ★0x7FE 금지 = «보통 그림자» 코드(2026-10-10 PoC 3차 테두리가 반투명으로 나옴)
CRAM_BK = 0x25F00000 + 0x7FC * 2
PRISB = 0x25F800F2; PRISB_SH = 0x060FFCC0 + 0xF2
BPF = 1470; LEAD = 12; STEP = 6; OFFN = 6   # ★스테레오 22,050 Hz 16비트 = 88,200 B/초 = 프레임당 1,470 B(2026-10-10, 예전 735 = 모노로 잘못 앎 — 받아쓰기 시각도 두 배였어서 우연히 맞았음) · 앞섬·덩이 프레임도 절반


def data_part():
    data = bytearray(); lab = {}
    def put(name, b):
        nonlocal data
        data += bytes(-len(data) % 4); lab[name] = DATA + len(data); data += b
    put('cur', bytes(4)); put('offc', bytes(4)); put('lcd', bytes(4)); put('cnt', bytes(4)); put('pay', bytes(4))
    put('cmd', struct.pack('>16H', 0x0000, 0, 0x00A8, 0, TEXA, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    assert DATA + len(data) <= BUF
    return bytes(data), lab


def assemble():
    data, dlab = data_part()
    a = A(RES); a.lab.update(dlab); W = a.w
    # ---- VBI 감싸개 ----
    a.L('vbi'); W(0x4F22); a.ld(0, VBI); W(0x400B, 0x0009)
    W(0x4F02, 0x4F12)                                                  # MACH·MACL 보존(시계에 dmulu)
    a.br('bsr', 'sub'); W(0x0009)
    W(0x4F16, 0x4F06, 0x4F26, 0x000B, 0x0009)
    # ---- sub ----
    a.L('sub'); W(0x4F22)
    a.ld(1, STREAM); W(0x5013, 0x8803); a.br('bf', 'none')            # 상태 +0x0C == 3(재생 중)
    W(0x5011, movi(2, NT), 0x3022); a.br('bt', 'none')                 # 번호 >= NT(부호 없는 비교) 면 없음
    W(shll2(0)); a.ld(2, TAB); W(0x042E, 0x2448); a.br('bt', 'none')   # r4 = 표[번호]
    a.ld(2, 'pay'); W(0x2242)
    W(0x5316, 0x2338); a.br('bt', 'none')                             # r3 = 넘긴 바이트(+0x18)
    a.ld(1, 'lcd'); W(0x6012, 0x3030); a.br('bt', 'samecd')
    W(0x2132); a.ld(1, 'cnt'); W(movi(0, 0), 0x2102); a.br('bra', 'calc'); W(0x0009)
    a.L('samecd'); a.ld(1, 'cnt'); W(0x6012, movi(2, STEP), 0x3022); a.br('bt', 'calc')
    W(addi(0, 1), 0x2102)
    a.L('calc'); a.ld(2, (1 << 32) // BPF + 1); W(0x3325, 0x030A)   # mach = 바이트 × (2^32/BPF) 의 위 32비트 = 실제 프레임
    a.ld(1, 'cnt'); W(0x6012, ADD(0, 3), addi(3, -LEAD))
    W(0x8542, exw(0, 6)); W(mov(4, 1), addi(1, 16))                    # r6 = 쪽 수, r1 = 쪽 표
    W(0x2668); a.br('bt', 'none')
    a.L('lp'); W(0x6015, exw(0, 0), 0x3303); a.br('bf', 'nx')
    W(0x6011, exw(0, 0), 0x3037); a.br('bf', 'nx')
    W(0x8511, exw(0, 5), ADD(4, 5)); a.ld(1, 'offc'); W(movi(0, 0), 0x2102); a.br('bra', 'have'); W(0x0009)
    a.L('nx'); W(addi(1, 6), dt(6)); a.br('bf', 'lp')
    # ★«없음»이 OFFN 프레임 연달아야 끔(2026-10-10 PoC 6차 반짝임 — 명령표·견본은 정상, 상태값이 프레임마다 흔들리는 것으로 의심)
    a.L('none'); a.ld(1, 'offc'); W(0x6012, addi(0, 1), 0x2102, movi(2, OFFN), 0x3023); a.br('bt', 'nz')
    a.ld(1, 'cur'); W(0x6512); a.br('bra', 'have'); W(0x0009)
    a.L('nz'); W(movi(5, 0))
    a.L('have'); a.ld(1, 'cur'); W(0x6012, 0x3050); a.br('bt', 'same')
    W(0x2152, 0x2558); a.br('bt', 'off')
    a.br('bsr', 'draw'); W(mov(5, 1))
    a.L('on')
    a.ld(1, CRAM_BK); a.ld(0, 0x00007FFF); W(0x2102)                  # 0x7FC 검정 · 0x7FD 흰색
    a.ld(1, PRISB_SH); W(0x6011, 0xC9FF)                               # r0 = 사본 PRISB 아래 바이트(S2)
    W(movi(2, 7), shll8(2), OR(2, 0), 0x2101); a.ld(1, PRISB); W(0x2101)   # S3 = 7(사본·레지스터)
    a.br('bsr', 'ins'); W(0x0009)
    a.br('bra', 'ret'); W(0x0009)
    a.L('same'); W(0x2558); a.br('bf', 'on')
    a.L('off'); a.br('bsr', 'unins'); W(0x0009)
    a.L('ret'); W(0x4F26, 0x000B, 0x0009)
    # ---- walk: VDP1 이 읽는 순서대로(다음 칸·점프·건너뛰기) 따라가 END 또는 우리 점프 칸 → r1(못 찾으면 0). r0‥r3 만 씀 ----
    #   ★명령표가 링크로 이어짐(2026-10-10 컷신 스테이트: 앞 300칸 안에 END 없음) → 칸 순서로 훑으면 엉뚱한 END 를 잡음
    a.L('walk'); a.ld(1, LIST); a.ld(3, 2048)
    a.L('wl'); W(0x6011, exw(0, 0)); a.ld(2, 0x8000); W(0x3022); a.br('bt', 'wret')          # END(비트 15)
    a.ld(2, 0x5000); W(0x3020); a.br('bf', 'wjp')
    W(0x8511, exw(0, 0)); a.ld(2, OWNL); W(0x3020); a.br('bt', 'wret')                       # 우리 점프
    W(0x6011, exw(0, 0))
    a.L('wjp'); W(shlr8(0), shlr2(0), shlr2(0), 0xC903, 0x8801); a.br('bf', 'wnx')           # 점프 지정(1·5 → 아래 3비트 1)
    W(0x8511, exw(0, 0), shll2(0), shll(0)); a.ld(2, LIST); W(ADD(2, 0), mov(0, 1)); a.br('bra', 'wdt'); W(0x0009)
    a.L('wnx'); W(addi(1, 32))
    a.L('wdt'); W(dt(3)); a.br('bf', 'wl')
    W(movi(1, 0))
    a.L('wret'); W(0x000B, 0x0009)
    # ---- ins: 찾은 칸을 «건너뛰고 점프 → 우리 칸» + 우리 칸(명령·END) ----
    a.L('ins'); W(0x4F22)
    a.ld(1, TPL); a.ld(0, 0x5000); W(0x2101); a.ld(0, OWNL); W(0x8111)   # 견본 = 우리 점프(다음 DMA 부터 게임이 써 넣음)
    a.br('bsr', 'walk'); W(0x0009)
    W(0x2118); a.br('bt', 'iret')
    a.ld(0, 0x5000); W(0x2101); a.ld(0, OWNL); W(0x8111)
    a.ld(1, OWN); a.ld(2, 'cmd'); W(movi(3, 8))
    a.L('ic'); W(0x6026, 0x2102, addi(1, 4), dt(3)); a.br('bf', 'ic')
    a.ld(0, 0x8000); W(0x2101)
    a.L('iret'); W(0x4F26, 0x000B, 0x0009)
    # ---- unins: 우리 점프 칸을 END 로 ----
    a.L('unins'); W(0x4F22)
    a.ld(1, TPL); a.ld(0, 0x8000); W(0x2101); W(movi(0, 0), 0x8111)      # 견본 = END
    a.br('bsr', 'walk'); W(0x0009)
    W(0x2118); a.br('bt', 'uret')
    W(0x6011, exw(0, 0)); a.ld(2, 0x5000); W(0x3020); a.br('bf', 'uret')
    a.ld(0, 0x8000); W(0x2101)
    a.L('uret'); W(0x4F26, 0x000B, 0x0009)
    # ---- VBlank-IN 감싸개: 원래 처리(레지스터 DMA) 뒤 자막이 켜져 있으면 PRISB = 사본 아래 바이트 | S3 7 ----
    a.L('vin'); W(0x4F22); a.ld(0, VIN); W(0x400B, 0x0009)
    a.ld(1, 'cur'); W(0x6012, 0x2008); a.br('bt', 'vret')
    a.ld(1, PRISB_SH); W(0x6011, 0xC9FF, movi(2, 7), shll8(2), OR(2, 0)); a.ld(1, PRISB); W(0x2101)
    a.L('vret'); W(0x4F26, 0x000B, 0x0009)
    # ---- DMA 끝(0x49) 감싸개: 원래 처리 뒤 자막이 켜져 있으면 점프 다시 넣기(★반짝임 — 명령표 DMA 직후·그리기 전에) ----
    a.L('dmae'); W(0x4F22); a.ld(0, DMAE); W(0x400B, 0x0009)
    a.ld(1, 'cur'); W(0x6012, 0x2008); a.br('bt', 'dret')
    a.br('bsr', 'ins'); W(0x0009)
    a.L('dret'); W(0x4F26, 0x000B, 0x0009)
    # ---- draw(r1 = 쪽) ----
    a.L('draw')
    W(0x4F22, push(1)); W(*[push(r) for r in range(8, 15)])
    W(0x58F7)
    a.ld(2, BUF); a.ld(3, BSTR * 34 // 4); W(movi(0, 0))
    a.L('cb'); W(0x2202, addi(2, 4), dt(3)); a.br('bf', 'cb')
    a.ld(9, 'pay'); W(0x6992)                                          # r9 = 지금 묶음
    W(0x8596, exw(0, 0), ADD(0, 9))
    W(ldb0(8, 3), exb(0, 10), mov(8, 11), addi(11, 4))
    W(0x2AA8); a.br('bt', 'chd')
    a.L('ch')
    W(ldbp(11, 0), exb(0, 1), shll(1), mov(1, 12), shll2(12), shll(12), ADD(1, 12), ADD(9, 12))
    W(ldbp(11, 0), exb(0, 13))
    W(ldbp(11, 0), exb(0, 0), mov(0, 2), mov(0, 1), shlr2(1))          # ★2·3편: 글자 번호 위 6비트(셋째 바이트 비트 2‥7) — 글꼴 한 벌 공유
    a.ld(3, 256 * 18); W(0x213E, 0x011A, ADD(1, 12))                   # mulu.w r3,r1 · sts macl,r1 · r12 += (번호>>8)·4608
    W(0xC901, shll8(0), OR(0, 13), addi(13, 8), shlr(2), mov(2, 0), 0xC901, mov(0, 2))
    W(shll2(2), shll2(2), addi(2, 4), movi(3, BSTR), 0x0237, 0x021A)
    a.ld(3, BUF); W(ADD(3, 2), mov(13, 0), shlr2(0), shlr(0), ADD(0, 2))
    W(mov(13, 0), 0xC907, mov(0, 14), movi(3, 6))
    a.L('gp')
    W(ldbp(12, 4), exb(4, 4), ldbp(12, 5), exb(5, 5), ldbp(12, 6), exb(6, 6))
    W(mov(4, 0), shll2(0), shll2(0), mov(5, 1), shlr2(1), shlr2(1))
    a.br('bsr', 'stamp'); W(OR(1, 0))
    W(mov(5, 0), 0xC90F, shll8(0))
    a.br('bsr', 'stamp'); W(OR(6, 0))
    W(dt(3)); a.br('bf', 'gp')
    W(dt(10)); a.br('bf', 'ch')
    a.L('chd')
    # 16비트 선형(팔레트 화소, 우선순위 번호 3): 행 y(nrow*8) × 열 cx(w8) × 8 화소
    W(ldb0(8, 1), exb(0, 9), shll2(9), shll(9))
    a.ld(10, BUF); W(addi(10, BSTR)); a.ld(11, TEX); a.ld(12, PIX)
    a.L('ry'); W(ldb0(8, 0), exb(0, 13), mov(10, 14))
    a.L('rx'); W(mov(14, 2))
    W(mov(2, 4), addi(4, -BSTR), mov(2, 5), addi(5, BSTR))
    W(ldb(4, 0), ldb(2, 1), OR(1, 0), ldb(5, 1), OR(1, 0), exb(0, 6), shll8(6))
    W(ldb0(4, 1), mov(0, 1), ldb0(2, 1), OR(0, 1), ldb0(5, 1), OR(1, 0), exb(0, 0), OR(0, 6), shll8(6))
    W(ldb0(4, 2), mov(0, 1), ldb0(2, 2), OR(0, 1), ldb0(5, 2), OR(1, 0), exb(0, 0), OR(0, 6))
    W(mov(6, 1), shlr8(1), mov(6, 0), shll(0), shlr8(0), OR(0, 1), mov(6, 0), shlr(0), shlr8(0), OR(0, 1))
    W(ldb0(2, 1), exb(0, 7), 0x6077, AND(0, 1), exb(1, 1))
    W(movi(3, 8))
    a.L('eb'); W(mov(7, 0), 0xC880); a.br('bt', 'e1')
    W(mov(12, 0)); a.br('bra', 'es'); W(0x0009)                        # 흰 글자 PIX
    a.L('e1'); W(mov(1, 0), 0xC880); a.br('bt', 'e0')
    W(mov(12, 0)); a.br('bra', 'es'); W(addi(0, -1))                   # 검정 테두리 PIX−1
    a.L('e0'); W(movi(0, 0))
    a.L('es'); W(0x2B01, addi(11, 2), shll(7), shll(1), dt(3)); a.br('bf', 'eb')
    W(addi(14, 1), dt(13)); a.br('bf', 'rx')
    W(movi(0, BSTR), ADD(0, 10), dt(9)); a.br('bf', 'ry')
    W(*[pop(r) for r in range(14, 7, -1)]); W(pop(1))
    # 명령 칸: SIZE · XA YA (지역 좌표 (160,112) 기준, 아래 가운데, 바닥 8px 여유)
    W(ldb0(1, 0), exb(0, 7), ldb0(1, 1), exb(0, 5))                   # r7 = w8 · r5 = nrow
    a.ld(2, 'cmd')
    W(mov(7, 0), shll8(0), mov(5, 6), shll2(6), shll(6), OR(6, 0), 0x8125)          # SIZE = w8<<8 | nrow*8
    W(mov(7, 0), shll2(0), 0x600B, 0x8126)                                           # XA = −w8*4
    # YA(지역 좌표 y 112 기준) = 112 − nrow*8 − (nrow<4 이면 (4−nrow)*4) → 컷신 아래 띠(화면 y 192‥224, 32 px): 두 줄은 꽉, 한 줄은 가운데
    #   ★2026-10-10 하스피 «자막이 좀 위» — 예전 바닥 8 px 띄움은 두 줄 윗줄이 영상에 걸침
    W(mov(5, 0), shll2(0), shll(0), movi(6, 112), 0x3608, movi(0, 4), 0x3057); a.br('bf', 'ya')
    W(0x3058, shll2(0), 0x3608)
    a.L('ya'); W(mov(6, 0), 0x8127)
    W(0x4F26, 0x000B, 0x0009)
    # ---- stamp ----
    a.L('stamp')
    W(shll8(0), shll2(0), shll2(0), mov(14, 1), 0x2118); a.br('bt', 'sd')
    a.L('sl'); W(shlr(0), dt(1)); a.br('bf', 'sl')
    a.L('sd'); W(mov(0, 7), shlr16(0), ldb(2, 1), OR(1, 0), stb(0, 2))
    W(mov(7, 1), shlr8(1), ldb0(2, 1), OR(1, 0), stb0(2, 1))
    W(ldb0(2, 2), OR(7, 0), stb0(2, 2), 0x000B, addi(2, BSTR))
    code = a.build(); assert len(code) <= DATA - RES, len(code)
    return code + bytes(DATA - RES - len(code)) + data, a.lab


def build(s0_0, s0_1, sub_blob):
    """→ (새 S0_0, 새 S0_1, 라벨)"""
    res, lab = assemble()
    s0 = bytearray(s0_0)
    assert struct.unpack_from('>I', s0, VBI_LIT - 0x06020000)[0] == VBI
    struct.pack_into('>I', s0, VBI_LIT - 0x06020000, lab['vbi'])
    assert struct.unpack_from('>I', s0, TPL_LIT - 0x06020000)[0] == TPL_OLD
    struct.pack_into('>I', s0, TPL_LIT - 0x06020000, 0x80000000 | TPL)
    o = TPL - 0x06020000; assert s0[o - 0x140:o + 0x140] == bytes(0x280)
    s0[o:o + 2] = bytes([0x80, 0])                                          # 견본 처음 = END
    assert struct.unpack_from('>I', s0, VIN_LIT - 0x06020000)[0] == VIN
    struct.pack_into('>I', s0, VIN_LIT - 0x06020000, lab['vin'])
    assert struct.unpack_from('>I', s0, DMAE_LIT - 0x06020000)[0] == DMAE
    struct.pack_into('>I', s0, DMAE_LIT - 0x06020000, lab['dmae'])
    pad = RES - 0x00200000
    assert len(s0_1) <= pad, (len(s0_1), pad)
    blob = res + bytes(TAB - RES - len(res)) + sub_blob
    assert RES + len(blob) <= END, ('상주 자료가 0x250000 을 넘음', hex(RES + len(blob)))
    return bytes(s0), s0_1 + bytes(pad - len(s0_1)) + blob, lab
