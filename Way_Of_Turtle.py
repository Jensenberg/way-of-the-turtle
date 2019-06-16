# -*- coding: utf-8 -*-
"""
Created on Wed May  8 10:13:24 2019

@author: admin
"""

import pickle
import pandas as pd
import BackTest as bt

class Way_Of_Turtle:
    
    risk_rate = 0.003 #风险比率，太大会导致cash out，太小则不够买入单位头寸的手数，unit size = 0
    slippage_N = 1 #滑点对于最小变动单位的倍数
    stop_N = 4 #止损对于ATR的倍数
    
    tlimit = 12 #总的单位头寸约束
    wlimit = 10 #弱相关的单位头寸约束
    slimit = 6 #强相关的单位头寸约束
        
    def __init__(self, date, pre_date, code):
        self.date = date
        self.pre_date = pre_date
        self.code = code #合约代码
        self.unit = Unit.loc[pre_date, code] #前一交易日的单位头寸
        self.hold = Hold.loc[pre_date, code] #前一交易日的持仓
        self.deal_price = Deal_Price.loc[pre_date, code] #前一交易日的成交价格
        self.gain = Gain.loc[pre_date, code] #前一交易日的每日盈亏
        self.gained = Gained.loc[pre_date, code] #前一交易日的平仓盈亏
        self.open0, self.high, self.low, self.close, *rest = OHLC.xs((date, code))
        self.high20 = High20.loc[pre_date, code] 
        self.high10 = High10.loc[pre_date, code]
        self.low20 = Low20.loc[pre_date, code]
        self.low10 = Low10.loc[pre_date, code]
    
    def unit_limits(self, ls_flag):
        
        pre_date, code = self.pre_date, self.code
        
        total_units = Unit.loc[pre_date, :]
        if ls_flag == 'long':
            total_long = sum(total_units[total_units > 0])
        elif ls_flag == 'short':
            total_short = abs(sum(total_units[total_units < 0]))
        else:
            total_long = total_short = None
        
        if code in Clusters[pre_date]['weak'].keys():
            weak_codes = Clusters[pre_date]['weak'][code]
            weak_units = Unit.loc[pre_date, weak_codes]
            if ls_flag == 'long':
                weak_long = sum(weak_units[weak_units > 0])
            elif ls_flag == 'short':
                weak_short = abs(sum(weak_units[weak_units < 0]))
            else:
                weak_long = weak_short = None
        else:
            weak_long = weak_short = 0
        
        if code in Clusters[pre_date]['strong'].keys():
            strong_codes = Clusters[pre_date]['strong'][code]
            strong_units = Unit.loc[pre_date,strong_codes]
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
            print("ls_flag should be specified as 'long' or 'short'")   
                
    def trade(self):
        
        code = self.code
        slippage = self.slippage_N * Basic.loc[code, 'min_move']
        
        cost_mode, cost_rate = Basic.loc[code, ['cost_mode', 'cost_rate']]
        margin, multiplier = Basic.loc[code, ['margin', 'multiplier']]
        
        tlimit, wlimit, slimit = self.tlimit, self.wlimit, self.slimit
        unit, hold, deal_price, gain, gained = self.unit, self.hold, self.deal_price, self.gain, self.gained
        
        stop_N = self.stop_N
        pre_date = self.pre_date
        base = Base[pre_date]
        atr =  ATR.loc[pre_date, self.code]
        unit_size = int(self.risk_rate * base / (multiplier * atr))
        
        preclose = OHLC.xs((pre_date, code))['close']
        open0, high, low, close = self.open0, self.high, self.low, self.close
        high20, low20 = self.high20, self.low20
        high10, low10 = self.high10, self.low10
        
        if hold == 0:
            if high > high20:
                total, weak, strong = self.unit_limits('long')
                if total < tlimit and weak < wlimit and strong < slimit:
                    if unit_size:
                        unit = 1 
                        hold = unit_size
                        if cost_mode == 1: #按成交金额收取手续费
                            deal_price = (max(open0, high20) + slippage) * (1 + cost_rate)
                        else: #按手数收取手续费
                            deal_price = (max(open0, high20) + slippage) + cost_rate / multiplier
                        gain = (close - deal_price) * multiplier * hold
                        gained = 0
#                        print('开多', end=' ')
                    else:
                        print('unit size is zero!')
                        deal_price = gain = gained = 0
                else:
                    deal_price = gain = gained = 0
            elif low < low20:
                total, weak, strong = self.unit_limits('short')
                if total < tlimit and weak < wlimit and strong < slimit:
                    if unit_size:
                        unit = -1
                        hold = -unit_size
                        if cost_mode == 1:
                            deal_price = (min(open0, low20) - slippage) * (1 - cost_rate)
                        else:
                            deal_price = (min(open0, low20) - slippage) - cost_rate / multiplier
                        gain = (close - deal_price) * multiplier * hold
                        gained = 0
#                        print('开空', end=' ')
                    else:
                        print('unit size is zero!')
                        deal_price = gain = gained = 0
                else:
                    deal_price = gain = gained = 0
            else:
                deal_price = gain = gained = 0
        elif hold > 0:
            stop = deal_price - stop_N * atr
            if low < stop:
#                print('止损多仓', end=' ')
                unit = 0
                if cost_mode == 1:
                    deal_price = (min(open0, stop) - slippage) * (1 - cost_rate)
                else:
                    deal_price = (min(open0, stop) - slippage) - cost_rate / multiplier
                gain = (deal_price - preclose) * multiplier * hold
                gained = (deal_price - self.deal_price) * multiplier * hold
                hold = 0
            elif low < low10:
