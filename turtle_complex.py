# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 15:49:18 2018

@author: 54326
"""

from collections import defaultdict

def TR(data):
    '''
    计算真实的波动幅度
    '''
    TRs = {}
    dates = data.index
    for i in range(1, len(dates)):
        t = dates[i]
        t_1 = dates[i-1]
        TR_t = max(data.loc[t, 'high'] - data.loc[t, 'low'], 
                   data.loc[t, 'high'] - data.loc[t_1, 'close'], 
                   data.loc[t_1, 'close'] - data.loc[t, 'low'])
        TRs[t] = TR_t
    return TRs        

def ATR(data_TR, span=20):
    '''
    真实波动幅度的均值
    span:
        时间跨度，过去多少天的TR的均值
    ''' 
    ATRs = {}
    dates = data_TR.index
    ATRs[dates[span-1]] = sum(data_TR[:span]) / span #最开始的20天为简单平均
    for i in range(span, len(dates)):
        t = dates[i]
        t_1 = dates[i-1]
        ATRs[t] = (19 * ATRs[t_1] + data_TR[t]) / span #指数平均
    return ATRs

def high_low(data, span=20):
    '''
    过去N天的最高价或最低价
    args:
        data:
            最高价或最低价序列，对应的名称必须为'high'或'low'
        span:
            时间跨度，过去多少天
    '''
    method = max if data.name == 'high' else min #最高价序列取最大值，最低价序列取最小值
    HL = {} 
    dates = data.index
    for i in range((len(dates) - span)):
        t = dates[i + span]
        data_t = data[i : i+span]
        HL[t] = method(data_t)
    return HL

def market(retn, span=60):
    '''
    获取可以交易的品种，基于过去N天的收益率的相关系数矩阵划分品种的关联程度
    Args:
        retn:
            品种的收益率数据
        span:
            计算相关系数的时间跨度
    Returns:
        markets:
            字典，以日期为键，每天的可交易品种的列表为值
        cluster:
            嵌套字典，第一层以日期为键，第二层为weak，strong，对应品种的列表为值
    '''
    markets = {}
    cluster = defaultdict(dict)
    dates = retn.index
    for i in range(len(dates) - span):
        t = dates[i+span]
        data_t = retn[i : i+span].dropna(axis=1) #删除有缺失数据的品种
        markets[t] = list(data_t.columns) #可交易的品种
        corrs = data_t.corr() #品种之间的相关系系数矩阵
        
        weak = corrs[(corrs >= 0.4) & (corrs < 0.7)].stack()
        weak_mkts = list(set(weak.index.get_level_values(0))) #弱关联的品种       
        cluster[t]['weak'] = weak_mkts
        
        strong = corrs[(corrs >= 0.7) & (corrs < 1)].stack()
        strong_mkts = list(set(strong.index.get_level_values(0))) #强关联的品种
        cluster[t]['strong'] = strong_mkts
        
    return markets, cluster

if __name__ == '__main__':
    import pandas as pd
    import matplotlib.pyplot as plt

    with pd.HDFStore(r'E:/data/futures.h5') as store:
        data = store['daily_price']
        Basic = store['basic']
       
    names = data.columns 
    data_ATR = {}
    High20 = {}; Low20 = {}
    High10 = {}; Low10 = {}
    for name in names:
        data_name = data[name].unstack()
        data_TR = pd.Series(TR(data_name)).sort_index().dropna()
        data_ATR[name] = ATR(data_TR)
        
        high = data_name['high']
        low = data_name['low']
        High20[name] = high_low(high, span=55) #span默认是20，可以设置成55日或20日,得到相应时期内的最高价
        Low20[name]=  high_low(low, span=55) #过去55日最低价
        High10[name] = high_low(high, span=20) #过去20日最高价
        Low10[name] =  high_low(low, span=20) #过去20日最低价  

    data_ATR = pd.DataFrame(data_ATR)
    High20 = pd.DataFrame(High20)
    Low20 = pd.DataFrame(Low20)
    High10 = pd.DataFrame(High10)
    Low10 = pd.DataFrame(Low10)            
    
    Close = data.xs('close', level=1)
    retn = Close.pct_change()
    Markets, Cluster = market(retn)
    
    dates = pd.Series(list(Markets.keys())).sort_index()
    Cash = pd.Series(index=dates)
    Account = pd.Series(index=dates)
    Asset = pd.Series(index=dates)
    
    Trade = pd.DataFrame(0, index=dates, columns=names)
    Deal_Price = pd.DataFrame(0,index=dates, columns=names)
    Deal_Date = pd.DataFrame(0,index=dates, columns=names)
    Hold = pd.DataFrame(0, index=dates, columns=names)
    PNL = pd.DataFrame(0, index=dates, columns=names)
    Units = pd.DataFrame(0, index=dates, columns=names)
    
    t_0 = dates[0]
    Cash[t_0] = Account[t_0] = Asset[t_0] = initial = 10**8
    
    High = data.xs('high', level=1)
    Low = data.xs('low', level=1)
    Open = data.xs('open', level=1)
    
    from turtle_class  import Turtle
    Turtle.Open, Turtle.High, Turtle.Low, Turtle.Close = Open, High, Low, Close
    
    basic_fields = ['multiplier', 'margin', 'min_move', 'cost_mode', 'cost_rate']
    for i in range(1, len(dates)):
        if i % 100 == 0:
            print(i)
        date = dates[i]
        pre_date = dates[i-1]
        aviables = Markets[date]
        cluster = Cluster[date]
        account= Account[pre_date]
        cash = Cash[pre_date]
        units = pd.DataFrame(Units.loc[pre_date, aviables]).T
        done = []
        todo = list(aviables)
        for name in aviables:
            hold = Hold.loc[pre_date, name]
            deal_price = Deal_Price.loc[pre_date, name]
            deal_date = Deal_Date.loc[pre_date, name]
            high20 = High20.loc[date, name]
            low20 = Low20.loc[date, name]
            high10 = High10.loc[date, name]
            low10 = Low10.loc[date, name]
            ATR = data_ATR.loc[pre_date, name]
            basic = Basic.loc[name, basic_fields]
            turtle = Turtle(date, pre_date, name, hold, units, deal_price, deal_date, 
                            high20, low20, high10, low10, ATR, basic)
            trade, unit, price, gain, cash = turtle.transaction(cluster, account, cash)
            
            
            Units.loc[date, name] = Units.loc[pre_date, name] + unit #更新品种的头寸
            done.append(name) #已评估过的品种
            todo.remove(name) #未评估的品种
            units_dict = dict(Units.loc[date, done])
            units_dict.update(dict(Units.loc[pre_date, todo]))
            #将已评估的品种的当前头寸和未评估品种的上一交易日头寸组合在一起
            #作为下一个品种评估的头寸数据
            units = pd.DataFrame(pd.Series(units_dict, name=pre_date)).T
            
            multiplier = basic['multiplier']
            hold_now = Hold.loc[date, name] = hold + trade
            close = Close.loc[date, name]
            #更新开仓价格，计算平仓的损益和持仓的盈亏               
            if hold == 0 and hold_now != 0: #开仓
                Deal_Price.loc[date, name] = price
                Deal_Date.loc[date, name] = date
                PNL.loc[date, name] = (close - price) * multiplier * hold_now
            elif hold != 0 and hold_now == 0: #平仓
                cash += gain * multiplier * hold #将平仓损益加入现金
                PNL.loc[date, name] = 0
            elif hold * hold_now < 0: #平仓后开仓
                Deal_Price.loc[date, name] = price
                Deal_Date.loc[date, name] = date
                cash += gain * multiplier * hold #将平仓损益加入现金
                PNL.loc[date, name] = (close - price) * multiplier * hold_now
            else: #无交易，保持原仓位
                Deal_Price.loc[date, name] = deal_price
                Deal_Date.loc[date, name] = deal_date
                PNL.loc[date, name] = hold * multiplier *  (close - deal_price)
            
        Cash[date] = cash
        Asset[date] = Cash[date] + PNL.loc[date, :].sum()
        ladder = Asset[date] - account
        #基于盈亏调整账户规模
        if ladder / account > 0.2:
            Account[date] = account * 1.2
        elif ladder / account < -0.2:
            Account[date] = account * 0.8
        else:
            Account[date] = account

nav = Asset / initial
Total_return = nav[-1]
T = len(nav) / 244
Ann = nav[-1]**(1/T) - 1
Sigma = nav.std() / (T**(1/2))
IR = Ann / Sigma
def drawdown(nav):
    dd = []
    for i in range(1, len(nav)):
        max_i = max(nav[:i])
        dd.append(min(0, nav[i] - max_i) / max_i)
    return dd
Drawdown = pd.Series(drawdown(nav), index=nav.index[1:])
MaxDD = min(Drawdown)
Calmar = abs(Ann / MaxDD)

fig, ax1 = plt.subplots(figsize=(15, 8))
ax1.set_xlim(nav.index[0], nav.index[-1])  
ax1.plot(nav.index, nav)
ax1.set_ylabel('Net Asset Value', fontdict={'fontsize':16})
ax1.set_xlabel('Date', fontdict={'fontsize':16})
ax2 =ax1.twinx()
ax2.plot(Drawdown.index, Drawdown, color='c')
ax2.set_ylabel('Max Drawdown', fontdict={'fontsize':16})
ax2.fill_between(Drawdown.index, Drawdown, color='c')
ax2.set_ylim(-1.5, 0)
words = '''risk rate:{:8.4f}
slippage:{:8d}
stop ATRs:{:8d}
safe ATRs:{:8d}
trail ATRs:{:8d}
sharp days:{:8d}

Total return:{:8.2f}
Annual return:{:8.2f}
Volatility:{:8.2f} 
IR:{:8.2f}
Max Drawdown:{:8.2f}
Calmar:{:8.2f}'''.format(Turtle.risk_rate, Turtle.slippage_n, Turtle.stop_n, Turtle.safe_n, 
                         Turtle.trail_n, Turtle.sharp_days, Total_return, Ann, Sigma, IR, MaxDD, Calmar)
ax2.text(ax2.get_xbound()[0]+650, -1, words, 
         fontsize=14, family='Fira Code', horizontalalignment='right', 
         bbox=dict(boxstyle='square', fc='white'))
plt.savefig('1.01 Turtle55(%.3f %d %d %d %d).png' % (
        Turtle.risk_rate, Turtle.stop_n, Turtle.safe_n, Turtle.trail_n, Turtle.sharp_days),
bbox_inches='tight')

print('最终回报率: %.2f' % Total_return, '\n',
      '年化收益率: %.2f' % Ann, '\n',
      '波动率: %.2f' % Sigma, '\n',
      'IR: %.2f' % IR, '\n',
      '最大回撤: %.2f' % MaxDD, '\n',
      'Calmar: %.2f' % Calmar)
