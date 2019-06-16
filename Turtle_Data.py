# -*- coding: utf-8 -*-
"""
Created on Mon May  6 15:19:58 2019

@author: admin
"""

#import pickle
from collections import defaultdict
import pandas as pd

def get_cluster(corrs):
    codes = corrs.columns.tolist()
    corrs_cluster = {}
    for code in codes:
        corrs_codes = corrs[code].dropna().index.tolist()
        for code_ in list(corrs_codes):
            corrs_codes.extend(corrs[code_].dropna().index.tolist())
        corrs_cluster[code] = list(set(corrs_codes))
    
    return corrs_cluster

def market(Retn, SPAN=60):
    markets = {}
    clusters = defaultdict(dict)
    dates = Retn.index
    for i in range(SPAN, len(dates) + 1):
        date = dates[i-1]
        retn = Retn.iloc[i-SPAN : i, :].dropna(axis=1)
        markets[date] = retn.columns.tolist()
        
        corrs = retn.corr()
        strong = corrs[(corrs >= 0.7) & (corrs < 1)]
        strong.dropna(how='all', inplace=True)
        strong.dropna(how='all', axis=1, inplace=True)
        clusters[date]['strong'] = get_cluster(strong)
        
        weak = corrs[(corrs >= 0.4) & (corrs < 0.7)]
        weak.dropna(how='all', inplace=True)
        weak.dropna(how='all', axis=1, inplace=True)
        clusters[date]['weak'] = get_cluster(weak)
        
    return markets, clusters

def get_clusters2(Retn, SPAN=60):
    clusters = defaultdict(dict)
    dates = Retn.index
    for i in range(SPAN, len(dates) + 1):
        date = dates[i-1]
        retn = Retn.iloc[i-SPAN : i, :].dropna(axis=1)
    
        corrs = retn.corr()
        strong = corrs[(corrs >= 0.7) & (corrs < 1)].stack()
        strong_codes = list(set(strong.index.get_level_values(0)))
        strong_corr_codes = {code: strong_codes for code in strong_codes}
        clusters[date]['strong'] = strong_corr_codes
        
        weak = corrs[(corrs >= 0.4) & (corrs < 0.7)].stack()
        weak_codes = list(set(weak.index.get_level_values(0)))
        weak_corr_codes = {code: weak_codes for code in weak_codes}
        clusters[date]['weak'] = weak_corr_codes
    return clusters

with pd.HDFStore('Turtle.h5') as store:
    Adj_Quotes = store['Adj_Quotes']        
Retn = Adj_Quotes['retn'].unstack()

#markets, clusters = market(Retn)
#with open('Turtle_markets.pkl', 'wb') as f:
#    pickle.dump(markets, f)    
#with open('Turtle_clusters.pkl', 'wb') as f:
#    pickle.dump(clusters, f)
#clusters2 = get_clusters2(Retn)
#with open('Turtle_clusters2.pkl', 'wb') as f:
#    pickle.dump(clusters2, f)

def get_TR(ohlc):
    TRs = {}
    dates = ohlc.index
    for i in range(1, len(ohlc)):
        dates = ohlc.index
        date = dates[i]
        pre_date = dates[i-1]
        tr = max(ohlc.loc[date, 'high'] - ohlc.loc[date, 'low'],
                 ohlc.loc[date, 'high'] - ohlc.loc[pre_date, 'close'],
                 ohlc.loc[pre_date, 'close'] - ohlc.loc[date, 'low'])
        TRs[date] = tr
    TRs = pd.Series(TRs)
    TRs.sort_index(inplace=True) 
    return TRs

def get_ATR(ohlc, SPAN=20):
    TRs = get_TR(ohlc)
    ATRs = {}
    dates = TRs.index
    ATRs[dates[SPAN - 1]] = sum(TRs[:SPAN]) / SPAN
    for i in range(SPAN, len(TRs)):
        date = dates[i]
        pre_date = dates[i-1]
        ATRs[date] = ((SPAN - 1) *  ATRs[pre_date] + TRs[date]) / SPAN
    ATRs = pd.Series(ATRs)
    ATRs.sort_index(inplace=True)
    return ATRs

OHLC = Adj_Quotes.loc[:, ['open', 'high', 'low', 'close']]
codes = list(set(OHLC.index.get_level_values(1)))
codes.sort()
ATR = {}
High55 = {}; Low55 = {}; High20 = {}; Low20 = {}; High10 = {}; Low10 = {}
for code in codes:
    ohlc = OHLC.xs(code, level=1)
    ohlc.dropna(inplace=True)
    ohlc.sort_index(inplace=True)
    
    ATR[code] = get_ATR(ohlc)
    
    High55[code] = ohlc['high'].rolling(55).max()
    High20[code] = ohlc['high'].rolling(20).max()
    High10[code] = ohlc['high'].rolling(10).max()
    
    Low55[code]= ohlc['low'].rolling(55).min()
    Low20[code] = ohlc['low'].rolling(20).min()
    Low10[code] = ohlc['low'].rolling(10).min()

ATR = pd.DataFrame(ATR)
High55 = pd.DataFrame(High55)
High20 = pd.DataFrame(High20)
High10 = pd.DataFrame(High10)

Low55 = pd.DataFrame(Low55)
Low20 = pd.DataFrame(Low20)
Low10 = pd.DataFrame(Low10)

with pd.HDFStore('Turtle.h5') as store:
    store['ATR'] = ATR
    store['High55'] = High55
    store['High20'] = High20
    store['High10'] = High10
    store['Low55'] = Low55
    store['Low20'] = Low20
    store['Low10'] = Low10
    