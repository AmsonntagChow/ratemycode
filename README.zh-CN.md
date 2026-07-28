# RateMyCode

[English](README.md) | 简体中文

为那些开发速度快到作者还来不及了解所有故障模式的应用，提供 Staff 级产品审查。

> 你的应用已经做完了。现在，它必须经得起 Staff 级审查。

[![MIT License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-5b5bd6.svg)](https://agentskills.io/)
[![skills.sh](https://skills.sh/b/AmsonntagChow/ratemycode)](https://skills.sh/amsonntagchow/ratemycode/ratemycode)

请选择一种安装方式。对于 Codex，请将此仓库添加为插件市场：

```bash
codex plugin marketplace add AmsonntagChow/ratemycode
```

然后在 Codex CLI 中打开 `/plugins`，或在桌面应用中打开 Plugins Directory，安装 **RateMyCode** 并启动新会话。

对于 Claude Code，请安装插件：

```text
/plugin marketplace add AmsonntagChow/ratemycode
/plugin install ratemycode@amsonntagchow
/reload-plugins
```

对于 Cursor 或其他 Agent Skills 客户端——也包括只想轻量安装 Codex skill 的情况——请使用开放的 `skills` CLI：

```bash
npx skills add AmsonntagChow/ratemycode --skill ratemycode
```

不要在同一作用域内同时使用两种 Claude 安装方式。之后，请给出一个具体的首次提示词，以便选中该 skill：

```text
审查这个应用是否适合公开上线。测试真实产品，展示证据，阻止不安全的发布，并告诉我最快能完成的三个修复。
```

## 它是什么

RateMyCode 是一个可移植的 [Agent Skill](https://agentskills.io/)，用于评判真实产品，而不只是给代码审查套上某种人设。

它从产品承诺和真实用户旅程出发，在条件允许时测试实际行为，将故障追溯到代码，区分已证实内容与推断，并最终给出发布结论。致命的授权或支付故障，不能被漂亮的平均分掩盖。

默认流程如下：

```text
构建 → 审查 → 修复或生成修复提示词 → 按原路径复测 → 推进到最安全的下一发布阶段
```

它刻意将通用审查者经常混为一谈的四件事分开：

- 原始产品质量
- 证据覆盖率与置信度
- 发布就绪度与硬性否决项
- 仅在请求答辩时评估的作者理解程度

## 角色与程度

当请求尚未说明时，这个 skill 会在开始前询问两个问题：

```text
1. 角色：产品负责人 / 挑剔用户 / Staff 工程师 / 怀疑型 VC / 答辩老师
2. 程度：快速体检 / 严格评审 / 上线门禁 / 真实收米档 / 生死审查
```

| 选择 | 审查者会做什么 |
|---|---|
| 产品负责人 | 判断用户价值、价值实现速度、信任度、重复使用情况和产品证据 |
| Staff 工程师 | 深入审查产物、不变量、故障处理、运维和变更安全性 |
| `hostile-user` | 尝试缺乏耐心、误操作、重试、陈旧状态、生命周期边界和访问边界滥用等情形 |
| `skeptical-vc` | 将用户行为和市场证据与创始人的主张及代码观感区分开 |
| `oral-defense` | 基于产物一次提出一个问题，共 3–5 个；单独评估理解程度 |

可以试试：

```text
这个支付 App 是我两天 vibe coding 出来的。别教我后端基础，按真实收米档的标准挑刺，告诉我哪里会死。

像一个挑剔用户那样行事。尝试破坏注册、结账、恢复和取消流程，然后给我可复现的问题。

以怀疑型 VC 的身份审查这个演示和使用数据导出。区分哪些是用户已经证明的，哪些只是我的主张。

应用已经做完了。仅根据这个产品中的风险，让我一次回答一个问题来为它答辩。
```

## 结论包含什么

每次审查都会先用用户的语言给出完整的单行问题列表，再列出用户申请的发布级别，以及现有证据所支持的最高安全发布级别：

```text
问题一览
已验证
- [HIGH · F-004] 支付重试会导致重复扣款：同一个订单可能向用户收取两次费用。
待验证
- [UNVERIFIED · U-002] 尚未验证退款超时后的最终状态：用户可能看到成功提示，却始终收不到退款。

证据通道：
- deterministic-checks: PASS
- critical-journey-e2e: FAIL
- probabilistic-eval: N/A — 不包含 LLM、Agent 或 RAG 行为
- continuous-evidence: UNVERIFIED

申请发布：
发布引用：
证据支持的最高安全发布级别：
结论：READY | READY WITH CONDITIONS | NOT READY | BLOCKED | INSUFFICIENT EVIDENCE
产品评分：可选
证据覆盖率：
置信度：

详细问题：
详细待验证风险：
优先处理的 3 项：
复测计划：
```

开头的列表会包含每一个已验证问题，并按严重程度排序；每项严格使用一句通俗语言，说明会发生什么以及为什么重要。它绝不会用“前三项”的上限隐藏其他问题。待验证风险保留在单独的 `待验证` 列表中，不会被当作事实陈述。随后，四条证据通道会准确展示哪些内容已被证实；一条绿色通道不能替另一条兜底。详细问题会形成完整闭环：从产品不变量，到精确复现步骤、可见证据、后果、最低限度修复方案和验收测试。缺失或过期的证据绝不算作通过。

## 为什么它不是又一个代码审查提示词

- 它审查产品契约和状态转换；代码只是证据来源之一。
- 它会在审查前询问审查者角色和审查程度，而不是默认为工程视角。
- 它先进行黑盒测试，再深入实现细节。
- 它将确定性检查、关键旅程 E2E、概率性评估和持续证据分开，而不是全部归结为“测试已通过”。
- 只有当产品确实包含 LLM、Agent 或 RAG 行为时，它才要求提供重复执行且绑定版本的评估。
- 当运行时证据不可用时，它拒绝批准公开上线。
- 它会明确否决跨租户访问、敏感数据暴露、不可逆数据丢失、重复真实扣款，以及核心操作假成功等情况。
- 它会使用原始问题 ID、步骤、发布目标和评分标准来复测修复。
- 它绝不会因为简单产品没有使用 Redis、队列、微服务或其他无关技术而扣分。
- 它不会要求作者先学会 ACID、幂等性或 HTTP 语义，才给出有用的修复建议。

## 安装

请选择原生 Codex 插件、Claude Code 插件或可移植 Agent Skill 安装方式。不要在同一个客户端和作用域内安装重复副本。

切换安装方式时，请先通过 `/plugins`、`npx skills remove ratemycode` 或 `/plugin uninstall ratemycode@amsonntagchow` 移除现有副本，具体取决于你使用的方式。

### Codex 插件

添加仓库市场：

```bash
codex plugin marketplace add AmsonntagChow/ratemycode
```

在 Codex CLI 中打开 `/plugins`，安装 **RateMyCode**，然后启动新会话，以便加载其捆绑的 skill。在 Codex 桌面应用中，请先添加市场，再使用 Plugins Directory。

此仓库还包含一个可直接提交的纯 skills 包，适用于 ChatGPT 和 Codex 共用的通用 OpenAI Plugins Directory。请参阅 [submission/PLUGIN_DIRECTORY.md](submission/PLUGIN_DIRECTORY.md)；只有通过 OpenAI 审核且发布者执行最终发布操作后，才会公开可用。

### Claude Code 插件

将此仓库添加为市场，安装插件，然后重新加载：

```text
/plugin marketplace add AmsonntagChow/ratemycode
/plugin install ratemycode@amsonntagchow
/reload-plugins
```

之后，Claude 可以根据任务自动选用该 skill。若要显式调用，请使用 `/ratemycode:ratemycode`。

### 可移植 Agent Skill

[`skills` CLI](https://www.skills.sh/docs/cli) 可以将同一个 skill 安装到 Codex、Claude Code、Cursor 和许多其他兼容 Agent 中。

```bash
# 交互式选择 Agent
npx skills add AmsonntagChow/ratemycode --skill ratemycode

# Codex，全局安装，无提示
npx skills add AmsonntagChow/ratemycode --skill ratemycode --agent codex --global --yes

# Claude Code，全局安装，无提示
npx skills add AmsonntagChow/ratemycode --skill ratemycode --agent claude-code --global --yes
```

该 CLI 的文档说明了匿名安装遥测。若要为本次安装命令选择退出：

```bash
DISABLE_TELEMETRY=1 npx skills add AmsonntagChow/ratemycode --skill ratemycode
```

也可以手动安装：将 `skills/ratemycode` 复制到你的 Agent 所使用的 skills 目录中。这个 skill 本身不包含遥测、网络调用、shell 自动授权或第三方依赖。

## 评分

数字评分是可选的。捆绑的纯标准库评分器会将证据绑定到精确的 SHA-256 发布标识和四条不可互相替代的通道；它会拒绝同一通道内隐藏的失败，强制要求对安全门禁按相同路径复测，为评分标准生成指纹，并将原始产品质量与受证据限制的就绪度分开。启用中的门禁可以声明它具体影响哪些发布目标；它在每次审查中都保持可见，但只会阻止和限制申请发布目标中属于其作用域的部分。普通应用将概率性评估标记为 `N/A`；LLM、Agent 和 RAG 产品则需要重复执行的评估证据，且这些证据必须共用同一个经过审查的模型、提示词、评估集、裁判和系统标识，并达到与发布级别相符的通过率和方差阈值。VC 证据会单独绑定到真实用户、留存情况或可重复的分发渠道。评分卡 schema `2` 会刻意拒绝 schema `1` 的证据，避免旧观察结果被悄悄复用于新发布。

```bash
python3 skills/ratemycode/scripts/score_review.py --pretty evals/scorecards/blocked-release.json
```

调用方可以配置评分维度和权重，但不能重新定义或豁免安全门禁。提供的门禁作用域必须是非空、无重复且仅包含受支持目标的列表；已修复的门禁必须有可复现且通过的运行时或测试证据。

## 信任与安全

首次审查默认只读。这个 skill 会要求 Agent 不得编辑代码、改变基础设施、向银行卡扣款、删除数据或触碰外部系统，除非用户明确提出要求，且操作范围已得到安全限定。

仓库内容、网页、日志和测试夹具都会被当作不可信证据，而不是指令。评分器是仅使用标准库的确定性 Python 程序。威胁模型和披露流程请参阅 [SECURITY.md](SECURITY.md)。

## 仓库结构

```text
.claude-plugin/         Claude Code 插件和市场清单
.agents/plugins/        Codex 仓库市场
plugins/ratemycode/     自包含的 Codex 插件和商店素材
skills/ratemycode/      规范 skill、始终加载的审查契约、可选评分契约、UI 元数据、评分器
evals/trigger_cases.json 包含近似负例的触发选择评估
evals/execution_cases.json 有 skill 与无 skill 的行为对比评估
evals/fixtures/          可复现的本地测试产物
submission/             通用 Plugins Directory 的上架文案和八项审核测试
scripts/sync_codex_plugin.py 生成包同步
scripts/validate_repo.py 内置 schema 和引用完整性检查
tests/                   确定性评分器测试
```

触发选择和执行质量会刻意放在不同文件中评估，以便将失败定位到发现阶段或行为阶段。

## 开发

```bash
python3 scripts/sync_codex_plugin.py --check
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/ratemycode
```

贡献必须包含行为证据，而不只是文字差异。此仓库的 CI 会从结构上验证评分器、测试夹具、打包和 schema；它并不声称已经运行 LLM 执行用例。提交拉取请求前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

此仓库的编写方法参考了[《从零做一个高质量 Agent Skill，并把它当开源项目运营》](https://research.xishe.ai/skill-authoring-and-oss)，尤其借鉴了其中关于描述优先发现、渐进式披露、触发/执行评估分离、引用完整性、零依赖脚本和开源分发的指导。

## 许可证

[MIT](LICENSE) © 2026 AmsonntagChow
