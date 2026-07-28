# Cloak, Honey, Trap: Proactive Defenses Against LLM Agents

## 1. 论文元数据 (Metadata)

- **标题**: Cloak, Honey, Trap: Proactive Defenses Against LLM Agents
- **作者**: Daniel Ayzenshteyn, Roy Weiss, Yisroel Mirsky
- **会议**: USENIX Security 2025
- **论文链接**: [USENIX 页面](https://www.usenix.org/conference/usenixsecurity25/presentation/ayzenshteyn)
- **开源材料**: [Zenodo artifact](https://doi.org/10.5281/zenodo.15601739)，包括 CHeaT 工具、数据集和 CTF machine files
- **核心关键词**: #LLMAgents #CyberDefense #Deception #Honeypots #PromptInjection
- **Zotero 追踪建议**:
  - Deng 等, 2024, *PentestGPT: Evaluating and Harnessing Large Language Models for Automated Penetration Testing*。
  - Fang 等, 2024, *LLM Agents Can Autonomously Hack Websites*。
  - Gallegos 等, 2024, *Bias and Fairness in Large Language Models: A Survey*，用于理解论文利用的 LLM bias 和 representation vulnerability 背景。

## 2. 核心摘要 (TL;DR)

这篇论文试图防御自动化 LLM penetration-testing agents 被攻击者用来规模化入侵网络资产的问题。它提出 Cloak、Honey、Trap 三类主动防御策略，共 6 类 tactics 和 15 个 techniques，通过误导、诱饵、tokenization/Unicode 特性、循环任务和代码执行诱导等方式拖延、检测或阻止恶意 agent。实验显示在 11 个 CTF machines 上，加入防御后 PentestGPT+GPT-4o 无法突破第一层防御；单点 technique 的 defense success rate 平均约 55-67%，多层组合后显著提升。

## 3. 技术原理解析 (Technical Breakdown)

### 算术化 (Arithmetization)

不适用。本文不是 ZKP 论文，没有 R1CS、QAP、AIR、sumcheck 或 polynomial constraints。它是一篇 LLM agent security/deception 论文，技术核心是如何布置对 LLM agents 有效、对人类管理员可控的环境数据点。

### 多项式承诺 (Polynomial Commitment)

不适用。论文没有使用 polynomial commitment、Merkle commitment 或 cryptographic proof system。它的“证明”来自实验评估，而不是密码学 soundness。

### 交互协议 (Interactive Oracle Proof, IOP)

不适用。本文没有 IOP/Fiat-Shamir。其交互模型是 defender $D$ 与 attacker agent $A$ 的 two-player game：$D$ 在环境 $E$ 中布置 manipulated data points $X'$，$A$ 通过工具调用读取这些数据点，并由 LLM 生成后续攻击步骤。

## 4. 数学公式推导梳理 (Math Walkthrough)

### 公式一：防御成功率

论文使用 Defense Success Rate (DSR) 衡量单个 payload/technique 是否达到预期目标：

$$\operatorname{DSR}=\frac{\#\operatorname{successful\ cases}}{\#\operatorname{total\ trials}}$$

成功条件按 technique 类型区分：

- misinformation 成功：payload 被插入 agent 的 knowledge summary 或影响其后续判断。
- model exploitation 成功：agent 表现出目标行为，例如停止、绕路、执行无效操作或触发检测。

这个指标不是密码学 soundness，而是经验安全指标。它依赖 agent framework、LLM backend、tool output 是否完整呈现、payload framing 和实验场景。

### 公式二：多层防御的累积概率

如果粗略假设每次遇到 trap 的失败概率相互独立，遇到 $n$ 个防御点后的成功防御概率可近似为：

$$P_{\mathrm{defense}}=1-\prod_{i=1}^{n}(1-p_i)$$

论文没有把这个作为严格理论定理，而是用实验说明“多点布置”像 minefield：即使单个 payload 的 DSR 中等，多次遇到后累计防御率会很高。文中报告，对最强模型 Llama-3.1-70B，随机遇到 5 个 trap techniques 后累计 DSR 超过 95%，遇到 5 个 honey techniques 后超过 90%。

如果 $p_i$ 之间高度相关，例如攻击者模型已经学会识别某类 payload，那么独立假设会高估效果；因此论文也测试了 adaptive adversaries。

## 5. 工程与代码实现视角 (Engineering Perspective)

三类策略：

- **Cloak**: 隐藏或扭曲高价值资产，让 agent 误判。例如错误 version number、Unicode/control character 扰动、误导性 banner。
- **Honey**: 放置 LLM-specific honeypots/honeytokens，引导 agent 暴露自己或消耗资源。
- **Trap**: 利用 LLM 的 context、search、alignment 或 code execution 弱点，让 agent 陷入循环、停止攻击或执行防御者设计的代码。

实验设置：

- 测试 PentestGPT、AutoAttacker、PenHeal 等 multi-LLM agents。
- LLM backends 包括 GPT-4o、Gemini-1.5-Pro、Claude 3.5 Sonnet、Llama-3.1-70B。
- 构造 249 payloads，植入 17 类 penetration-testing 常见 data points，得到 4233 data points。
- CTF end-to-end 评估使用 11 台 Team bi0s machines，每台无防御/有防御各多次运行。

结果：

- 单点 technique 平均 DSR 约 55-67%。
- 最优 1x1 technique-data point 组合在多个模型上达到 100%。
- 5x5 组合在多个模型上仍能维持约 75-87% 平均 DSR。
- 加 prompt injection 并不总是更好；许多模型会把它识别为 manipulation，从而触发拒绝或安全响应。
- 在 11 个 CTF machines 上，加入 defense 后 agent 在所有运行中都未能完成 initial access。

开源实现：

- 论文发布 Zenodo artifact，包含 CHeaT 工具、数据集和 CTF machine files。
- CHeaT 可自动插入 cloaks、traps 和 honeytokens，适合复现实验和研究防御部署。

## 6. 安全边界与局限

- 这是经验防御，不提供密码学 guarantee。
- 防御依赖当前 LLM agents 的偏差、上下文限制、工具调用习惯和安全对齐行为；未来 agent 可能通过专门训练降低 DSR。
- 许多 payload 对人类也可能造成维护负担，需要避免污染真实生产配置。
- 强适应性攻击者可能使用 filtering、RAG、cross-checking 或 deterministic parsing 减少误导。
- 代码执行类反制具有明显 dual-use 与法律/伦理风险，只应在隔离授权环境中研究。

## 7. 与 ZKP 阅读线的关系

这篇论文不属于零知识证明路线，但对“AI agent 安全治理”有参考价值。它与 SAGA 形成互补：SAGA 通过身份、授权和 token 缩小 agent-to-agent 滥用窗口；Cloak/Honey/Trap 通过环境欺骗和行为诱导防御恶意 autonomous agents。
