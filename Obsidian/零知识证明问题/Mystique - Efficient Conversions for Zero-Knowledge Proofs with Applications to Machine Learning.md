# Mystique: Efficient Conversions for Zero-Knowledge Proofs with Applications to Machine Learning

## 1. 论文元数据 (Metadata)

- **标题**: Mystique: Efficient Conversions for Zero-Knowledge Proofs with Applications to Machine Learning
- **作者**: Chenkai Weng, Kang Yang, Xiang Xie, Jonathan Katz, Xiao Wang
- **会议**: USENIX Security 2021
- **论文链接**: [USENIX 页面](https://www.usenix.org/conference/usenixsecurity21/presentation/weng)
- **核心关键词**: #sVOLE #MPCinTheHead #ZKML #Rosetta #AuthenticatedValues
- **Zotero 追踪建议**:
  - Weng 等, 2020, *Wolverine: Fast, Scalable, and Communication-Efficient Zero-Knowledge Proofs for Boolean and Arithmetic Circuits*。
  - Weng 等, 2021, *Rosetta: A Privacy-Preserving Framework Based on TensorFlow*。
  - Yang 等, 2020, *FLASH: Fast and Memory-Efficient Zero-Knowledge Proofs for Boolean Circuits*。

## 2. 核心摘要 (TL;DR)

Mystique 试图解决真实神经网络同时包含 arithmetic、Boolean、fixed-point 和 floating-point 运算，而现有 sVOLE-based ZK 往往只擅长其中一种表示的问题。它提供 arithmetic/Boolean、public commitment/private authentication、fixed-point/floating-point 三类转换，并为矩阵乘法设计低于朴素乘法复杂度的 ZK 协议，再集成到 TensorFlow/Rosetta。实验中可证明私有 ResNet-101 inference，private model/private input 约 28 分钟，public model/private input 约 5 分钟，CIFAR-10 accuracy 下降约 0.02%。

## 3. 技术原理解析 (Technical Breakdown)

### 算术化 (Arithmetization)

Mystique 不是 R1CS/QAP 型 preprocessing SNARK，而是基于 sVOLE 的 interactive ZK protocol。值在有限域上以 authenticated wire value 表示，协议可以在 arithmetic circuit 和 Boolean circuit 之间切换。

三类核心转换：

- **A2B/B2A**: arithmetic value 与 bit vector 之间转换。
- **C2A**: public commitment value 转为 prover/verifier 私下都认证的 value。
- **Fix2Float/Float2Fix**: 有限域 fixed-point 编码与 IEEE-754 floating-point circuit 之间转换。

### 多项式承诺 (Polynomial Commitment)

本文没有以 polynomial commitment 为中心，而是以 sVOLE、IT-MAC 和 authenticated values 为中心。public commitment 可以通过 hash/PRF/commitment 转成 privately authenticated value，再直接进入 sVOLE-based ZK execution。

因此安全模型更接近 UC security in the $F_{\mathrm{authZK}}$-hybrid model，而不是 KZG/IPA/FRI 的 commitment opening 安全模型。主要假设包括：

- hash 作为 random oracle；
- PRF 安全；
- sVOLE/IT-MAC 功能正确；
- 统计安全参数 $\rho$ 与计算安全参数 $\lambda$ 足够大。

### 交互协议 (Interactive Oracle Proof, IOP)

Mystique 的协议是两方交互式 ZK：

- prover 拥有私有模型或输入；
- verifier 拥有 private authenticated key/material；
- 双方通过 sVOLE correlation 和 circuit-based commands 计算；
- 每个 operator 输出新的 authenticated value；
- 最终 verifier 得到结果或验证关系成立。

没有 Fiat-Shamir 作为核心步骤，因为论文目标是 interactive two-party ZK 和 UC composition，而不是 public-verifiable NIZK。

## 4. 数学公式推导梳理 (Math Walkthrough)

### 公式一：arithmetic/Boolean conversion

对有限域元素 $x\in F_p$，prover 提供 bit decomposition：

$$x=\sum_{i=0}^{m-1}x_i2^i\pmod p$$

并证明：

$$x_i(x_i-1)=0,\quad\forall i\in[0,m)$$

第一组等式保证每个 $x_i$ 是 bit；第二个等式保证这些 bit 重新编码后就是原始 authenticated value $x$。

Mystique 使用 zk-edaBits 预处理随机 bits，避免每次都用完整 arithmetic circuit 检查 bit decomposition。这样 Boolean layer 可以使用 XOR/AND，arithmetic layer 可以使用 ADD/MULT，而转换成本主要由预处理和通信带宽决定。

### 公式二：矩阵乘法的随机检查

要证明 $C=A\cdot B$，协议使用 Freivalds-style random projection。verifier 采样随机向量 $u,v$，prover 证明：

$$u^\top C v=u^\top A B v$$

如果 $C\ne AB$，令差矩阵 $D=C-AB\ne0$，则随机 $u,v$ 使 $u^\top Dv=0$ 的概率很小。这样不用逐项证明 $m^3$ 个乘法，只需证明少量向量/矩阵乘法和 authenticated linear combinations。

论文进一步把随机向量生成和 key-dependent computation 预处理化，使 communication 从依赖完整矩阵维度的形式降到与随机投影向量相关的规模；实测相比先前矩阵乘法 ZK 协议约 7 倍提升。

## 5. 工程与代码实现视角 (Engineering Perspective)

- **实现**: C++ ZK backend，集成 TensorFlow/Rosetta，前端仍可用 Python 写模型。
- **安全参数**: $p=2^{61}-1$，计算安全参数 $\lambda=128$，统计安全参数 $\rho\ge40$。
- **模型**: LeNet-5、ResNet-50、ResNet-101，后者约 42.5M parameters、101 layers。
- **主要瓶颈**: Batch Normalization、ReLU、convolution、fixed/floating-point conversion；ResNet-101 中 BatchNorm 约占大量总时间。
- **矩阵乘法**: 512、1024、2048 维约分别为 185ms、1.4-1.5s、约 11s；比已有 1024 维方案约 7 倍快。
- **端到端**: ResNet-101 private model/private input 约 28 分钟，public model/private input 约 5 分钟，private benchmark 场景可达数小时。
- **框架**: Rosetta 支持把 ZK、MPC、HE 混合进 TensorFlow graph；论文给出了 [Rosetta repository](https://github.com/LatticeX-Foundation/Rosetta) 作为工程入口。

路线 tradeoff：

- 与 zk-SNARK 相比，sVOLE ZK prover 更贴近真实 mixed-mode ML，但通信量大、通常只能面向单个 verifier。
- 与 MPC-in-the-head/garbled circuits 相比，authenticated arithmetic 对大矩阵更友好，但需要复杂 preprocessing。
- 与 GKR/PCS 路线相比，Mystique 不追求 polylog proof，而是追求在两方 private inference 中降低 conversion 和 communication。
