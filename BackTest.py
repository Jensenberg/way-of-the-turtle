# -*- coding: utf-8 -*-
"""
Created on Fri Apr  5 17:16:19 2019

@author: 54326
"""
from math import sqrt
import pandas as pd
import matplotlib.pyplot as plt

def drawdown(nav):
    """
    根据净值序列计算回撤序列，返回名称为drawdown的pd.Series
    nav: series
        净值序列     
    """
    DD = [0]
    for i in range(1, len(nav)):
        max_i = max(nav[:i])
        DD.append(min((nav[i] - max_i) / max_i,  0))
    dd = pd.Series(DD, index=nav.index, name='drawdown')
    return dd

def evaluate(port_ret, retn_col='retn', nav_col='nav', rf=0.00, Tdays=242):
    """
    计算最大回撤，最长回撤期，年化收益率，calmar比率等评价指标
    Nav表中会新增drawdonw列和duration列
    
    Args:
        port_ret: Series or DataFrame
            索引为时间，收益率序列
        port_ret_col: str
            收益率所在列的名称
        nav_col: str
            净值所在列的名称
        rf: float
             无风险利率
        Tdays: int
            一年的交易日天数
    Returns:
        metrics: dict
            包含各项指标的字典
    """
    Nav = pd.DataFrame(port_ret)
    Nav[nav_col] = (1 + Nav[retn_col]).cumprod()
    Nav['drawdown'] = drawdown(Nav[nav_col]) # 回撤序列
    
    #计算最长回撤期
    Nav['duration'] = 0
    drawdown_idx = Nav.columns.tolist().index('drawdown')
    duration_idx = Nav.columns.tolist().index('duration')
    for i in range(0, len(Nav)):
        if Nav.iloc[i, drawdown_idx] == 0:
            Nav.iloc[i, duration_idx] = 0
        else:
            Nav.iloc[i, duration_idx] = Nav.iloc[i-1, duration_idx] + 1
    mddd = Nav['duration'].max()
    
    #计算平均回撤期、平均回撤
    drawdown_count = 1
    for i in range(1,len(Nav['duration'])):
        if Nav.iloc[i, duration_idx] == 0 and Nav.iloc[i-1, duration_idx] != 0:
            drawdown_count += 1
    dd_days = len(Nav[Nav['drawdown'] != 0])
    ddd_mean = dd_days / drawdown_count #平均回撤期
    dd_mean = Nav['drawdown'].mean() #平均回撤
    
    #最大回撤与最长回撤期开始、结束的日期
    mdd_end = Nav['drawdown'].idxmin().strftime('%Y-%m-%d')
    mdd_begin = Nav.loc[:mdd_end, nav_col].idxmax().strftime('%Y-%m-%d')
    mddd_end = Nav['duration'].idxmax().strftime('%Y-%m-%d')
    mddd_end_1_idx = len(Nav.loc[:mddd_end, :]) - 2
    pre_mddd_end = Nav.index[mddd_end_1_idx]
    mddd_begin = Nav.loc[:pre_mddd_end, nav_col].idxmax().strftime('%Y-%m-%d')
    
    #收益率的各阶矩
    ann = (Nav[nav_col][-1] / Nav[nav_col][0]) ** (Tdays / len(Nav)) - 1 # 年化收益率
    ann_vol = Nav[retn_col].std() * sqrt(Tdays)
    ret_skew = Nav[retn_col].skew()
    ret_kurt = Nav[retn_col].kurt()
    
    mdd = Nav['drawdown'].min()
    calmar = abs(ann / mdd) # calmar比率
    sharpe = (Nav[retn_col] - rf / Tdays).mean() / Nav[retn_col].std() * sqrt(Tdays)
    win = len(Nav[Nav[retn_col] > 0]) / len(Nav) #胜率
    
    metrics = {'ann': ann,
               'ann_vol': ann_vol,
               'ret_skew': ret_skew,
               'ret_kurt': ret_kurt,
               'win': win,
               'sharpe': sharpe,
               'calmar': calmar,
               'mdd': mdd,
               'dd_mean': dd_mean,
               'ddd_mean': ddd_mean,
               'mdd_begin': mdd_begin,
               'mdd_end': mdd_end,
               'mddd': mddd,
               'mddd_begin': mddd_begin,
               'mddd_end': mddd_end}
    
    return metrics

