# DIZK: A Distributed Zero Knowledge Proof System

## 1. 论文元数据 (Metadata)

- **标题**: DIZK: A Distributed Zero Knowledge Proof System
- **作者**: Howard Wu, Wenting Zheng, Alessandro Chiesa, Raluca Ada Popa, Ion Stoica
- **会议**: 27th USENIX Security Symposium, 2018
- **论文链接**: [USENIX 页面](https://www.usenix.org/conference/usenixsecurity18/presentation/wu)
- **本地文件**: `/Users/xsl/Desktop/Obsidian/零知识证明/sec18-wu.pdf`
- **核心关键词**: #zk-SNARKs #DIZK #Groth16 #R1CS #QAP
- **Zotero 追踪建议**:
  - Jens Groth, 2016, *On the Size of Pairing-Based Non-interactive Arguments*。DIZK 直接分布式实现的底层 zkSNARK 协议。
  - Gennaro, Gentry, Parno, Raykova, 2013, *Quadratic Span Programs and Succinct NIZKs without PCPs*。理解 QAP/QSP 这条 SNARK 算术化路线的基础文献。
  - Parno, Gentry, Howell, Raykova, 2013, *Pinocchio: Nearly Practical Verifiable Computation*。DIZK 对比的经典工程化 zk-SNARK 系统，也是 R1CS/QAP 工程语境的重要前置论文。

## 2. 核心摘要 (TL;DR)

DIZK 试图解决传统 zkSNARK prover 和 setup 被单机内存限制卡住的问题：当电路达到千万级 gates 时，libsnark 一类单机系统会超过内存或成本过高。它没有提出全新的证明系统，而是把 Groth 的 pairing-based preprocessing zkSNARK 中最重的 QAP reduction、FFT/Lagrange、多标量乘法等步骤改造成 Apache Spark 上的分布式计算。论文声称 DIZK 可支持十亿级逻辑 gates，约比 prior art 大 $100\times$，prover 成本约 $10\mu s$ per gate，约比 prior art 快 $100\times$，同时 proof 仍为常数大小约 $128B$，verifier 保持单机快速验证。

## 3. 技术原理解析 (Technical Breakdown)

### 算术化 (Arithmetization)

论文采用传统 R1CS 到 QAP 的路线。一个 R1CS instance 写作：

$$\phi=(k,N,M,a,b,c)$$

其中 $k$ 是 public input 个数，$N$ 是变量数，$M$ 是约束数，$a,b,c\in\mathbb{F}^{(1+N)\times M}$ 是三组稀疏矩阵。给定 public input $x\in\mathbb{F}^k$ 和 witness $w\in\mathbb{F}^{N-k}$，构造：

$$z=(1,x,w)\in\mathbb{F}^{1+N}$$

每个约束 $j\in[M]$ 要满足：

$$\left(\sum_{i=0}^{N}a_{i,j}z_i\right)\cdot\left(\sum_{i=0}^{N}b_{i,j}z_i\right)=\sum_{i=0}^{N}c_{i,j}z_i$$

直观地说，左边第一项是 gate 的左输入线性组合，第二项是右输入线性组合，右边是输出线性组合；R1CS 要求每个 gate 都满足“左输入乘右输入等于输出”。

然后 DIZK 沿用 Groth 协议，把 R1CS 归约为 QAP。选取大小为 $M$ 的域子集 $D$，对每个变量索引 $i$，构造多项式 $A_i(X),B_i(X),C_i(X)$，使它们分别插值矩阵 $a,b,c$ 的第 $i$ 行。于是原本 $M$ 个离散约束被打包为一个多项式整除关系：

$$\left(\sum_{i=0}^{N}A_i(X)z_i\right)\cdot\left(\sum_{i=0}^{N}B_i(X)z_i\right)-\sum_{i=0}^{N}C_i(X)z_i=H(X)Z_D(X)$$

其中 $Z_D(X)=\prod_{\alpha\in D}(X-\alpha)$。这句话的计算含义是：如果每个 R1CS 约束在 $D$ 中对应点都成立，那么左侧多项式会在 $D$ 上全部为零，因此必然被 vanishing polynomial $Z_D(X)$ 整除。

DIZK 的核心贡献不在这个算术化本身，而在如何让这些对象在 $N,M$ 达到十亿级时还能被计算。它把大对象表示成 Spark RDD，例如将 R1CS 矩阵表示成记录 $(j,(i,v))$，表示矩阵第 $(i,j)$ 项为 $v$。

### 多项式承诺 (Polynomial Commitment)

这篇论文没有使用现代意义上独立抽象出来的 KZG、IPA 或 FRI polynomial commitment。它分布式实现的是 Groth pairing-based preprocessing zkSNARK：setup 在秘密随机点 $t$ 上评估 QAP 多项式，并把这些评估值编码到 pairing-friendly elliptic curve group 的 CRS/proving key 中。

可以把它理解为“QAP 多项式在隐藏点 $t$ 上的双线性编码检查”，而不是 PLONK/KZG 那种显式 commitment/opening API。安全性由 Groth 协议继承；论文正文没有把安全假设展开成 AGM/ROM 这类现代术语，而是强调它继承 Groth 协议的 correctness 和 security。工程上最重要的安全前提是 preprocessing trusted setup：setup 采样的 $t,\alpha,\beta,\gamma,\delta$ 必须保持秘密，一旦泄露，soundness 会被破坏。

论文实验使用 256-bit Barreto-Naehrig curve，并为了支持十亿级 FFT domain，生成了满足 $p-1$ 可被大 $2^a$ 整除的 BN 曲线，其中论文选择 $a=50$。这说明 DIZK 的工程可扩展性不仅依赖 Spark，还依赖底层曲线阶是否支持足够大的 radix-2 FFT domain。

### 交互协议 (Interactive Oracle Proof, IOP)

DIZK 不是 IOP/FRI/STARK 路线，也不是先设计交互式协议再通过 Fiat-Shamir 变换非交互化的论文。它实现的是 publicly-verifiable preprocessing zkSNARK：setup 生成 proving key $pk$ 和 verification key $vk$，prover 用 $pk,x,w$ 生成 proof $\pi$，verifier 用 $vk,x,\pi$ 输出 accept/reject。

协议交互结构可以概括为：

- setup: 把 R1CS 转成 QAP，在秘密点 $t$ 以及随机数 $\alpha,\beta,\gamma,\delta$ 下生成编码后的 proving key 和 verification key。
- prover: 用 witness 计算 QAP witness $h$，再通过 varMSM 组合 proving key 中的大量 group encodings，输出常数大小 proof。
- verifier: 保持原 Groth verifier 不变，只检查一个 pairing equation，因此可继续用现有 verifier 实现快速验证。

DIZK 分布式化的是 setup 和 prover，不分布式化 verifier。论文明确强调 verifier 简单且快速，实验中直接使用 libsnark verifier，约为 $2ms+0.5\mu s\cdot k$，其中 $k$ 是 R1CS public input 的 field element 数。

### DIZK 的分布式设计主线

DIZK 把 Groth zkSNARK 的重计算拆成三类：

- 大素数域上的多项式算术：FFT、插值、多项式乘除。
- 椭圆曲线群上的多标量乘法：fixMSM 用于 setup，varMSM 用于 prover。
- R1CS 到 QAP 的 instance/witness reduction。

分布式 FFT 采用 Sze 的 MapReduce 风格思路，把大小为 $n$ 的 FFT 拆成两批大小约为 $\sqrt{n}$ 的 FFT，并尽量减少全量 shuffle。Lagrange interpolant evaluation 则利用 domain 是乘法子群这一结构，让每个 executor 只需要拿到随机点 $t$ 和一段 index space，就能局部计算对应的 $L_i(t)$。

MSM 部分的取舍很工程化：varMSM 使用 Pippenger 算法，但实际分布式时没有把 bucket 作为 Spark partition key 做大规模 shuffle，而是将问题均匀切分给 executors，各自本地运行 Pippenger 后再合并结果。fixMSM 使用预计算表；由于 Spark executor/partition 模型不方便共享本地表，DIZK 让 driver 构建 lookup table 并广播给 executors。

QAP reduction 的难点是“稀疏但不均匀”。矩阵整体只有 $O(N+M)$ 个非零项，但某些列或行可能很 dense，朴素 join 会让某些 executor 变成 straggler，甚至超出 heap。DIZK 的解决方案是先轻量识别 dense rows/columns，再用 hybrid job：dense 部分切成多 partition，sparse 部分走普通 join，最后 union 和 reduce。

## 4. 数学公式推导梳理 (Math Walkthrough)

### 公式一：R1CS 到 QAP 的整除关系

核心公式是：

$$\left(\sum_{i=0}^{N}A_i(X)z_i\right)\cdot\left(\sum_{i=0}^{N}B_i(X)z_i\right)=\sum_{i=0}^{N}C_i(X)z_i+H(X)Z_D(X)$$

其中：

- $z=(1,x,w)$ 是完整 assignment。
- $A_i(X),B_i(X),C_i(X)$ 是由 R1CS 三个矩阵的第 $i$ 行插值得到的低度多项式。
- $D$ 是大小为 $M$ 的 evaluation domain，每个点对应一个 R1CS constraint。
- $Z_D(X)=\prod_{\alpha\in D}(X-\alpha)$ 是在 $D$ 上全部为零的 vanishing polynomial。
- $H(X)$ 是 quotient polynomial，它的系数向量就是 QAP witness 中额外的 $h$。

逐步理解：

1. 对任意 $\alpha_j\in D$，$A_i(\alpha_j)=a_{i,j}$，$B_i(\alpha_j)=b_{i,j}$，$C_i(\alpha_j)=c_{i,j}$。也就是说，多项式在第 $j$ 个点上的取值还原第 $j$ 条 R1CS 约束的系数。
2. 把 $X$ 替换成 $\alpha_j$，左侧变成 $\left(\sum_i a_{i,j}z_i\right)\left(\sum_i b_{i,j}z_i\right)$，右侧的 $\sum_i C_i(\alpha_j)z_i$ 变成 $\sum_i c_{i,j}z_i$。
3. 如果 witness 正确，那么每个 $\alpha_j$ 上都有“左乘右等于输出”，所以左侧减去 $\sum_i C_i(X)z_i$ 后，在所有 $\alpha_j\in D$ 上都为 $0$。
4. 一个多项式在 $D$ 上全部为 $0$，等价于它可以被 $Z_D(X)$ 整除，因此存在 $H(X)$ 使整除关系成立。

密码学意义：prover 不再需要逐条把 $M$ 个约束交给 verifier 检查，而是证明一个多项式恒等式在隐藏随机点 $t$ 上成立。若 witness 造假，则对应多项式差值不是 $Z_D(X)$ 的倍数；在随机点 $t$ 上侥幸通过的概率受 Schwartz-Zippel 类思想约束。

### 公式二：Groth verifier 的 pairing check

论文附录图 10 给出的 verifier check 可整理为：

$$e([A_r]_1,[B_s]_2)=e([\alpha]_1,[\beta]_2)+e\left(\sum_{i=0}^{k}x_i[K_i^{vk}(t)]_1,[\gamma]_2\right)+e([K_{r,s}]_1,[\delta]_2)$$

其中：

- $\pi=([A_r]_1,[B_s]_2,[K_{r,s}]_1)$ 是 proof。
- $x_0=1$，$x_1,\dots,x_k$ 是 public input。
- $[K_i^{vk}(t)]_1$ 是 verification key 中与 public input 相关的编码。
- $r,s$ 是 prover 采样的随机数，用来实现 zero knowledge。
- $e:G_1\times G_2\to G_T$ 是双线性 pairing。

逐步理解：

1. $[A_r]_1$ 和 $[B_s]_2$ 编码了 assignment 对 $A(t)$ 和 $B(t)$ 的线性组合，并混入随机项 $r[\delta]_1$ 与 $s[\delta]_2$。
2. pairing 的双线性让 verifier 可以在不知道 witness 的情况下检查“两个隐藏线性组合的乘积”是否与 QAP 关系一致。
3. public input 部分必须单独暴露给 verifier，因此 $\sum_{i=0}^{k}x_i[K_i^{vk}(t)]_1$ 只包含 $x$，不包含 secret witness $w$。
4. $[K_{r,s}]_1$ 把 witness 部分、quotient polynomial 部分和随机性校正项合在一起；如果 prover 没有满足 QAP 的 witness，就无法构造出通过该 pairing equation 的元素。

这条等式背后的关键是“在编码态里做代数检查”。如果 pairing equation 不成立，说明 prover 给出的三个 group elements 不能同时对应一个满足 QAP 的 assignment；如果 setup secret 泄露，则攻击者可能伪造这些编码关系，所以 trusted setup 是该路线的核心风险。

## 5. 工程与代码实现视角 (Engineering Perspective)

DIZK 的工程对象不是普通小电路 SNARK，而是十亿级 R1CS/QAP 工作负载。实际编码时最大的挑战不是 verifier，而是让 setup/prover 中的数组、多项式和 group elements 不落到单机内存里。

主要工程挑战：

- **RDD 数据布局**: R1CS 三个矩阵 $a,b,c$ 以 sparse records 存储，partition size 必须适配 executor heap，否则 join/reduce 很容易爆内存。
- **shuffle 成本**: QAP instance reduction 需要按 column join，QAP witness reduction 需要按 row join；dense columns/rows 会造成 straggler。DIZK 的 hybrid dense/sparse 策略本质上是在避免全局 skewjoin 的复制和 re-key 成本。
- **FFT domain 和曲线选择**: 十亿级约束要求 field 支持足够大的 $2^a$ 阶乘法子群。论文因此生成支持 $a=50$ 的 256-bit BN curve，而不是直接复用当时常见曲线。
- **MSM 热点**: setup 的 fixMSM 和 prover 的 varMSM 是主要 group arithmetic 热点。Pippenger、本地合并、广播预计算表等细节会直接决定性能。
- **trusted setup 操作风险**: setup 也被分布式化了，但这会把“必须保护 secret randomness”的问题带到集群环境。论文承认这比单机更难保护，并指出 MPC ceremony 是否能自然扩展到这种分布式 setup 仍需研究。

现有开源实现：

- 论文称实现基于 Apache Spark，约 $10K$ 行 Java。
- 已确认存在 [scipr-lab/dizk](https://github.com/scipr-lab/dizk) 仓库，README 描述其为 Java library for distributed zero knowledge proof systems，包含 distributed polynomial evaluation/interpolation、Lagrange polynomials、MSM 和 distributed zkSNARK。
- 仓库 README 明确警告它是 academic proof-of-concept prototype，not ready for production use。因此它适合作为研究/复现实验入口，不适合作为生产级证明系统依赖。

与现代工程栈对照：

- 与 `libsnark`/Groth16: DIZK 解决的是单机 prover/setup 的规模瓶颈，但仍继承 circuit-specific trusted setup 和 pairing-based CRS。
- 与 PLONKish/Halo2: PLONKish 系统通常更强调 universal/updatable setup、自定义 gates、lookup、递归友好性和电路工程体验；DIZK 的强项是把 R1CS/QAP/Groth 这条旧路线扩展到超大电路，而不是改善电路表达能力。
- 与 STARK/FRI: STARK 通常透明、基于 hash/FRI、无 trusted setup，但 proof size 较大，verifier/hash 成本模型不同。DIZK 保持 Groth proof 小和 verifier 快的优点，但付出 trusted setup 和 pairing-friendly curve 假设。
- 与 KZG/IPA 承诺系统: DIZK 的 CRS 中隐藏点评估和 pairing check 与 KZG 思路有亲缘性，但论文没有采用现代 polynomial commitment 抽象。若迁移到 PLONK/KZG 语境，setup 通用性和 opening batching 会成为新的中心问题。

## 6. 适合精读的段落

- §2.2: R1CS language and interface。这里是整篇论文的约束系统入口。
- §2.3: Groth protocol background。重点看 R1CS$\to$QAP、bilinear encodings 和图 10。
- §4: Distributed arithmetic。理解为什么 FFT/Lag/MSM 是 setup/prover 的真正瓶颈。
- §5 和 §6: dense column/row hybrid solution。这是 DIZK 相对“直接把 libsnark 搬到 Spark”真正有技术含量的地方。
- §10 和 §13: 实验结果与限制。这里能避免只记住“十亿 gates”而忽视“仍然昂贵、setup 更难保护”的现实约束。

## 7. 一句话定位

DIZK 是一篇“把 Groth16/R1CS/QAP zkSNARK prover 和 setup 扩展到集群规模”的系统论文：它的贡献主要是分布式算法和工程数据流，而不是新的零知识证明安全模型或新的 polynomial commitment。
