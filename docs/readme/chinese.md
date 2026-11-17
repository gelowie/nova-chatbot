<div align="center">

![Nova banner](../img/banner.png)

<a href="../../CHANGELOG.md"><img src="../img/badges/version.svg" alt="version: 1.0"></a> <a href="../../LICENSE"><img src="../img/badges/license.svg" alt="license: MIT"></a> <a href="../../help/installing-nova.md"><img src="../img/badges/runtime.svg" alt="runtime: Python 3.10+"></a> <a href="../nova.md"><img src="../img/badges/dependencies.svg" alt="dependencies: none"></a>

</div>

# Nova — Local JSON-Powered Chatbot

> 本文是英文 [README](../../README.md) 的译文，英文版为准。译文可能滞后于英文版；发现差异请提交 issue。

一个友好、能容错拼写错误的聊天机器人，**完全在你自己的电脑上运行**。
无需云端 API、无需 API 密钥、无需第三方服务，也无需 `pip install`。

<div align="center">

[English](../../README.md) | [中文](chinese.md) | [日本語](japanese.md) | [한국어](korean.md) | [Español](spanish.md)

</div>

## 目录

- [Nova 是什么？](#nova-是什么)
- [功能特性](#功能特性)
- [局限性](#局限性)
- [快速开始](#快速开始)
- [与 Nova 对话](#与-nova-对话)
- [工作原理](#工作原理)
- [仓库结构](#仓库结构)
- [Java 实现](#java-实现)
- [测试](#测试)
- [扩展 Nova](#扩展-nova)
- [文档](#文档)
- [参与贡献](#参与贡献)
- [许可证](#许可证)

## Nova 是什么？

Nova 是一个自托管的聊天机器人，证明构建一个友好实用的助手并不需要云服务。让它运行起来的一切都在本仓库中：

- **个性**（回复、笑话、建议）是纯 JSON：[`src/json/brain.json`](../../src/json/brain.json)
- **逻辑**（路由、数学、日期）是简短的 Python：[`src/py/`](../../src/py/)
- **界面**是单个 HTML 文件：[`src/index.html`](../../src/index.html)
- 一个仅用标准库的小型**服务器**把它们连接起来：[`server.py`](../../server.py)

Nova 是一个学习项目，是构建本地助手的模板，也是私密的聊天伙伴：你的消息不会离开你的电脑。能力范围见[局限性](#局限性)。

## 功能特性

- **离线且零依赖。** 仅使用 Python 标准库。
- **精确的数学计算。** “whats 5 plus 3 times 2”、“144 divided by 12”、“15% of 200”、“2^10”、“3 squared plus 4 squared”。由受限的语法树遍历器求值，从不使用 `eval()`。
- **时间与日期。** 当前时间、今天的日期和星期、明天/昨天、下个月/上个月，以及“in 3 weeks”这类偏移（读取你电脑的时钟）。
- **JSON 大脑**，包含 62 个对话主题：问候、闲聊、情绪、建议、推荐，以及笑话（10 条）、趣闻（7 条）、名言（5 条）和谜语（4 条）。
- **容忍拼写错误和俚语。** 127 条拼写修正和 61 条短语修正，加上模糊匹配，因此 “helo”、“hru”、“wat r u doin”、“helloooo thereeee” 都能识别。
- **精致的聊天页面。** 输入中提示、快捷回复按钮、时间戳、清空按钮、响应式布局。
- **本地且私密。** 服务器只监听 `127.0.0.1`。

## 局限性

- 基于规则：没有语言模型。Nova 只做模式匹配并运行小程序。
- 没有记忆：每条消息都是独立回答的。
- 不能上网，因此没有实时数据（天气、新闻、股票），也无法读取文件或图片。
- 匹配仅支持英文（大脑会忽略其他文字和带重音的字母）。
- 内容量不大，超出范围的内容会得到兜底回复。
- 单用户、单机器。
- [Java 实现](#java-实现)只包含数学和时间技能。

## 快速开始

**环境要求：** Python 3.10 或更高版本（使用 3.12 开发和测试）以及网页浏览器。只有可选的 Java 演示才需要 JDK。

```bash
git clone https://github.com/gelowie/nova-chatbot.git
cd nova-chatbot
python server.py        # 在 macOS/Linux 上可能需要：python3 server.py
```

在浏览器中打开 <http://127.0.0.1:8000>。按 `Ctrl+C` 停止服务器。

检查服务器是否在运行：

```bash
curl http://127.0.0.1:8000/health
# {"ok":true}
```

更多细节和故障排除：[安装 Nova](../../help/installing-nova.md)。

## 与 Nova 对话

| 你输入 | Nova 使用 | 示例回复 |
|---|---|---|
| `whats 5 plus 3 times 2` | 数学技能 | Solved **5 + 3 × 2** = **11** |
| `15% of 200` | 数学技能 | Solved **(15 ÷ 100) × 200** = **30** |
| `100 / 0` | 数学技能 | I can't divide by zero — that one breaks the universe. |
| `what time is it` | 时间技能 | It's **15:03** on your system clock. |
| `what is the date in 3 weeks` | 时间技能 | That lands on **Friday, 06 November 2026** (2026-11-06). |
| `helo` / `hru` / `sup` | JSON 大脑 | 问候或“你好吗”类回复。 |
| `tell me a joke` | JSON 大脑 | 保存的笑话之一。 |
| `i feel great today` | JSON 大脑 | 一句对话式回复，而不是日期。 |
| `asdfghjkl` | 兜底回复 | 一句友好的“没听懂”并附带建议。 |

完整的提问指南和 HTTP API：[如何使用 Nova](../../help/how-to-use-nova.md)。

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "whats 5 plus 3 times 2"}'
# {"text": "Solved **5 + 3 × 2** = **11**", "skill": "math", "suggestions": [...]}
```

## 工作原理

```
Browser (src/index.html) ── POST /chat ──► server.py ──► NovaEngine.respond()   (src/py/engine.py)
                                                              │
                                      1. math_solver.solve       → "math"
                                      2. time_reader.handle      → "time"
                                      3. JSON brain (fuzzy match) → "brain"
                                      4. fallback                → "fallback"
```

1. 第一个给出答案的层胜出。
2. 技能先运行，因此精确的问题会被计算，而不是模糊匹配。
3. 大脑先规范化消息（小写、俚语与拼写修正），按词重叠度与每个模式打分（模式原样出现在消息中时加分），最高分不低于 0.35 才作答。
4. 每条回复都是 `{"text", "skill", "suggestions"}`。

更深入的说明：[架构](../nova.md)和 [JSON 大脑](../../help/the-json-brain.md)。

## 仓库结构

```
nova-chatbot/
├── server.py                  # HTTP 服务器和运行入口
├── src/
│   ├── index.html             # 浏览器聊天页面
│   ├── json/brain.json        # 回复、模式、拼写与俚语修正
│   ├── py/                    # Python 引擎（受支持的实现）
│   │   ├── engine.py          #   路由、规范化、匹配
│   │   ├── math_solver.py     #   数学技能
│   │   └── time_reader.py     #   日期/时间技能
│   └── java/                  # Java 数学和时间技能及命令行演示
├── tests/test_nova.py         # 自动化测试
├── docs/                      # 文档、译文、图片
│   ├── _docs.md               #   文档索引
│   ├── nova.md                #   架构与组件
│   ├── compatible/            #   各平台兼容性说明
│   ├── readme/                #   README 译文
│   └── img/                   #   横幅、图标、徽章
├── help/                      #   指南（安装、使用、大脑、技能）
├── .github/                   # Issue 表单、PR 模板、CI、Dependabot
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Java 实现

[`src/java/`](../../src/java/) 包含**数学和时间技能**的 Java 版本以及一个命令行演示。这是一个部分移植：它没有 HTTP 服务器，也不读取 `brain.json`，因此无法进行对话，也不能与 Python 引擎互换。对相同的输入，两边的技能输出相同，只是 Java 使用 `double` 运算，所以大于 2^53 的整数结果会不同。

```bash
javac -encoding UTF-8 -d out src/java/*.java
java -cp out nova.NovaEngine
```

建议使用 JDK 17 或更高版本（已在 OpenJDK 21 上编译并运行）。如果特殊字符显示为 `?`，请使用 `-Dstdout.encoding=UTF-8`（Java 19+）运行，或把终端切换为 UTF-8。

## 测试

```bash
python -m unittest discover -s tests -v
```

该测试集检查 `brain.json` 是否有效、数学和时间的答案、普通聊天不会被误认为时间问题、意图路由、拼写错误处理、兜底回复，以及 HTTP 服务器（健康检查、页面、图标、聊天、错误请求）。它不需要运行中的服务器，也不需要额外的包。GitHub Actions 会运行同一测试集并编译 Java 文件（[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)）。

## 扩展 Nova

- **新的回复、意图、拼写修正：** 编辑 [`brain.json`](../../src/json/brain.json)；见 [JSON 大脑指南](../../help/the-json-brain.md)。
- **新的精确回答技能：** 按照[创建你自己的技能](../../help/_create-skill/create-your-own-skill.md)操作（经过测试的教程）。

## 文档

全部文档的索引见 [`docs/_docs.md`](../_docs.md)： [Nova 是什么](../../help/what-is-nova.md) · [为什么存在](../../help/why-nova.md) · [好用吗](../../help/is-nova-good.md) · [安装](../../help/installing-nova.md) · [使用](../../help/how-to-use-nova.md) · [图片](../img/_img.md)

## 参与贡献

欢迎贡献。请阅读[贡献指南](../../.github/CONTRIBUTING.md)，然后提交 [Bug 报告或功能请求](https://github.com/gelowie/nova-chatbot/issues/new/choose)，或发送 Pull Request。另见[更新日志](../../CHANGELOG.md)。

## 许可证

Nova 以 [MIT 许可证](../../LICENSE)发布。版权所有 (c) 2026 Angelo MT。
