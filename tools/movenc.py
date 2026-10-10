# -*- coding: utf-8 -*-
r"""(버닝 레인저 tools/movenc.py 에서 2026-10-10) 자막 덮은 프레임만 cinepak 으로 다시 굽고 FILM 을 다시 묶는다.
  건담 외전 MV_OPD·MV_PRV = 160×120 · 띠 1개 · 30fps · ★프레임 전부 키 프레임(구간 = 프레임 1장)
  → 바뀐 프레임을 한꺼번에(-g 1, 전부 키) 굽고, 원래 프레임 바이트를 넘은 것만 global_quality 를 올려 다시 — 프레임마다 원래 크기 이하.
  소리 조각·나머지 프레임은 원본 그대로, 항목 순서도 그대로. (tools/moviesub.py 가 부름)
"""
import glob, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import filmcpk

FF = r'C:\claude\utils\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe'
STRIPS = 1
TMP = os.path.join(ROOT, 'work', 'movie', 'sub', '_enc')
LADDER = (0, 1000, 2000, 4000, 7000, 12000, 20000, 35000, 60000, 100000, 200000, 400000, 800000)


def encode(frames, q):
    if os.path.isdir(TMP):
        for f in glob.glob(os.path.join(TMP, '*')):
            os.remove(f)
    os.makedirs(TMP, exist_ok=True)
    for i, p in enumerate(frames):
        shutil.copyfile(p, os.path.join(TMP, 'g%05d.png' % (i + 1)))
    avi = os.path.join(TMP, 'o.avi')
    subprocess.run([FF, '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(TMP, 'g%05d.png'),
                    '-c:v', 'cinepak', '-min_strips', str(STRIPS), '-max_strips', str(STRIPS), '-max_extra_cb_iterations', '4',
                    '-g', '1'] + (['-global_quality', str(q)] if q else []) + [avi], check=True)
    pk = filmcpk.avi_packets(open(avi, 'rb').read())
    assert len(pk) == len(frames), (len(pk), len(frames))
    return [filmcpk.to_saturn(p, True) for p in pk]


def reencode(src, fr, kr, out, room, log=print):
    film = filmcpk.read(open(src, 'rb').read())
    vid = [i for i, e in enumerate(film['stab']) if e[2] != 0xFFFFFFFF]
    assert all(not film['stab'][i][2] & 0x80000000 for i in vid), '키 아닌 프레임이 있음 — 구간 굽기(버닝 레인저 판)로'
    todo = sorted(int(os.path.basename(p)[1:5]) - 1 for p in glob.glob(os.path.join(kr, 'f*.png')))
    chunks = list(film['chunks'])
    stat = {}
    for q in LADDER:
        if not todo:
            break
        new = encode([os.path.join(kr, 'f%04d.png' % (f + 1)) for f in todo], q)
        left = []
        for f, c in zip(todo, new):
            if len(c) <= len(film['chunks'][vid[f]]) or q == LADDER[-1]:
                assert len(c) <= len(film['chunks'][vid[f]]), ('가장 높은 gq 로도 넘침', f + 1, len(c))
                chunks[vid[f]] = c; stat[q] = stat.get(q, 0) + 1
            else:
                left.append(f)
        todo = left
    assert all(len(c) % 4 == 0 for c in chunks), '4 바이트 정렬 아님'
    data = filmcpk.write(film, chunks, [e[2] for e in film['stab']])
    assert len(data) <= room, ('자리 초과', len(data), room)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'wb').write(data)
    log('다시 구운 프레임 %d (gq별 %s) · %s %d B (원본 %d)' % (sum(stat.values()), stat, out, len(data), os.path.getsize(src)))
    return len(data)
