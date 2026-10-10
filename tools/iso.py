# -*- coding: utf-8 -*-
r"""트랙 01 파일 바꿔 넣기(2026-10-10) — 트랙 크기 그대로.
  원본: 마지막 진짜 파일이 LBA 104474 에서 끝, 트랙 01 = 104,774섹터 → 뒤 300섹터가 빈 자리(1편과 같은 꼴).
        XX_CDA.X00‥X21 은 오디오 트랙 자리를 가리키는 기록 → 트랙 01 을 늘리면 안 됨(그래서 늘리지 않음).
  규칙: 새 파일이 원래 섹터 수 안이면 제자리(남는 곳 0), 넘치면 빈 자리(52472 부터)에 차례로 → 52772 넘으면 빌드 실패.
        디렉터리 기록 LBA·크기(양 엔디안), 쓴 섹터는 헤더·EDC/ECC 새로(유나 리믹스 iso.sector).
  from iso import patch; patch(dst, {'/S0_1.BIN': bytes, ...})
"""
import importlib.util, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import disc

_sp = importlib.util.spec_from_file_location('yuna_iso', r'C:\claude\project\yunaremix-kr-patch\tools\iso.py')
_y = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(_y)
sector = _y.sector
FREE = 104474; TRACK = 104774


def records(f):
    pvd = disc.sec(f, 16); out = []
    def walk(lba, size, pre):
        for k in range((size + 2047) // 2048):
            d = disc.sec(f, lba + k); i = 0
            while i < 2048 and d[i]:
                L = d[i]; nm = d[i + 33:i + 33 + d[i + 32]]
                if nm not in (b'\0', b'\1'):
                    n = nm.decode('latin1').split(';')[0]
                    l2, s2 = struct.unpack_from('<I', d, i + 2)[0], struct.unpack_from('<I', d, i + 10)[0]
                    if d[i + 25] & 2: walk(l2, s2, pre + n + '/')
                    else: out.append((pre + n, lba + k, i, l2, s2))
                i += L
    walk(struct.unpack_from('<I', pvd, 158)[0], struct.unpack_from('<I', pvd, 166)[0], '/')
    return out


def patch(dst, files, log=print):
    src = disc.BIN
    assert os.path.getsize(src) == TRACK * 2352
    f = open(src, 'rb'); recs = {r[0]: r for r in records(f)}
    assert max(l + (s + 2047) // 2048 for n, _, _, l, s in recs.values() if not n.startswith('/XX_CDA')) == FREE
    plan = {}; cur = FREE
    for name, data in files.items():
        _, dl, di, lba, size = recs[name]
        if (len(data) + 2047) // 2048 <= (size + 2047) // 2048: plan[name] = lba
        else: plan[name] = cur; cur += (len(data) + 2047) // 2048
    assert cur <= TRACK, ('트랙 01 빈 자리 넘침', cur, TRACK)
    with open(src, 'rb') as i, open(dst, 'wb') as o:
        while True:
            b = i.read(1 << 24)
            if not b: break
            o.write(b)
    with open(dst, 'r+b') as o:
        for name, data in files.items():
            lba = plan[name]; _, dl, di, olba, osize = recs[name]
            n = max((len(data) + 2047) // 2048, (osize + 2047) // 2048 if lba == olba else 0)
            for k in range(n):
                o.seek((lba + k) * 2352); o.write(sector(lba + k, data[k * 2048:(k + 1) * 2048].ljust(2048, b'\0')))
        dirs = {}
        for name, data in files.items():
            _, dl, di, _, _ = recs[name]
            if dl not in dirs:
                o.seek(dl * 2352 + 16); dirs[dl] = bytearray(o.read(2048))
            d = dirs[dl]; lba = plan[name]
            struct.pack_into('<I', d, di + 2, lba); struct.pack_into('>I', d, di + 6, lba)
            struct.pack_into('<I', d, di + 10, len(data)); struct.pack_into('>I', d, di + 14, len(data))
        for dl, d in dirs.items():
            o.seek(dl * 2352); o.write(sector(dl, bytes(d)))
    for name, data in files.items():                                 # 되읽기 검산
        assert disc.read(name, dst) == data, name
    log('트랙 01: 크기 그대로 %d섹터 · 바뀐 파일 %d · 빈 자리 %d/%d 사용' % (TRACK, len(files), cur - FREE, TRACK - FREE))
