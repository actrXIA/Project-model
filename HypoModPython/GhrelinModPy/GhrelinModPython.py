                                                                                                                                                                                                                                                                                             ## GhrelinModPy.py
## Based on AgentModPython.py
## XIA Ziyue


import wx
from HypoModPy.hypomain import *


app = wx.App(False)
pos = wx.DefaultPosition
size = wx.Size(400, 500)
mainpath = ""
respath = ""
modname = "Ghrelin"
mainwin = HypoMain("HypoMod", pos, size, respath, mainpath, modname)
mainwin.Show()
mainwin.SetFocus()
app.MainLoop()