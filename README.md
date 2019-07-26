# IBGUI
A tool for Interactive Broker software, help to deal with orders and control risks

Interactive Brokers(IB) is the largest electronic brokerage firm in the US by number of daily average revenue trades, and is the leading forex broker. 
Interactive Brokers also targets commodity trading advisors, making it the fifth-largest prime broker servicing them.

https://www.interactivebrokers.com/en/home.php

It has a rich and powerful API system(C++, java, python, excel)

https://interactivebrokers.github.io/tws-api/introduction.html

as well as TWS(trading workstation) that helps traders to do quantitative trading and visulize technique indicators. It also has a risk controlling panel that manage the risk of current portifolio.

However, we still want to self-designed tool to help look at more deep risk controlling parameters and optimize our portifolio.
This project is an assistant software bringing more risk management tool, written in Python3 and wxPython framework.
More importantly, it is flexible and we can implement modern portifolio theory into our real trading. Even we have some model generating alpha produced offline, we are able to adjust our trading stragety accordingly and timely.

Here is a overview of the software panel:
![Panel Overview](https://xuqiao.tk/wp-content/uploads/2019/07/Screen-Shot-2019-07-26-at-11.09.09-AM-1024x567.png)

Some features:

* List current positions and p&l
* List current open orders
* Calculate VaR of the whole portfolio
* Calculate VaR of individual positions
* Submit and Cancel orders
* Draw Efficient Frontier based on the positions in the current portfolio
* Recommend maximize Sharpe Ratio portfolio and compare to current portfolio
* Can select VaR calculation method, including Var-Cov method, Historical method and Monte-Carlo method
* Can select various time period, including one-day, one-week and one-month

Some caveats:
* Only apply to US stocks
* Daily adjusted close data from alphavantage are used
* Only support limit order and market order
* Some times you need to refresh to get a few blanks filled
* Due to computation limit, the number of Monte-Carlo simulated portfolios are not so many, so some times the recommended portfolio are not identical in different runs
* The message from server is not well formatted

Usage:
log in your TWS workstation first. (recommend first try it in a paper account), go to “Global configurations…”, and “API -> Settings”, check “Enable ActiveX and Socket Clients”, make sure the socket port is 7497. If you do not want to place order through the tool, just check “Read API only”.

Only through the TWS or the gateway the tool could make connections with the IB server. Currently you can use username “test” to test the features.

```python
mkdir Data
python3 MainFrame.py
```

To do:
* Add setup.py
* Support more than one account switch and calculation, submit sychronized orders
* Add more test case to make it more robust
* Get from more reliable source, like IB historical data database
