import pandas as pd
from collections import OrderedDict, defaultdict
import collections
import datetime
import matplotlib.pyplot as plt

def plotMineffFrontier():
    figure = plt.figure()
    axes = figure.add_subplot(121)
    im = axes.scatter([1,2,3], [3,4,5], c=[0,1,2], cmap='viridis')
    plt.colorbar(im,label='Sharpe Ratio')
    plt.xlabel('Volatility')
    plt.ylabel('Return')
    axes = figure.add_subplot(122)
    axes.plot([0,1,2],[2,1,0], 'r--', linewidth=3)
    figure.tight_layout()    
    plt.show()

#plotMineffFrontier()

class Hashabledict(OrderedDict):
    def __init__(self, o=OrderedDict(),name="other"):
        super().__init__(o)
        self.name = name
    def __hash__(self):
        if self.name == "AccountSummary":
            return hash(self['Tag'])
        elif self.name == "Positions":
            return hash(self['ConId'])
        elif self.name == "OrderStatus":
            return hash(self['Id'])        
        elif self.name == "OpenOrder":
            return hash(self['OrderId'])
        elif self.name == "HistoricalData":
            #return hash(self['requestId'])
            return hash(self['Symbol'])
        else:
            return hash(frozenset(self))
    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
s=set()
s.add(Hashabledict({'Tag':'t','o':'1'},name="AccountSummary"))
s.add(Hashabledict({'Tag':'s','o':'2'},name="AccountSummary"))
s.add(Hashabledict({'Tag':'1','o':'3'},name="AccountSummary"))
s.add(Hashabledict({'Tag':'t','o':'4'},name="AccountSummary"))
print(s)

#d = datetime.datetime.today()
#today = d.strftime('%m-%d-%Y')
#ret = collections.defaultdict(set)
#f1 = "Data/data_alphavantage_adjustclose_daily_{}_{}.csv".format('TSLA', today)
#df = pd.read_csv(f1,index_col="date")
#f1 = "Data/data_alphavantage_adjustclose_daily_{}_{}.csv".format('AMD', today)
#df_1 = pd.read_csv(f1,index_col="date")
#stocks_df = pd.concat([df,df_1],axis=1,sort=True)
#print(stocks_df.head())
#print(stocks_df/stocks_df.shift(1))
#ret['d'].add(Hashabledict({'b':'d','a':df,'Symbol':'s'},name="HistoricalData"))
#ret['d'].add(Hashabledict({'b':'d','a':df_1,'Symbol':'s'},name="HistoricalData"))

