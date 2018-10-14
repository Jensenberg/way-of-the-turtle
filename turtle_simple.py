# -*- coding: utf-8 -*-
"""
Created on Sat Oct  6 23:57:32 2018

@author: 54326
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 15:49:18 2018

@author: 54326
"""

from collections import defaultdict

def TR(data):
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
    ATRs = {}
    dates = data_TR.index
    ATRs[dates[span-1]] = sum(data_TR[:span]) / span
    for i in range(span, len(dates)):
        t = dates[i]
        t_1 = dates[i-1]
        ATRs[t] = (19 * ATRs[t_1] + data_TR[t]) / span
    return ATRs

def high_low(data, span=20):
    method = max if data.name == 'high' else min
    HL = {} 
    dates = data.index
    for i in range((len(dates) - span)):
        t = dates[i + span]
        data_t = data[i : i+span]
        HL[t] = method(data_t)
    return HL

def market(retn, span=60):
    markets = {}
    cluster = defaultdict(dict)
    dates = retn.index
    for i in range(len(dates) - span):
        t = dates[i+span]
        data_t = retn[i : i+span].dropna(axis=1)
        markets[t] = list(data_t.columns)
        corrs = data_t.corr()
        
        weak = corrs[(corrs >= 0.4) & (corrs < 0.7)].stack()
        weak_mkts = list(set(weak.index.get_level_values(0)))        
        cluster[t]['weak'] = weak_mkts
        
        strong = corrs[(corrs >= 0.7) & (corrs < 1)].stack()
        strong_mkts = list(set(strong.index.get_level_values(0)))
        cluster[t]['strong'] = strong_mkts
        
    return markets, cluster

class Turtle():
    
    risk_rate = 0.003
    slippage_n = 1
    slimit = 6
    wlimit = 10
    tlimit = 12
    stop_n = 2
    
    def __init__(self, date, pre_date, name, hold, units, deal_price, open_,
                 high, low, high20, low20, high10, low10, ATR, basic):
        self.date = date
        self.pre_date = pre_date
        self.name = name
        self.hold = hold 
        self.units = units #当日所有品种的头寸单位
        self.deal_price = deal_price
        self.open_ = open_
        self.high = high
        self.low = low
        self.high20 = high20
        self.low20 = low20
        self.high10 = high10
        self.low10 = low10
        self.ATR = ATR
        self.basic = basic
    
    def units_limits(self, cluster, ls_flag):
        units = self.units
        pre_date = self.pre_date
        
        total_units = units.loc[pre_date, :]
        if ls_flag == 'long':
            total_long = sum(total_units[total_units > 0])
        elif ls_flag == 'short':
            total_short = abs(sum(total_units[total_units < 0]))
        else:
            total_long = total_short = None
        
        if 'weak' in cluster.keys():
            weak_names = cluster['weak']
            weak_units = units.loc[pre_date, weak_names]
            if ls_flag == 'long':
                weak_long = sum(weak_units[weak_units > 0])
            elif ls_flag == 'short':
                weak_short = abs(sum(weak_units[weak_units < 0]))
            else:
                weak_long = weak_short = None
        else:
            weak_long = weak_short = 0

        if 'strong' in cluster.keys():
            strong_names = cluster['strong']
            strong_units = units.loc[pre_date, strong_names]
            if ls_flag == 'long':
                strong_long = sum(strong_units[strong_units > 0])
            elif ls_flag == 'short':
                strong_short = abs(sum(strong_units[strong_units < 0]))
            else:
                strong_long = strong_short = None
        else:
            strong_long = strong_short = 0
        
        if ls_flag == 'long':
            return(total_long, weak_long, strong_long)
        elif ls_flag == 'short':
            return(total_short, weak_short, strong_short)
        else:
            print("ls_flag should be 'long' or 'short'")     
                
    def trade_rule(self, cluster, unit_size):
        hold = self.hold
        open_ = self.open_
        high = self.high
        low = self.low
        high20 = self.high20
        low20 = self.low20
        high10 = self.high10
        low10 =self.low10
        deal_price = self.deal_price
        ATR = self.ATR
        tlimit = self.tlimit
        slimit = self.slimit
        wlimit = self.wlimit
        slippage = self.slippage_n * self.basic['min_move']
        stop_n = self.stop_n        
        
        if hold == 0 and high > high20: 
            #开多仓
            tl, wl, sl = self.units_limits(cluster, 'long')
            if tl < tlimit and wl < wlimit and sl < slimit:            
                trade = unit_size
                unit = 1 if unit_size else 0
#                if open_ > high20:
#                    price = open_ + slippage
#                else:
#                    price = high20 + slippage
                price = high20 +slippage
            else:
                trade = unit = price = 0
            return trade, unit, price, 0
        
        elif hold == 0 and low < low20:
            #开空仓
            ts, ws, ss = self.units_limits(cluster, 'short')
            if ts < tlimit and ws < wlimit and ss < slimit:            
                trade = -unit_size
                unit = -1 if unit_size else 0
#                if open_ < low20:
#                    price = open_ - slippage
#                else:
#                    price = low20 - slippage
                price = low20 +slippage
            else:
                trade = unit = price = 0
            return trade, unit, price, 0
        
        elif hold < 0 and self.high > deal_price + stop_n * ATR:
            #止损空仓
            trade = -hold
            unit = 1
            stop = deal_price + stop_n * ATR
