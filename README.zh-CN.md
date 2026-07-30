# RateMyCode

[English](README.md) | 简体中文

为那些开发速度快到作者还来不及了解所有故障模式的应用，提供 Staff 级产品审查。

> 你的应用已经做完了。现在，它必须经得起 Staff 级审查。

要一次审查，就得到一个结论：

```text
审查这个应用是否适合公开上线。测试真实产品，展示证据，阻止不安全的发布，列出全部问题，并指出我现在最该动手的三件事。
```

给会话挂一个持久目标（Codex 里用 `/goal`；Claude Code 里把同一句话当第一条消息发出去），同一个 skill 就会跨很多轮盯着这个目标：

```text
/goal 用 ratemycode 把这个应用推到能公开上线：先审计，再修我授权的部分，复测到阻断项清零
```

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

不要在同一作用域内同时使用两种 Claude 安装方式。之后，用上面任意一条提示词开场，即可选中该 skill。

## 它是什么

RateMyCode 是一个可移植的 [Agent Skill](https://agentskills.io/)，用于评判真实产品，而不只是给代码审查套上某种人设。

它从产品承诺和真实用户旅程出发，在条件允许时测试实际行为，并比较内部文档、`llms.txt`、接口 schema、示例、界面文案与在线文档中的重叠事实；随后将故障追溯到代码，区分已证实内容与推断，并最终给出发布结论。致命的授权或支付故障，不能被漂亮的平均分掩盖。

默认流程如下：

```text
构建 → 审查 → 完整结论
                  ├─ 只看报告（默认，不改代码）
                  ├─ 生成可复制的修复提示词（不改代码）
                  └─ 授权直接修复 → 原路径与相邻路径复测 → 更新审计台账
```

它刻意将通用审查者经常混为一谈的四件事分开：

- 原始产品质量
- 证据覆盖率与置信度
- 发布就绪度与硬性否决项
- 仅在请求答辩时评估的作者理解程度

在询问角色和程度之前，RateMyCode 会先做一次最小化、只读的产物门禁检查。它要确认的是一个连贯的产品目标；同一产品关联的仓库、部署地址、日志、数据和文档可以共同作为证据面，不会被误判成多个项目。如果当前工作区为空或与产品无关、指定目标不存在，或者同时有多个互不相关的产品却无法确定目标，它会请用户提供项目路径、仓库、部署地址、附件或产品证据文件，然后停止；此时不会检查内容、评分或给出结论。项目确实存在但无法运行时，仍可继续进行明确受限的静态审查。

## 角色与程度

确认唯一审查目标后，当请求尚未说明时，这个 skill 会在开始前询问两个问题：

```text
1. 角色：产品负责人 / 挑剔用户 / Staff 工程师 / 怀疑型 VC / 答辩老师
2. 程度：快速体检 / 严格评审 / 上线门禁 / 真实收米档 / 生死审查
```

| 选择 | 审查者会做什么 |
|---|---|
| 产品负责人 | 判断用户价值、价值实现速度、信任度、重复使用情况和产品证据 |
| Staff 工程师 | 深入审查产物、不变量、故障处理、运维和变更安全性 |
| 挑剔用户 | 尝试缺乏耐心、误操作、重试、陈旧状态、生命周期边界和访问边界滥用等情形 |
| 怀疑型 VC | 将用户行为和市场证据与创始人的主张及代码观感区分开 |
| 答辩老师 | 基于产物一次提出一个问题，共 3–5 个；单独评估理解程度 |

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
一句话问题清单
- [HIGH · F-004 · open] 支付重试会导致重复扣款：同一个订单可能向用户收取两次费用。
- [HIGH · F-006 · open] 内部文档、llms.txt 与 /api-keys/docs 对 API Key 有效期的说法不一致：接入方无法判断凭证何时失效。
- [MEDIUM · F-007 · verified-fixed] 结账曾在保存订单前报告成功：用户可能付了钱却没有订单。

待验证
- [UNKNOWN · U-002 · UNVERIFIED] 尚未验证退款超时后的最终状态：用户可能看到成功提示，却始终收不到退款。

证据通道：
- deterministic-checks: PASS
- critical-journey-e2e: FAIL
- probabilistic-eval: N/A — 不包含 LLM、Agent 或 RAG 行为
- continuous-evidence: UNVERIFIED

申请发布：
发布引用：
证据支持的最高安全发布级别：
结论：READY | READY_WITH_CONDITIONS | NOT_READY | BLOCKED | INSUFFICIENT_EVIDENCE
产品评分：可选
证据覆盖率：
置信度：

详细问题：
详细待验证风险：
优先处理的 3 项：
复测计划：
```

开头会把所有已确认问题——未处理、处理中、用户接受或已独立验证修复——放进同一份按严重程度排序的列表；每项严格使用一句通俗语言，说明会发生什么以及为什么重要。它绝不会用“前三项”的上限隐藏其他问题。无法验证的修复、仍开放的待验证项和生效中的流程阻塞保留在 `待验证` 下，不会被写成已经解决的事实。随后，四条证据通道会准确展示哪些内容已被证实；一条绿色通道不能替另一条兜底。详细问题会形成完整闭环：从产品不变量，到精确复现步骤、可见证据、后果、最低限度修复方案和验收测试。缺失或过期的证据绝不算作通过。

当多个文档入口描述同一件事时，RateMyCode 默认比较事实而不是逐字相同：措辞可以不同，但同一版本与环境里的接口、权限、默认值、限制、有效期、错误和生命周期规则必须兼容。只有用户明确要求，或生成镜像契约规定必须完全相同时，才进行逐字节比较。已经确认的文字矛盾会作为普通问题进入开头清单；打不开的内部文档或在线页面会明确保留为待验证，绝不会被偷偷算成“一致”，文档本身也不会被当成运行时行为的证明。

## 审计台账与修复闭环

当你要求保存审计结果，或授权 Agent 直接修复时，RateMyCode 会保存一份规范 JSON 台账，并由它生成易读的中英文 Markdown 视图。JSON 始终是唯一事实来源。生成的报告先给出完整的一句话问题清单，紧接着展示四条证据通道，再展示流程阻塞、发布检查、可选评分、适用时的投资证据、审查标识、进度、共同根因、门禁、问题详情、待验证项和证据。复测结果为 `unverifiable` 时，仍会保留在完整问题清单中，并在“待验证”中再次提示；它绝不会被写成已经修复。

台账采用快照链。第一份文件使用 `previous_ledger_ref: null`；此后每份文件都记录上一份 JSON 精确字节的 SHA-256，并通过 `--prior` 校验连续性。旧证据和记录身份不能被悄悄删除或改写。审计对象使用 `sha256-file`、`sha256-tree` 或 `sha256-deployment-manifest` 绑定，同时用结构化 `identity_scope` 明确记录根目录、包含项、排除项和符号链接策略。目录树身份来自确定性、已排序的文件摘要清单，并排除台账本身。整条链中的初始版本身份、哈希方法、范围、角色、程度、目标、评分标准 ID 和 AI 行为分类都保持不变。

非 VC 审查的程度与目标严格对应：快速体检 → 内部演示，严格评审 → 私测，上线门禁 → 公开上线，真实收米档 → 真实资金，生死审查 → 高风险场景。VC 审查使用 `venture-case`，五档程度依次对应初筛、结构化尽调、合伙人审查、完整尽调和投委会。`ai_behavior` 只能是 `none`、`llm`、`agent`、`rag` 或 `mixed`。

每条证据都绑定稳定的对象和验证过程：复现、验收、相邻回归和变异证据必须指向一个 `F-###`；待验证项的解决证据指向一个 `U-###`；发布通道证据不绑定具体问题。流程阻塞、发布检查和投资信号的证据还必须明确写出自己支持的那一项，避免一条漂亮结果被悄悄复用成多个结论。只有当 `deployment_coverage` 明确说明已检查完整部署范围，并排除了补偿层时，完整的代码或文档检查才可以触发门禁；它不能关闭门禁、排除待验证项或证明修复。E0 主张永远不算证据。

非 VC 审查的必需证据通道采用失败关闭：每个软件发布级别都需要关键旅程 E2E；私测及以上需要确定性检查；公开上线及以上需要持续证据；包含 LLM、Agent、RAG 或混合行为时需要重复执行的概率性评估。结论顺序固定为：作用域内门禁生效或存在具名阻塞 → `BLOCKED`；必需通道或发布检查失败，或仍有 Blocker/High 问题 → `NOT_READY`；必需通道或检查未验证、问题无法验证或存在开放待验证项 → `INSUFFICIENT_EVIDENCE`；就绪度低于阈值 → `NOT_READY`；只剩可选缺口 → `READY_WITH_CONDITIONS`；否则 → `READY`。VC 台账把四条软件通道全部标为 `N/A`，再根据真实用户、留存、可重复分发、阻塞项、待验证项和可选评分，单独得出 `INVESTABLE`、`INTERESTING_BUT_UNPROVEN`、`NOT_INVESTABLE_YET` 或 `INSUFFICIENT_EVIDENCE`。

台账会保留全部问题和待验证项、共同根因、精确版本标识、用户授权、变更引用、复测证据，以及下列状态：

```text
未处理 → 修复中 → 已改待复测 → 已验证修复
                              ├→ 部分修复 / 未修复 / 出现回归 / 无法验证
外部变更 ─────→ 已改待复测
任何工作或验证状态 → 受阻（注明原因、缺失条件和解除方式）
任何技术上未解决的状态 → 用户接受风险（必须来自用户的明确原话）
```

Agent 直接修复使用 `origin: authorized-agent`，并保留用户原话和明确范围；在别处已经完成的修改使用 `origin: external-change`，授权字段保持 `null`，RateMyCode 可以复测它，但不会虚构追溯授权。代码 diff 永远不能单独证明修复完成。要标记为 `verified-fixed`，必须由独立 Agent 或全新审查上下文，在当前版本上分别取得验收和相邻回归证据；条件允许时，还要通过“重新引入原故障”的变异检查。只有用户能接受风险；原因说明 `rationale` 可选，但用户原话和范围必填，而且接受风险仍代表技术问题未解决。若审查契约中的门禁省略了作用域，台账会把它展开为显式排序的 `affected_targets` 列表，风险接受不能豁免门禁。

内置的纯标准库工具可以校验台账，并生成英文或中文 Markdown：

```bash
python3 skills/ratemycode/scripts/audit_ledger.py validate evals/ledgers/initial.json
python3 skills/ratemycode/scripts/audit_ledger.py validate --prior evals/ledgers/initial.json evals/ledgers/closed-loop.json
python3 skills/ratemycode/scripts/audit_ledger.py render --prior evals/ledgers/initial.json --language zh-CN --output audit-report.md evals/ledgers/closed-loop.json
```

校验器会检查结构一致性、版本与验证过程绑定；每个链式快照都必须提供 `--prior`，并验证连续性；修复者与复测者 ID 必须不同。它不是密码学身份验证、签名、可信时间戳或防篡改审计系统。高风险治理仍需使用存放在受审仓库之外的外部签名证明。完整 schema 和身份生成方法请参阅 [`audit-ledger.md`](skills/ratemycode/references/audit-ledger.md)。

## 为什么它不是又一个代码审查提示词

- 它审查产品契约和状态转换；代码只是证据来源之一。
- 它会在审查前询问审查者角色和审查程度，而不是默认为工程视角。
- 它先进行黑盒测试，再深入实现细节。
- 它会比较内部文档、`llms.txt`、schema、示例、界面文案和在线文档中的可执行事实，同时忽略无害的措辞差异。
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

仓库内容、网页、日志和测试夹具都会被当作不可信证据，而不是指令。评分器和审计台账渲染器都是仅使用标准库的确定性 Python 程序。威胁模型和披露流程请参阅 [SECURITY.md](SECURITY.md)。

## 仓库结构

```text
.claude-plugin/         Claude Code 插件和市场清单
.agents/plugins/        Codex 仓库市场
plugins/ratemycode/     自包含的 Codex 插件和商店素材
skills/ratemycode/      规范 skill、审查/台账/评分契约、UI 元数据、校验器和渲染器
evals/trigger_cases.json 包含近似负例的触发选择评估
evals/execution_cases.json 有 skill 与无 skill 的行为对比评估
evals/fixtures/          可复现的本地测试产物
evals/ledgers/           已通过校验的审计—修复闭环示例
submission/             通用 Plugins Directory 的上架文案和八项审核测试
scripts/sync_codex_plugin.py 生成包同步
scripts/validate_repo.py 内置 schema 和引用完整性检查
tests/                   确定性评分器与审计台账测试
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
