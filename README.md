# 海龟交易法则（Way of The Turtle)

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

4. 关联市场单方向的限制：

   （1）单个品种4个头寸（实际设为1个头寸）

   （2）强关联品种6个头寸

   （3）弱关联10个头寸

   （4）总头寸12个

5. 入市与退出：

   （1）法则1：20日突破进入，考虑假突破的情况；10日突破退出；

   （2）法则2：55日突破进入，均为有效突破，20日突破退出；

6. 止损：与最新成交价相比发生了$2N$的不利变动

7. 加仓：每$\frac{1}{2}N$个间隔，加一个头寸

8. 账户规模：根据盈亏阶梯调整账户规模，每20%的变动调整一次

### turtle_simple.py

海龟交易系统的简单版本，仅考虑滑点的影响和开盘价的影响

![Turtle20(0.0030)](E:\GitHub\way-of-the-turtle\Turtle20(0.0030).png)

### turtle_class.py & turtle_complex.py

海龟交易系统的复杂版本，考虑了移动止损，多翻空和空翻多

![Turtle55(0.0050 1 6 2 4)](E:\GitHub\way-of-the-turtle\Turtle55(0.0050 1 6 2 4).png)

### turtle_class_add.py & turtle_complex_add.py

考虑了加仓的情况

