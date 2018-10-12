# -*- coding: utf-8 -*-
"""
Created on Sun Oct  7 01:49:16 2018

@author: 54326
"""

class Turtle():
    '''
    海龟交易系统
    必须首先建立四个类属性：Open, High, Low, Close，并为此赋值
    '''
    
    risk_rate = 0.005 #风险比例
    slippage_n = 1 #滑点，最小变动单位的倍数，
    slimit = 6 #强关联市场单方向的头寸限制
    wlimit = 10 #弱关联市场单方向的头寸限制
    tlimit = 12 #全部市场单方向的头寸限制
    stop_n = 1 #止损，ATR的倍数
    safe_n = 6 #最优价格相比于前期有利变动的幅度，ATR的倍数
    trail_n = 2 #最优价格相比于当前价格不利变动的幅度，ATR的倍数
    sharp_days = 4 #刻画价格快速变动的时间跨度
    
    def __init__(self, date, pre_date, name, hold, units, deal_price, deal_date,
                 high20, low20, high10, low10, ATR, basic):
        self.date = date #当前交易日
        self.pre_date = pre_date #前一交易日
        self.name = name #品种名称
        self.hold = hold #前一交易日品种的持仓量
        self.units = units #当日所有品种的头寸单位
        self.deal_price = deal_price #开仓交个
        self.deal_date = deal_date #开仓日期
        self.open_ = self.Open.loc[date, name] #开盘价
        self.high = self.High.loc[date, name]#最高价
        self.low = self.Low.loc[date, name] #最低价
        self.high20 = high20 #20日最高价
        self.low20 = low20 #20日最低价
        self.high10 = high10 #10日最高价
        self.low10 = low10 #10日最低价
        self.ATR = ATR #平均真实波动幅度
        self.basic = basic #品种的基本资料
    
    def units_limits(self, cluster, ls_flag):
        '''
        统计三个层次品种的每个方向的合计头寸
        cluster:
            嵌套字典，第一层以日期为键，第二层分为weak，strong，保存了每个交易日基于收益率
            相关性的品种之间的关联性的划分
        ls_flag:
            long\short标记，指明统计多头还是空头的头寸
        '''
        units = self.units #每个品种交易后的头寸数据，动态更新
        pre_date = self.pre_date
        
        #全部市场的合计头寸
        total_units = units.loc[pre_date, :]
        if ls_flag == 'long':
            total_long = sum(total_units[total_units > 0])
        elif ls_flag == 'short':
            total_short = abs(sum(total_units[total_units < 0]))
        else:
            total_long = total_short = None
        
        #弱关联市场的合计头寸
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
        
        #强关联市场的合计头寸
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
    
    def Short2Long(self, stop, unit_size, slippage):
        '''
        空翻多，平空仓且反向开多仓
        Args:    
            stop:
                止损或退出的价格
            unit_size:
                每个头寸单位的规模
            slippage:
                滑点
        Returns:
            trade:
                交易量
            unit:
                交易头寸
            price:
                交易价格
            gain:
                平仓损益
        '''
        hold = self.hold
        open_ = self.open_
        high20 = self.high20
        deal_price = self.deal_price
        
        trade = -hold + unit_size
        unit = 2 if unit_size else 1 #unit_size可能为0
        
        if open_ <= stop and open_ <= high20: 
            gain = stop - deal_price + slippage
            price = high20 + slippage
            
        elif open_ > stop and open_ <= high20:
            gain = open_ - deal_price + slippage
            price = high20 + slippage
            
        else: #开盘价就高于了止损价和20日最高价
            gain = open_ - deal_price + slippage
            price = open_ + slippage
        
        return trade, unit, price, gain
        
    def close_short(self, stop, slippage):
        '''
        仅平空仓
        '''
        hold = self.hold
        open_ = self.open_
        deal_price = self.deal_price
        
        trade = -hold
        unit = 1
        if open_ > stop:
            price = open_ + slippage
        else:
            price = stop + slippage
        gain = price - deal_price
        
        return trade, unit, price, gain
    
    def short(self, cluster, stop, unit_size, slippage):
        '''
        空仓的处理，可能平仓后开仓，可能仅平仓
        '''
#        name = self.name
        tlimit = self.tlimit
        wlimit = self.wlimit
        slimit = self.slimit
        if self.high > self.high20:
            tl, wl, sl = self.units_limits(cluster, 'long') #当时多头头寸的数量合计
