# FAIR ZK: A Scalable System to Prove Machine Learning Fairness in Zero-Knowledge

## 1. 论文元数据 (Metadata)

- **标题**: FAIR ZK: A Scalable System to Prove Machine Learning Fairness in Zero-Knowledge
- **作者**: Tianyu Zhang, Shen Dong, O. Deniz Kose, Yanning Shen, Yupeng Zhang
- **版本**: arXiv:2505.07997v2, 2025 年 5 月 19 日
- **论文链接**: [arXiv:2505.07997](https://arxiv.org/abs/2505.07997)
- **代码**: [FairZK](https://github.com/tnyuzg/FairZK)
- **核心关键词**: #zk-SNARKs #MLFairness #GKR #Sumcheck #Brakedown
- **Zotero 追踪建议**:
  - Chenkai Weng 等, 2021, *Mystique: Efficient Conversions for Zero-Knowledge Proofs with Applications to Machine Learning*。
  - Srinath Setty, 2020, *Spartan: Efficient and General-Purpose zkSNARKs without Trusted Setup*。
  - O. Deniz Kose and Yanning Shen, 2024, *FairGAT: Fairness-Aware Graph Attention Networks*，用于理解本文公平性界的来源和演进。

## 2. 核心摘要 (TL;DR)

FAIR ZK 试图解决模型所有者想证明机器学习模型具有公平性、但又不能公开模型参数和完整数据集的问题。它不对每个测试样本重复证明模型推理，而是利用模型参数和数据的聚合统计量推导公平性上界，再用 GKR/sumcheck、lookup arguments 和多变量 polynomial commitment 证明这个上界。实验中，FAIR ZK 在单 CPU 上支持 4700 万参数的 DNN，证明时间约 343 秒，并在多个数据集和模型上显著超过逐样本 inference proof 与 OATH 基线。

## 3. 技术原理解析 (Technical Breakdown)

### 算术化 (Arithmetization)

本文不是传统 Groth16/R1CS 电路，而是 GKR-style zkSNARK：

- 用 multilinear extension 将向量、矩阵和层输出表示成多变量多项式。
- 用 sumcheck 证明大规模求和、矩阵乘法和逐层递推。
- 用 lookup arguments 证明量化值、绝对值、截断误差和最大值位于合法范围。
- 用额外的 polynomial commitment 在随机点打开模型权重、辅助 witness 和中间多项式。

设二分类模型的两个敏感群为 $S_0,S_1$，输入特征均值差为：

$$\delta_{x,i}=\operatorname{mean}(x_{j,i}\mid s_j=0)-\operatorname{mean}(x_{j,i}\mid s_j=1)$$

设每个群内第 $i$ 个特征距离群均值不超过 $\Delta_{x,i}$，则 $\Delta_x$ 是输入数据的聚合范围信息。FAIR ZK 的关键思路是：只要模型参数 $W$ 和这些聚合统计量满足一个公开关系，就能给出对所有输入的 fairness bound，而不需要逐条证明所有样本的推理。

### 多项式承诺 (Polynomial Commitment)

实验使用 Brakedown 作为多变量 polynomial commitment。它不是 KZG pairing commitment，而是基于线性纠错码和 hash 的承诺路线；论文选择它主要因为 prover efficiency，而不是 proof size。

本文没有把安全假设展开成 AGM/ROM 形式，而是基于 GKR、sumcheck、lookup 和 PCS 的标准组合安全性。工程上需要特别注意：

- Brakedown 的 proof size 在本文实验中较大，通常为数百 MB 到超过 1 GB。
- proof size 的主因是底层纠错码距离和多变量 opening，而不是 fairness bound 本身。
- 若切换到其他兼容多变量多项式的承诺方案，proof size 和 verifier time 可能改善，但 prover tradeoff 会变化。

### 交互协议 (Interactive Oracle Proof, IOP)

基础协议是公开随机挑战的 sumcheck/GKR 交互式证明：

1. prover 声明一个多变量多项式求和或随机点评估等式。
2. verifier 逐轮发送随机 challenge。
3. prover 将 $k$ 变量求和递归降为一个随机点上的低度多项式值。
4. 最后 verifier 通过 PCS opening 检查模型和辅助 witness 的一致性。

这些公开随机挑战可以用 Fiat-Shamir 变换编译为非交互式证明，但本文的实验重点是 GKR/PCS 后端的具体 prover、proof size 和 verifier 成本；不要把它误读成一个新的 Fiat-Shamir 变换。

### 公平性界

对 logistic regression，模型为 $z=\langle w,x\rangle$，sigmoid 的 Lipschitz 常数取 $L=0.25$。论文得到：

$$\delta_{\hat y}\le L|\langle w,\delta_x\rangle|+2L\langle|w|,\Delta_x\rangle$$

第一项描述两组输入均值差异经过模型权重后的传播；第二项描述每组内部输入波动经过权重放大后的保守误差。

对 DNN，论文按层递推：

$$\|\delta h^\ell\|_2\le L\|W^{\ell-1}\|_2\|\delta h^{\ell-1}\|_2+2L\|\Delta_z^\ell\|_2$$

$$\Delta_z^\ell\le L|W^{\ell-1}|\Delta_z^{\ell-1}$$

其中 $\|W^{\ell-1}\|_2$ 是 spectral norm，$\Delta_z^\ell$ 表示第 $\ell$ 层 pre-activation 在两个群内的最大偏差向量。输出层的 disparity 就是最终 fairness score。

## 4. 数学公式推导梳理 (Math Walkthrough)

### 公式一：logistic regression fairness score

令 $z_j=\langle w,x_j\rangle$，两个群的线性输出均值差为：

$$\bar z^{(0)}-\bar z^{(1)}=\langle w,\delta_x\rangle$$

推导步骤：

1. 线性模型把输入均值的差异直接映射为权重与均值差的内积。
2. 由于 $|\sigma(a)-\sigma(b)|\le L|a-b|$，sigmoid 后的群体差异最多被 $L$ 倍放大。
3. 数据不是只取均值，实际样本还可能偏离群均值；用 $\Delta_x$ 上界每个特征偏差。
4. 三角不等式和绝对值给出 $2L\langle|w|,\Delta_x\rangle$ 的误差项。

密码学意义：prover 不需要把每个样本的 $\sigma(\langle w,x_j\rangle)$ 都放进 witness，只需证明 $w$ 的 commitment 与该上界计算一致。

### 公式二：spectral norm 的证明

对于权重矩阵 $W$，令 $A=W W^\top$。论文让 prover 提供特征分解的近似：

$$A=V\Lambda V^\top+E$$

并额外证明：

$$V V^\top=I+E'$$

其中 $E,E'$ 通过 lookup argument 被限制在小误差表 $T_{\mathrm{err}}$ 中。

验证逻辑：

1. 检查每个 $v_i$ 的范围和归一化，避免 prover 提供零向量。
2. 检查 $V V^\top\approx I$，保证 eigenvectors 足够正交，防止重复提交同一个 eigenvalue/eigenvector。
3. 用 sumcheck 检查 $W W^\top=V\Lambda V^\top+E$，但不在 zk 电路中显式构造 $A$。
4. 对 $\lambda$ 使用 maximum gadget 得到 $\lambda_{\max}$。
5. 检查 $\|W\|_2^2=\lambda_{\max}+e$，最后对 $\lambda_{\max}+e$ 开平方。

如果省略正交性检查，恶意 prover 可以重复使用同一个 eigenpair，使 maximum gadget 看到的最大值不对应真实矩阵的最大特征值；如果省略误差表约束，量化误差就可能被用来伪造谱范数。

## 5. 工程与代码实现视角 (Engineering Perspective)

- **实现**: Rust，约 12,400 行；域运算基于 Arkworks，sumcheck 使用库实现，PCS 参考 Brakedown 实现。
- **实验环境**: M3 MacBook Air，16GB 内存，单 CPU core，实验实现为 serialized prover。
- **大模型结果**: 808K 参数约 3.48 秒；25M 参数约 51.32 秒；47M 参数约 342.74 秒，proof size 约 1175MB，verifier time 约 15.77 秒。
- **主要热点**: spectral norm、lookup table、量化和截断、multilinear polynomial opening。
- **模型泄漏**: verifier 会知道模型层数、矩阵维度和 activation 类型；若这些信息也敏感，需要用 dummy layers/neurons padding。
- **精度问题**: real number 被编码进有限域，谱分解和 eigenvector 只能近似满足，需要显式 error terms。
- **代码复现**: 论文给出 [FairZK GitHub](https://github.com/tnyuzg/FairZK)。需要注意，论文结果是在单核环境完成的，不能直接等同于 GPU/并行部署性能。

与其他路线的 tradeoff：

- 与逐样本 inference proof 相比，FAIR ZK 证明的是模型级 fairness bound，牺牲了 bound 的紧度，换来与数据集规模弱相关的 prover cost。
- 与 Groth16/KZG 相比，Brakedown 路线避免 pairing/trusted setup 依赖，但 proof size 显著更大。
- 与 STARK/FRI 类系统类似，本文更依赖 hash/纠错码和多变量 oracle；其主要瓶颈从 MSM/FFT 转移到大型 commitment/opening。

## 6. 论文限制

- fairness score 是上界，不等于真实 fairness metric；论文也承认不同架构之间需要归一化或 reference score。
- 当前重点是 logistic regression 和 fully-connected DNN，attention network 等模型留作未来工作。
- proof size 仍然很大，限制了链上或带宽敏感部署。
- 证明输入聚合统计量的正确性需要额外的 dataset-statistics zkSNARK。
