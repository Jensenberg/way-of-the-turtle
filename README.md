### 1、Code

* Turtle_Data.py：计算ATR、品种关联性、突破系统指标
* Way_of_Turtle.py：实现海龟交易法则的交易过程

### 2、Data

- **合约**：39个活跃品种的主力合约（包括了五个金融期货）
- **时间**：2008年01月01日至2019年06月15日
- **日收益率**：$r_t = \frac{主合约的收盘价} {同一主力合约前一交易日的收盘价} -1$，必须是同一主力合约
- **主力合约的迁移和价格连续化**：按新主力合约和旧主力合约在合约迁移日的收盘价的价差进行平移
- **交易成本**：交易所手续费 + 一个最小变动单位的滑点

![回测曲线](https://github.com/Jensenberg/way-of-the-turtle/blob/master/data/Way_Of_Turtle.png)

### 3、海龟交易法则（Way of The Turtle)

1. 真实波动幅度（**TR**, True Range）：

   $TR = max(H-L, H-PDC, PDC - L )$

   $H：最高价$

   $L：最低价$

   $PDC：前一日收盘价$

2. 真实波动幅度均值（**ATR**）也称为N：

   $ATR = \frac {19 \times PDN + TR} {20}$

   $PDN：前一日的N值$

   $TR：当日的真实波动幅度$

3. 头寸规模（**unit size**)

   $unit \hspace{2mm} size = \frac{{risk\hspace{2mm}rate} \times Account}{ATR \times Multiplier}$

   $risk \space rate = 0.003$（自行设定，可以调节）

4. 关联市场单方向的限制：

   （1）单个品种**1**个头寸（书中设为4个头寸）

   （2）强关联品种6个头寸

   （3）弱关联10个头寸

   （4）总头寸12个

   **关联性**的衡量是：过去60天的日收益率的相关系数**$\rho = Corr(r_i, r_j) $**

   * 强相关：$0.7 \le\rho \le 1 $
   * 弱相关：$0.4 \le \rho \lt 0.7 $

   例如：

   与品种$A$强相关的集合为：$S_A=\{B, C, D\}$

   与品种$B$强相关的集合为：$S_B=\{A, E\}$

   与品种$C$强相关的集合为：$S_C=\{A, D, F\}$

   与品种$D$强相关的集合为：$S_D=\{A, C, D\}$

   与品种$E$强相关的集合为：$S_E=\{B\}$

   则与$A$强关联的品种为$S_A^*=S_A \cup S_B \cup S_C \cup S_D \ - A = \{B, C, D, E, F\}$

   则与$B$强关联的品种为$S_B^*=S_B \cup S_A \cup S_E -B =\{A, C, D, E\}$

   依次类推；

5. 入市与退出：

   （1）法则1：20日突破进入，10日突破退出；

   （2）法则2：55日突破进入，20日突破退出；

6. **止损**：与最新成交价相比发生了$4\times ATR$的不利变动，也可以尝试换成其他倍数，如$2\times ATR$ 

8. **账户规模调节**：根据盈亏阶梯调整账户规模，每**20%**的变动调整一次

### 4、参考文献
Curtis Faith，海龟交易法则（Way of the Turtle），“尾声：万事俱备”

