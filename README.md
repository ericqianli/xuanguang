# 玄光 × Starlia

个人作品集，中英两版，同一套源码生成 **PDF** 和 **网页**（电脑上是书页，手机自动重排）。

| | 网页 | PDF |
|---|---|---|
| 中文 | https://xuanguang.starlia.ai | https://xuanguang.starlia.ai/Starlia_XuanGuang.pdf |
| English | https://xuanguang.starlia.ai/en/ | https://xuanguang.starlia.ai/Starlia_XuanGuang_EN.pdf |

网页右上角可切换语言；右下角下载当前语言的 PDF。

## 改文字

- 中文改 **`content.yaml`**，英文改 **`content_en.yaml`**。标题、正文、目录、联系方式、各板块网址都在里面，文件顶部有写法提示。
- 在 GitHub 网页上点开文件 → 铅笔图标编辑 → Commit changes。约 2 分钟后 GitHub Actions 自动重新生成两版网页和两份 PDF 并发布；进度在 **Actions** 标签页，绿色勾即完成。
- 两个文件各自完整；共用的内容（网址、联系方式、照片名）改的时候记得两边同步。

## 每页可调的版式参数（写在 content.yaml / content_en.yaml 各页下）

| 参数 | 作用 |
|---|---|
| `image` | 照片名（对应 `build_outline.py` 顶部 `IMG` 表）；写成列表 `[a, b]` 则上下叠放两张 |
| `side` | 照片在 `L` 左 / `R` 右 |
| `edge` | 照片与留白的衔接：`deckle` 撕边 · `deckle2:种子:种子` 两侧撕边 · `grain:宽度` 颗粒溶解 · `fade` 长渐变 · `ink:宽度` 墨晕 · `wall+ink` 墙色延展 · `bar:宽度:颜色` 实线镶边 · `near` 文字贴近照片 |
| `inset` | 照片离页边的距离（配合 `deckle2`） |
| `width` / `x` / `align: near` / `valign` | 仅英文版：栏宽、左边位置、靠近照片、垂直位置（`top` / `middle` / `bottom` 或 `0.333` 这样的比例，表示空白上下如何分） |
| 封面 `mark` / `mark_size` / `mark_color` / `mark_margin` | 名字与 STARLIA 之间的符号及其大小、颜色、上下间距 |

## 换照片

把新照片放进 `img/`，在 `build_outline.py` 顶部 `IMG` 表里起个名字，再在页面的 `image:` 里引用。立花照片用竖幅原图，不要裁；方图页（水晶、Lumilab、器物）用正方形。favicon 来自 `img/favicon_src.png`（带透明通道的 PNG）。

## 本地生成（可选）

```bash
pip install -r requirements.txt && python -m playwright install chromium
# 字体：把 fonts 分支里的三个 .otf 放到 fonts/ 目录（或系统装 Noto Serif CJK 全字重）
python build.py            # → out/Starlia_final.pdf、out/Starlia_final_EN.pdf、web/
```

## 文件

| 文件 | 作用 |
|---|---|
| `content.yaml` / `content_en.yaml` | 全书文字与每页版式参数（日常只改这两个） |
| `img/` | 原始照片、logo、favicon |
| `build_outline.py` | 中文书页：页面结构、竖排规则、照片边缘库（撕边 / 颗粒 / 渐变 / 墨晕 / 墙色 / 镶边）、中英文对齐 |
| `build_en.py` | 英文书页：同一套照片与边缘，文字横排 |
| `make_pdf.py` | 用 Chromium 把书页输出为矢量 PDF（链接保留） |
| `build_web.py` | 生成网页：两版书页 + 手机重排版、语言切换、字体子集、favicon、CNAME |
| `build.py` | 一键跑完以上全部 |
| `base.css` | 基础样式 |
| `.github/workflows/publish.yml` | push 后自动构建并发布到 `gh-pages` 分支 |
| `fonts` 分支 | Noto Serif CJK SC 三个字重，构建时取用，保证每次渲染一致 |

版式规则（横版 16:10、中文全书竖排、照片不裁、边缘处理等）都写在代码注释里；改版式请改 `build_outline.py` / `build_en.py`。
