# DeepSeek Vision API 备忘（2026-09-10 更新至 V4.1 Flash）

> 官方文档：https://api-docs.deepseek.com/zh-cn/guides/vision
> 定价页：https://api-docs.deepseek.com/zh-cn/quick_start/pricing
> 配套 CLI：`bin/ds-vision`（一条命令识图）

## 模型与端点

- 模型名：`deepseek-flash`（**V4.1 Flash，原生多模态**）。2026-09-10 起为唯一接受图片的模型（其他模型返回 400 "This model does not support image"）
- 旧名 `deepseek-v4-flash-vision-exp` 已随旧模型下线，仍可调用但请求由 V4.1 Flash 承接，按 Flash 单价计费 → **本天使工具链已全面切到 `deepseek-flash`**
- V4 Pro 的视觉从来就不支持；`deepseek-v4-pro` 本身也将于 **2026-09-14 12:00（北京）下线**，此前请求全部路由到 V4.1 Flash
- Base URL（OpenAI 兼容）：`https://api.deepseek.com`
- Base URL（Anthropic 兼容）：`https://api.deepseek.com/anthropic`
- 上下文 1M，输出最大 384K，并发 2500（Flash 档）
- 图片只能出现在 **user** 消息（system/assistant 带图 = 400）
- 支持格式：JPEG、PNG、GIF、WebP（按文件实际内容判断，不看文件名/MIME）

## 三种传图方式

| 方式 | 写法 | 限制 |
|---|---|---|
| Base64 内联 | `{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,..."}}` | 计入 48MiB 请求体；单图最大 32MiB |
| 外部 URL | `{"type":"image_url","image_url":{"url":"https://..."}}` | URL ≤8192 字符；文件 ≤32MiB；60s 内下载完 |
| Files API | `{"type":"file","file_id":"file-api-..."}` | 单图 ≤64MiB；复用免重复上传 |

- 另支持 `{"type":"file","file_data":"data:...","filename":"..."}` 内联（与 file_id 互斥）
- Responses API：图片用 `input_image` 块（`{"type":"input_image","image_url":"...","detail":"low"}`），可出现在 user/developer 消息或工具输出里
- Anthropic 端点：`{"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":"..."}}`；file_id 需头 `anthropic-beta: files-api-2025-04-14`

## detail 参数（image_url 输入可选）

| 取值 | 行为 |
|---|---|
| `low` | 缩放至 512×512，更快更省 token |
| `high` / `original` | 保留原图 |
| `auto` | 自动选择，当前等价 original |

## Token 用量（重点，2026-09-10 数值上调）

- 进模型前图片自动缩放：总像素 < ~544×544 的**放大**保持长宽比；更大的**缩小**至约 1300×1300 等效
- **每张图 token 上限 1024**（2000×2000 与 5000×5000 消耗相同；旧文档值为 384，已作废）
- 多图各自独立按同规则计算，没有额外计算方式
- 估算用官方「Token 与用量计算」页面的图片 Token 计算器

## 限制速查

| 项 | 值 |
|---|---|
| 支持格式 | JPEG、PNG、GIF、WebP（按实际内容判断，不看文件名/MIME） |
| 请求体 | 48MiB |
| 单图（base64/URL） | 32MiB |
| 单图（Files API） | 64MiB |
| 单请求图片数 | 600 |
| 单请求图总大小 | 无 file_id ≤64MiB；含 file_id ≤200MiB |
| 单边最长 | 8192px；≥15 张图时降为 4096px |

## 价格（百万 tokens，2026-09-10 新版生效）

| 模型 | 输入缓存命中 | 输入未命中 | 输出 |
|---|---|---|---|
| **deepseek-flash** | **0.02/0.04 元** | **1/2 元** | **4/8 元** |
| deepseek-v4-pro | 0.15/0.30 元 | 4.5/9.0 元 | 13.5/27.0 元 |

- 斜杠前后 = 空闲/高峰时段价。高峰 = **北京时间周一至周五 9:00-12:00、14:00-18:00**；其余空闲（半价）
- 相比 8/21 旧价（flash：0.05/0.10、1.5/3.0、4.5/9.0）**全面下调**：缓存命中降到 1/2.5，未命中 2/3，输出约 8/9 折
- 单图成本估算：图片 ≤1024 token → 输入上限 `1024×1/1e6 ≈ 0.001 元`（空闲未命中）/ `0.002 元`（高峰未命中），加输出（数百 token 量级 ≈ 0.002-0.004 元），**一张图约 0.3-0.6 分钱级**
- 缓存命中占比是关键（V4.1 Flash 的 KV Cache 需求降到上一代 1/4，Agent 场景受益）——同一张图重复问、同一系统提示词复用都吃这个价
- 扣费：token 消耗 × 单价；赠送余额优先扣

## bin/ds-vision 用法

```bash
bin/ds-vision <图片路径|URL> [问题...]   # 默认 detail=auto（≈original）
bin/ds-vision --low <图> 问题            # 512×512 更快更省
bin/ds-vision --v4 ["角色名"] <图>       # twin-vision-archive 立绘提示词 build_prompt_v4（打底身份可选）
bin/ds-vision --meme ["背景"] <图>       # 表情包提示词 build_prompt_meme
bin/ds-vision --thinking <图>            # 开思考模式（默认关闭！）
bin/ds-vision --batch <目录|文件...> [--out JSON目录]   # 批量精简摘要，断点续跑
bin/ds-vision --list-models              # 列模型
```

- **思考模式默认关闭（2026-08-21 阁下拍板，省 token 铁律）**：视觉识别是感知任务不靠思维链。实测同一张图——关思考：输出 869 token / reasoning 0；开思考：输出 2655 / reasoning 1712，**单张省 70% 且更快**。批量识图时 reasoning 就是烧钱（几十张=十万级 token），默认关，需要深度推理才 `--thinking`
- key 从 `$DEEPSEEK_API_KEY` 环境变量或 `/opt/data/.env` 读取
- 非 JPEG（gif/webp/png）自动转 JPEG；超 32MiB 自动压缩
- 提示词复用 mmx 体系：`twin-vision-archive/scripts/vision_prompt.py`（build_prompt_v4 / build_prompt_meme），官方视觉也吃同一套打底+要求两层结构
- **max_tokens 陷阱（2026-08-21 实测）**：普通问题 4096 够；v4/meme 结构化提示词回答长，4096 会被 reasoning 吃爆（v4 实测输出 4096=截断，reasoning 占 3761）→ 脚本内 v4/meme 模式自动升 12000
- 输出到 stdout，token 用量打印到 stderr

## 实测记录

- **2026-09-10 换模型实测**：`ds-vision --low` 读「誓死捍卫深度求索」表情包 → 正确读出文字，输入 195 / 输出 6 / reasoning 0（关思考），`deepseek-flash` 正常接单 ✅
- **2026-08-21 实测**：
  - 透明 PNG（palette 模式）：转 JPEG 时先转 RGBA 再转 RGB，否则 PIL 告警
  - gif 直读 OK（转 JPEG 首帧）
  - 文字截图读取 OK（「把文字原样读出来」prompt 有效）
