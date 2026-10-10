# -*- coding: utf-8 -*-
"""자막 훅 검산(2026-10-10 PoC): 스트림 구조 흉내 → 쪽 고르기·16비트 그림·명령 칸·END 점프·꺼짐"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.append(r'C:\claude\project\burningrangers-kr-patch\tools')
import glyphpack as G
import hook as H, subs, sh2sim as S, disc


def mem(blob):
    m = S.Mem(); m.add(0x06000000, 0x100000); m.add(0x00200000, 0x100000); m.add(0x05C00000, 0x80000); m.add(0x05F00000, 0x1000); m.add(0x05F80000, 0x200); m.w16(H.PRISB_SH, 0x0505)
    m._f(H.RES)[0][H.RES - 0x00200000:H.RES - 0x00200000 + len(blob)] = blob
    return m


def ref_tex(lines):
    w8, nrow, chars = G.layout(lines); px = G.reference(w8, nrow, chars)
    return w8, nrow, b''.join({0: b'\0\0', 1: struct.pack('>H', H.PIX - 1), 15: struct.pack('>H', H.PIX)}[int(v)] for v in px.ravel())


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sb, info = subs.blob(H.TAB)
    _, s1, lab = H.build(disc.read('/S0_0.BIN'), disc.read('/S0_1.BIN'), sb)
    blob = s1[H.RES - 0x00200000:]; res = blob[:H.DATA - H.RES]
    ok = True
    for v in ('V53', 'V29'):
        pages = subs.pages_for(subs.load()[v]); k = int(v[1:]) - 6
        for pi in (0, len(pages) - 1):
            t0, t1, lines = pages[pi]; t = int(round(t0 * 60)) + 2
            for listlen in (0, 3):
                m = mem(blob)
                for q in range(listlen): m.w16(H.LIST + 32 * q, 0x0000); m.w16(H.LIST + 32 * q + 8, 0x1234)
                m.w16(H.LIST + 32 * listlen, 0x8000); m.w16(H.LIST + 32 * listlen + 32, 0x4321)
                m.w32(H.STREAM + 0x0C, 3); m.w32(H.STREAM + 4, k); m.w32(H.STREAM + 0x18, (t + H.LEAD) * H.BPF + 1)
                S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None})
                X = H.LIST + 32 * listlen; O = H.OWN
                w8, nrow, tex = ref_tex(lines)
                cmd = [m.r16(O + 2 * i) for i in range(8)]
                want = [0, 0, 0xA8, 0, H.TEXA, w8 << 8 | nrow * 8, (-w8 * 4) & 0xFFFF, (112 - nrow * 8 - (max(0, 4 - nrow) * 4)) & 0xFFFF]
                got = bytes(m.r8(H.TEX + i) for i in range(len(tex)))
                c0 = m.r16(H.CRAM_BK) == 0 and m.r16(H.CRAM_BK + 2) == 0x7FFF and m.r16(H.PRISB_SH) == 0x0705 and m.r16(H.PRISB) == 0x0705
                c = (cmd == want and c0, m.r16(X) == 0x5000 and m.r16(X + 2) == H.OWNL, m.r16(O + 32) == 0x8000,
                     m.r16(X + 32) == 0x4321, got == tex)
                m.w32(H.STREAM + 0x0C, 5)
                S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None}); keep = m.r16(X) == 0x5000          # 한 프레임 «없음»은 유지
                for _ in range(H.OFFN): S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None})
                c += (keep and m.r16(X) == 0x8000,)
                print('%s 쪽%d 게임명령%d: 명령 %s · 점프 %s · 우리END %s · 다음칸 그대로 %s · 그림 %s · 끝나면 END %s  %s' % ((v, pi, listlen) + c + (lines,)))
                if not c[0]: print('   ', [hex(x) for x in cmd], [hex(x) for x in want])
                ok &= all(c)
    # 링크로 이어진 명령표: 0번 → 5번(점프 지정), 1번 = 가짜 END → 진짜 END(5번)에만 점프
    v = 'V53'; pages = subs.pages_for(subs.load()[v]); t = int(round(pages[0][0] * 60)) + 2
    m = mem(blob); m.w16(H.LIST, 0x1000); m.w16(H.LIST + 2, 5 * 32 // 8); m.w16(H.LIST + 32, 0x8000); m.w16(H.LIST + 5 * 32, 0x8000)
    m.w32(H.STREAM + 0x0C, 3); m.w32(H.STREAM + 4, int(v[1:]) - 6); m.w32(H.STREAM + 0x18, (t + H.LEAD) * H.BPF + 1)
    S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None})
    hit = m.r16(H.LIST + 5 * 32) == 0x5000 and m.r16(H.LIST + 32) == 0x8000
    m.w16(H.LIST + 5 * 32, 0x8000); S.run(m, lab['dmae'], calls={H.DMAE: lambda r, mm: None})     # DMA 가 지운 뒤 DMA 끝 → 다시 넣음
    hit2 = m.r16(H.LIST + 5 * 32) == 0x5000
    print('링크 따라 진짜 END 에 점프 %s · DMA 끝에 다시 넣기 %s' % (hit, hit2)); ok &= hit and hit2
    m.w16(H.PRISB, 0x0505); m.w16(H.PRISB_SH, 0x0505); S.run(m, lab['vin'], calls={H.VIN: lambda r, mm: None})   # 레지스터 DMA 가 5 로 되돌린 뒤
    hit3 = m.r16(H.PRISB) == 0x0705; print('VBlank-IN 뒤 S3=7 다시 %s' % hit3); ok &= hit3
    hit4 = m.r16(H.TPL) == 0x5000 and m.r16(H.TPL + 2) == H.OWNL
    m.w32(H.STREAM + 0x0C, 5)
    for _ in range(H.OFFN + 1): S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None})
    hit4 &= m.r16(H.TPL) == 0x8000; print('견본: 켜지면 점프·꺼지면 END %s' % hit4); ok &= hit4
    # 표에 없는 스트림 = 자막 없음
    m = mem(blob); m.w16(H.LIST, 0x8000); m.w32(H.STREAM + 0x0C, 3); m.w32(H.STREAM + 4, 2); m.w32(H.STREAM + 0x18, 100 * H.BPF)   # V08 = 자막 없음
    S.run(m, lab['vbi'], calls={H.VBI: lambda r, mm: None}); hit = m.r16(H.LIST) == 0x8000
    print('표에 없는 스트림 = 자막 없음', hit); ok &= hit
    print('코드 %d B · 상주 끝 %s(한계 %s)' % (len(res), hex(H.TAB + len(sb)), hex(H.END)))
    print('결과', '통과' if ok else '실패')


if __name__ == '__main__':
    main()
