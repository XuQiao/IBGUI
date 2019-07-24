import pandas as pd
from collections import OrderedDict, defaultdict
import collections
import datetime
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
d = datetime.datetime.today()
today = d.strftime('%m-%d-%Y')
ret = collections.defaultdict(set)
f1 = "Data/data_alphavantage_adjustclose_daily_{}_{}.csv".format('GE', today)
df = pd.read_csv(f1)
f1 = "Data/data_alphavantage_adjustclose_daily_{}_{}.csv".format('AMD', today)
df_1 = pd.read_csv(f1)
ret['d'].add(Hashabledict({'b':'d','a':df,'Symbol':'s'},name="HistoricalData"))
ret['d'].add(Hashabledict({'b':'d','a':df_1,'Symbol':'s'},name="HistoricalData"))

