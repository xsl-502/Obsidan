# zkCNN: Zero Knowledge Proofs for Convolutional Neural Network Predictions and Accuracy

## 1. 论文元数据 (Metadata)

- **标题**: zkCNN: Zero Knowledge Proofs for Convolutional Neural Network Predictions and Accuracy
- **作者**: Tianyi Liu, Xiang Xie, Yupeng Zhang
- **会议**: CCS 2021
- **论文链接**: [ACM DOI](https://doi.org/10.1145/3460120.3485379)
- **核心关键词**: #zkCNN #GKR #Sumcheck #NeuralNetworkZKP #PolynomialCommitment
- **Zotero 追踪建议**:
  - Seunghwa Lee 等, 2020, *vCNN: Verifiable Convolutional Neural Network based on zk-SNARKs*。
  - Feng 等, 2020, *ZEN: An Optimized Zero-Knowledge Proof System for Neural Networks*。
  - Goldwasser, Kalai, Rothblum, 2015, *Delegating Computation: Interactive Proofs for Muggles*，GKR 体系的基础来源。

## 2. 核心摘要 (TL;DR)

zkCNN 试图解决 CNN 模型参数通常是商业机密、但用户又想验证推理确实由指定模型完成的问题。论文使用 GKR/sumcheck 和多变量 polynomial commitment，专门为 FFT、二维 convolution、ReLU 和 max pooling 设计低开销证明，而不是把整个 CNN 展开成巨大 R1CS 电路。实验中 VGG16 的 1500 万参数模型单次 prediction proof 约 88.3 秒，proof size 341KB，verifier time 59.3ms，并支持对同一模型的 20 张图证明 accuracy。

## 3. 技术原理解析 (Technical Breakdown)

### 算术化 (Arithmetization)

zkCNN 把 CNN 表示为 layered arithmetic circuit，但不直接构造所有乘法门，而是使用：

- **MLE**: 将数组、矩阵和每层输出扩展成 multilinear polynomial。
- **GKR**: 从输出层开始逐层把“这一层的输出正确”归约为下一层随机点评估。
- **Sumcheck**: 检查多变量多项式在 Boolean hypercube 上的和。
- **Specialized convolution proof**: 将 convolution 写成 FFT、Hadamard product、IFFT 的组合，直接证明变换关系。
- **Bit decomposition/GKR**: 支持有限域中的 ReLU、max pooling 和量化值。

二维 convolution 可抽象为：

$$U[j,k]=\sum_{\sigma}\sum_{a,b}X[\sigma,j+a,k+b]W[\sigma,a,b]$$

输入通道 $\sigma$、kernel 位置 $(a,b)$ 和输出位置 $(j,k)$ 都被编码为 Boolean index；prover 不需要为每一个乘法门分别提交 commitment。

### 多项式承诺 (Polynomial Commitment)

论文使用支持多变量 polynomial 的 zero-knowledge polynomial commitment。模型参数 $W$ 的 multilinear extension $\widetilde W$ 被 commitment，辅助 bit-decomposition witness 也被 commitment；在 GKR/sumcheck 结束时，verifier 只需检查随机点 opening。

与 vCNN 的区别是：vCNN 通过 QAP/polynomial-QAP 和 pairing-based SNARK 证明 convolution；zkCNN 直接证明 FFT/convolution 的代数关系，减少额外 commitment。论文实现使用 BLS12-381 和 `mcl`，并采用具有较好 prover time 与合理 proof size 的 commitment 方案。

这条路线不是 Groth16 的 constant-size proof：它更接近 interactive oracle proof + PCS。优势是无需数十 GB 的 pairing-based CRS/trusted setup；代价是 proof size 随模型结构和 opening 数增长。

### 交互协议 (Interactive Oracle Proof, IOP)

zkCNN 的主协议是交互式：

1. prover 发送 prediction 和必要的 commitment。
2. verifier 发送 GKR/sumcheck 随机 challenge。
3. 每个 CNN layer 通过一个或多个 sumcheck 归约到随机点评估。
4. 最后一层打开模型、输入和 auxiliary polynomial 的 commitment。

论文以 interactive ZK proof 描述协议；若要做 NIZK，需要把公开随机挑战通过 Fiat-Shamir 编译，并在实现中严格绑定模型 commitment、输入、层编号和每轮 transcript。

## 4. 数学公式推导梳理 (Math Walkthrough)

### 公式一：FFT 关系转成 sumcheck

设 $c=(c_0,\ldots,c_{N-1})$ 是多项式系数，$a$ 是在单位根上的 evaluations，$\omega^M=1$。FFT 关系为：

$$a_j=\sum_{i=0}^{N-1}c_i\omega^{ji}$$

将数组索引写成 Boolean vector 后，论文把它改写成：

$$\widetilde a(y)=\sum_{x\in\{0,1\}^{\log N}}\widetilde c(x)\widetilde F(y,x)$$

其中 $\widetilde F$ 是 Fourier matrix 的 multilinear extension。这样做的关键是把一个看似密集的矩阵向量乘法变成 sumcheck 可处理的多变量求和。

论文进一步利用 Fourier matrix 的结构，避免显式构造 $O(MN)$ 个非零项，使 prover 可以用动态规划 bookkeeping tables 在线性于输入规模的时间生成 sumcheck messages。结果是 FFT proof 的额外 prover time 为 $O(N)$，而普通 FFT 计算本身是 $O(N\log N)$。

### 公式二：GKR 的层间归约

对第 $i$ 层，令 $\widetilde V_i$ 是该层 gate values 的 MLE，$\widetilde{\operatorname{add}}_i$ 和 $\widetilde{\operatorname{mult}}_i$ 是 wiring predicates，则 verifier 检查形如：

$$\widetilde V_i(g)=\sum_{x,y}\left(\widetilde{\operatorname{add}}_i(g,x,y)(\widetilde V_{i+1}(x)+\widetilde V_{i+1}(y))+\widetilde{\operatorname{mult}}_i(g,x,y)\widetilde V_{i+1}(x)\widetilde V_{i+1}(y)\right)$$

步骤含义：

1. verifier 已知当前层随机点 $g$ 和目标值 $\widetilde V_i(g)$。
2. sumcheck 将右侧的高维求和压缩到随机点 $(u,v)$。
3. verifier 根据 wiring predicate 自己计算 gate 连接关系。
4. prover 只需打开下一层的 $\widetilde V_{i+1}(u)$ 和 $\widetilde V_{i+1}(v)$。
5. 重复直到 input layer，再用 polynomial commitment 检查 input/model 的一致性。

若某层计算错误，则对应多项式在随机点不一致；sumcheck 的 soundness error 约为低度与变量数除以有限域大小。

## 5. 工程与代码实现视角 (Engineering Perspective)

- **实现**: C++，约 5000 行；基于已有 GKR/sumcheck 开源实现，使用 `mcl` 处理 BLS12-381 field/curve。
- **并行性**: 论文实现未并行化，VGG16 最大内存约 24GB；这说明算法结构高效，但仍然是重型 prover。
- **VGG16**: 15M parameters，prediction proof 88.3s，proof size 341KB，verifier 59.3ms。
- **多图 accuracy**: 20 images 的 proof size 约 635KB，verifier time 121ms，利用相同模型参数只证明一次相关结构。
- **量化**: 使用 8-bit integer 量化；ReLU、max pooling 和 bit decomposition 是非线性层的主要工程成本。
- **代码参考**: 论文明确使用了既有开源 GKR/PCS 实现，并比较了 [vCNN](https://github.com/snp-labs/VCNN) 与 [ZEN](https://github.com/UCSB-TDS/ZEN)；本文自身代码地址在论文正文中未明确给出。

路线 tradeoff：

- 与 pairing-based vCNN 相比，zkCNN 的 convolution proof 直接利用 FFT 结构，不需要额外 commitment convolution result，prover 更快。
- 与 Groth16/PLONK 相比，zkCNN proof 更大、需要交互式 sumcheck/PCS，但避免了巨大 circuit 和 trusted setup。
- 与后来的 Brakedown/FRI-style systems 相比，zkCNN 的重点是 CNN 结构专用优化，而不是通用透明 SNARK。