#            if open_ > stop:
#                price = open_ + slippage
#            else:
#                price = stop + slippage
            price = stop +slippage
            gain = price - deal_price
            return trade, unit, price, gain
                
        elif hold > 0 and self.low < deal_price - stop_n * ATR:
            #止损多仓
            trade = -hold
            unit = -1
            stop = deal_price - stop_n * ATR
#            if open_ < stop:
#                price = open_ - slippage
#            else:
#                price = stop - slippage
            price = stop - slippage
            gain = price - deal_price
            return trade, unit, price, gain
        
        elif hold < 0 and high > high10:
            #退出空仓
            trade = -hold
            unit = 1
            stop = high10
#            if open_ > stop:
#                price = open_ + slippage
#            else:
#                price = stop + slippage
            price = stop + slippage
            gain = price - deal_price
            return trade, unit, price, gain        
            
        elif hold > 0 and low < low10:
            #退出多仓
            trade = -hold
            unit = -1
            stop = low10
#            if open_ < stop:
#                price = open_ - slippage
#            else:
#                price = stop - slippage
            price = stop - slippage
            gain = price - deal_price
            return trade, unit, price, gain
        
        else:
            #无交易
            return 0, 0, 0, 0
    
    def transaction(self, cluster, account, cash):
        multiplier, margin, _, cost_mode, cost_rate = self.basic
        
        unit_size = int(self.risk_rate * account / (multiplier * self.ATR))
        trade, unit, price, gain = self.trade_rule(cluster, unit_size)        
        
        if cost_mode == 1:
            cost = price * multiplier * trade * margin\
                 + price * multiplier * abs(trade) * cost_rate
        else:
            cost = price * multiplier * trade * margin\
                 + abs(trade) * cost_rate       
        
        if cash >= cost:
            #交易成功
            cash -= cost
            return trade, unit, price, gain, cash
        else:
            #交易失败
            print('Cash is out. Not Enough Money!')
            return 0, 0, 0, 0, cash

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
        High20[name] = high_low(high)
        Low20[name]=  high_low(low)
        High10[name] = high_low(high, span=10)
        Low10[name] =  high_low(low, span=10)       

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
            open_ = Open.loc[date, name]
            high = High.loc[date, name]
            low = Low.loc[date, name]
            high20 = High20.loc[date, name]
            low20 = Low20.loc[date, name]
            high10 = High10.loc[date, name]
            low10 = Low10.loc[date, name]
            ATR = data_ATR.loc[pre_date, name]
            basic = Basic.loc[name, basic_fields]
            turtle = Turtle(date, pre_date, name, hold, units, deal_price, open_, 
                            high, low, high20, low20, high10, low10, ATR, basic)
            trade, unit, price, gain, cash = turtle.transaction(cluster, account, cash)
                        
            Units.loc[date, name] = Units.loc[pre_date, name] + unit
            done.append(name)
            todo.remove(name)
            units_dict = dict(Units.loc[date, done])
            units_dict.update(dict(Units.loc[pre_date, todo]))
            units = pd.DataFrame(pd.Series(units_dict, name=pre_date)).T
            
            multiplier = basic['multiplier']
            hold_now = Hold.loc[date, name] = hold + trade
            close = Close.loc[date, name]               
            if hold == 0 and hold_now != 0: #开仓
                Deal_Price.loc[date, name] = price
                PNL.loc[date, name] = (close - price) * multiplier * hold_now
            elif hold != 0 and hold_now == 0: #平仓
                cash += gain * multiplier * hold
                PNL.loc[date, name] = 0
            elif hold * hold_now < 0: #平仓后开仓
                Deal_Price.loc[date, name] = price
                cash += gain * multiplier * hold
                PNL.loc[date, name] = (close - price) * multiplier * hold_now
            else: #无交易，保持原仓位
                Deal_Price.loc[date, name] = deal_price
                PNL.loc[date, name] = hold * multiplier *  (close - deal_price)
            
        Cash[date] = cash
        Asset[date] = Cash[date] + PNL.loc[date, :].sum()
        ladder = Asset[date] - account
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
words = \
'''Risk Rate: {:8.4f}
slippage: {:8d}

Total return: {:8.2f}
Annual return: {:8.2f}
Volatility: {:8.2f} 
IR: {:8.2f}
Max Drawdown: {:8.2f}
Calmar: {:8.2f}'''.format(Turtle.risk_rate, Turtle.slippage_n, Total_return, Ann,
 Sigma, IR, MaxDD, Calmar)
ax2.text(ax2.get_xbound()[0]+750, -1.3, words, 
         fontsize=16, horizontalalignment='right', 
         bbox=dict(boxstyle='square', fc='white'))
plt.savefig('Turtle(%.4f).png' % Turtle.risk_rate, bbox_inches='tight')

print('最终回报率: %.2f' % Total_return, '\n',
      '年化收益率: %.2f' % Ann, '\n',
      '波动率: %.2f' % Sigma, '\n',
      'IR: %.2f' % IR, '\n',
      '最大回撤: %.2f' % MaxDD, '\n',
      'Calmar: %.2f' % Calmar)
