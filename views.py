import datetime

from ibapi.contract import Contract
from core.program import TestApp, TestClient, TestWrapper, Hashabledict
from ibapi.contract import * # @UnusedWildImport
from ibapi.order import * # @UnusedWildImport
from ibapi.order_state import * # @UnusedWildImport
from ibapi.account_summary_tags import *
from ibapi.utils import (current_fn_name, BadMessage)
from Forms import OrderForm

import time
import os.path
import numpy as np
import pandas as pd
import urllib.request, json
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import matplotlib

class Actions():
    def __init__(self):
        try:
            self.app = TestApp()
            self.app.globalCancelOnly = False
        except:
            raise
        finally:
            pass
            #self.app.dumpTestCoverageSituation()
            #self.app.dumpReqAnsErrSituation()
        if (not self.app.started) or (not self.app.isConnected()) or (not self.app.done):
            try:
                self.app.connect("127.0.0.1", 7497, clientId=0)
                print("serverVersion:%s connectionTime:%s" % (self.app.serverVersion(),
                                                          self.app.twsConnectionTime()))
                if self.app.isConnected():
                    self.app.started = True
            except (KeyboardInterrupt, SystemExit):
                self.app.keyboardInterrupt()
                self.app.keyboardInterruptHard()
            except BadMessage:
                self.app.conn.disconnect()
        self.context = {}
        self.app.callMap = {}
        self.method = "VarCov"
        self.time_p = 'OneWeek'

    def get_msg(self):
        msgs = [msg.replace(b'\x00',b'').decode('utf-8') for msg in self.app.msgs]
        msgs = "\n".join(msgs)
        self.context = {"isConnected":self.app.isConnected()}
        self.context.update({"Msgs": msgs or 
            ("\n".join(list(self.app.ret['Error'])[-1]['Msg']) if 
                len(self.app.ret['Error'])>0 else "Unknown Error")})
        self.context["Positions"] = sorted(list(self.app.ret["Positions"]),
            key=lambda k: k['Symbol'])
        self.context["OrderStatus"] = sorted(list(self.app.ret["OrderStatus"]),
            key=lambda k:k['Id'])
        self.context["OpenOrder"] = sorted(list(self.app.ret["OpenOrder"]),
            key=lambda k:k['OrderId'])
        self.context["AccountSummary"] = sorted(list(self.app.ret["AccountSummary"]),
            key=lambda k:k['Tag'])
        self.context["HistoricalData"] = sorted(list(self.app.ret["HistoricalData"]),
            key=lambda k:k['Symbol'])
        self.context.update({k:v for k,v in self.app.ret.items() if k not in self.context})
    
    def clear(self):
        self.context["Msgs"] = ""

    def connect(self):
        self.app.reqIds(-1)
        with self.app.msg_queue.mutex:
            self.app.msg_queue.queue.clear()
        self.app.msgs.clear()
        self.app.ret.clear()
        self.context.clear()
        if self.app.globalCancelOnly:
            print("Executing GlobalCancel only")
            self.app.reqGlobalCancel()
        else:
            print("Executing requests")
            self.app.reqMarketDataType(3); # delayed
            self.app.reqManagedAccts()
            time.sleep(0.2)
            self.app.reqAccountSummary(self.app.nextOrderId(), "All", 
                #AccountSummaryTags.AllTags)
                "AvailableFunds, NetLiquidation, BuyingPower")
            time.sleep(0.2)
            self.app.cancelAccountSummary(self.app.nextValidOrderId-1);
            self.app.run()

            time.sleep(0.2)
            #self.app.reqPnL(self.app.nextOrderId(), self.app.account, "")
            time.sleep(0.2)
            self.app.reqPositions()
            time.sleep(0.2)
            self.app.cancelPositions()
            time.sleep(0.2)
            self.app.run()
            if len(self.app.ret['Error']) > 0:
            #    self.app.disconnect()
                pass
            else:
                for positions in self.app.ret["Positions"]:
                    contract = Contract()
                    contract.symbol = positions['Symbol']
                    contract.secType = positions['SecType']
                    contract.currency = positions['Currency']
                    contract.conId = positions['ConId']
                    contract.exchange = "SMART"
                    self.app.callMap[self.app.nextValidOrderId] = positions['ConId']
                    time.sleep(0.2)
                    self.app.reqPnLSingle(self.app.nextOrderId(), 
                        self.app.account, "", positions['ConId'])
                    time.sleep(0.2)
                    self.app.cancelPnLSingle(self.app.nextValidOrderId-1)
                    time.sleep(0.2)
                    self.app.callMap[self.app.nextValidOrderId] = positions['ConId']
                    self.app.reqMktData(self.app.nextOrderId(), contract, "104,106,258", False, False, []);
                    time.sleep(0.2)
                    self.app.cancelMktData(self.app.nextValidOrderId-1)
                self.app.run()
                temp_Positions = set()
                for positions in self.app.ret["Positions"]:
                    temp_Positions.add(positions)
                    for daily_PnL_Single in self.app.ret['Daily_PnL_Single']:
                        for reqId, ConId in self.app.callMap.items():
                            if reqId == daily_PnL_Single['ReqId'] and ConId == positions['ConId']:
                                temp_Positions.remove(positions)
                                if(daily_PnL_Single['RealizedPnL'] > 1e20):
                                    daily_PnL_Single['RealizedPnL'] = 0
                                positions.update(daily_PnL_Single)
                                temp_Positions.add(positions)
                del self.app.ret["Positions"]
                self.app.ret["Positions"] = temp_Positions
                
                temp_Positions = set()
                for positions in self.app.ret["Positions"]:
                    temp_Positions.add(positions)
                    for tickGeneric in self.app.ret['TickGeneric']:
                        #for reqId, contract in self.app.callMap.items(): 
                        for reqId, ConId in self.app.callMap.items(): 
                            if reqId == tickGeneric['TickerId'] and ConId == positions['ConId'] and tickGeneric['TickType'] == 24:
                                temp_Positions.remove(positions)
                                positions.update({'ImpVol': tickGeneric['Value']})
                                temp_Positions.add(positions)

                del self.app.ret["Positions"]
                self.app.ret["Positions"] = temp_Positions
                self.app.reqPnL(self.app.nextOrderId(), self.app.account, "")
                time.sleep(0.2)
                self.app.cancelPnL(self.app.nextValidOrderId-1)
                time.sleep(0.2)
                self.app.reqAllOpenOrders()
                time.sleep(0.2)
                # ! [clientrun]
                self.app.run()
                print("Executing requests ... finished")
                # ! [clientrun]
        self.get_msg()

    def disconnect(self):
        self.app.disconnect()
        self.app.started = False
        self.app.msgs = []
        self.app.done = True
        self.app.run()
        self.get_msg()

    def place_order(self, orderform = None):
        Symbol = orderform.cleaned_data['Symbol']
        OrderType = orderform.cleaned_data['OrderType']
        Quantity = orderform.cleaned_data['Quantity']
        Action = orderform.cleaned_data['Action']
        LmtPrice = orderform.cleaned_data['LmtPrice']
        #self.app.reqIds(-1)
        order = Order()
        order.transmit = True
        order.action = Action
        order.orderType = OrderType
        order.totalQuantity = Quantity
        order.lmtPrice = LmtPrice
        #order.tif = "OPG"
        contract = Contract()
        contract.symbol = Symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        self.app.placeOrder(self.app.nextOrderId(), contract, order)
        self.get_msg()
        self.context.update({'orderform':orderform})
        self.connect()
    
    def cancel_order(self, Id):
        print("cancelling")
        self.app.cancelOrder(Id)
        self.connect()

    def risks(self):
        self.get_stats()
        self.get_msg()

    def efffter(self):
        self.get_efffrontier()
        self.get_msg()

    def get_stats(self):
        self.get_historydata()
        self.getcovmatrix()
        self.getbeta()
        self.getVaR()
        #contract = Contract()
        #contract.symbol = "EUR"
        #contract.secType = "CASH"
        #contract.currency = "GBP"
        #contract.exchange = "IDEALPRO"
        #queryTime = (datetime.datetime.today() - datetime.timedelta(days=180)).strftime("%Y%m%d %H:%M:%S")
        #self.app.reqHistoricalData(self.app.nextOrderId(), contract, queryTime,"1 M", "1 day", "MIDPOINT", 1, 1, False, [])
    def get_efffrontier(self):
        self.get_stats()
        self.getMCeffFrontier()
        self.plotMCeffFrontier()
        self.getMineffFrontier()
        self.plotMineffFrontier()

    def get_historydata(self):
        print("get historydata************* ")
        self.time_interval = 1
        if self.time_p == "OneDay": self.time_interval = 1
        if self.time_p == "OneWeek": self.time_interval = 5
        if self.time_p == "OneMonth": self.time_interval = 20
        symbols = "SPY,"
        for position in self.app.ret["Positions"]:
            symbols = symbols + position["Symbol"] + ","
        if len(self.app.ret["Positions"]) > 0:
            symbols = symbols[:-1]
        symbols = [position["Symbol"] for position in self.app.ret["Positions"]]
        if "SPY" not in symbols:
            symbols.append("SPY")
        d = datetime.datetime.today()
        today = d.strftime('%m-%d-%Y')
        for symbol in symbols:
        #down_url = "https://api.iextrading.com/1.0/stock/market/batch?symbols="+symbols+"&types=chart&range=5y"
            #down_url="https://cloud.iexapis.com/stable/stock/market/batch?symbols="+ \
                #symbol+"&types=chart&range=5y&token="+"pk_973c542cc778404cba237ec8c52453af"
            #down_url = "https://eodhistoricaldata.com/api/eod/"+symbol+".US?from=2004-07-01&to=2019-07-01& \
                #api_token=OeAFFmMliFG5orCUuwAKQ8l4WWFQ67YX&period=d&fmt=json"
            
            down_url = "https://www.alphavantage.co/query?apikey=W06CSNGZGRK6S2MB&function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full&symbol="+symbol
            file = "Data/data_alphavantage_adjustclose_daily_{}_{}.csv".format(symbol, today)
            while not os.path.exists(file):
                simple_list = []
                with urllib.request.urlopen(down_url) as url:
                    data = json.loads(url.read().decode())
                    for date, time_series in data['Time Series (Daily)'].items():
                        adjclose = time_series['5. adjusted close']
                        simple_list.append([date, adjclose])
                    df = pd.DataFrame(simple_list,columns=['date','adjclose'],index=None)
                    df = df.set_index("date")
                    df.to_csv(file)
            df = pd.read_csv(file,index_col="date")
            self.app.ret["HistoricalData"].add(Hashabledict({'Symbol':symbol, 'TS':df},name="HistoricalData"))
            self.get_msg()

    def getcovmatrix(self):
        print("get covmatrix************* ")
        self.covMatrix = {}
        stocks_df = []
        self.stocks = []
        for historicalData in self.context["HistoricalData"]:
            contract = historicalData['Symbol']
            for positions in self.app.ret['Positions']:
                if positions['Symbol'] == contract:
                    stocks_df.append(historicalData['TS'])
                    self.stocks.append(historicalData['Symbol'])
        self.stocks_df = pd.concat(stocks_df,axis=1,sort=False)
        self.stocks_df.columns = self.stocks
        self.log_ret = np.log(self.stocks_df/self.stocks_df.shift(-self.time_interval))
        self.ret = self.stocks_df/self.stocks_df.shift(-self.time_interval) - 1
        self.covMatrix = self.log_ret.cov()

    def getbeta(self):
        print("get beta************* ")
        for historicalData in self.context["HistoricalData"]:
            contract = historicalData['Symbol']
            temp_Positions = set()
            for positions in self.app.ret['Positions']:
                temp_Positions.add(positions)
                if positions['Symbol'] == contract:
                    temp_Positions.remove(positions)
                    positions['Beta'] = self.covMatrix[contract]['SPY'] / self.covMatrix['SPY']['SPY']
                    temp_Positions.add(positions)

    def getVaR(self):
        print(self.method)
        print("get VaR************* ")
        assets = {}
        for historicalData in self.context["HistoricalData"]:
            contract = historicalData['Symbol']
            meanreturn = np.mean(self.ret[contract].dropna())
            stdreturn = np.std(self.ret[contract].dropna())
            temp_Positions = set()
            for positions in self.app.ret['Positions']:
                temp_Positions.add(positions)
                if positions['Symbol'] == contract:
                    temp_Positions.remove(positions)
                    #positions['Beta'] = self.covMatrix[contract]['SPY'] / self.covMatrix['SPY']['SPY']
                    positions['Assets'] = positions["AvgCost"] * positions['Position']
                    assets.update({contract : positions['Assets']})
                    if self.method == "VarCov":
                        positions["VaR_90"] = meanreturn + 1.282 * stdreturn
                        positions["VaR_95"] = meanreturn + 1.645 * stdreturn
                        positions["VaR_99"] = meanreturn + 2.326 * stdreturn
                    elif self.method == "Historical":
                        positions["VaR_90"] = -np.percentile(self.ret[contract].dropna(), 10);
                        positions["VaR_95"] = -np.percentile(self.ret[contract].dropna(), 5);
                        positions["VaR_99"] = -np.percentile(self.ret[contract].dropna(), 1);
                    elif self.method == "MonteCarlo":
                        np.random.seed(42)
                        n_sims = 1000
                        sim_returns = np.random.normal(meanreturn, stdreturn, n_sims)
                        positions["VaR_90"] = -np.percentile(sim_returns, 10)
                        positions["VaR_95"] = -np.percentile(sim_returns, 5)
                        positions["VaR_99"] = -np.percentile(sim_returns, 1)
                    else:
                        positions["VaR_90"] = 0
                        positions["VaR_95"] = 0
                        positions["VaR_99"] = 0

                    positions["VaR_90"] = positions['Assets'] * positions["VaR_90"]
                    positions["VaR_95"] = positions['Assets'] * positions["VaR_95"]
                    positions["VaR_99"] = positions['Assets'] * positions["VaR_99"]
                    temp_Positions.add(positions)
            del self.app.ret['Positions']
            self.app.ret['Positions'] = temp_Positions
        self.assets = np.array(list(assets.values()))
        self.app.ret['AccountSummary'].discard(Hashabledict({"Tag": "VaR_90"},name="AccountSummary"))
        self.app.ret['AccountSummary'].discard(Hashabledict({"Tag": "VaR_95"},name="AccountSummary"))
        self.app.ret['AccountSummary'].discard(Hashabledict({"Tag": "VaR_99"},name="AccountSummary"))
        self.app.ret['AccountSummary'].add(Hashabledict({"ReqId": -1, "Account": self.app.account, 
              "Tag": "VaR_90", "Currency": "",
              "Value": 1.282 * np.sqrt(np.dot(self.assets.T, np.dot(self.covMatrix, self.assets)))},
            name="AccountSummary"))
        self.app.ret['AccountSummary'].add(Hashabledict({"ReqId": -1, "Account": self.app.account,
              "Tag": "VaR_95", "Currency": "",
              "Value": 1.645 * np.sqrt(np.dot(self.assets.T, np.dot(self.covMatrix, self.assets)))},
            name="AccountSummary"))
        self.app.ret['AccountSummary'].add(Hashabledict({"ReqId": -1, "Account": self.app.account,
              "Tag": "VaR_99", "Currency": "",
              "Value": 2.326 * np.sqrt(np.dot(self.assets.T, np.dot(self.covMatrix, self.assets)))},
            name="AccountSummary"))

    def getMCeffFrontier(self):
        self.num_ports = 100
        self.log_ret = np.log(self.stocks_df/self.stocks_df.shift(-self.time_interval))
        self.all_weights = np.zeros((self.num_ports, len(self.stocks)))
        self.ret_arr = np.zeros(self.num_ports)
        self.vol_arr = np.zeros(self.num_ports)
        self.sharpe_arr = np.zeros(self.num_ports)
        self.timespan = 252/self.time_interval
        for x in range(self.num_ports):
            # Weights
            weights = np.array(np.random.random(len(self.stocks)))
            weights = weights/np.sum(weights)
            
            # Save weights
            self.all_weights[x,:] = weights
            
            # Expected return
            self.ret_arr[x] = np.sum( (self.log_ret.mean() * weights * self.timespan))
            
            # Expected volatility
            self.vol_arr[x] = np.sqrt(np.dot(weights.T, np.dot(self.log_ret.cov()*self.timespan, weights)))
            
            # Sharpe Ratio
            self.sharpe_arr[x] = self.ret_arr[x]/self.vol_arr[x]

    def plotMCeffFrontier(self):
        self.max_sr_ret = self.ret_arr[self.sharpe_arr.argmax()]
        self.max_sr_vol = self.vol_arr[self.sharpe_arr.argmax()]
        self.curr_weight = self.assets/np.sum(self.assets)
        print("weights for max sharpe", self.stocks, self.all_weights[self.sharpe_arr.argmax(),:])
        self.curr_sr_ret = np.sum( (self.log_ret.mean() * self.curr_weight * self.timespan))
        self.curr_sr_vol = np.sqrt(np.dot(self.curr_weight.T, np.dot(self.log_ret.cov()*self.timespan, self.curr_weight)))
        #plt.figure(figsize=(12,8))
        #plt.scatter(self.vol_arr, self.ret_arr, c=self.sharpe_arr, cmap='viridis')
        #plt.colorbar(label='Sharpe Ratio')
        #plt.xlabel('Volatility')
        #plt.ylabel('Return')
        #plt.scatter(max_sr_vol, max_sr_ret,c='red', s=50) # red dot
        #plt.scatter(curr_sr_vol, curr_sr_ret,c='black', s=50) # black dot
        #plt.savefig('figs/mcftier.png')
        #plt.show()

    def get_ret_vol_sr(self,weights):
        weights = np.array(weights)
        ret = np.sum(self.log_ret.mean() * weights) * self.timespan
        vol = np.sqrt(np.dot(weights.T, np.dot(self.log_ret.cov()*self.timespan, weights)))
        sr = ret/vol
        return np.array([ret, vol, sr])

    def neg_sharpe(self,weights):
    # the number 2 is the sharpe ratio index from the get_ret_vol_sr
        return get_ret_vol_sr(weights)[2] * -1

    def check_sum(self,weights):
        #return 0 if sum of the weights is 1
        return np.sum(weights)-1
    
    def minimize_volatility(self,weights):
        return self.get_ret_vol_sr(weights)[1]

    def getMineffFrontier(self):
        self.frontier_y = np.linspace(0,0.5,20)
        self.frontier_x = []
        bounds = [(0,1)]*len(self.stocks)
        init_guess = [1./len(self.stocks)]*len(self.stocks)

        for possible_return in self.frontier_y:
            cons = ({'type':'eq', 'fun':self.check_sum},
                    {'type':'eq', 'fun': lambda w: self.get_ret_vol_sr(w)[0] - possible_return})
            
            result = minimize(self.minimize_volatility,init_guess,method='SLSQP', bounds=bounds, constraints=cons)
            self.frontier_x.append(result['fun'])

    def plotMineffFrontier(self):
        self.figure = plt.figure()
        axes = self.figure.add_subplot(211)
        im = axes.scatter(self.vol_arr, self.ret_arr, c=self.sharpe_arr, cmap='viridis')
        plt.colorbar(im,label='Sharpe Ratio')
        axes.set_xlabel('Yearly Volatility')
        axes.set_ylabel('Yearly Return')
        axes.scatter(self.max_sr_vol, self.max_sr_ret,c='red', s=50, label="max sharpe portifolio") # red dot
        axes.scatter(self.curr_sr_vol, self.curr_sr_ret,c='black', s=50, label='current portifolio') # black dot
        axes.legend()
        axes.plot(self.frontier_x,self.frontier_y, 'r--', linewidth=3)
        axes = self.figure.add_subplot(212)
        N = len(self.curr_weight)
        width = 0.8
        _X = np.arange(N)
        bar1 = axes.bar(_X-width/2.+0/2.*width, self.curr_weight, 
            width=width/2., color='b', align='edge')
        bar2 = axes.bar(_X-width/2.+1/2.*width, self.all_weights[self.sharpe_arr.argmax(),:], 
            width=width/2., color='g', align='edge')

        def autolabel(rects):
            """
            Attach a text label above each bar displaying its height
            """
            for rect in rects:
                height = rect.get_height()
                axes.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                        '%.1f%%' % (height*100),
                        ha='center', va='bottom')
        autolabel(bar1)
        autolabel(bar2)
        axes.set_ylabel("portifolio weights")
        axes.set_xticks(_X)
        axes.set_xticklabels(self.stocks)
        axes.legend( (bar1, bar2), ('current portifolio','optimized portifolio'),loc='best' )
        self.figure.tight_layout()
        plt.savefig('figs/bdftier.png')
        #plt.show()