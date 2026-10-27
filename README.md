# 玄光 × Starlia

个人作品集：同一份源码生成 **PDF** 和 **网页**（电脑是书页，手机自动重排）。
线上地址：https://xuanguang.starlia.ai ·  PDF：https://xuanguang.starlia.ai/Starlia_XuanGuang.pdf

## 改文字

只改 **`content.yaml`**：标题、正文、目录、联系方式、各板块网址都在里面，文件顶部有写法提示。
在 GitHub 网页上点开文件 → 铅笔图标编辑 → Commit changes。约 3 分钟后 GitHub Actions 自动重新生成网页和 PDF 并发布。
进度在仓库的 **Actions** 标签页里看；绿色勾即发布完成。

## 换照片

把新照片放进 `img/`，在 `content.yaml` 对应页改 `image:`（名字对应 `build_outline.py` 顶部 `IMG` 表）。
立花照片用竖幅原图，不要裁；方图页（水晶、Lumilab、器物）用正方形。

## 本地生成（可选）

```bash
pip install -r requirements.txt && python -m playwright install chromium
# 需要系统装有 Noto Serif CJK（含 ExtraLight / Light 字重）：Ubuntu 为 fonts-noto-cjk fonts-noto-cjk-extra
python build.py            # → out/Starlia_final.pdf 和 web/
```

## 文件

| 文件 | 作用 |
|---|---|
| `content.yaml` | 全书文字（日常只改这个） |
| `img/` | 原始照片 + logo |
| `build_outline.py` | 排版：页面结构、竖排规则、照片边缘（毛边 / 颗粒 / 渐变 / 墨晕）、中英文对齐 |
| `make_pdf.py` | 用 Chromium 把书页输出为矢量 PDF（链接保留） |
| `build_web.py` | 生成网页：书页版 + 手机重排版，字体子集，CNAME |
| `build.py` | 一键跑完以上三步 |
| `base.css` | 基础样式 |
| `.github/workflows/publish.yml` | push 后自动构建并发布到 `gh-pages` 分支 |

版式规则（横版 16:10、全书竖排、照片不裁、边缘处理等）都写在代码注释里；改版式请改 `build_outline.py`。