#                print('平多仓', end=' ')
                unit = 0
                if cost_mode == 1:
                    deal_price = (min(open0, low10) - slippage) * (1 - cost_rate)
                else:
                    deal_price = (min(open0, low10) - slippage) - cost_rate / multiplier
                gain = (deal_price - preclose) * multiplier * hold
                gained = (deal_price - self.deal_price) * multiplier * hold
                hold = 0
            else:
                gain = (close - preclose) * multiplier * hold
                gained = 0
                
        else:
            stop = deal_price + stop_N * atr
            if high > stop:
#                print('止损空仓', end=' ')
                unit = 0
                if cost_mode == 1:
                    deal_price = (max(open0, stop) + slippage) * (1 + cost_rate)
                else:
                    deal_price = (max(open0, stop) + slippage) + cost_rate / multiplier
                gain = (deal_price - preclose) * multiplier * hold
                gained = (deal_price - self.deal_price) * multiplier * hold
                hold = 0
            elif high > high10:
#                print('平空仓', end=' ')
                unit = 0
                if cost_mode == 1:
                    deal_price = (max(open0, high10) + slippage) * (1 + cost_rate)
                else:
                    deal_price = (max(open0, high10) + slippage) + cost_rate / multiplier
                gain = (deal_price - preclose) * multiplier * hold
                gained = (deal_price - self.deal_price) * multiplier * hold
                hold = 0
            else:
                gain = (close - preclose) * multiplier * hold
                gained = 0
                
        cash = Cash[pre_date]
        hold_change = abs(hold - self.hold)
        if self.hold == 0 and hold != 0:
            if cost_mode == 1:
                cost = deal_price * multiplier * (margin + cost_rate) * hold_change
            else:
                cost = (deal_price * multiplier * margin + cost_rate) * hold_change
        else:
            if cost_mode == 1:
                cost = deal_price * multiplier * cost_rate * hold_change
            else:
                cost = cost_rate * hold_change
        if cash < cost:
            print(date.strftime('%Y-%m-%d'), 
                  'Cash is out! Not enough money.')
            return self.unit, self.hold, deal_price, gain, gained, cash
        else:
            cash -= cost
            return unit, hold, deal_price, gain, gained, cash
if __name__ == '__main__':

    with open('basic.pkl', 'rb') as f:
        Basic = pickle.load(f)
    with open('Turtle_markets.pkl', 'rb') as f:
        Markets = pickle.load(f) #各个日期的可交易品种   
    with open('Turtle_clusters.pkl', 'rb') as f:
        Clusters = pickle.load(f) #约束分类
#        
    with pd.HDFStore('Turtle.h5') as store:
        OHLC = store['Adj_Quotes']
        ATR = store['ATR']
        High20 = store['High20']
        High10 = store['High10']
        Low20 = store['Low20'] 
        Low10 = store['Low10']
#    
    codes = High20.columns.tolist(); codes.sort()
    dates = list(Markets.keys()); dates.sort()
##    有3个记录在同一天达到 high20,low20
##    2008-07-11, C.DCE; 2014-04-25, AU.SHF; 2016-11-14, TA.CZC
#    for i in range(1, len(dates)):
#        pre_date = dates[i-1]
#        date = dates[i]
#        for code in Markets[date]:
#            open0, high, low, *res = OHLC.xs((date, code))
#            high20 = High20.loc[pre_date, code]
#            low20 = Low20.loc[pre_date, code]
#            if high > high20 and low < low20:
#                print(date, code)
#    不能使用Unit = Hold = Deal_Price ...会引发浅复制带来的引用问题，所有表都指向第一个表
    Unit = pd.DataFrame(0, columns=codes, index=dates)
    Hold = pd.DataFrame(0, columns=codes, index=dates)
    Deal_Price = pd.DataFrame(0, columns=codes, index=dates)
    Gain = pd.DataFrame(0, columns=codes, index=dates)
    Gained = pd.DataFrame(0, columns=codes, index=dates)    
    
    Asset = pd.Series(0, index=dates, name='asset') #净值
    Base = pd.Series(0, index=dates, name='base') #基础规模
    Cash = pd.Series(0, index=dates, name='cash') #现金
    Asset[0] = Base[0] = Cash[0] = 10**8;
    
    for i in range(1, len(dates)):
        if i % 100 == 0:
            print(i, dates[i].strftime('%Y-%m-%d'))
        date = dates[i]
        pre_date = dates[i-1]
        aviables = Markets[pre_date]
        for code in aviables:
            turtle = Way_Of_Turtle(date, pre_date, code)
            unit, hold, deal_price, gain, gained, cash = turtle.trade()
            Unit.loc[pre_date, code] = Unit.loc[date, code] = unit #更新品种的单位头寸，必须覆盖过去一个交易日的头寸，以方便统计头寸
            Hold.loc[date, code] = hold
            Deal_Price.loc[date, code] = deal_price
            Gain.loc[date, code] = gain
            Gained.loc[date, code] = gained
        Cash[date] = Cash[pre_date] + Gained.loc[date, :].sum() #更新账户的现金
        Asset[date] = Asset[pre_date] + Gain.loc[date, :].sum() #计算每日的净值
        
        base = Base[pre_date]
        value_add = Asset[date] / base - 1
        if value_add > 0.2: #调整账户哦基础规模
            Base[date] = base * 1.2
        elif value_add < -0.2:
            Base[date] = base * 0.8
        else:
            Base[date] = base
    retn = pd.DataFrame(Asset.pct_change())
    retn.dropna(inplace=True)
    bt.Nav_plot(retn, retn_col='asset', r_ylim=-1.5)
    a = retn.iloc[:-500, :]
    bt.Nav_plot(a, retn_col='asset', r_ylim=-1.5)
    
