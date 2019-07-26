import wx
from wx.lib.masked import NumCtrl
from wx.lib.intctrl import IntCtrl
from collections import defaultdict

class OrderForm(wx.Panel):
    def __init__(self, parent = None, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.parent = parent
        self.pnl = self.parent.pnl
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cleaned_data = {'OrderType':'LMT','Action':'BUY','Symbol':'','Quantity':0, 'LmtPrice':0}
        self.createControls()
        self.bindEvents()
        self.doLayout()

    def createControls(self):
        self.OrderType = wx.RadioBox(self.pnl, label = 'OrderType', pos = (80,30), choices = ["LMT","MKT"], 
            majorDimension = 1, style = wx.RA_SPECIFY_ROWS) 
        self.Action = wx.RadioBox(self.pnl, label = 'Action', pos = (60,30), choices = ["BUY","SELL"], 
            majorDimension = 1, style = wx.RA_SPECIFY_ROWS) 
        self.hbox1 = wx.BoxSizer(wx.VERTICAL)
        l1 = wx.StaticText(self.pnl, -1, "Symbol") 
        self.hbox1.Add(l1, 1, wx.ALIGN_LEFT|wx.ALL,5)
        self.Symbol = wx.TextCtrl(self.pnl)
        self.hbox1.Add(self.Symbol)

        self.hbox2 = wx.BoxSizer(wx.VERTICAL)
        l2 = wx.StaticText(self.pnl, -1, "Quantity") 
        self.hbox2.Add(l2, 1, wx.ALIGN_LEFT|wx.ALL,5) 
        self.Quantity = IntCtrl(self.pnl)
        self.hbox2.Add(self.Quantity)

        self.hbox3 = wx.BoxSizer(wx.VERTICAL)
        l3 = wx.StaticText(self.pnl, -1, "LmtPrice") 
        self.hbox3.Add(l3, 1, wx.ALIGN_LEFT|wx.ALL,5) 
        self.LmtPrice = NumCtrl(self.pnl,fractionWidth = 2,min=0,max=None)
        self.hbox3.Add(self.LmtPrice)

    def bindEvents(self):
        for control, event, handler in \
             [(self.OrderType, wx.EVT_RADIOBOX, self.OnRadioBox1),
             (self.Action, wx.EVT_RADIOBOX, self.OnRadioBox2),
             (self.Symbol, wx.EVT_TEXT, self.OnSymbol),
             (self.Quantity, wx.EVT_TEXT, self.OnQuantity),
             (self.LmtPrice, wx.EVT_TEXT, self.OnLmtPrice)]:
            control.Bind(event, handler)
        
    def doLayout(self):
        self.sizer.AddMany([self.OrderType,self.Action,self.hbox1,self.hbox2,self.hbox3])

    def OnRadioBox1(self,e): 
        self.cleaned_data['OrderType'] = self.OrderType.GetStringSelection()
        self.parent.SetStatusText('{} is clicked from Radio Box'.format(self.OrderType.GetStringSelection()))

    def OnRadioBox2(self,e): 
        self.cleaned_data['Action'] = self.Action.GetStringSelection()
        self.parent.SetStatusText('{} is clicked from Radio Box'.format(self.Action.GetStringSelection()))

    def OnSymbol(self, e):
        self.cleaned_data['Symbol'] = self.Symbol.GetValue()
        self.parent.SetStatusText("Entered Symbol: {}".format(self.Symbol.GetValue()))

    def OnQuantity(self, e):
        self.cleaned_data['Quantity'] = self.Quantity.GetValue()
        self.parent.SetStatusText("Entered Quantity: {}".format(self.Quantity.GetValue()))

    def OnLmtPrice(self, e):
        self.parent.SetStatusText("Entered Limit Price: {}".format(self.LmtPrice.GetValue()))
        if self.OrderType.GetStringSelection() == "LMT":
            # Only do something if both fields are valid so far.
            if not self.LmtPrice.GetValue():
                wx.MessageBox('Please Fill in the Limit Price', 'Error', wx.OK)
            else:
                self.cleaned_data["LmtPrice"] = self.LmtPrice.GetValue()
        if self.OrderType.GetStringSelection() == "MKT":
            self.LmtPrice.SetValue(0)
            self.cleaned_data["LmtPrice"] = 0
