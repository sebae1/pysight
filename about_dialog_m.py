import wx
import pathlib

class AboutDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, id=-1, title='About PySight', size=(400,300))
        BACKGROUNDCOLOR = '#fdfdfe'
        self.SetBackgroundColour(BACKGROUNDCOLOR)

        img = wx.Image(str(pathlib.Path(__file__).parent)+'\icons\PySight.ico', type=wx.BITMAP_TYPE_ICO)
        img.Rescale(70,70)
        img = img.ConvertToBitmap()
        subject = 'PySight 4.03'
        description = '''This program is designed to monitor and acquire data from Keysight MSO-X 3104A oscilloscope. You may need \'Keysight Connection Expert\' to locate the VISA address of it. The program can perform real-time post-processing from the panel on the right.'''
        signature = '2019, Sangeun Bae'

        bitmap = wx.StaticBitmap(self, bitmap=img)
        txt1 = wx.StaticText(self, label=subject, style=wx.ALIGN_CENTER_HORIZONTAL)
        txt1.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        txt2 = wx.StaticText(self, label=description, size=(-1,60), style=wx.ALIGN_CENTER_HORIZONTAL|wx.TE_MULTILINE)
        txt3 = wx.StaticText(self, label=signature, style=wx.ALIGN_CENTER_HORIZONTAL)
        txt3.SetFont(wx.Font(10, wx.DEFAULT, wx.ITALIC, wx.NORMAL))
        spacer = (-1,10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany([
            (bitmap, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 10),
            (txt1, 0, wx.EXPAND),
            (spacer, 0),
            (txt2, 0, wx.EXPAND|wx.ALL, 10),
            (spacer, 0),
            (txt3, 0, wx.EXPAND)
        ])

        self.SetSizer(sizer)