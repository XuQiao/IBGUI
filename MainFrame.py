# -*- encoding: utf-8 -*-
#!/bin/python

import wx
import Login
import views
from Forms import OrderForm

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
        self.Maximize()
        self.basiclayout()

    def basiclayout(self):
        # create a panel in the frame
        self.pnl = wx.Panel(self, wx.ID_ANY)
        self.action = views.Actions()
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
        
        self.sizer.Add(self.sizer_greet,1,wx.ALL|wx.EXPAND,5)
        self.sizer.Add(self.sizer_commands,1,wx.ALL|wx.EXPAND,5)
        #msg box
        Msgs = self.action.context.get("Msgs", "")
        st3 = wx.StaticText(self.pnl, label=Msgs, size=(100,300), pos = (500,300))
        #self.sizer.Add(st3)
        # create a menu bar
        self.makeMenuBar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Log in successful!")
        self.pnl.SetSizer(self.sizer)
        #self.pnl.Layout()
        #self.pnl.Refresh()
        self.Show()

    def update(self):
        if self.action.app.ret:
            btn_refresh = wx.Button(self.pnl, label="Refresh",pos = (10,20))
            btn_refresh.Bind(wx.EVT_BUTTON, self.OnRefresh)
            btn_disconn = wx.Button(self.pnl, label="DisConnect",pos = (310,20))
            btn_disconn.Bind(wx.EVT_BUTTON, self.OnDisconnect)
            btn_clear = wx.Button(self.pnl, label="Clear",pos = (410,20))
            btn_clear.Bind(wx.EVT_BUTTON, self.OnClear)
            
            btn_risk = wx.Button(self.pnl, label="Risk Factors", pos = (510, 20))
            btn_risk.Bind(wx.EVT_BUTTON, self.OnRisk)
            
            btn_placeorder = wx.Button(self.pnl, label="Submit Order", pos = (610, 20))
            btn_placeorder.Bind(wx.EVT_BUTTON, self.OnPlaceOrder)

            self.sizer_commands.AddMany([btn_refresh,btn_disconn,btn_clear,
            btn_risk,btn_placeorder])

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        st4 = wx.StaticText(self.pnl, label = "account list:", pos = (10,150))
        self.sizer2.Add(st4)
        self.list_ctrl4 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,200), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        for column, prop in enumerate(['Account']):
            self.list_ctrl4.InsertColumn(column, prop)
            for row, account_list in enumerate(self.action.context['Account_list']):
                if column == 0:    
                    self.list_ctrl4.InsertItem(column, account_list) 
                else:
                    self.list_ctrl4.SetItem(row, column, account_list)
        self.sizer2.Add(self.list_ctrl4,1,wx.EXPAND)

        # account property
        self.list_ctrl1 = wx.ListCtrl(self.pnl, pos = (10, 50), size=(-1,200), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)  
        for column, prop in enumerate(['Tag','Value']):
            self.list_ctrl1.InsertColumn(column, prop)
            for row, accountSummary in enumerate(self.action.context['AccountSummary']):
                if column == 0:    
                    self.list_ctrl1.InsertItem(column, accountSummary[prop]) 
                else:
                    self.list_ctrl1.SetItem(row, column, accountSummary[prop])
        self.sizer2.Add(self.list_ctrl1,1,wx.EXPAND)
        
        #p & l
        st2 = wx.StaticText(self.pnl, label="P && L:", pos = (10,200))
        self.sizer2.Add(st2)
        self.list_ctrl2 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,200), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        for column, prop in enumerate(['DailyPnL','RealizedPnL','UnrealizedPnL']):
            self.list_ctrl2.InsertColumn(column, prop)
            row = 0
            for row, daily_PnL in enumerate(self.action.context['Daily_PnL']):
                temp = daily_PnL[prop]
                if type(temp) in [float, int]:
                    temp = '%.2f' % temp
                if column == 0:
                    self.list_ctrl2.InsertItem(column, temp)
                else:
                    self.list_ctrl2.SetItem(row, column, temp)

        self.sizer2.Add(self.list_ctrl2,1,wx.EXPAND)

        self.sizer3 = wx.BoxSizer(wx.VERTICAL)
        self.sizer3.Add(self.sizer2)

        #open orders
        st5 = wx.StaticText(self.pnl, label="Open Orders:", pos = (10,200))
        self.sizer_cancelform = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_cb = wx.BoxSizer(wx.VERTICAL)
        self.sizer3.Add(st5)
        self.list_ctrl4 = wx.ListCtrl(self.pnl, pos = (10, 100), size=(-1,200),
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING) 
        btn_cancelorders = {}
        for column, prop in enumerate(['Id','Status','Filled','Remaining','AvgFillPrice','WhyHeld'
            ,'MktCapPrice','Status','OrderId','Symbol','SecType','Action','OrderType','LmtPrice'
            ,'TotalQty']):
            self.list_ctrl4.InsertColumn(column, prop)
            for row, orderstatus in enumerate(self.action.context["OrderStatus"]):
                for openorder in self.action.context["OpenOrder"]:
                    if openorder["OrderId"] == orderstatus["Id"]:
                        temp = orderstatus[prop] if column < 8 else openorder[prop]
                        if type(temp) in [float, int]:
                            temp = '%.2f' % temp
                        if column == 0:
                            self.list_ctrl4.InsertItem(column, temp)
                        else:
                            self.list_ctrl4.SetItem(row, column, temp)
                btn_cancelorders[openorder['OrderId']] = wx.Button(self.pnl, label="Cancel Order",name=str(openorder['OrderId']))
                btn_cancelorders[openorder['OrderId']].Bind(wx.EVT_BUTTON, self.OnCancelOrder)
        for button in btn_cancelorders.values():
            self.sizer_cb.Add(button)
        self.sizer_cancelform.AddMany([self.list_ctrl4, self.sizer_cb])
        self.sizer3.Add(self.sizer_cancelform)

        #positions
        st1 = wx.StaticText(self.pnl, label="current Positions:", pos=(70,150))
        self.sizer3.Add(st1)
        self.list_ctrl3 = wx.ListCtrl(self.pnl, pos = (10, 50), size=(-1,200), 
            style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SORT_ASCENDING)
        for column, prop in enumerate(['Symbol','Position','AvgCost','DailyPnL','UnrealizedPnL','RealizedPnL'
            ,'Value','Beta','ImpVol','VaR_90','VaR_95','VaR_99']):
            self.list_ctrl3.InsertColumn(column, prop)
            for row, positions in enumerate(self.action.context['Positions']):
                if prop not in positions:
                    positions[prop] = ""
                temp = positions[prop]
                if type(positions[prop]) in [float, int]:
                    temp = '%.2f' % positions[prop]
                if column == 0:
                    self.list_ctrl3.InsertItem(column, temp)
                else:
                    self.list_ctrl3.SetItem(row, column, temp)
        self.sizer3.Add(self.list_ctrl3,1,wx.EXPAND)

        #make orders

        self.orderform = OrderForm(self)
        self.sizer3.Add(self.orderform.sizer,1,wx.ALL|wx.EXPAND,5)

        self.sizer.Add(self.sizer3)
        self.pnl.SetSizerAndFit(self.sizer)
        self.Refresh()
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
        wx.MessageBox("not saved...")

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

    def OnRisk(self, event):
        self.SetStatusText("Calculating...")
        self.action.risks()
        self.SetStatusText("Calculated.")

    def OnPlaceOrder(self, event):
        self.SetStatusText("Placing...")
        self.action.place_order(self.orderform)
        self.SetStatusText("Place Done.")

    def OnCancelOrder(self, event):
        self.SetStatusText("Canceling...")
        button = event.GetEventObject()
        ID = int(button.GetName())
        self.action.cancel_order(ID)
        self.SetStatusText("Cancel Done.")

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