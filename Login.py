import wx
import hashlib

########################################################################
class LoginDialog(wx.Dialog):
    """
    Class to define login dialog
    """
 
    #----------------------------------------------------------------------
    def __init__(self):
        wx.Dialog.__init__(self, None, title="Login")
        self.logged_in = False
 
        # user info
        user_sizer = wx.BoxSizer(wx.HORIZONTAL)
 
        user_lbl = wx.StaticText(self, label="Username:")
        user_sizer.Add(user_lbl, 0, wx.ALL|wx.CENTER, 5)
        self.user = wx.TextCtrl(self)
        user_sizer.Add(self.user, 0, wx.ALL, 5)
 
        # pass info
        p_sizer = wx.BoxSizer(wx.HORIZONTAL)
 
        p_lbl = wx.StaticText(self, label="Password:")
        p_sizer.Add(p_lbl, 0, wx.ALL|wx.CENTER, 5)
        self.password = wx.TextCtrl(self, style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
        self.password.Bind(wx.EVT_TEXT_ENTER, self.onLogin)
        p_sizer.Add(self.password, 0, wx.ALL, 5)
 
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(user_sizer, 0, wx.ALL, 5)
        main_sizer.Add(p_sizer, 0, wx.ALL, 5)
 
        btn = wx.Button(self, label="Login")
        btn.Bind(wx.EVT_BUTTON, self.onLogin)
        main_sizer.Add(btn, 0, wx.ALL|wx.CENTER, 5)
 
        self.SetSizer(main_sizer)
 
    #----------------------------------------------------------------------
    def onLogin(self, event):
        """
        Check credentials and login
        """
        hashed_username = "bff180dc56eefca884e2b382327cf7ca3088dbbda67ba2e43e6ae6116b13804fc6f6dd5ffeae3fb3f1d447c0252c12ae7296599c6337fa3eaa13acf60ca02d64"
        hashed_password = "22fb21d43ebb50bc53fcf719a610a24cb2aa897182457ccc46ad66d75a74670c2b40d28db82e01b892b18bc3ffa31bb57bd607f8ae4aa7f918a9ddfe48517809"
        user_name = self.user.GetValue()
        user_password = self.password.GetValue()
        if user_name == 'd': # for test
        #hashlib.sha512(user_password.encode('utf-8')).hexdigest() == hashed_password and \
        #hashlib.sha512(user_name.encode('utf-8')).hexdigest() == hashed_username:
            print("You are now logged in!")
            #wx.MessageBox("You are now logged in!")
            self.logged_in = True
            self.Close()
        else:
            self.logged_in = False
            print("Username or password is incorrect!")
            wx.MessageBox("Username or password is incorrect!")