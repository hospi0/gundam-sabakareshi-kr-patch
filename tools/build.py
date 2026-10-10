# -*- coding: utf-8 -*-
r"""건담 외전 III 빌드(2026-10-10, 1편 tools/build.py 에서) — 음성 자막 훅 + 자막 자료.
  ① S0_0.BIN: VBI 등록 리터럴 → 우리 감싸개(hook.build)
  ② S0_1.BIN: port.RES 까지 0 채움 + 훅 코드 + 자막 표·묶음(subs.blob) → 하위 RAM port.RES 에 상주
  ④ 동영상 MV_OPD·MV_PRV: work/kr/*.BIN(먼저 python tools/moviesub.py) — 원본 크기 그대로 제자리
  ③ 디스크: iso.patch(트랙 01 크기 그대로, 늘어난 S0_1 은 뒤 빈 자리로) → work/out/
  python tools/build.py [--write]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import disc, hook, iso, subs, scgfx, menugfx, svgfx, apsp

MOVIES = ('MV_OPD', 'MV_EDA', 'MV_EDB', 'MV_EDC', 'MV_EDD', 'MV_EDE')          # 동영상 자막(먼저 tools/moviesub.py)
OUT = os.path.join(ROOT, 'work', 'out', 'Mobile Suit Gundam Side Story III - Sabakareshi Mono (Japan) (Track 01).bin')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sb, info = subs.blob(hook.TAB)
    s01 = scgfx.patch_s01(disc.read('/S0_1.BIN'))                     # 시나리오 제목 5장(크기 그대로) — 훅 붙이기 전에
    s0, s1, lab = hook.build(disc.read('/S0_0.BIN'), s01, sb)
    sc1, glog, ns, nu = scgfx.patch_sc1(disc.read('/SC_1.BIN'))        # 결과 화면 한마디 14·항목 이름·평가(제자리)
    assert len(sc1) == len(disc.read('/SC_1.BIN'))
    print('① 자막 묶음 %d개 · 쪽 기록 %d B · 글꼴 %s · 상주 끝 %s(한계 %s)' % (len([k for k in info if k.startswith('V')]), info['쪽 기록'], info['글꼴'], hex(hook.TAB + len(sb)), hex(hook.END)))
    print('② S0_1 %d B(원래 %d) · S0_0 VBI → %s' % (len(s1), len(disc.read('/S0_1.BIN')), hex(lab['vbi'])))
    print('③ 그림: 제목 5 · 한마디 %d · 항목 이름 %d곳 · 평가 %d곳' % (len(glog), ns, nu))
    if '--write' in sys.argv:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        files = {'/S0_0.BIN': s0, '/S0_1.BIN': s1, '/SC_1.BIN': sc1}
        files['/3.BIN'] = menugfx.patch(scgfx.patch_3bin(disc.read('/3.BIN')))   # 타이틀 로고 부제 + STAGE SELECT 글 그림(크기 그대로)
        files['/SV_1.BIN'] = svgfx.patch(disc.read('/SV_1.BIN'))       # MS VIEWER 띠 «형식번호»·«개»(크기 그대로)
        for k in range(1, apsp.NFILE + 1):                            # 막간 화면 글 그림(tools/apsp.py, 크기 그대로)
            files['/AP_SP%d.BIN' % k] = apsp.patch('AP_SP%d' % k, disc.read('/AP_SP%d.BIN' % k))
        for mv in MOVIES:                                             # 동영상 자막(tools/moviesub.py 가 구운 것, 원본 크기 그대로 → 제자리)
            p = os.path.join(ROOT, 'work', 'kr', mv + '.BIN')
            d = open(p, 'rb').read()
            assert len(d) == len(disc.read('/%s.BIN' % mv)), ('동영상 크기 다름', mv)
            files['/%s.BIN' % mv] = d
        iso.patch(OUT, files)


if __name__ == '__main__':
    main()
