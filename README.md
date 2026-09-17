# 视觉模型识图陷阱 · Vision Recognition Traps

> 用视觉模型识图前先读——问法诱导、文字自动纠错、发色色准、角色点名、场景归属脑补……19 条实测陷阱与对策。
> **与工具无关**：判据换任何视觉模型都成立（GPT-4V / Gemini / Qwen-VL / 本地模型都行）。

## 这是什么

一份踩出来的识图避坑手册。心法只有三句：

- **重心永远在画面层**——先答「这是什么」，再谈其余；文件层（EXIF／块结构／尾拼／LSB）图有蹊跷时才动
- **模型输出是「它认为的」，不是图上事实**——文字、颜色、身份、数量与视角全部实测翻车过
- **「两张图是不是同一张」不靠描述判**——只认硬字段（尺寸／时间戳／md5／dhash）

19 条陷阱每条都是真事：问法诱导让模型交出「严重崩坏」的假瑕疵、手写体被按语境补全（`Kasutaria` vs 官方 `Castalia`）、一行平台图标读出三个互斥答案、AI 生图「总觉得哪里不对劲」其实是部件之间没有物理接触、图片源站已删却对着占位图下结论……

除陷阱之外还有三块独立工具链：**界面截图/表格的真 OCR**（小字一律以 OCR 为准，视觉模型读小字必错）、**AI 生图的物理体检**（按部件要接触／投影／遮挡的事实）、**两图差分定位**（水印／改图取证）。

## 怎么装

```bash
git clone https://github.com/feverZHONG/liya-vision-recognition-traps.git ~/.hermes/skills/vision-recognition-traps
```

只当资料读也行 —— `SKILL.md` 是索引，正文在 `references/`。

## 路径与工具前提（先看这条）

文中出现的 `/opt/data` 是**作者环境的仓库根**，读者按自己的路径替换。

文中出现的 `mmx` / `ds-vision` / `vprompt` 是作者环境的视觉入口——**判据部分与工具无关**，把自己的调用替换进去即可：

| 作者环境用的 | 你换成 |
|:---|:---|
| `mmx vision describe <图>` | 任何视觉模型 CLI / API |
| `bin/ds-vision <图> "<问题>"` | 同上（作者用它做 gif 直读、批量扫图、成本敏感场景） |
| `vision_analyze(image_url=…, region=[…])` | 支持**区域裁切放大**的调用（裁切复核是文字类小字/水印的专属手段） |
| `bin/vprompt`（提示词库） | 你自己的提示词集合 |

## 目录

| 路径 | 内容 |
|:---|:---|
| `SKILL.md` | 总入口：选入口／三条心法／19 条陷阱速查／通用对策速记／场景索引 |
| `references/traps-detail.md` | 陷阱 1-9 的完整案例与判读细节 |
| `references/entrypoints.md` | 视觉入口细节、收图与验原图、批量识图的提示词体系 |
| `references/ui-ocr-workflow.md` | 界面截图／表格的**真 OCR** 通道（rapidocr，带坐标框） |
| `references/ai-image-physics-check.md` | AI 生图质检：接触／投影／遮挡三件事 |
| `references/general-countermeasures.md` | 通用对策全文：环境坑、多模型交叉验证、方言字判据、长截图分段 |
| `references/multi-source-arbitration.md` | 几方读数打架时的终审流程 |
| `references/image-diff-forensics.md` | 两图差分定位（水印／改图取证） |
| `references/deepseek-vision-api.md` | 某家视觉 API 的参数与价格实录（可当格式参考） |
| `templates/objective-describe.md` | 「先答这是什么」的客观描述问法模板 |
| `scripts/vtrap.py` | 统一入口：`vtrap ocr <图>` ／ `vtrap diff A.jpg B.jpg` |
| `scripts/ui_ocr.py` | 真 OCR（依赖 `rapidocr_onnxruntime`） |
| `scripts/imgdiff.py` | 两图差分（依赖 `numpy` / `Pillow` / `scipy`） |

## 工具依赖与用法

```bash
pip install rapidocr_onnxruntime        # ui_ocr.py：真 OCR
pip install numpy pillow scipy          # imgdiff.py：两图差分
```

统一入口会自动挑解释器：优先 `$VTRAP_PYTHON`，其次技能仓库根的 `.venv`，都没有就用当前 python。

```bash
python3 scripts/vtrap.py ocr shot.png --json /tmp/blocks.json
python3 scripts/vtrap.py ocr shot.png --crop 495,300,700,420 --scale 6 --read
python3 scripts/vtrap.py diff 有水印.jpg 无水印.jpg
```

两个子命令也可以直接单跑 `scripts/ui_ocr.py` / `scripts/imgdiff.py`，参数原样透传。

## 提思路 / 提修正

这个仓库最想要的不是「更漂亮的对策」，是**别处踩出来的新陷阱**——哪张图、什么问法、模型答了什么、实际是什么。

- 开 [Issue](https://github.com/feverZHONG/liya-vision-recognition-traps/issues)，说清场景就行
- 想直接改 → Fork + PR

## 姊妹仓库


- [liya-chat-game-referee](https://github.com/feverZHONG/liya-chat-game-referee) · [liya-spy-game](https://github.com/feverZHONG/liya-spy-game) · [liya-sea-turtle-soup](https://github.com/feverZHONG/liya-sea-turtle-soup) —— 聊天里能玩的三件（回合制裁判引擎 / 谁是卧底 / 海龟汤）
- [liya-subtraction-skill](https://github.com/feverZHONG/liya-subtraction-skill) —— 技能库做减法的方法论
- [liya-persona-authoring](https://github.com/feverZHONG/liya-persona-authoring) —— 人格／身份文件的写法与减法
- [liya-sillytavern-cards](https://github.com/feverZHONG/liya-sillytavern-cards) —— 酒馆（SillyTavern）角色卡：写法、格式规格、三个 Python 工具

## 许可

MIT —— 拿去用、改、再发，保留版权声明即可。

---

*莉娅（[@feverZHONG](https://github.com/feverZHONG)）· 宇宙美好记录官*
