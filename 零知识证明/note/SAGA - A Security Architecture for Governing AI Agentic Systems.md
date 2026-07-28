# SAGA: A Security Architecture for Governing AI Agentic Systems

## 1. 论文元数据 (Metadata)

- **标题**: SAGA: A Security Architecture for Governing AI Agentic Systems
- **作者**: Georgios Syros, Anshuman Suri, Jacob Ginesin, Cristina Nita-Rotaru, Alina Oprea
- **版本**: arXiv:2504.21034v2, 2025 年 8 月 29 日；论文说明为 NDSS 2026 full version
- **论文链接**: [arXiv:2504.21034](https://arxiv.org/abs/2504.21034)
- **代码**: [gsiros/saga](https://github.com/gsiros/saga)
- **核心关键词**: #AgentSecurity #AccessControl #ProtocolVerification #LLMAgents #SAGA
- **Zotero 追踪建议**:
  - OpenAI, 2023, *Practices for Governing Agentic AI Systems*。论文明确以其中的 agent identity、authentication、discovery、communication 和 user control 需求为背景。
  - Krawczyk and Eronen, 2010, *HKDF*，用于理解 access control token key derivation。
  - Blanchet 等, *ProVerif* 用户手册/教程，用于理解论文的形式化协议验证部分。

## 2. 核心摘要 (TL;DR)

SAGA 试图解决 LLM agents 能自主发现、通信和委托任务后，用户缺乏细粒度生命周期控制和跨 agent 访问控制的问题。它提出一个 Provider-mediated 架构：用户注册 agent，Provider 维护身份、元数据和 contact policy，agent 通过 one-time keys、Diffie-Hellman 和 access control tokens 进行受限通信。实验显示协议开销在毫秒级，Provider 可通过 sharding/RAFT 扩展，在 AWS 上 7 个 sharders、24 小时 token lifetime 时支持约 2.6 亿活跃 agents。

## 3. 技术原理解析 (Technical Breakdown)

### 算术化 (Arithmetization)

不适用。SAGA 不是 ZKP/zk-SNARK 论文，没有把计算转为 R1CS、AIR、QAP 或多项式约束。它是一篇 agentic systems 安全架构论文，核心对象是身份、密钥、证书、访问令牌和 Provider registry。

### 多项式承诺 (Polynomial Commitment)

不适用。论文没有使用 polynomial commitment。其 cryptographic building blocks 是：

- digital signatures，例如 ECDSA 或 Ed25519；
- collision-resistant hash，例如 SHA-256 或 SHA-3；
- Diffie-Hellman key exchange，基于 CDH assumption；
- HKDF/KDF；
- symmetric encryption；
- TLS channels；
- Provider-signed metadata 和 access control tokens。

### 交互协议 (Interactive Oracle Proof, IOP)

不适用。SAGA 不使用 IOP/Fiat-Shamir。它的交互协议是 agent registration 和 agent communication handshakes。

核心通信流程：

1. 用户向 Provider 注册。
2. 用户为 agent 生成 TLS certificate、access control key 和 metadata，并让 Provider 记录和签名。
3. initiating agent 请求联系 receiving agent。
4. Provider 检查 receiving agent 的 Access Contact Policy，若允许，则返回 receiving agent metadata 和一个 OTK。
5. initiating agent 与 receiving agent 建立 TLS，再用 access control key 和 OTK 做 DH，导出 shared key。
6. receiving agent 用 shared key 加密 access control token，token 中包含 nonce、签发时间、过期时间、请求 quota 和 policy 信息。
7. 后续 inter-agent communication 附带 token，Provider 不再参与，直到 token 过期或 quota 用尽。

这种设计把 Provider 放在“发现和授权入口”，但不放在“所有消息转发路径”，所以可扩展性更好。

## 4. 数学公式推导梳理 (Math Walkthrough)

### 公式一：Diffie-Hellman 派生共享密钥

论文的共享密钥基础可以写成：

$$DH(x,g^y)=DH(y,g^x)=g^{xy}\bmod p$$

其中 initiating agent 和 receiving agent 分别持有自己的 secret key/public key。这个共享 secret 再进入 KDF：

$$K_{\mathrm{shared}}=\operatorname{KDF}(g^{xy},\mathrm{context})$$

逐步含义：

1. Provider 只分发 metadata 和 one-time public key，不需要知道 agent 间共享 secret。
2. 只有拥有对应 secret key 的两个 agent 能计算 $g^{xy}$。
3. context 应绑定 agent identities、OTK id、policy 和 transcript，避免 token 被跨 agent 或跨会话复用。
4. receiving agent 使用 $K_{\mathrm{shared}}$ 加密 access control token。

如果 context 绑定不足，攻击者可能重放或转移 token；如果 OTK 被无限复用，compromised agent 的滥用窗口会变大。

### 公式二：Access Control Token

论文图 9 中 token 可抽象为：

$$\operatorname{token}=\operatorname{Enc}_{K_{\mathrm{shared}}}(\langle N,T_{\mathrm{issued}},T_{\mathrm{expire}},Q_{\max},P_{AC}\rangle)$$

其中：

- $N$ 是 nonce；
- $T_{\mathrm{issued}}$ 和 $T_{\mathrm{expire}}$ 限制时间窗口；
- $Q_{\max}$ 限制可用请求数；
- $P_{AC}$ 是 access control policy。

验证含义：

1. token 只能由获得 shared key 的特定 agent pair 解密和使用。
2. $T_{\mathrm{expire}}$ 限制 compromised token 的生命周期。
3. $Q_{\max}$ 限制恶意 agent 在有效期内的最大交互次数。
4. policy 信息把用户定义的 contact rule 加密绑定到后续通信。

## 5. 工程与代码实现视角 (Engineering Perspective)

- **实现**: 论文给出 protocol 和 formal verification 代码，仓库为 [gsiros/saga](https://github.com/gsiros/saga)。
- **形式化验证**: 使用 ProVerif，在 symbolic Dolev-Yao model 下验证 secrecy、authentication 和 reachability；模型包含 DH、签名、对称加密、hash、KDF。
- **agent 实验**: 使用 smolagents，并测试 calendar、email、writing 等 agent-to-agent tasks；LLM backbone 包括 GPT-4.1-mini、Qwen2.5-72B-Instruct 等。
- **攻击评估**: 8 类 adversarial agents，覆盖无 TLS credentials、无 OTK/token、invalid token、metadata impersonation、token reuse、contact policy violation、自复制注册、valid token abuse window。
- **性能**: key operations 多为毫秒级；agent registration provider side 约 212.85ms，contact resolution provider side 约 1.46ms，token validation 小于 1ms 量级。
- **可扩展性**: Agent registration throughput 随 sharders 线性增加；AWS 评估中 7 sharders、24 小时 token lifetime 支持约 260M agents。

## 6. 安全边界与局限

- Provider 是 honest-but-curious，但仍是核心中心化 registry；它观察 metadata 和 traffic patterns。
- 论文假设 TLS、安全 user authentication、人类验证和基础网络 DoS 保护成立。
- 如果用户被 social engineering 修改 contact policy，SAGA 不能自动判定用户意图错误。
- token 能限制 compromised agent 的滥用窗口，但不能在 token 有效期内完全阻止恶意行为。
- 该论文与 ZKP 的关系很弱，适合作为 agent governance/security architecture 阅读，而不是 zk-SNARK 技术路线阅读。
