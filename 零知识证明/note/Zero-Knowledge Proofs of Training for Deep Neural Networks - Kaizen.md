# Zero-Knowledge Proofs of Training for Deep Neural Networks - Kaizen

## 1. 论文元数据 (Metadata)

- **标题**: Zero-Knowledge Proofs of Training for Deep Neural Networks
- **作者**: Kasra Abbaszadeh, Christodoulos Pappas, Jonathan Katz, Dimitrios Papadopoulos
- **会议**: CCS 2024
- **论文链接**: [ACM DOI](https://doi.org/10.1145/3658644.3670316)
- **代码**: [zkPoTs/kaizen](https://github.com/zkPoTs/kaizen)
- **核心关键词**: #zkPoT #Kaizen #GKR #IVC #PolynomialCommitment
- **Zotero 追踪建议**:
  - Srinath Setty, 2020, *Spartan: Efficient and General-Purpose zkSNARKs without Trusted Setup*。
  - Benedikt Bünz 等, 2020, *Halo: Recursive Proof Composition without a Trusted Setup*。
  - Srinath Setty, 2021, *Nova: Recursive Zero-Knowledge Arguments from Folding Schemes*。

## 2. 核心摘要 (TL;DR)

Kaizen 试图证明一个深度神经网络确实按照公开的 mini-batch gradient descent 算法、在某个 committed dataset 上训练得到，同时隐藏模型和数据。它为单次梯度下降构造 PoGD，并用 GKR/sumcheck、量化检查、Merkle dataset commitment 和多变量 polynomial commitment aggregation 递归组合所有迭代。最终 proof size 和 verifier time 与训练迭代数、数据集大小无关，VGG-11 约 1000 万参数时每迭代 prover 约 15 分钟，最终 proof 约 1.63MB、verifier 约 130ms。

## 3. 技术原理解析 (Technical Breakdown)

### 算术化 (Arithmetization)

Kaizen 证明的是训练过程，而不是单次 inference。一次 iteration 包含：

1. forward pass；
2. loss 和 backward pass；
3. 梯度平均；
4. 权重更新。

对第 $i$ 次 iteration 和第 $\ell$ 层，权重更新为：

$$W_{i,\ell}=W_{i-1,\ell}-\eta_\ell G_{i,\ell}$$

其中 $G_{i,\ell}$ 是 batch 上的平均梯度。每一步都可表示为 layered arithmetic circuit，但直接把所有 iterations 展成一个大电路会造成线性增长的 prover memory 和 verifier cost。

Kaizen 的 PoGD 使用 GKR/sumcheck；矩阵乘法和 convolution 使用专门的 sublinear sumcheck；ReLU、tanh、Sigmoid、Softmax 和 pooling 用量化后的算术电路和通用 GKR 处理。

### 多项式承诺 (Polynomial Commitment)

Kaizen 使用：

- dataset 的 Merkle root $\rho_D$ 作为 position-binding commitment；
- model weights 的 multilinear extension commitment；
- Orion 作为实验中的多变量 polynomial commitment；
- commitment aggregation 将多次迭代中的多个 commitment/opening 合并。

递归的难点在于 GKR 需要多变量 polynomial opening，而许多已有 aggregation scheme 只适用于单变量 polynomial。Kaizen 提出线性 prover overhead、对 verifier 只有对数级 overhead 的多变量 commitment aggregation。

理论协议还需要 zero-knowledge sumcheck 和 zero-knowledge PCS。论文的当前实现明确没有实现这些 zero-knowledge variants、Orion 完整实现和 aggregation 的全部优化，因此“理论上是 zkPoT”和“公开代码已经完整实现 zkPoT”必须区分。

### 交互协议 (Interactive Oracle Proof, IOP)

单次 PoGD 是 GKR-style interactive proof。Kaizen 再把 baseline verifier 包装成递归 circuit：

$$F_A(i,z_0,z_i,\omega_i,\pi_i)=(z_{i+1},1)$$

第 $i+1$ 次 proof 同时证明：

- 本轮从 $z_i$ 到 $z_{i+1}$ 的 gradient descent 正确；
- 上一轮 proof $\pi_i$ 正确；
- 之前所有 iterations 的递归摘要正确。

实现使用 Fiat-Shamir 生成 sumcheck challenges，并使用 MiMC 等 sumcheck-friendly hash 来降低递归验证成本。为了支持任意多轮，论文实现采用 arity $m=12$ 的 tree-based recursion，而不是只采用线性递归。

## 4. 数学公式推导梳理 (Math Walkthrough)

### 公式一：单次训练 iteration

训练模型的核心关系是：

$$W_i=GD(W_{i-1},B_{i-1})$$

其中 $B_{i-1}$ 是从 committed dataset 中按伪随机位置抽取的 batch。训练证明必须同时检查：

1. batch 中每个数据项确实来自 $\rho_D$；
2. forward/backward 使用的权重和 batch 一致；
3. $G_i$ 是梯度计算和 batch averaging 的结果；
4. 更新后的 $W_i$ 符合学习率 $\eta$。

单次 proof 的 challenge 会把大批量矩阵运算压缩为少数 multilinear polynomial evaluations。这样 prover 仍然要扫描数据和生成 sumcheck messages，但 verifier 不需要重新执行整个训练。

### 公式二：递归组合

递归 proof 可以抽象为：

$$\pi_i=\operatorname{Prove}\left(i,\rho_D,\sigma_{W_0},\sigma_{W_{i-1}},B_{i-1},\pi_{i-1}\right)$$

verifier 最终只接收 $\rho_D$、初始权重 commitment、最终权重 commitment 和 $\pi_i$。递归压缩成立的条件是：

- 每一层只保留上一层 proof 的 succinct digest；
- polynomial commitments 的 opening 被聚合，而不是每轮独立验证；
- dataset batch 通过 Merkle opening 绑定到同一个 $\rho_D$；
- Fiat-Shamir challenge 的 transcript 包含 iteration counter 和 previous proof digest，避免跨轮 replay。

若没有 commitment aggregation，验证每一轮的多变量 polynomial openings 会使 proof size 和 verifier time 随 iteration 数线性增长，失去 zkPoT 的核心目标。

## 5. 工程与代码实现视角 (Engineering Perspective)

- **实现**: 公开代码基于 Virgo++ 的 GKR-style proof 和 Orion commitment；当前实现未完成完整 zero-knowledge variants。
- **参数**: $F_{p^2}$，$p=2^{61}-1$，MiMC-$p^2/p^2$ 与 SHA-256，量化位宽 $q=64$，递归树 arity $12$、depth $4$，最多支持 $12^4=20736$ iterations。
- **VGG-11**: 约 10.1M parameters、batch size 16，每 iteration 约 882 秒，最大内存约 466.3GB，proof size 1.627MB，verifier 130ms。
- **比较**: 对 VGG-11，论文报告 prover 比 Nova 快约 23.7 倍，memory efficiency 约 27 倍；但 generic IVC 的结果部分依赖外推和针对 R1CS 的实现优化，不能当作完全同条件实测。
- **主要热点**: Merkle tree/Orion commitment、递归节点中的 aggregation、非线性量化和 GKR verifier circuit。
- **训练随机性**: 每个 epoch 使用由 hash 派生的 PRP 打乱 dataset，避免 prover 每轮选择有利 batch。
- **部署现实**: proof 虽然与 iterations 无关，但 prover 每迭代仍然很重，且实现需要数百 GB 内存；适合高价值模型 provenance，不适合低延迟训练服务。

与其他路线的 tradeoff：

- 与 Nova/HyperNova 等 R1CS folding IVC 相比，Kaizen 直接利用 GKR/sumcheck 对矩阵和 convolution 做专门优化，减少单轮 prover cost；代价是递归 verifier 和多变量 commitment 更复杂。
- 与 Halo/IPA 类递归相比，Kaizen 的 aggregation 专门适配 multivariate polynomial，不是简单复用 univariate opening aggregation。
- 与通用 zkSNARK 相比，Kaizen 的 proof/verifier 更适合多轮训练，但当前代码的 zero-knowledge 完整性仍是明显工程缺口。
