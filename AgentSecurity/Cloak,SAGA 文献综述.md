<h1>综述：Agent Security 文库</h1><p>由 Codex 根据本地 Zotero 文献整理生成。正文保留 Markdown 引用键。</p><pre># Agent Security 文库综述：从身份治理到可验证自主执行

## Introduction

大模型 Agent 的安全风险来自其自主性和外部行动能力。与传统聊天模型不同，Agent 会规划任务、调用工具、访问本地或云端资源，并与其他 Agent 通信；因此，安全问题不再局限于模型输出内容，而是扩展到身份、授权、通信、工具调用、状态管理和跨组织协作 [@MWDGQAZZ]。SAGA 明确指出，安全 Agent 系统需要支持唯一身份、认证、发现、安全通信、用户生命周期控制和细粒度访问控制 [@MWDGQAZZ]。Cloak, Honey, Trap 则从攻防角度展示，自动化 LLM Agent 在渗透测试和网络攻击场景中会被误导信息、伪凭证、上下文噪声和 token 异常影响，因而既是威胁主体，也是可被主动防御机制利用的对象 [@Z7L3K9NA]。

在“零知识证明与 Agent Security”的交叉视角下，ZKP 并不是现有 Agent 安全系统的主流组件。SAGA 的核心是传统密码协议、Provider-mediated registry、one-time keys、Diffie-Hellman 派生密钥和 access control token，而非零知识证明 [@MWDGQAZZ]。Cloak, Honey, Trap 的核心是 deception、honeytoken、trap 和对 LLM 行为弱点的利用，也不依赖 ZKP [@Z7L3K9NA]。因此，本综述将 Agent Security 文献作为威胁与系统需求基础，并将 ZKP 文献作为可验证性增强方向来分析。

## Background

Agent Security 的威胁图景可划分为三层。第一层是输入与上下文攻击：Agent 会把网页、日志、文件名、服务 banner、工具输出和用户消息纳入上下文，攻击者或防御者均可通过这些数据点影响其后续计划 [@Z7L3K9NA]。第二层是工具调用越权：Agent 一旦错误解释环境信息，就可能执行扫描、SSH、邮件、文件读写、API 调用等真实操作，造成安全后果 [@Z7L3K9NA]。第三层是跨 Agent 协作风险：恶意 Agent 可通过冒充、非法联系、token 重放、策略绕过或大量复制身份影响其他 Agent，SAGA 对这些行为给出明确攻击模型并在协议层进行处理 [@MWDGQAZZ]。

从防御机制看，SAGA 偏向“治理与访问控制”：用户注册 Agent，Provider 维护用户和 Agent registry，接收方 Agent 通过用户定义的 Access Contact Policy 控制谁能联系自己，communication token 用过期时间和请求 quota 限制滥用窗口 [@MWDGQAZZ]。Cloak, Honey, Trap 偏向“主动诱捕与对抗”：防御者预先在环境中植入 cloak、honey 和 trap payload，使恶意 LLM Agent 被误导、暴露或停止 [@Z7L3K9NA]。前者建立制度化边界，后者利用攻击型 Agent 的行为脆弱性。

## Taxonomy &amp; Deep Dive

### 1. 身份、发现与跨 Agent 授权

SAGA 的核心贡献是将 Agent 安全从抽象原则推进到可实现协议。其系统目标包括用户管理 Agent 生命周期、用户策略控制 Agent 访问、有限信任、可扩展性、限制恶意 Agent 影响范围和保持任务效用 [@MWDGQAZZ]。协议上，SAGA 使用 Provider 做注册和发现，但让后续 Agent 通信经 TLS 直接进行；access control token 由接收方 Agent 加密给发起方，并绑定过期时间与请求次数，从而减少 Provider 在线负担并限制被攻陷 Agent 的滥用窗口 [@MWDGQAZZ]。

