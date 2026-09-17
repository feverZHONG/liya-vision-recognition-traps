#!/usr/bin/env python3
"""两图差分定位：两个版本差在哪一小块。

用法（要 numpy/PIL/scipy——别用没装这些的裸 python3）：
    python3 imgdiff.py A.jpg B.jpg
    python3 imgdiff.py A.jpg B.jpg --grid 64 --top 8 --thresh 25
  作者环境这两条脚本都在技能仓库根的 .venv 里跑；统一入口 `vtrap diff A.jpg B.jpg` 会自动挑解释器。

只读不写：不动任何输入文件；要裁图自己按输出的 bbox 裁。
"""
import argparse
import hashlib
import sys

from PIL import Image, ImageFilter
import numpy as np


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def brief(path):
    im = Image.open(path)
    ex = im.getexif()
    keep = {}
    for tag in ('Make', 'Model', 'DateTime', 'Software'):
        v = ex.get({'Make': 271, 'Model': 272, 'DateTime': 306, 'Software': 305}[tag])
        if v:
            keep[tag] = str(v).strip('\x00 ')
    xmp = im.info.get('xmp')
    flags = []
    if xmp:
        s = xmp.decode('utf-8', 'ignore')
        for key, label in (('MotionPhoto="1"', 'MotionPhoto'),
                           ('timewatermark', 'timewatermark-layer'),
                           ('Item:Semantic="GainMap"', 'GainMap')):
            if key in s:
                flags.append(label)
    return {'size': im.size, 'format': im.format,
            'frames': getattr(im, 'n_frames', 1),
            'xmp': ','.join(flags) or '-', 'exif': keep}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--grid', type=int, default=64, help='热点块边长，默认 64')
    ap.add_argument('--top', type=int, default=8, help='列前几块')
    ap.add_argument('--thresh', type=int, default=25,
                    help='模糊后差分的连通域阈值，默认 25；噪声大就调高')
    args = ap.parse_args()

    for p in (args.a, args.b):
        info = brief(p)
        print('%-28s %s %s frames=%s xmp[%s] exif=%s' % (
            p, info['format'], info['size'], info['frames'], info['xmp'], info['exif']))
    ma, mb = md5(args.a), md5(args.b)
    print('md5 %s / %s  %s' % (ma, mb, 'SAME FILE' if ma == mb else 'different bytes'))
    if ma == mb:
        return 0

    a = Image.open(args.a).convert('RGB')
    b = Image.open(args.b).convert('RGB').resize(a.size, Image.LANCZOS)
    na, nb = np.asarray(a).astype(np.int16), np.asarray(b).astype(np.int16)
    d = np.abs(na - nb).sum(axis=2)
    print('raw diff: mean %.2f max %d' % (d.mean(), d.max()))

    dblur = np.asarray(Image.fromarray(np.clip(d, 0, 255).astype('uint8'))
                       .filter(ImageFilter.GaussianBlur(6))).astype(np.float32)
    gs = args.grid
    gh, gw = dblur.shape[0] // gs, dblur.shape[1] // gs
    if gh and gw:
        grid = dblur[:gh * gs, :gw * gs].reshape(gh, gs, gw, gs).mean(axis=(1, 3))
        order = np.dstack(np.unravel_index(np.argsort(-grid, axis=None), grid.shape))[0][:args.top]
        print('top-%d blocks (%dpx):' % (args.top, gs))
        for by, bx in order:
            print('   y %5d-%-5d x %5d-%-5d  score %6.1f'
                  % (by * gs, (by + 1) * gs, bx * gs, (bx + 1) * gs, grid[by, bx]))

    try:
        from scipy import ndimage
    except ImportError:
        print('(scipy 不在，跳过连通域；只看热点块)')
        return 0
    lab, n = ndimage.label(dblur > args.thresh)
    if not n:
        print('no cluster above threshold %d — 差异是均匀噪声级，多半只是重编码' % args.thresh)
        return 0
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    print('clusters above %d: %d' % (args.thresh, n))
    for i in np.argsort(-sizes)[:args.top]:
        ys, xs = np.where(lab == i + 1)
        print('   size %7d  bbox y %d-%d x %d-%d  w=%d h=%d  maxdiff %d'
              % (sizes[i], ys.min(), ys.max(), xs.min(), xs.max(),
                 xs.max() - xs.min() + 1, ys.max() - ys.min() + 1, d[ys, xs].max()))
    print('判读：宽高比≈一行字、边缘锐利 = 水印/叠加文字；弥散云块 = 光照/色调映射差异')
    return 0


if __name__ == '__main__':
    sys.exit(main())
