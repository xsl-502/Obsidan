# ZKML 与 Agent Security 论文阅读索引

## 综合设计文档

- [[IDEAL - zk-SNARK Agent 安全治理架构]]
  - 基于下列论文综合出的现实可行方案，重点是 zk-SNARK + agent tool-use attestation + 大模型安全治理。

## ZKML 主线

建议按以下顺序读：

1. [[DIZK - A Distributed Zero Knowledge Proof System]]
   - 理解传统 R1CS/QAP/Groth 路线在大规模计算上的 setup/prover 瓶颈。
2. [[Mystique - Efficient Conversions for Zero-Knowledge Proofs with Applications to Machine Learning]]
   - 理解真实 ML 系统为什么需要 arithmetic/Boolean/floating-point/fixed-point 转换。
3. [[zkCNN - Zero Knowledge Proofs for Convolutional Neural Network Predictions and Accuracy]]
   - 理解 GKR/sumcheck 如何利用 CNN 的 convolution/FFT 结构证明推理。
4. [[Zero-Knowledge Proofs of Training for Deep Neural Networks - Kaizen]]
   - 理解从 proving inference 到 proving training 的跨度，以及 IVC/递归组合的必要性。
5. [[FAIR ZK - A Scalable System to Prove Machine Learning Fairness in Zero-Knowledge]]
   - 理解不证明逐样本推理、转而证明模型级 fairness bound 的新思路。

## Agent Security 支线

这两篇不是 ZKP 论文，但与 AI agent 安全治理相关：

1. [[SAGA - A Security Architecture for Governing AI Agentic Systems]]
   - 身份、注册、Provider、OTK、access control token、ProVerif。
2. [[Cloak Honey Trap - Proactive Defenses Against LLM Agents]]
   - 针对 LLM attack agents 的 deception、honeypot、trap 和 CHeaT 工具。

## 快速对比

| 论文 | 核心对象 | 证明/安全路线 | 主要瓶颈 |
|---|---|---|---|
| DIZK | 大规模 R1CS/Groth prover | QAP + pairing zkSNARK | 分布式 FFT/MSM/QAP reduction |
| Mystique | 神经网络推理 | sVOLE interactive ZK | 类型转换、BatchNorm、通信 |
| zkCNN | CNN prediction/accuracy | GKR + sumcheck + PCS | convolution/FFT、ReLU、pooling |
| Kaizen | DNN training provenance | GKR + IVC + PCS aggregation | 递归、Orion commitments、内存 |
| FAIR ZK | ML fairness | GKR + sumcheck + Brakedown | spectral norm、lookup、proof size |
| SAGA | agent governance | signatures/DH/TLS/tokens | Provider scalability、policy management |
| Cloak/Honey/Trap | LLM attack agents | empirical deception defense | adaptive adversaries、deployment hygiene |