#            tl += 1
#            if name in cluster['strong']:
#                sl += 1
#                if name in cluster['weak']:
#                    wl += 1
#                    limit_flag = (sl <= slimit and wl <= wlimit and tl <= tlimit)
#                else:
#                    limit_flag = (sl <= slimit and tl <= tlimit)
#            elif name in cluster['weak']:
#                wl += 1
#                limit_flag = (wl <= wlimit and tl <= tlimit)
#            else:
#                limit_flag = (tl <= tlimit)
#            if limit_flag:
            if sl < slimit and wl < wlimit and tl < tlimit:
                print('#平空仓，开多单，空翻多')
                return self.Short2Long(stop, unit_size, slippage)
            else:
                #平空仓
                return self.close_short(stop, slippage)
        else:      
            #平空仓
            return self.close_short(stop, slippage)
        
    def Long2Short(self, stop, unit_size, slippage):
        '''
        多翻空，平多仓且反向开空仓
        '''
        hold = self.hold
        open_ = self.open_
        low20 = self.low20
        deal_price = self.deal_price
        
        trade = -hold - unit_size
        unit = -2 if unit_size else -1 #unit_size可能为0
        
        if open_ >= stop and open_ >= low20:
            gain = stop - deal_price - slippage
            price = low20 - slippage
        
        elif open_ < stop and open_ >= low20:
            gain = open_ - deal_price - slippage
            price = low20 - slippage
        
        else:
            gain = open_ -deal_price - slippage
            price = open_ - slippage
        
        return trade, unit, price, gain
    
    def close_long(self, stop, slippage):
        '''
        仅平多仓
        '''
        hold = self.hold
        open_ = self.open_
        deal_price = self.deal_price
        
        trade = -hold
        unit = -1
        if open_ < stop:
            price = open_ - slippage
        else:
            price = stop - slippage
        gain = price - deal_price
        
        return trade, unit, price, gain
    
    def long(self, cluster, stop, unit_size, slippage):
        '''
        多仓的处理
        '''
#        name = self.name
        tlimit = self.tlimit
        wlimit = self.wlimit
        slimit = self.slimit
        if self.low <= self.low20:
            ts, ws, ss = self.units_limits(cluster, 'short') #当时空头头寸的数量合计
#            ts += 1
#            if name in cluster['strong']:
#                ss += 1
#                if name in cluster['weak']:
#                    ws += 1
#                    limit_flag = (ss <= slimit and ws <= wlimit and ts <= tlimit)
#                else:
#                    limit_flag = (ss <= slimit and ts <= tlimit)
#            elif name in cluster['weak']:
#                ws += 1
#                limit_flag = (ws <= wlimit and ts <= tlimit)
#            else:
#                limit_flag = (ts <= tlimit)
#            if limit_flag:
            if ss < slimit and ws < wlimit and ts < tlimit:
                print('#平多仓，开空仓，多翻空')
                return self.Long2Short(stop, unit_size, slippage)
            else:
                #平多仓
                return self.close_long(stop, slippage)
        else:                        
            #平多仓
            return self.close_long(stop, slippage)        
                
    def trade_rule(self, cluster, unit_size):
        '''
        交易法则，如何开仓，平仓
        '''
        name = self.name
        date = self.date
        pre_date = self.pre_date
        hold = self.hold
        deal_price = self.deal_price
        deal_date = self.deal_date
        open_ = self.open_
        high = self.high
        low = self.low
        high20 = self.high20
        low20 = self.low20
        high10 = self.high10
        low10 =self.low10
        ATR = self.ATR
        tlimit = self.tlimit
        slimit = self.slimit
        wlimit = self.wlimit
        slippage = self.slippage_n * self.basic['min_move'] #滑点是最小变动单位的倍数
        stop_n = self.stop_n
        safe_n = self.safe_n
        trail_n =self.trail_n
        sharp_days = self.sharp_days
        
        #计算移动止损的止损价格和安全边际
        if hold < 0:
            #开仓至目前的价格
            hold_trail = self.Low.loc[deal_date : pre_date, name]
            #持仓期间的最低价，和最低价的日期
            trail, trail_date = min(hold_trail), hold_trail.idxmin()
            #不利变动的天数
            trail_days = len(self.Low.loc[trail_date : date, name]) - 1
            #基于最低价的止损价
            trail_stop = trail + trail_n * ATR
            #安全边际，获得safe_n个ATR需要的价格
#            days = len(self.Close.loc[:trail_date, name])
#            close_10_date = self.Close.index[days-10]
#            close_10 = self.Close.loc[close_10_date, name]
#            trail_margin = close_10 - safe_n * ATR
            trail_margin = deal_price - safe_n * ATR
        elif hold > 0:
            #开仓至目前的价格
            hold_trail = self.High.loc[deal_date : pre_date, name]
            #持仓期间的最高价，和最高价对应的日期
            trail, trail_date = max(hold_trail), hold_trail.idxmax()
            #不利变动的天数
            trail_days = len(self.High.loc[trail_date : date, name]) - 1
            #基于最高价的止损价
            trail_stop = trail - trail_n * ATR
            #安全边际，获得safe_n个ATR需要的价格