def Nav_plot(Nav, retn_col='retn', nav_col='nav', figsize=(10, 6), r_ylim=-0.5, box_x=0.38, box_y=0.9):
    """
    绘制回测曲线图
    
    Args:
        Nav: Series or DataFrame
            至少包含组合收益率净值，可以包含净值序列
        nav_col: str
            净值所在列的名称
        fig_size: tuple
            图形大小
        r_ylim: float
            回撤曲线的纵轴的下界
        box_x: float
            0-1，评价指标汇总框右边框的x轴的相对位置
        box_y: float
            r_ylim - 0，汇总框下边框的在右边y轴的y坐标到x轴的距离
    Returns: 
        None, 输出回测曲线图
    """
    metrics = evaluate(Nav, retn_col=retn_col, nav_col=nav_col)
    mdd_begin, mdd_end = metrics['mdd_begin'], metrics['mdd_end']
    mddd_begin, mddd_end = metrics['mddd_begin'], metrics['mddd_end']
    mddd_center = Nav.index[(len(Nav.loc[:mddd_begin, :]) + len(Nav.loc[:mddd_end, :])) // 2]
    
    #净值曲线图
    fig, ax = plt.subplots(figsize=figsize)
    idx = Nav.index
    ax.plot(idx, Nav[nav_col])
    ax.set_xlim(idx[0], idx[-1])
    ax.set_ylabel('Net Aseet Value', fontsize=10)
    offset = (Nav[nav_col].max() - Nav[nav_col].min()) / 20
    
    #标记最长回撤期的开始、结束日期
    ax.annotate("", xy=(mddd_end, Nav[nav_col][mddd_begin]), xycoords='data',
                 xytext=(mddd_begin, Nav[nav_col][mddd_begin]), textcoords='data',
                 arrowprops=dict(arrowstyle="<->", connectionstyle="arc3"))
    ax.text(mddd_center, Nav[nav_col][mddd_begin]+offset*1.2, 'max drawdown duration', 
            {'color': 'k', 'fontsize': 12, 'ha': 'center', 'va': 'top',})
    
    #标记最大回撤的开始、结束日期
    ax.annotate("", xy=(mdd_end, Nav[nav_col][mdd_begin]), xycoords='data', 
                xytext=(mdd_end, Nav[nav_col][mdd_end]), textcoords='data',
                arrowprops=dict(arrowstyle="<->", connectionstyle="arc3"))
    ax.text(mdd_end, Nav[nav_col][mdd_end]-offset, 'max drawdown',
            {'color': 'k', 'fontsize': 12, 'ha': 'center', 'va': 'bottom',})
    
    #回撤曲线
    ax2 = ax.twinx()
    ax2.set_ylim(r_ylim, 0)
    ax2.plot(Nav['drawdown'], color='c')
    ax2.fill_between(idx, Nav['drawdown'], color='c')
    ax2.set_ylabel('Drawdown', fontsize=10)
    
    words = '''annual: {ann: 10.2%}
ann_vol: {ann_vol: 10.2%}
retn_skew: {ret_skew: 10.2f}
retn_kurt: {ret_kurt: 10.2f}

win: {win: 10.2f}
sharpe: {sharpe: 10.2f}
calmar: {calmar: 10.2f}

mdd: {mdd: 10.2%}
mddd: {mddd: 10d}
dd_mean: {dd_mean: 10.2%}
ddd_mean: {ddd_mean: 10.2f}

mdd_begin: {mdd_begin}
mdd_end: {mdd_end}
mddd_begin: {mddd_begin}
mddd_end: {mddd_end}'''.format(**metrics)
    
    #评价指标注释汇总
#    ax2_long = (ax2.get_xbound()[-1] - ax2.get_xbound()[0]) / figsize[0]
#    box_xpos = ax2.get_xbound()[0] + ax2_long * 10 * box_x
#    ax2.text(box_xpos, r_ylim * box_y, words, fontsize=12, 
#             horizontalalignment='right', family='monospace',
#             bbox=dict(boxstyle='square', fc='white'))

    ax2_long = (ax2.get_xbound()[-1] - ax2.get_xbound()[0]) / figsize[0]
    box_xpos = ax2.get_xbound()[-1] + ax2_long * 10 * box_x
    ax2.text(box_xpos, r_ylim * box_y, words, fontsize=12, 
             horizontalalignment='right', family='monospace',
             bbox=dict(boxstyle='square', fc='white'))    
