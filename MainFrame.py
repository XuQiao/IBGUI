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
        self.basiclayout()
        self.Show()
        self.action = views.Actions()

    def basiclayout(self):
        # create a panel in the frame
        self.pnl = wx.Panel(self, wx.ID_ANY)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        btn_logout = wx.Button(self.pnl, label="Logout",pos = (210,20))
        btn_logout.Bind(wx.EVT_BUTTON, self.OnLogout)
        btn_conn = wx.Button(self.pnl, label="Connect",pos = (110,20))
        btn_conn.Bind(wx.EVT_BUTTON, self.OnConnect) 

        # and put some text with a larger bold font on it
        st = wx.StaticText(self.pnl, label="Hi, {}".format(self.dlg.user.GetValue()), pos=(10,10))
        font = st.GetFont()
        font = font.Bold()
        st.SetFont(font)
        self.sizer_greet = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_greet.Add(st)
        self.sizer_commands = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_commands.AddMany([btn_conn,btn_logout])
        
        self.sizer.Add(self.sizer_greet,0,wx.ALL|wx.EXPAND,3)
        self.sizer.Add(self.sizer_commands,0,wx.ALL|wx.EXPAND,3)

        self.pnl.SetSizer(self.sizer)
        self.pnl.Layout()
        #self.pnl.Refresh()

    def update(self):
        self.Maximize()
        if 'sizer2' in self.__dict__:
            self.sizer2.Clear(True)
        if 'sizer1' in self.__dict__:
            self.sizer1.Clear(True)
        self.sizer_commands.Clear(True)
        self.sizer.Clear(True)
        self.basiclayout()
        self.Method = wx.RadioBox(self.pnl, label = 'Method', pos = (80,30), choices = ["VarCov","Historical","MonteCarlo"], 
            majorDimension = 1, style = wx.RA_SPECIFY_ROWS)
        self.Method.SetStringSelection(self.action.method)
        self.Time_p = wx.RadioBox(self.pnl, label = 'Time_Interval', pos = (60,30), choices = ["OneDay","OneWeek","OneMonth"], 
            majorDimension = 1, style = wx.RA_SPECIFY_ROWS) 
        self.Time_p.SetStringSelection(self.action.time_p)
        self.Method.Bind(wx.EVT_RADIOBOX, self.OnMethod),
        self.Time_p.Bind(wx.EVT_RADIOBOX, self.OnTime_p),

        if self.action.app.ret:
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

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        #account list
        self.st4 = wx.StaticText(self.pnl, label = "account list:", pos = (10,150))
        self.sizer2.Add(self.st4)
        self.list_ctrl4 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,100), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        for column, prop in enumerate(['Account']):
            self.list_ctrl4.InsertColumn(column, prop)
            for row, account_list in enumerate(self.action.context['Account_list']):
                if column == 0:    
                    self.list_ctrl4.InsertItem(row, account_list) 
                else:
                    self.list_ctrl4.SetItem(row, column, account_list)
        self.sizer2.Add(self.list_ctrl4,0,wx.EXPAND)

        # account property
        self.list_ctrl1 = wx.ListCtrl(self.pnl, pos = (10, 50), size=(-1,100), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)  
        for column, prop in enumerate(['Tag','Value']):
            self.list_ctrl1.InsertColumn(column, prop)
            for row, accountSummary in enumerate(self.action.context['AccountSummary']):
                temp = accountSummary[prop]
                if type(temp) in [float, int, np.float64]:
                    temp = '%.2f' % temp
                if 'Value' in prop and 'VaR' in self.action.context['AccountSummary'][row]['Tag']:
                    temp = '%s(%.2f%%)'%(temp,float(accountSummary[prop])/np.sum(self.action.assets)*100)
                if column == 0:
                    self.list_ctrl1.InsertItem(row, temp) 
                else:
                    self.list_ctrl1.SetItem(row, column, temp)
            self.list_ctrl1.SetColumnWidth(column, wx.LIST_AUTOSIZE)

        self.sizer2.Add(self.list_ctrl1,0,wx.EXPAND)
        
        #p & l
        self.st2 = wx.StaticText(self.pnl, label="P && L:", pos = (10,200))
        self.sizer2.Add(self.st2)
        self.list_ctrl2 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,100), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        for column, prop in enumerate(['DailyPnL','RealizedPnL','UnrealizedPnL']):
            self.list_ctrl2.InsertColumn(column, prop)
            self.list_ctrl2.SetColumnWidth(column, wx.LIST_AUTOSIZE)
            for row, daily_PnL in enumerate(self.action.context['Daily_PnL']):
                temp = daily_PnL[prop]
                if type(temp) in [float, int, np.float64]:
                    temp = '%.2f' % temp
                if column == 0:
                    self.list_ctrl2.InsertItem(row, temp)
                else:
                    self.list_ctrl2.SetItem(row, column, temp)
            self.list_ctrl2.SetColumnWidth(column, wx.LIST_AUTOSIZE)

        self.sizer2.Add(self.list_ctrl2,0,wx.EXPAND)

        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer1.Add(self.sizer2)

        #positions
        self.st1 = wx.StaticText(self.pnl, label="current Positions:", pos=(70,150))
        self.sizer1.Add(self.st1)
        self.list_ctrl3 = wx.ListCtrl(self.pnl, pos = (10, 50), size=(-1,200), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        for column, prop in enumerate(['Symbol','Position','AvgCost','DailyPnL','UnrealizedPnL','RealizedPnL'
            ,'Value','Beta','ImpVol','VaR_90','VaR_95','VaR_99']):
            self.list_ctrl3.InsertColumn(column, prop)
            for row, positions in enumerate(self.action.context['Positions']):
                if prop not in positions:
                    positions[prop] = ""
                temp = positions[prop]
                if type(positions[prop]) in [float, int, np.float64]:
                    temp = '%.2f' % positions[prop]
                if 'VaR' in prop and positions[prop]:
                    temp = '%s(%.2f%%)'%(temp,
                        float(positions[prop])/(float(positions['AvgCost'])*float(positions['Position']))*100)
                if column == 0:
                    self.list_ctrl3.InsertItem(row, temp)
                else:
                    self.list_ctrl3.SetItem(row, column, temp)
                self.list_ctrl3.SetColumnWidth(column, wx.LIST_AUTOSIZE)
        self.sizer1.Add(self.list_ctrl3,1,wx.EXPAND)

        #open orders
        self.st5 = wx.StaticText(self.pnl, label="Open Orders:", pos = (10,200))
        self.sizer_cancelform = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_cb = wx.BoxSizer(wx.VERTICAL)
        self.sizer1.Add(self.st5)
        self.list_ctrl4 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,150),
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING) 
        self.btn_cancelorders = {}
        for column, prop in enumerate(['OrderId','Symbol','SecType','Action','OrderType','LmtPrice'
            ,'TotalQty','Status','Filled','Remaining','AvgFillPrice','WhyHeld'
            ,'MktCapPrice','Id']):
            self.list_ctrl4.InsertColumn(column, prop)
            for row, orderstatus in enumerate(self.action.context["OrderStatus"]):
                for openorder in self.action.context["OpenOrder"]:
                    if openorder["OrderId"] == orderstatus["Id"]:
                        temp = openorder[prop] if column < 8 else orderstatus[prop]
                        if type(temp) in [float, int]:
                            temp = '%.2f' % temp
                        if column == 0:
                            self.list_ctrl4.InsertItem(row, temp)
                            self.btn_cancelorders[orderstatus['Id']] = wx.Button(self.pnl, label="Cancel Order",name=str(orderstatus['Id']))
                            self.btn_cancelorders[orderstatus['Id']].Bind(wx.EVT_BUTTON, self.OnCancelOrder)
                        else:
                            self.list_ctrl4.SetItem(row, column, temp)
                self.list_ctrl4.SetColumnWidth(column, wx.LIST_AUTOSIZE)
        self.sizer_cb.AddSpacer(16);
        for button in self.btn_cancelorders.values():
            self.sizer_cb.Add(button)
        self.sizer_cancelform.AddMany([self.list_ctrl4, self.sizer_cb])
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
        self.pnl.SetSizerAndFit(self.sizer)
        self.Show()

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

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)
        self.Bind(wx.EVT_MENU, self.OnExport, exportItem)
    
    def OnHello(self, event):
        """Say hello to the user."""
        wx.MessageBox("Hello again from wxPython")

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)

    def OnConnect(self, event):
        self.SetStatusText("Connecting...")
        self.action.connect()
        if self.action.app.isConnected():
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

    def OnLogout(self, event):
        self.authenticated = False
        self.action.disconnect()
        self.Close()
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
        print('orderform',self.orderform.cleaned_data)
        self.SetStatusText("Placing...")
        self.action.place_order(self.orderform)
        self.SetStatusText("Place Done.")
        if len(self.action.app.ret['Error']) > 0:
            self.st3.SetValue(str(self.action.app.ret['Error']))
        else:
            self.update()

    def OnCancelOrder(self, event):
        self.SetStatusText("Canceling...")
        button = event.GetEventObject()
        ID = int(button.GetName())
        self.action.cancel_order(ID)
        self.SetStatusText("Cancel Done.")
    
    def OnMethod(self, event):
        self.action.method = self.Method.GetStringSelection()
        self.SetStatusText("{} is clicked from Radio Box".format(self.Method.GetStringSelection()))

    def OnTime_p(self, event):
        self.action.time_p = self.Time_p.GetStringSelection()
        self.SetStatusText("{} is clicked from Radio Box".format(self.Time_p.GetStringSelection()))

    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("This is a Program for Interactive Broker System",
                      "Developed by Qiao Xu",
                      wx.OK|wx.ICON_INFORMATION)

if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frame = MainFrame(None, title='Interactive Broker Trader Tool')
    app.MainLoop()