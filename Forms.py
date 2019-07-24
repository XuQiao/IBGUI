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
        self.cleaned_data = defaultdict(str)
        self.createControls()
        self.bindEvents()
        self.doLayout()

    def createControls(self):
        self.OrderType = wx.RadioBox(self.pnl, label = 'OrderType', pos = (80,30), choices = ["lmt","mkt"], 
            majorDimension = 1, style = wx.RA_SPECIFY_ROWS) 
        self.Action = wx.RadioBox(self.pnl, label = 'Action', pos = (60,30), choices = ["buy","sell"], 
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
        self.LmtPrice = NumCtrl(self.pnl,integerWidth=9,min=0,max=None)
        self.hbox3.Add(self.LmtPrice)

        self.btn = wx.Button(self.pnl, label="Submit Order")

    def bindEvents(self):
        for control, event, handler in \
            [(self.btn, wx.EVT_BUTTON, self.OnSubmit),
             (self.OrderType, wx.EVT_RADIOBOX, self.OnRadioBox1),
             (self.Action, wx.EVT_RADIOBOX, self.OnRadioBox2),
             (self.Symbol, wx.EVT_TEXT_ENTER, self.OnSymbol),
             (self.Quantity, wx.EVT_TEXT_ENTER, self.OnQuantity),
             (self.LmtPrice, wx.EVT_TEXT_ENTER, self.OnLmtPrice)]:
            control.Bind(event, handler)
        
    def doLayout(self):
        self.sizer.AddMany([self.btn, self.OrderType,self.Action,self.hbox1,self.hbox2,self.hbox3])

    def OnRadioBox1(self,e): 
        self.parent.SetStatusText(self.OrderType.GetStringSelection() +' is clicked from Radio Box')
        
    def OnRadioBox2(self,e): 
        self.parent.SetStatusText(self.Action.GetStringSelection() +' is clicked from Radio Box')

    def OnSymbol(self, e):
        self.parent.SetStatusText("Entered Symbol: " + self.Symbol.GetValue())

    def OnQuantity(self, e):
        self.parent.SetStatusText("Entered Quantity: " + self.Quantity.GetValue())

    def OnLmtPrice(self, e):
        self.parent.SetStatusText("Entered Limit Price: " + self.LmtPrice.GetValue())

    def OnSubmit(self, event):
        self.cleaned_data['OrderType'] = self.OrderType.GetStringSelection()
        self.cleaned_data['Action'] = self.Action.GetStringSelection()
        self.cleaned_data['Symbol'] = self.Symbol.GetValue()
        if self.OrderType.GetStringSelection() == "lmt":
            # Only do something if both fields are valid so far.
            if not self.LmtPrice.GetValue():
                wx.MessageBox('Please Fill in the Limit Price', 'Error', wx.OK)
            else:
                self.cleaned_data["LmtPrice"] = 0
        if self.OrderType.GetStringSelection() == "mkt":
            self.LmtPrice.SetValue(0)
            self.cleaned_data["LmtPrice"] = 0
        self.cleaned_data['Quantity'] = self.Quantity.GetValue()