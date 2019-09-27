# -*- encoding: utf-8 -*-
#!/bin/python

import wx
import Login
import views
from Forms import OrderForm
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import csv
from pandas.io.json import json_normalize
import numpy as np
import flatten_json
import time, socket, threading
import wx.lib.agw.flatnotebook as fnb
import wx.lib.scrolledpanel as scrolled

def autoexec(function):
    def wrapper():
        #nexttime = time.time()
        #while True:
        #    function()          # take t sec
        #    nexttime += 10
        #    sleeptime = nexttime - time.time()
        #    if sleeptime > 0:
        #        time.sleep(sleeptime)
        threading.Timer(10.0, function).start() # not thread safe
        #wx.CallLater(10000, function)
    return wrapper

class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(MainFrame, self).__init__(*args, **kw)

        # Ask user to login
        self.dlg = Login.LoginDialog()
        self.dlg.ShowModal()
        self.authenticated = self.dlg.logged_in
        if not self.authenticated:
            self.Close()
        # create a menu bar
        self.makeMenuBar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Log in successful!")
        self.makeTabs()
        self.Show()
        self.RefreshTime = 10

    def makeTabs(self):
        self.pnl = wx.Panel(self, wx.ID_ANY)
        self.nb = fnb.FlatNotebook(self.pnl)
        self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTabChange)
        # How many instances do we open right now?
        self.nins = 0
        self.ports = []
        for port in range(7490,7500):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind(("127.0.0.1", port))
            except Exception as e:
                self.ports.append(port)
            finally:
                s.close()
        self.tabs = []
        print(self.ports)
        self.master = None
        self.slavery = None
        for port in self.ports:
            name = "port %d" % port
            tab = Tab(self.nb, self, port=port, clientId = port-7497)
            self.tabs.append(tab)
            self.nb.AddPage(tab, name)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        st = wx.StaticText(self.pnl, label="Hi, {}".format(self.dlg.user.GetValue()), pos=(10,10))
        font = st.GetFont()
        font = font.Bold()
        st.SetFont(font)
        self.sizer_greet = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_greet.Add(st)
        self.sizer.Add(self.sizer_greet,0,wx.ALL|wx.EXPAND,3)
        self.sizer.Add(self.nb, 1, wx.EXPAND)
        self.pnl.SetSizer(self.sizer)

    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        helloItem = fileMenu.Append(-1, "&Hello...\tCtrl-H",
                "Help string shown in status bar for this menu item")
        fileMenu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)
        fileMenu.AppendSeparator()
        exportItem = fileMenu.Append(-1, "Export to csv file","save to disk")
        
        # Now a help menu for the about item
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        self.toolMenu = wx.Menu()
        self.MonitorItem = self.toolMenu.Append(-1, "&Start Monitor...\tCtrl-M",
                "Start to Monitor new orders")
        self.Monitored = False
        self.orderpool = {}

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(self.toolMenu, "&Tool")
        menuBar.Append(helpMenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
        self.Bind(wx.EVT_MENU, self.OnMonitor, self.MonitorItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)
        self.Bind(wx.EVT_MENU, self.OnExport, exportItem)

    def OnTabChange(self, event):
        # Works on Windows, Linux and Mac
        self.current_page = self.nb.GetCurrentPage()
        self.SetStatusText("tab " + str(self.current_page.clientId))
        event.Skip()

    def OnHello(self, event):
        """Say hello to the user."""
        wx.MessageBox("Hello again from wxPython")

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnMonitor(self, event):
        if not(self.master and self.slavery):
            wx.MessageBox("Please indicate Master and Slavery")
            return
        self.Monitored = not self.Monitored
        status = "Stop" if self.Monitored else "Start"
        rev_status = "Stop" if not self.Monitored else "Start"
        self.MonitorItem.SetItemLabel("&{} Monitor...\tCtrl-M".format(status));
        self.MonitorItem.SetHelp("{} to Monitor".format(status));
        self.Refresh()
        if self.Monitored:
            wx.MessageBox("{} Auto Monitor every 10 seconds!".format(rev_status))

        def Execute():
            #threading.Timer(10.0, Execute).start()
            if not self.Monitored:
                return
            for openorder in self.master.action.context.get("OpenOrder",[]):
                if (openorder["OrderId"] not in self.orderpool.keys()) and openorder['Account'] == self.master.currentAccount:
                    exists = False
                    for openorder_s in self.slavery.action.context.get("OpenOrder",[]):
                        if openorder_s.same(openorder) and openorder_s['Account'] == self.slavery.currentAccount:
                            exists = True
                        if openorder_s['OrderId'] in self.orderpool.values():
                            exists = True
                    if not exists:
                        self.orderpool.update({openorder["OrderId"]:self.slavery.app.nextValidOrderId})
                        self.slavery.action.place_order(openorder=openorder)
            self.master.action.connect()
            if self.master.action.app.isConnected():
                self.master.update()
            self.master.isChecked = self.Monitored
            self.slavery.action.connect()
            if self.slavery.action.app.isConnected():
                self.slavery.update()
            self.slavery.isChecked = self.Monitored
            if self.Monitored:
                wx.CallLater(self.RefreshTime*100,Execute)
        Execute()

    def OnExport(self, event):
        with wx.FileDialog(self, "Save CSV file", wildcard="CSV files (*.csv)|*.csv",
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                self.action.context.pop('HistoricalData',None)
                flat = flatten_json.flatten(self.action.context)
                flat = json_normalize(flat)
                flat.to_csv(pathname)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)
            wx.MessageBox("Saved")

    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("This is a Program for Interactive Broker System",
                      "Developed by Qiao Xu",
                      wx.OK|wx.ICON_INFORMATION)
        
class Tab(wx.Panel):
    def __init__(self, parent, frame, ip = "127.0.0.1", port = 7497, clientId = 0):
        self.ip = ip
        self.port = port
        self.clientId = clientId
        self.frame = frame
        self.pnl = self
        wx.Panel.__init__(self, parent)
        try:
            self.action = views.Actions(self.ip, self.port, self.clientId)
        except:
            self.btn_conn.Disable()
            self.btn_logout.Disable()
        
        self.basiclayout()
        self.SetSizer(self.sizer)
        self.isChecked = False

        #self.Show()

    def basiclayout(self):
        # create a panel in the frame
        #self.pnl = wx.Panel(self, wx.ID_ANY)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.btn_logout = wx.Button(self.pnl, label="Logout",pos = (210,20))
        self.btn_logout.Bind(wx.EVT_BUTTON, self.OnLogout)
        self.btn_conn = wx.Button(self.pnl, label="Connect",pos = (110,20))
        self.btn_conn.Bind(wx.EVT_BUTTON, self.OnConnect)
        # and put some text with a larger bold font on it

        self.sizer_commands = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_commands.AddMany([self.btn_conn,self.btn_logout])
        
        self.sizer.Add(self.sizer_commands,0,wx.ALL|wx.EXPAND,3)
        #self.pnl.Layout()
        #self.pnl.Refresh()

    def update(self):
        for child in self.GetChildren():
            child.Destroy()
        #if 'sizer2' in self.__dict__:
        #    self.sizer2.Clear(True)
        #if 'sizer1' in self.__dict__:
        #    self.sizer1.Clear(True)
        #if 'sizer0' in self.__dict__:
        #    self.sizer0.Clear(True)
        #self.sizer_commands.Clear(True)
        #self.sizer.Clear(True)
        #self.basiclayout()

        self.btn_master = wx.Button(self.pnl, label="Master",pos = (400,30))
        self.btn_master.Bind(wx.EVT_BUTTON, self.OnMaster)
        self.btn_slavery = wx.Button(self.pnl, label="Slavery",pos = (500,30))
        self.btn_slavery.Bind(wx.EVT_BUTTON, self.OnSlavery)
        if self.frame.master == self:
            self.btn_master.SetBackgroundColour('#1E90FF')
        else:
            self.btn_master.SetBackgroundColour('#FFFFFF')
        if self.frame.slavery == self:
            self.btn_slavery.SetBackgroundColour('#FF6347')
        else: 
            self.btn_slavery.SetBackgroundColour('#FFFFFF')
        self.checkbox = wx.CheckBox(self.pnl, label='Auto Refresh',pos = (600,30))
        self.checkbox.SetValue(self.isChecked)
        self.checkbox.Bind(wx.EVT_CHECKBOX, self.OnAutoRefresh)

        self.sizer_auto = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_auto.AddMany([self.btn_master, self.btn_slavery, self.checkbox])
        self.sizer.Add(self.sizer_auto)

        self.Method = wx.RadioBox(self.pnl, label = 'Method', pos = (80,30), choices = ["VarCov","Historical","MonteCarlo"], 
            majorDimension = 1, style = wx.RA_SPECIFY_ROWS)
        self.Method.SetStringSelection(self.action.method)
        self.Time_p = wx.RadioBox(self.pnl, label = 'Time_Interval', pos = (60,30), choices = ["OneDay","OneWeek","OneMonth"], 
            majorDimension = 1, style = wx.RA_SPECIFY_ROWS) 
        self.Time_p.SetStringSelection(self.action.time_p)
        self.Method.Bind(wx.EVT_RADIOBOX, self.OnMethod),
        self.Time_p.Bind(wx.EVT_RADIOBOX, self.OnTime_p),

        self.btn_refresh = wx.Button(self.pnl, label="Refresh",pos = (10,20))
        self.btn_refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
        self.btn_disconn = wx.Button(self.pnl, label="DisConnect",pos = (310,20))
        self.btn_disconn.Bind(wx.EVT_BUTTON, self.OnDisconnect)
        self.btn_clear = wx.Button(self.pnl, label="Clear",pos = (410,20))
        self.btn_clear.Bind(wx.EVT_BUTTON, self.OnClear)
        
        self.btn_risk = wx.Button(self.pnl, label="Risk Factors", pos = (510, 20))
        self.btn_risk.Bind(wx.EVT_BUTTON, self.OnRisk)
        self.btn_efffter = wx.Button(self.pnl, label="Eff Frontier", pos = (610, 20))
        self.btn_efffter.Bind(wx.EVT_BUTTON, self.OnEfffter)
        
        self.btn_placeorder = wx.Button(self.pnl, label="Submit Order", pos = (710, 20))
        self.btn_placeorder.Bind(wx.EVT_BUTTON, self.OnPlaceOrder)

        self.sizer_commands.AddMany([self.btn_refresh,self.btn_disconn,self.btn_clear,
        self.btn_risk,self.btn_placeorder,self.btn_efffter,self.Method, self.Time_p])
        #if self.action.app.ret:

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        #account list
        self.st4 = wx.StaticText(self.pnl, label = "account list:", pos = (10,150))
        self.sizer2.Add(self.st4)
        #self.list_ctrl4 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,100), 
        #    style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        #for column, prop in enumerate(['Account']):
        #    self.list_ctrl4.InsertColumn(column, prop)
        #    for row, account_list in enumerate(self.action.context.get('Account_list',[])):
        #        if column == 0:    
        #            self.list_ctrl4.InsertItem(row, account_list) 
        #        else:
        #            self.list_ctrl4.SetItem(row, column, account_list)
        #self.sizer2.Add(self.list_ctrl4,0,wx.EXPAND)
        self.chbox=wx.ComboBox(self.pnl,-1,value=self.currentAccount,choices=list(self.action.context['Account_list']))
        self.chbox.Bind(wx.EVT_COMBOBOX,self.OnCombobox)
        self.sizer2.Add(self.chbox)

        # account property
        self.list_ctrl1 = wx.ListCtrl(self.pnl, pos = (10, 50), size=(-1,100), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)  
        for column, prop in enumerate(['Tag','Value']):
            self.list_ctrl1.InsertColumn(column, prop)
            irow = 0
            for row, accountSummary in enumerate(self.action.context.get('AccountSummary',[])):
                if accountSummary['Account'] == self.currentAccount:
                    temp = accountSummary[prop]
                    if type(temp) in [float, int, np.float64]:
                        temp = '%.2f' % temp
                    if 'Value' in prop and 'VaR' in self.action.context['AccountSummary'][irow]['Tag']:
                        temp = '%s(%.2f%%)'%(temp,float(accountSummary[prop])/np.sum(self.action.assets)*100)
                    if column == 0:
                        self.list_ctrl1.InsertItem(irow, temp) 
                    else:
                        self.list_ctrl1.SetItem(irow, column, temp)
                    irow += 1
            self.list_ctrl1.SetColumnWidth(column, wx.LIST_AUTOSIZE)

        self.sizer2.Add(self.list_ctrl1,0,wx.EXPAND)
        
        #p & l
        self.st2 = wx.StaticText(self.pnl, label="P && L:", pos = (10,200))
        self.sizer2.Add(self.st2)
        self.list_ctrl2 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,100), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        for column, prop in enumerate(['DailyPnL','RealizedPnL','UnrealizedPnL']):
            self.list_ctrl2.InsertColumn(column, prop)
            irow = 0
            for row, daily_PnL in enumerate(self.action.context.get('Daily_PnL',[])):
                if daily_PnL.get('Account','') == self.currentAccount:
                    temp = daily_PnL[prop]
                    if type(temp) in [float, int, np.float64]:
                        temp = '%.2f' % temp
                    if column == 0:
                        self.list_ctrl2.InsertItem(irow, temp)
                    else:
                        self.list_ctrl2.SetItem(irow, column, temp)
                    irow += 1
            self.list_ctrl2.SetColumnWidth(column, wx.LIST_AUTOSIZE)

        self.sizer2.Add(self.list_ctrl2,0,wx.EXPAND)

        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer1.Add(self.sizer2)

        #positions
        self.st1 = wx.StaticText(self.pnl, label="current Positions:", pos=(70,150))
        self.sizer1.Add(self.st1)
        self.list_ctrl3 = wx.ListCtrl(self.pnl, pos = (10, 50), size=(-1,200), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        for column, prop in enumerate(['Symbol','Position','Currency','SecType','AvgCost','DailyPnL','UnrealizedPnL','RealizedPnL'
            ,'Value','Beta','ImpVol','VaR_90','VaR_95','VaR_99']):
            self.list_ctrl3.InsertColumn(column, prop)
            irow = 0
            for row, positions in enumerate(self.action.context.get('Positions',[])):
                if positions['Account'] == self.currentAccount and positions['Position']!=0:  
                    if prop not in positions:
                        positions[prop] = ""
                    temp = positions[prop]
                    #if positions['Currency'] != 'USD' and positions['SecType'] == 'CASH' and column == 'Symbol':
                    #    temp = temp + " " + positions['Currency']
                    if type(positions[prop]) in [float, int, np.float64]:
                        temp = '%.2f' % temp
                    if 'VaR' in prop and positions[prop]:
                        temp = '%s(%.2f%%)'%(temp,
                            float(temp)/(float(positions['AvgCost'])*float(positions['Position']))*100)
                    if column == 0:
                        self.list_ctrl3.InsertItem(irow, temp)
                    else:
                        self.list_ctrl3.SetItem(irow, column, temp)
                    irow += 1
            self.list_ctrl3.SetColumnWidth(column, wx.LIST_AUTOSIZE)
        self.sizer1.Add(self.list_ctrl3,1,wx.EXPAND)

        #open orders
        self.st5 = wx.StaticText(self.pnl, label="Open Orders:", pos = (10,200))
        self.sizer_cancelform = wx.BoxSizer(wx.HORIZONTAL)
        #self.sizer_cb = wx.BoxSizer(wx.VERTICAL)
        #self.sizer_cb.Add(self.st1)
        self.sizer1.Add(self.st5)
        self.list_ctrl4 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,150),
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING) 
        self.btn_cancelorders = {}
        self.cancelMap = {}
        #self.scrolledpanel = scrolled.ScrolledPanel(self.pnl,-1, style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        for column, prop in enumerate(['OrderId','Symbol','SecType','Action','OrderType','LmtPrice'
            ,'TotalQty','Status','Filled','Remaining','AvgFillPrice','WhyHeld'
            ,'MktCapPrice','Id','Operation']):
            self.list_ctrl4.InsertColumn(column, prop)
            irow = 0
            for row, orderstatus in enumerate(self.action.context.get("OrderStatus",[])):
                for openorder in self.action.context["OpenOrder"]:
                    if openorder["OrderId"] == orderstatus["Id"] and openorder['Account'] == self.currentAccount:
                        temp = openorder[prop] if column < 8 else (orderstatus[prop] if column < 14 else 'cancel')
                        if type(temp) in [float, int]:
                            temp = '%.2f' % temp
                        if column == 0:
                            self.list_ctrl4.InsertItem(irow, temp)
                            #self.btn_cancelorders[orderstatus['Id']] = wx.Button(self.pnl, label="Cancel Order",name=str(orderstatus['Id']))
                            #self.btn_cancelorders[orderstatus['Id']].Bind(wx.EVT_BUTTON, self.OnCancelOrder)
                        else:
                            self.list_ctrl4.SetItem(irow, column, temp)
                        item = self.list_ctrl4.GetItem(irow, column)
                        if prop == "Operation":
                            self.cancelMap.update({irow: str(orderstatus['Id'])})
                            #wx.EVT_LEFT_DOWN(item, self.OnCancelOrder)
                            item.SetBackgroundColour(wx.RED)  
                        irow += 1
                self.list_ctrl4.SetColumnWidth(column, wx.LIST_AUTOSIZE)
        self.list_ctrl4.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnCancelOrder)
        #self.sizer_cb.AddSpacer(14)
        #for button in self.btn_cancelorders.values():
        #    self.sizer_cb.Add(button)
        #self.scrolledpanel.SetSizer(self.sizer_cb)
        #self.scrolledpanel.SetAutoLayout(1)
        #self.scrolledpanel.SetupScrolling()
        self.sizer_cancelform.Add(self.list_ctrl4)
        self.sizer1.Add(self.sizer_cancelform)
        #make orders
        self.orderform = OrderForm(self)
        self.sizer1.Add(self.orderform.sizer,0,wx.EXPAND,1)

        #msg box
        self.st6 = wx.StaticText(self.pnl, label="Message from the server", size=(-1,30))
        self.sizer1.Add(self.st6,0, wx.EXPAND,1)
        Msgs = self.action.context.get("Msgs", "Nothing wrong from server")
        self.st3 = wx.TextCtrl(self.pnl,value=Msgs, size=(-1,100),style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_BESTWRAP)
        #self.st3.SetValue(str(Msgs))
        self.sizer1.Add(self.st3,0,wx.EXPAND|wx.ALL)
               
        self.sizer0 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer0.Add(self.sizer1)
        # risk plot
        if 'figure' in self.action.__dict__:
            self.canvas = FigureCanvas(self.pnl, -1, self.action.figure)
            self.sizer0.Add(self.canvas, 0, wx.EXPAND)
        
        self.sizer.Add(self.sizer0,0,wx.EXPAND,1)
        #self.Refresh()
        #print(self.action.context)
        self.pnl.SetSizer(self.sizer)
        #self.pnl.Fit()
        self.Layout()
        self.Show()
        self.frame.Maximize()        

    def SetStatusText(self, text):
        self.frame.SetStatusText(text)

    def OnMaster(self, event):
        if self.frame.slavery == self:
            wx.MessageBox("Cannot set up same master and slavery!")
            return
        if self.frame.master == self:
            self.frame.master = None
            self.btn_master.SetBackgroundColour('#FFFFFF')
        else:
            self.frame.master = self
            self.btn_master.SetBackgroundColour('#1E90FF')
            self.btn_master.SetForegroundColour('#1E90FF')
            for tab in self.frame.tabs:
                if tab != self:
                    tab.btn_master.SetBackgroundColour('#FFFFFF')
        self.Refresh()

    def OnSlavery(self, event):
        if self.frame.master == self:
            wx.MessageBox("Cannot set up same master and slavery!")
            return
        if self.frame.slavery == self:
            self.frame.slavery = None
            self.btn_slavery.SetBackgroundColour('#FFFFFF')
        else:
            self.frame.slavery = self
            self.btn_slavery.SetBackgroundColour('#FF6347')
            self.btn_slavery.SetForegroundColour('#FF6347')
            for tab in self.frame.tabs:
                if tab != self:
                    tab.btn_slavery.SetBackgroundColour('#FFFFFF')
        self.Refresh()

    def OnCombobox(self, event):
        self.currentAccount = event.GetString()
        self.action.app.account = self.currentAccount
        self.update()

    def OnConnect(self, event):
        self.SetStatusText("Connecting...")
        self.action.connect()
        if self.action.app.isConnected():
            self.currentAccount = list(self.action.context['Account_list'])[0]
            self.update()
            self.SetStatusText("Connected.")
        else:
            self.SetStatusText("Not connected.")

    def OnRefresh(self, event):
        self.SetStatusText("Refreshing...")
        self.action.connect()
        if self.action.app.isConnected():
            self.update()
            self.SetStatusText("Refreshed.")
        else:
            self.SetStatusText("Not connected.")

    def OnLogout(self, event):
        self.authenticated = False
        self.action.disconnect()
        self.frame.Close()
        frame = MainFrame(None, title='Interactive Broker Trader Tool')
        frame.Show()
    
    def OnDisconnect(self, event):
        self.SetStatusText("Disconnecting...")
        self.action.disconnect()
        self.SetStatusText("Disconnected.")

    def OnClear(self, event):
        self.SetStatusText("Clearing...")
        self.action.clear()
        self.SetStatusText("Cleared.")
        self.update()

    def OnRisk(self, event):
        self.SetStatusText("Calculating...")
        self.action.risks()
        self.SetStatusText("Calculated.")
        self.update()

    def OnEfffter(self, event):
        self.SetStatusText("Getting Frontier...")
        self.action.efffter()
        self.SetStatusText("Ready.")
        self.update()
        
    def OnPlaceOrder(self, event):
        self.SetStatusText("Placing...")
        self.action.place_order(orderform=self.orderform)
        orderform = self.orderform
        self.SetStatusText("Place Done.")
        if len(self.action.app.ret['Error']) > 0 and list(self.action.app.ret['Error'])[-1]['Code']!=399:
            print('error',self.action.app.ret['Error'])
            self.st3.SetValue(str(list(self.action.app.ret['Error'])[-1]))
            wx.MessageBox("Order Not Placed Successfully!")
        else:
            wx.MessageBox("Order Placed Successfully!")
            self.update()
            if self.frame.master == self:
                if self.frame.slavery:
                    self.frame.slavery.action.place_order(orderform=orderform)
                    #self.frame.slavery.update()
                else:
                    wx.MessageBox("No slavery is set!")

    def OnCancelOrder(self, event):
        self.SetStatusText("Canceling...")
        ind = event.GetIndex()
        #button = event.GetEventObject()
        #ID = int(button.GetName())
        ID = self.cancelMap[ind]
        self.action.cancel_order(ID)
        self.SetStatusText("Cancel Done.")
        if len(self.action.app.ret['Error']) > 0:
            self.st3.SetValue(str(self.action.app.ret['Error']))
            wx.MessageBox("Order Not Canceled Successfully!")
        else:
            wx.MessageBox("Order Canceled Successfully!")
            self.update()
    
    def OnMethod(self, event):
        self.action.method = self.Method.GetStringSelection()
        self.SetStatusText("{} is clicked from Radio Box".format(self.Method.GetStringSelection()))

    def OnTime_p(self, event):
        self.action.time_p = self.Time_p.GetStringSelection()
        self.SetStatusText("{} is clicked from Radio Box".format(self.Time_p.GetStringSelection()))
    
    def OnAutoRefresh(self, event):
        self.isChecked = event.GetEventObject().GetValue()
        if not self.isChecked:
            wx.MessageBox("Stop Refresh every 10 seconds!")
            return
        else:
            wx.MessageBox("Auto Refresh every 10 seconds!")
        self.ii = 0
        def Execute():
            self.action.connect()
            print(self.ii)
            self.update()
            if self.isChecked:
                wx.CallLater(self.RefreshTime*100,Execute)
            self.ii = self.ii+1
        Execute()

if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frame = MainFrame(None, title='Interactive Broker Trader Tool')
    app.MainLoop()