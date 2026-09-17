#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ui_ocr —— 界面截图/密集表格文字的「真 OCR」通道（rapidocr_onnxruntime）

用途：阁下说「OCR 读图」「把字读准」，或图是软件界面/表格/参数面板/文档截图时——
用真 OCR 引擎拿**带坐标**的文字块，而不是让视觉模型「描述」。

为什么：视觉模型读小字会错（实测 avatar_1001_01_full_hx → _fx、
"Mip map bias: 0" → "0 iseq dew dn"），而且它自报的文字位置不可靠。

用法:
  ui_ocr.py <图片...>                        # 单张/多张：全图 OCR → 按行聚合输出（带 y 坐标）
  ui_ocr.py <图片> --json out.json          # 同时落盘原始块（坐标+置信度）
  ui_ocr.py <图片> --crop x1,y1,x2,y2 --scale 6        # 只裁块放大存盘（再喂 ds-vision 也行）
  ui_ocr.py <图片> --crop x1,y1,x2,y2 --scale 6 --read # 裁块放大后直接复跑 OCR
  ui_ocr.py --dir <目录> --write <输出目录>   # **成批扒页**：每张一个 .txt（带 y 坐标文本行）+ _INDEX.txt 汇总
                                             # 书页/文档照片成批转录走这条——阁下只拍照，不用手打

标准流程:
  1) ui_ocr.py shot.png                # 拿坐标，看文字块落在哪些 x/y 区间
  2) 按坐标裁块放大 3~8 倍 → --read     # 复核可疑行 / 被整图读错的行
  3) 视觉模型（bin/ds-vision --desc）只用来答「这是什么」；小字一律以 OCR 为准
  * 成批场景：ui_ocr.py --dir ~/image_cache --write out/ —— 同一行里多个并排块用 ' || ' 分隔
    （跨页左右栏会落在同一 y，靠这个分隔符拆）

坑:
  * 别用固定网格硬裁——会切掉整块文字（实测：预览面板参数在 x≈495-614，
    按 x=620 起裁 → 参数区全丢，连读三轮「无文字」）。先 OCR 定位，再按坐标裁。
  * 放大 3~8 倍有效；单字裁 + 过度放大反而幻觉，裁块要带上下文（整行）。
  * rapidocr 也会漏块（实测漏掉 Name 列一行）→ 与视觉模型交叉核对，两边都跑。
"""
import argparse
import json
import sys
from pathlib import Path


def load_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        sys.exit("缺 rapidocr_onnxruntime——用装了它的解释器跑本脚本"
                 "（作者环境是技能仓库根的 .venv；统一入口 `vtrap ocr` 会自动挑）")
    return RapidOCR()


def ocr(engine, path):
    """返回 [{x,y,x2,y2,t,s}]，左上角坐标，按 y 再 x 排序。"""
    res, _ = engine(str(path))
    out = []
    for box, txt, score in (res or []):
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        out.append({
            "x": int(min(xs)), "y": int(min(ys)),
            "x2": int(max(xs)), "y2": int(max(ys)),
            "t": txt, "s": round(float(score), 2),
        })
    out.sort(key=lambda r: (r["y"], r["x"]))
    return out


def group_lines(blocks, tol=8):
    """按中心 y 聚类成行（界面上同一行的多个文字块合成一行）。"""
    lines, cur, last = [], [], None
    for r in blocks:
        cy = (r["y"] + r["y2"]) / 2
        if last is None or abs(cy - last) <= tol:
            cur.append(r)
            last = cy if last is None else (last + cy) / 2
        else:
            lines.append(cur)
            cur, last = [r], cy
    if cur:
        lines.append(cur)
    for L in lines:
        L.sort(key=lambda r: r["x"])
    return lines


def crop_and_scale(src, box, scale, out_path):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    x1, y1, x2, y2 = box
    c = im.crop((x1, y1, x2, y2))
    w, h = c.size
    c = c.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    c.save(out_path)
    return out_path


def print_lines(lines):
    for L in lines:
        y = min(r["y"] for r in L)
        print(f"y={y:>4} | " + " || ".join(f'{r["t"]}({r["s"]})' for r in L))


def write_pages(engine, paths, outdir):
    """成批扒页：每张一个 .txt（带 y 坐标的文本行）+ _INDEX.txt 汇总。"""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    index = []
    for i, p in enumerate(paths, 1):
        blocks = ocr(engine, p)
        lines = group_lines(blocks)
        txt = "\n".join(
            f'y={min(r["y"] for r in L):>4} | ' + " || ".join(r["t"] for r in L)
            for L in lines)
        dst = outdir / (p.stem + ".txt")
        dst.write_text(txt + "\n", encoding="utf-8")
        head = lines[0][0]["t"] if lines else "-"
        index.append(f"{p.name}\t行数={len(lines)}\t首行={head}\t-> {dst.name}")
        print(f"[{i}/{len(paths)}] {p.name} 行={len(lines)} -> {dst.name}", file=sys.stderr)
    (outdir / "_INDEX.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"汇总: {outdir / '_INDEX.txt'}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="界面/书页真 OCR（rapidocr，带坐标）")
    ap.add_argument("image", nargs="*", help="一张或多张图片")
    ap.add_argument("--dir", help="批量：目录下的图片（jpg/jpeg/png/webp/bmp）")
    ap.add_argument("--write", help="批量输出目录：每张一个 .txt + _INDEX.txt")
    ap.add_argument("--json", help="原始块（含坐标/置信度）落盘路径（单张时用）")
    ap.add_argument("--crop", help="只裁块：x1,y1,x2,y2")
    ap.add_argument("--scale", type=float, default=4.0, help="裁块放大倍率（默认 4，小字用 6~8）")
    ap.add_argument("--out", help="裁块输出路径（默认 /tmp/ui_ocr_crop.png）")
    ap.add_argument("--read", action="store_true", help="裁块放大后直接复跑 OCR")
    args = ap.parse_args()

    paths = [Path(p) for p in args.image]
    if args.dir:
        d = Path(args.dir)
        if not d.is_dir():
            sys.exit(f"不是目录: {d}")
        found = sorted(f for f in d.iterdir()
                       if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".bmp"))
        paths += [f for f in found if f not in paths]
    if not paths:
        sys.exit("用法：ui_ocr.py <图片...> 或 ui_ocr.py --dir <目录> [--write <输出目录>]")
    for p in paths:
        if not p.exists():
            sys.exit(f"找不到图片: {p}")
    src = paths[0]

    if args.crop:
        try:
            box = tuple(int(v) for v in args.crop.split(","))
            assert len(box) == 4
        except Exception:
            sys.exit("--crop 格式：x1,y1,x2,y2")
        out = args.out or "/tmp/ui_ocr_crop.png"
        crop_and_scale(src, box, args.scale, out)
        print(f"裁块已存: {out}（scale={args.scale}）", file=sys.stderr)
        if not args.read:
            print(out)
            return
        blocks = ocr(load_engine(), out)
        print_lines(group_lines(blocks))
        print(f"N={len(blocks)}", file=sys.stderr)
        return

    if args.write:
        write_pages(load_engine(), paths, args.write)
        return

    engine = load_engine()
    for p in paths:
        blocks = ocr(engine, p)
        if args.json and len(paths) == 1:
            json.dump(blocks, open(args.json, "w"), ensure_ascii=False, indent=1)
            print(f"原始块已存: {args.json}", file=sys.stderr)
        print(f"# {p.name}  块数={len(blocks)}  行数={len(group_lines(blocks))}", file=sys.stderr)
        print_lines(group_lines(blocks))


if __name__ == "__main__":
    main()
