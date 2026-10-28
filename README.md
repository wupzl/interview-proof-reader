# 面试官的审判

七章小说式技术面试阅读，以及七组本地训练。米白卷宗风格，手机与桌面均可阅读。

- [在线阅读](https://wupzl.github.io/interview-proof-reader/)
- [面试训练](https://wupzl.github.io/interview-proof-reader/practice.html)
- [Markdown 全书导航](chapters/00-全书导航.md)
- [学习书架](https://wupzl.github.io/)

当前七章正文，第八章只有预告，保持连载状态。

## 阅读与练习

章内目录、上下章、全文搜索、三种背景、字号调整、进度恢复与书签。七组训练涵盖项目真实性、连续追问、指标论证、九十秒介绍、反问清单、优势证据和压力面试，共二十个训练情境。

项目素材参考 Agent Runtime 与 RAG 检索项目，涉及 Provider 流式事件适配、JSONL Memory、上下文压缩、MCP 延迟加载、Heading Path 分块、pgvector、元数据排序与检索评测。简历原件及身份、联系信息不收录。

训练提供填写、情境独立保存、自查与参考思路、计时、比例变化计算、Markdown 导出与 JSON 备份。AI 点评按钮只复制提示词，没有模型请求或后端。记录保存在当前浏览器，不跨设备同步。自查结果不代表自动评分。

## 维护与构建

```sh
python -m pip install -r requirements.txt
python build.py
python -m http.server 4188 --directory docs --bind 127.0.0.1
```

网站位于 `docs/`，GitHub Pages 使用 `main` 分支的 `/docs`。所有运行时资源均为本地静态文件，没有 CDN 或在线字体依赖。

`source/interviewdescription.md` 保存原稿；`chapters/01.md` 至 `07.md` 为编辑后的正文，日常维护应直接修改它们。`assets/` 为样式、行为和训练题库。`book.json` 保存章节信息。`EDITORIAL.md` 说明编辑方式、素材边界与关键技术依据。

`scripts/prepare_content.py` 仅用于从已归档原稿重新生成初始编辑版本，会覆盖章节和元数据；日常改文后只运行 `build.py`。准备脚本不会覆盖已归档原稿。

## 验证

```sh
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python verify.py
```

验证包括原稿校验、七章完整性、公开材料的个人信息检查、链接与锚点，以及 390/768/1440px 浏览器布局。功能检查覆盖二十个情境的保存恢复、搜索、主题、字号、进度、书签、计时、自查、导出、剪贴板及存储不可用的降级提示。截图输出到忽略的 `test-results/`。

各页保留学习书架与八项目切换入口。`scripts/integrate_bookshelf.py` 同步相邻阅读项目的菜单、生成器、书架首页与持续检查配置。它只修改可识别的导航位置，重复运行不会新增重复菜单项。