SAGA 的优势是安全语义清晰、实现和评估完整。其形式化验证使用 ProVerif，在 Dolev-Yao 攻击者模型下证明 token secrecy、Agent 与 Provider 认证、Agent 间认证等属性；攻击评估覆盖无证书连接、无 token 联系、invalid token、metadata impersonation、token 重用、违反 contact policy、恶意注册和 valid-token abuse 等场景 [@MWDGQAZZ]。性能上，SAGA 报告最快 calendar task 中协议开销低于端到端成本的 0.6%，Provider 在 10 sharders 与 24 小时 token lifetime 下可支持约 3 亿活跃 Agent，AWS 7-sharder 实验中约为 2.6 亿 [@MWDGQAZZ]。

但 SAGA 的局限也很明确：它依赖 Provider 作为中心化治理实体，虽然可通过 RAFT 和 sharding 扩展，但跨组织或弱信任环境仍需身份服务和离线身份核验假设 [@MWDGQAZZ]。此外，SAGA 不提供零知识属性凭证：Agent 不能在隐藏具体身份或组织关系的同时证明“我属于某授权集合”或“我满足某权限属性” [@MWDGQAZZ]。因此，zk-DID/zk-Credentials 与 SAGA-style access control 的结合，是当前文库显示出的直接研究空白。

### 2. 输入操纵、诱捕与主动防御

Cloak, Honey, Trap 把 Agent 安全问题从“防止模型被 prompt injection”扩展到“利用 LLM Agent 的系统性弱点做主动防御”。该工作提出 6 类策略和 15 种技术，核心机制包括用 misdirection 隐藏关键资产、用 honeytoken 区分 LLM 和人类、用 trap 使 Agent 进入循环、扩大搜索空间或执行防御者准备的诱饵路径 [@Z7L3K9NA]。其威胁模型把防御者和攻击 Agent 建模为 Stackelberg game：防御者先在环境数据点中布置 payload，攻击 Agent 后续通过工具收集这些数据并据此规划 [@Z7L3K9NA]。

与 SAGA 相比，这一路线不保证形式化访问控制，而是改变攻击 Agent 的信息环境。实验上，论文在 11 个 CTF machines 上对黑盒假设下的攻击 Agent 防御达到 100% success rate，并显示即使采用 hardened system prompt、输入预处理、上下文加入已知防御信息或 fine-tuning，adaptive adversary 也会面临高 false positive rate 或防御绕过问题 [@Z7L3K9NA]。这说明 Agent 安全不能只依赖 prompt-level mitigation；工具输出、任务记忆和上下文检索质量同样是攻击面 [@Z7L3K9NA]。

该方向的局限在于语义上更经验化。Cloak/Honey/Trap 能证明在特定 Agent、模型和 CTF 环境中有效，但其防御成功依赖模型行为偏置和攻击自动化程度；论文也指出如果人类攻击者中途介入，防御效果会转化为增加调试成本，而不是严格阻止攻击 [@Z7L3K9NA]。因此，它适合作为运行时检测和延迟层，而不应替代身份、授权和审计机制。

### 3. ZKP 对 Agent Security 的赋能场景

第一类赋能是可信推理证明。若 Agent 调用私有模型做分类、风险评分或工具选择，zkCNN 和 Mystique 可提供“输出由承诺模型正确计算”的证明，而无需公开模型参数 [@6TLEUB7G; @U9FM7YHK]。但当前性能仍更适合高价值、低频或异步验证任务：zkCNN 的 VGG16 prover time 为 88.3 秒，Mystique 的 ResNet-101 私有模型推理证明为 28 分钟 [@6TLEUB7G; @U9FM7YHK]。

第二类赋能是模型 provenance 与合规证明。Kaizen 可用于证明 Agent 模型按承诺数据集和训练过程生成，适合供应链、版权和模型所有权证明 [@VISC9A95]。FAIRZK 可用于证明模型满足公平性界限，适合金融、医疗和公共服务 Agent 的审计 [@N2T72PVW]。不过，FAIRZK 的公平性语义仍需与具体治理要求对齐，不能把形式化界限直接等同于现实公平 [@N2T72PVW]。

第三类赋能是可验证 workflow。Agent workflow 可被视为状态机：每一步包含输入、计划、工具调用、返回值、权限检查和状态更新。Jolt 等 zkVM 路线可把工具执行轨迹表示为 VM execution proof，lookup arguments 可用于权限表、范围检查和指令约束，folding/IVC 可把多步流程压缩为最终可验证状态 [@8ISXM5Y2; @45G2X7UA; @PE7TRYZJ; @7RPCRUQD; @JLZNJY6Y; @PEEA6I9F]。当前文库中尚未出现完整实现这一目标的 Agent 系统，因此这仍属于未来方向。

