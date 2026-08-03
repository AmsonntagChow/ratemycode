# RateMyCode

[English](README.md) | 简体中文

哪些功能真能用、哪些不能，往往没人说得准。这个 Skill 给你的应用做一次 Staff 级产品审查。

> 做完了，不等于能上线。

发这一段过去，它还你一个结论，不是一份建议清单：

```text
审这个应用能不能公开上线。真的把产品跑一遍，证据摆出来，不安全就别放行，问题一条不漏地列，再告诉我先动哪三件。
```

懒得盯着？把下面这段挂成会话的长期目标就行 —— Codex 里用 `/goal`，Claude Code 里把它当第一条消息发出去：

```text
/goal 用 ratemycode 把这个应用推进到可以公开上线
```

不用你规定 goal 要做多少。它不会自己说自己修好了，改完得重新验过才算。还剩什么没弄完，它也会讲。

[![MIT License](https://img.shields.io/badge/license-MIT-2f855a.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-5b5bd6.svg)](https://agentskills.io/)
[![ratemy.sh](https://img.shields.io/badge/ratemy.sh-code-C4500F.svg)](https://code.ratemy.sh/zh/)
[![skills.sh](https://skills.sh/b/AmsonntagChow/ratemycode)](https://skills.sh/amsonntagchow/ratemycode/ratemycode)

请选择一种安装方式。`skills` CLI 最短，且在 Codex、Claude Code、Cursor 以及其他所有 Agent Skills 客户端都能用：

```bash
npx skills add AmsonntagChow/ratemycode --skill ratemycode
```

如果想在 Claude Code 里装成插件，**只执行下面这一条**——`/plugin` 会把它后面的全部内容当作一个参数，多行粘贴会被读成一个畸形的仓库名：

```text
/plugin marketplace add AmsonntagChow/ratemycode
```

然后打开 `/plugins`，在菜单里安装 **RateMyCode**，再开一个新会话。

如果想在 Codex 里装成插件，请将此仓库添加为插件市场：

```bash
codex plugin marketplace add AmsonntagChow/ratemycode
codex plugin add ratemycode@amsonntagchow-ratemycode
```

然后启动新会话。Codex 桌面应用里可以用 Plugins Directory 代替第二条命令。

不要在同一作用域内同时使用两种 Claude 安装方式。所有方式都不会自动更新：要升级到新版本，重新执行一次安装命令即可。之后，用上面任意一条提示词开场，即可选中该 skill。

## 它是什么

RateMyCode 是一个可移植的 [Agent Skill](https://agentskills.io/)。它评判的是真实产品，不是给代码审查套上某种人设。

它从产品承诺和那几条关键用户旅程入手，能跑就跑一遍看真实行为，再把内部文档、`llms.txt`、schema、示例、界面文案和线上文档里重叠的事实两两对上。发现故障就追回代码，分清哪些是证实的、哪些是推断，最后给出发布结论。

致命的授权或支付故障，不会被漂亮的平均分掩盖。

默认流程：

```text
build → audit → complete verdict
                  ├─ report only (default; no edits)
                  ├─ copy-ready fix prompts (no edits)
                  └─ authorized fixes → same-path + adjacent retests → updated audit ledger
```

它刻意把四件事分开。通用审查者经常把这四件事混为一谈：

- 原始产品质量
- 证据覆盖率与置信度
- 发布就绪度与硬性否决项
- 作者的理解程度。只有请求口头答辩时，才会评估这一项。

在询问角色和程度之前，RateMyCode 会先做一次最小化、只读的产物门禁检查。它要确认一个连贯的产品目标。关联的仓库、部署地址、日志、数据和文档可以共同作为证据面，不会被误判成多个项目。

如果当前工作区为空，或与产品无关，或指定目标不存在，或同时有多个互不相关的产品却无法确定目标，它会请你提供项目路径、仓库、部署地址、附件或产品证据文件。然后它停止。它不会检查内容，不会评分，不会给出结论。

项目确实存在但无法运行时，它仍会继续。此时它进行明确受限的静态审查。

## 角色与程度

确认唯一审查目标后，这个 skill 会在开始前询问两个问题。如果请求里已经回答了，它就不再问。

```text
1. Role: Product lead / Hostile user / Staff engineer (systems/backend) / Staff Frontend engineer / Skeptical VC / Oral-defense examiner
2. Degree: Quick checkup (default) / Strict review / Launch gate / Real-revenue tier / Life-or-death review
```

| 选择 | 审查者会做什么 |
|---|---|
| Product lead | 判断用户价值、价值实现速度、信任度、重复使用情况和产品证据 |
| Staff engineer (systems/backend) | 深入审查不变量、安全边界、并发、故障处理、运维和变更安全性 |
| Staff Frontend engineer | 测试真实浏览器行为、异步状态、无障碍、性能、响应式支持、组件体系和交互细节 |
| Hostile user | 尝试缺乏耐心、误操作、重试、陈旧状态、生命周期边界和访问边界滥用等情形 |
| Skeptical VC | 将用户行为和市场证据与创始人的主张及代码观感区分开 |
| Oral-defense examiner | 基于产物一次提出一个问题，共 3–5 个。单独评估理解程度 |

### 从快速体检开始

跑一次完整审查很贵：要把你的产品真跑起来、把故障追到代码里、再重跑一遍检查，花的时间和 token 是快速体检的好几倍。

而你用的是 Claude Code 的 Pro、Max，或者 Codex、Cursor 的包月套餐——额度就那么多，**审计吃掉的，就是你写代码要用的那份**。所以默认是快速体检：只查那几项最容易决定“这东西能不能放出去”的，查完就停。

它少查了东西，但没有少说话。查出来的问题一条不落地报给你；没查的那些会写明“这块没验”，并且告诉你要验它该跑哪一个测试。

什么时候值得升级？真金白银、别人的私密数据、真实用户，或者一个改回不来的决定——这几种情况才值得多花那份额度。

```text
Quick checkup on this app. Tell me the few things that would stop me shipping it, and what you did not check.
```

可以试试这些：

```text
I vibe-coded this payments app in two days. Do not teach me backend basics. Review it against the real-revenue standard and tell me what could kill it.

As a Staff Frontend engineer at launch-gate depth, audit this dashboard in a real browser. Check keyboard and screen-reader use, async state, mobile layouts, performance, and interaction quality.

Act like a hostile user. Try to break signup, checkout, recovery, and cancellation, then give me reproducible findings.

Be a skeptical VC. Review this demo and usage export. Separate what users proved from what I merely claimed.

The app is done. Make me defend it one question at a time, based only on risks in this product.
```

## 结论包含什么

每次审查都会先用用户的语言给出完整的单行问题列表。然后列出用户申请的发布级别，以及现有证据所支持的最高安全发布级别。

```text
One-line problem list
- [HIGH · F-004 · open] Payment retries cause duplicate charges: the same order may charge a user twice.
- [HIGH · F-006 · open] API-key expiry differs between the internal doc, llms.txt, and /api-keys/docs: integrators cannot know when credentials will stop working.
- [MEDIUM · F-007 · verified-fixed] Checkout reported success before saving the order: the user could pay for an order that did not exist.

Pending verification
- [UNKNOWN · U-002 · UNVERIFIED] The final state after a refund timeout has not been verified: users may see a success message but never receive the refund.

Evidence lanes:
- deterministic-checks: PASS
- critical-journey-e2e: FAIL
- probabilistic-eval: N/A — no LLM, agent, or RAG behavior
- continuous-evidence: UNVERIFIED

Requested release:
Release ref:
Maximum safe release:
Decision: READY | READY_WITH_CONDITIONS | NOT_READY | BLOCKED | INSUFFICIENT_EVIDENCE
Product score: optional
Evidence coverage:
Confidence:

Detailed findings:
Detailed unverified risks:
Top 3 actions:
Retest plan:
```

开头的列表包含所有已确认的问题。包括未处理的、处理中的、用户接受的、已独立验证修复的。所有问题按严重程度排序。每一项用一句通俗语言说明会发生什么，以及为什么重要。

它不会用“前三项”的上限隐藏其他问题。无法验证的修复、开放的未知项、生效中的流程阻塞，都保留在 `Pending verification` 下面。它们不会被写成已经解决的事实。

四条证据通道展示哪些内容已被证实。一条绿色通道不能替另一条兜底。详细问题形成完整闭环：从产品不变量，到精确复现步骤、可见证据、后果、最低限度修复方案和验收测试。缺失或过期的证据，绝不算通过。

多个文档入口描述同一件事时，默认比较事实，不比较字节。措辞可以不同。但同一版本、同一环境里，接口、权限、默认值、限制、有效期、错误和生命周期规则必须兼容。只有用户明确要求，或生成镜像契约规定必须完全相同时，才进行逐字节比较。

已确认的文字矛盾，作为普通问题进入开头清单。打不开的内部文档或在线页面，明确保留为未知。它不会被偷偷算成“一致”。文档本身，永远不能当成运行时行为的证明。

## 审计台账与修复闭环

你要求保存审计结果，或授权直接修复时，RateMyCode 会保存一份规范 JSON 台账。它还会生成易读的英文或中文 Markdown 视图。JSON 始终是唯一事实来源。

生成的报告先给出完整的一句话问题清单。紧接着展示四条证据通道。然后展示流程阻塞、发布检查、可选评分、适用时的投资证据、审查标识、进度、共同根因、门禁、问题详情、未知项和证据。

复测结果为 `unverifiable` 时，它保留在待验证中。它不会被写成已经修复。

台账采用快照链。第一份文件使用 `previous_ledger_ref: null`。此后每份文件都记录上一份 JSON 精确字节的 SHA-256，并通过 `--prior` 校验。旧证据和记录身份不能被悄悄删除或改写。

审计对象使用 `sha256-file`、`sha256-tree` 或 `sha256-deployment-manifest` 绑定。同时用结构化 `identity_scope` 明确记录根目录、包含项、排除项和符号链接策略。目录树身份来自确定性、已排序的文件摘要清单，并排除台账本身。

整条链中，初始版本身份、哈希方法、范围、角色、程度、目标、评分标准 ID 和 AI 行为分类都保持不变。

非 VC 审查的程度与目标严格对应：

- 快速体检 → 内部演示
- 严格评审 → 私测
- 上线门禁 → 公开上线
- 真实收米档 → 真实资金
- 生死审查 → 高风险场景

VC 审查使用 `venture-case`。五档程度依次对应初筛、结构化尽调、合伙人审查、完整尽调和投委会。`ai_behavior` 只能是 `none`、`llm`、`agent`、`rag` 或 `mixed`。

每条证据都绑定稳定的对象和验证过程。复现、验收、相邻回归和变异证据必须指向一个 `F-###`。未知项的解决证据指向一个 `U-###`。发布通道证据不绑定具体问题。

流程阻塞、发布检查和投资信号的证据，还必须明确写出自己支持的那一项。这样一条漂亮结果就不能被悄悄复用成多个结论。

只有当 `deployment_coverage` 明确说明已检查完整部署范围，并排除了补偿层时，完整的代码或文档检查才可以触发门禁。它不能关闭门禁，不能清除未知项，不能证明修复。E0 主张永远不算证据。

非 VC 审查的必需证据通道采用失败关闭：

- 每个软件发布级别都需要关键旅程 E2E
- 私测及以上需要确定性检查
- 公开上线及以上需要持续证据
- 包含 LLM、Agent、RAG 或混合行为时，需要重复执行的概率性评估

结论顺序固定：

- 作用域内门禁生效，或存在具名阻塞 → `BLOCKED`
- 必需通道或发布检查失败，或仍有 Blocker/High 问题 → `NOT_READY`
- 必需通道或检查未验证、问题无法验证、或存在开放未知项 → `INSUFFICIENT_EVIDENCE`
- 就绪度低于阈值 → `NOT_READY`
- 只剩可选缺口 → `READY_WITH_CONDITIONS`
- 否则 → `READY`

VC 台账把四条软件通道全部标为 `N/A`。它根据真实用户、留存、可重复分发、阻塞项、未知项和可选评分，单独得出 `INVESTABLE`、`INTERESTING_BUT_UNPROVEN`、`NOT_INVESTABLE_YET` 或 `INSUFFICIENT_EVIDENCE`。

台账会保留全部问题和未知项、共同根因、精确版本标识、用户授权、变更引用、复测证据，以及下列状态：

```text
open → fixing → fixed-pending-retest → verified-fixed
                                   ├→ partially-fixed / not-fixed / regressed / unverifiable
external-change ─────→ fixed-pending-retest
any work or verification state → blocked (named reason, missing requirement, resolving action)
any technically unresolved state → accepted-risk (only from an explicit user statement)
```

Agent 直接修复使用 `origin: authorized-agent`。它保留用户原话和明确范围。在别处已经完成的修改使用 `origin: external-change`。授权字段保持 `null`。RateMyCode 可以复测它，但不会虚构追溯授权。

代码 diff 永远不能单独证明修复完成。要标记为 `verified-fixed`，必须由独立 Agent 或全新审查上下文，在当前版本上分别取得验收和相邻回归证据。条件允许时，还要通过“重新引入原故障”的变异检查。

只有用户能接受风险。原因说明 `rationale` 可选。用户原话和范围必填。接受风险仍代表技术问题未解决。

若审查契约中的门禁省略了作用域，台账会把它展开为显式排序的 `affected_targets` 列表。风险接受不能豁免门禁。

内置的纯标准库工具可以校验台账，并生成英文或中文 Markdown：

```bash
python3 skills/ratemycode/scripts/audit_ledger.py validate evals/ledgers/initial.json
python3 skills/ratemycode/scripts/audit_ledger.py validate --prior evals/ledgers/initial.json evals/ledgers/closed-loop.json
python3 skills/ratemycode/scripts/audit_ledger.py render --prior evals/ledgers/initial.json --language zh-CN --output audit-report.md evals/ledgers/closed-loop.json
```

校验器检查结构一致性、版本与验证过程绑定。每个链式快照都必须提供 `--prior`，并验证连续性。修复者与复测者 ID 必须不同。

它不是密码学身份验证、签名、可信时间戳或防篡改审计系统。高风险治理仍需使用存放在受审仓库之外的外部签名证明。完整 schema 和身份生成方法请参阅 [`audit-ledger.md`](skills/ratemycode/references/audit-ledger.md)。

## 为什么它不是又一个代码审查提示词

- 它审查产品契约和状态转换。代码只是证据来源之一。
- 它会在审查前询问审查者角色和审查程度，而不是默认为工程视角。
- 它先进行黑盒测试，再深入实现细节。
- 它比较内部文档、`llms.txt`、schema、示例、界面文案和在线文档中的可执行事实。它忽略无害的措辞差异。
- 它将确定性检查、关键旅程 E2E、概率性评估和持续证据分开，而不是全部归结为“测试已通过”。
- 只有当产品确实包含 LLM、Agent 或 RAG 行为时，它才要求提供重复执行且绑定版本的评估。
- 当运行时证据不可用时，它拒绝批准公开上线。
- 它会明确否决跨租户访问、敏感数据暴露、不可逆数据丢失、重复真实扣款，以及核心操作假成功等情况。
- 它使用原始问题 ID、步骤、发布目标和评分标准来复测修复。
- 它不会因为简单产品没有使用 Redis、队列、微服务或其他无关技术而扣分。
- 它不会要求作者先学会 ACID、幂等性或 HTTP 语义，才给出有用的修复建议。

## 安装

请选择原生 Codex 插件、Claude Code 插件或可移植 Agent Skill 安装方式。不要在同一个客户端和作用域内安装重复副本。

切换安装方式时，请先通过 `/plugins`、`npx skills remove ratemycode` 或 `/plugin uninstall ratemycode@amsonntagchow-ratemycode` 移除现有副本，具体取决于你使用的方式。

### Codex 插件

添加仓库市场：

```bash
codex plugin marketplace add AmsonntagChow/ratemycode
codex plugin add ratemycode@amsonntagchow-ratemycode
```

启动新会话，以便加载其捆绑的 skill。Codex 桌面应用里可以用 Plugins Directory 代替第二条命令。

此仓库还包含一个可直接提交的纯 skills 包，适用于 ChatGPT 和 Codex 共用的通用 OpenAI Plugins Directory。请参阅 [submission/PLUGIN_DIRECTORY.md](submission/PLUGIN_DIRECTORY.md)；只有通过 OpenAI 审核且发布者执行最终发布操作后，才会公开可用。

### Claude Code 插件

将此仓库添加为市场，安装插件，然后重新加载：

```text
/plugin marketplace add AmsonntagChow/ratemycode
/plugin install ratemycode@amsonntagchow-ratemycode
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
