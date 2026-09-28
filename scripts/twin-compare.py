#!/usr/bin/env python3
"""孪生图判定：一张目标图 vs 多个候选，谁才是同一张——用像素误差说话，不用眼睛。

用法：
  python3 twin-compare.py <目标图> <候选1> <候选2> [...]
  python3 twin-compare.py shot.png 052-成品.png 031-成品.png --region 30,250,857,1720

说明：
  · 目标图若是**带 UI 的截图**，先用 --region 裁到画面区域（相册等比显示时按 9:16 估：宽 887 的屏上约 827×1470）。
  · 判据：多尺度 + 平移微搜索下的最小 MAE。**同一张 ≈20 以内；同族另一张 ≈40+**（本机实测）。
  · 只读不写，不碰原文件。
"""
import argparse
import sys

import numpy as np
from PIL import Image

TARGET = (450, 800)  # 统一比对尺寸（w, h）


def load(path, region=None):
    im = Image.open(path)
    if region:
        im = im.crop(region)
    return im.convert('RGB')


def norm(im, size=TARGET):
    return np.asarray(im.resize(size, Image.LANCZOS)).astype(np.float32)


def min_mae(base, cand):
    """对候选做缩放 + 平移微搜索，返回最小 MAE 及参数。"""
    best = None
    for scale in (0.94, 0.96, 0.98, 1.0, 1.02, 1.04, 1.06):
        tw, th = int(TARGET[0] * scale), int(TARGET[1] * scale)
        r = np.asarray(cand.resize((tw, th), Image.LANCZOS)).astype(np.float32)
        sx, sy = int(TARGET[0] * 0.05), int(TARGET[1] * 0.05)
        step = max(1, TARGET[1] // 80)
        for dy in range(-sy, sy + 1, step):
            for dx in range(-sx, sx + 1, step):
                ox, oy = (tw - TARGET[0]) // 2 + dx, (th - TARGET[1]) // 2 + dy
                if ox < 0 or oy < 0 or ox + TARGET[0] > tw or oy + TARGET[1] > th:
                    continue
                v = float(np.mean(np.abs(base - r[oy:oy + TARGET[1], ox:ox + TARGET[0]])))
                if best is None or v < best[0]:
                    best = (v, scale, dx, dy)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target', help='目标图（截图或裁好的画面）')
    ap.add_argument('candidates', nargs='+', help='候选图，2 张以上')
    ap.add_argument('--region', help='先裁目标图：x0,y0,x1,y1')
    ap.add_argument('--regions', help='多区域复核：x0,y0,x1,y1;x0,y0,x1,y1（与 --region 二选一）')
    args = ap.parse_args()

    regions = []
    if args.regions:
        regions = [tuple(int(v) for v in r.split(',')) for r in args.regions.split(';')]
    elif args.region:
        regions = [tuple(int(v) for v in args.region.split(','))]
    else:
        regions = [None]

    table = {}
    for reg in regions:
        base = norm(load(args.target, reg))
        tag = '全图' if reg is None else f'区域{reg[2]-reg[0]}x{reg[3]-reg[1]}'
        row = {}
        for p in args.candidates:
            v = min_mae(base, load(p))
            row[p] = v
        table[tag] = row
        print(f'--- {tag} ---')
        for p, v in sorted(row.items(), key=lambda kv: kv[1][0]):
            print(f'  {v[0]:7.2f}  scale={v[1]:.2f} dx={v[2]:+d} dy={v[3]:+d}  {p}')

    print('\n=== 汇总（各区域最小 MAE，越小越像）===')
    names = args.candidates
    for tag, row in table.items():
        line = '  '.join(f'{n.split("/")[-1][:24]}={row[n][0]:.1f}' for n in names)
        win = min(row, key=lambda n: row[n][0])
        print(f'{tag}: {line}  → {win.split("/")[-1]}')

    # 跨区域一致性
    if len(table) > 1:
        winners = {min(row, key=lambda n: row[n][0]) for row in table.values()}
        if len(winners) == 1:
            w = winners.pop()
            avg = np.mean([table[t][w][0] for t in table])
            print(f'\n判定：{w.split("/")[-1]}（三区域一致，平均 MAE {avg:.1f}）')
        else:
            print('\n⚠️ 各区域结论不一致——目标区域没裁准，先看行/列亮度剖面重新定位')


if __name__ == '__main__':
    sys.exit(main())