### 4. 技术权衡：低延迟治理 vs 强可验证性

Agent 安全系统需要处理不同时间尺度。SAGA 的 access control token 和 Provider lookup 是低延迟在线机制，适合每次跨 Agent 通信前执行 [@MWDGQAZZ]。Cloak/Honey/Trap 是预部署机制，几乎不增加正常交互中的密码计算开销，但其效果依赖攻击 Agent 是否接触诱饵数据 [@Z7L3K9NA]。ZKP 则提供更强的可验证性和隐私保证，但当前 prover cost 明显更高 [@6TLEUB7G; @U9FM7YHK; @VISC9A95]。

因此，合理架构并不是把每个 Agent 动作都同步放进 ZKP，而是分层组合：在线路径使用 SAGA-style identity and token control，运行时防御使用 honey/trap 检测异常 Agent，高价值或事后审计路径使用 ZKP 证明模型、策略或 workflow trace 的关键性质 [@MWDGQAZZ; @Z7L3K9NA; @VISC9A95]。对于长流程任务，可用 folding/IVC 逐步累计证明，降低 verifier 负担；对于工具调用策略，可用 lookup/zkVM 编码权限表和执行轨迹 [@7RPCRUQD; @JLZNJY6Y; @8ISXM5Y2; @PE7TRYZJ]。

## Challenges &amp; Future Directions

第一，Agent 安全文献与 ZKP 文献之间尚未真正融合。SAGA 没有使用 ZKP，Cloak/Honey/Trap 也不是可证明安全框架；ZKP 文献则主要关注 ML 或底层 proof system，而不是 Agent runtime policy [@MWDGQAZZ; @Z7L3K9NA; @6TLEUB7G; @VISC9A95]。

第二，prompt/context 攻击难以形式化为 ZK relation。ZKP 擅长证明确定性计算和明确约束，而 prompt injection、诱导性日志、伪凭证和上下文噪声涉及模型语义与概率行为 [@Z7L3K9NA]。未来需要把“可证明部分”限定为输入来源、解析规则、权限检查和工具调用状态，而不是试图直接证明模型没有被操纵。

第三，隐私授权机制仍缺位。当前 Agent governance 多依赖身份注册、token 和中心化 Provider [@MWDGQAZZ]。未来可研究零知识属性凭证，使 Agent 能证明自己属于某组织、拥有某 delegation scope 或满足某合规要求，同时不披露不必要身份信息。

第四，可验证 workflow 需要工程抽象。Agent trace 往往包含自然语言、API 结果、文件内容和非确定性模型输出。要使用 zkVM 或 folding 证明，需要先定义可复现的事件日志、确定性工具适配层、策略 DSL 和承诺格式；否则 ZKP 难以覆盖真实 Agent 行为 [@8ISXM5Y2; @7RPCRUQD; @JLZNJY6Y]。

## Conclusion

现有 Agent Security 文库表明，当前最成熟的方向是身份治理、访问控制和主动诱捕防御：SAGA 提供低延迟、可扩展且形式化验证的跨 Agent 通信控制，Cloak/Honey/Trap 展示了针对恶意 LLM Agent 的实用主动防御策略 [@MWDGQAZZ; @Z7L3K9NA]。ZKP 在该领域的角色尚处于基础设施和未来集成阶段：它能够增强模型推理、训练来源、合规属性和 workflow trace 的隐私保持可验证性，但还缺少面向 Agent runtime 的端到端系统 [@6TLEUB7G; @U9FM7YHK; @VISC9A95; @N2T72PVW; @8ISXM5Y2]。

因此，下一阶段研究应从“Agent governance + verifiable execution”出发，把 SAGA-style 身份授权、Cloak/Honey/Trap-style 运行时防御、zkML provenance proof、zkVM trace proof 和 folding-based workflow proof 统一到可部署架构中。

</pre>