#            days = len(self.Close.loc[:trail_date, name])
#            close_10_date = self.Close.index[days-10]
#            close_10 = self.Close.loc[close_10_date, name]
#            trail_margin = close_10 + safe_n * ATR  
            trail_margin = deal_price + safe_n * ATR
        else:
            trail_stop = trail_margin = None
        
        if hold == 0 and high > high20: 
            #统计多头头寸的数量
            tl, wl, sl = self.units_limits(cluster, 'long')
#            tl += 1
#            if name in cluster['strong']:
#                sl += 1
#                if name in cluster['weak']:
#                    wl += 1
#                    limit_flag = (sl <= slimit and wl <= wlimit and tl <= tlimit)
#                else:
#                    limit_flag = (sl <= slimit and tl <= tlimit)
#            elif name in cluster['weak']:
#                wl += 1
#                limit_flag = (wl <= wlimit and tl <= tlimit)
#            else:
#                limit_flag = (tl <= tlimit)
#            if limit_flag:  
            if sl < slimit and wl < wlimit and tl < tlimit:
                #开多仓
                trade = unit_size
                unit = 1 if unit_size else 0 #unit_size可能为0
                if open_ > high20:
                    price = open_ + slippage
                else:
                    price = high20 + slippage
            else:
                trade = unit = price = 0
            return trade, unit, price, 0
        
        elif hold == 0 and low < low20:
            #开空仓
            ts, ws, ss = self.units_limits(cluster, 'short')
#            ts += 1
#            if name in cluster['strong']:
#                ss += 1
#                if name in cluster['weak']:
#                    ws += 1
#                    limit_flag = (ss <= slimit and ws <= wlimit and ts <= tlimit)
#                else:
#                    limit_flag = (ss <= slimit and ts <= tlimit)
#            elif name in cluster['weak']:
#                ws += 1
#                limit_flag = (ws <= wlimit and ts <= tlimit)
#            else:
#                limit_flag = (ts <= tlimit)
#            if limit_flag:
            if ss < slimit and ws < wlimit and ts < tlimit:            
                trade = -unit_size
                unit = -1 if unit_size else 0
                if open_ < low20:
                    price = open_ - slippage
                else:
                    price = low20 - slippage
            else:
                trade = unit = price = 0
            return trade, unit, price, 0
        
        elif hold < 0 and self.high > deal_price + stop_n * ATR:
            #止损空仓
            stop = deal_price + stop_n * ATR
            return self.short(cluster, stop, unit_size, slippage)
                
        elif hold > 0 and self.low < deal_price - stop_n * ATR:
            #止损多仓
            stop = deal_price - stop_n *ATR
            return self.long(cluster, stop, unit_size, slippage)
        
        elif hold < 0 and self.high > trail_stop and trail_days < sharp_days and trail < trail_margin:
            #空仓时，如果当日最高价高于移动止损价，且发生在较短的时期内，此外，持仓期内的最低价低于安全边际，则获利退出
            print('移动止损空仓')
            stop = trail + trail_n * ATR            
            return self.short(cluster, stop, unit_size, slippage)
            
        elif hold > 0 and self.low < trail_stop and trail > trail_margin and trail_days < sharp_days:
            #多仓时，如果当日最低价低于于移动止损价，且发生在较短的时期内，此外，持仓期内的最高价高于安全边际，则获利退出
            print('移动止损多仓')
            stop = trail - trail_n * ATR
            return self.long(cluster, stop, unit_size, slippage)
        
        elif hold < 0 and high > high10:
            #退出空仓
            stop = high10
            return self.short(cluster, stop, unit_size, slippage)        
            
        elif hold > 0 and low < low10:
            #退出多仓
            stop = low10
            return self.long(cluster, stop, unit_size, slippage)
        else:
            #无交易
            return 0, 0, 0, 0
    
    def transaction(self, cluster, account, cash):
        multiplier, margin, _, cost_mode, cost_rate = self.basic
        
        #计算每个品种的头寸规模，保证每个ATR只会带来risk rate的资产价值变动
        unit_size = int(self.risk_rate * account / (multiplier * self.ATR))
        trade, unit, price, gain = self.trade_rule(cluster, unit_size)        
        
        if cost_mode == 1: #按成交金额收取手续费
            cost = price * multiplier * trade * margin\
                 + price * multiplier * abs(trade) * cost_rate
        else: #按成交数量收取手续费
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
