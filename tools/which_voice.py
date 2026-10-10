# -*- coding: utf-8 -*-
r"""스테이트의 사운드 RAM(u16 뒤집힘) 고리 버퍼 → SS_SND 몇 번 덩어리·어디쯤 재생 중인지(2026-10-10)
  python tools/which_voice.py <스테이트…>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r'C:\claude\project\df2-kr-patch\tools')
import rzip, dump_state as ds, snd


def sram(p):
    raw = open(p, 'rb').read(); snap = rzip.unpack(p)[0] if raw[:5] == b'#RZIP' else raw
    for i, nm, off, sz in ds.find_vars(snap):
        if nm == 'RAM' and sz == 524288:
            r = snap[off:off + sz]; return bytes(b for k in range(0, len(r), 2) for b in (r[k + 1], r[k]))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    d = open(snd.PATH, 'rb').read(); tb = snd.table(d)
    for p in sys.argv[1:]:
        s = sram(p); hits = {}
        for off in range(0, 0x20000, 0x800):
            pr = s[off:off + 32]
            if len(set(pr)) < 8: continue
            i = d.find(pr)
            if i < 0: continue
            for k in snd.VOICES:
                o, z = tb[k]
                if o <= i < o + z: hits.setdefault(k, []).append((i - o) / 44100)
        print(os.path.basename(p), {'V%02d' % k: '%.0f~%.0f초' % (min(v), max(v)) for k, v in hits.items()} or '음성 없음')


if __name__ == '__main__':
    main()
