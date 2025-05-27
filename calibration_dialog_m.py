import wx
import wx.lib.plot as wplt
import numpy as np
from post_process_m import PropertyRegression
from post_process_m import isnumber

class CalibrationDialog(wx.Dialog):
    def __init__(self, parent, title, x, y):
        wx.Dialog.__init__(self, parent, id=-1, title=title, size=(700,300))
        canvas_font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        BACKGROUNDCOLOR = '#fdfdfe'
        self.SetBackgroundColour(BACKGROUNDCOLOR)

        self.x = x
        self.y = y

        self.textctrlPECx = wx.TextCtrl(self, value=x['label'], style=wx.TE_READONLY|wx.TE_CENTER)
        self.textctrlPECx1 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.textctrlPECx2 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.textctrlPECx3 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.textctrlPECx4 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.textctrlPECx5 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.widget_x = {'1':self.textctrlPECx1, '2':self.textctrlPECx2, '3':self.textctrlPECx3, '4':self.textctrlPECx4, '5':self.textctrlPECx5}
        for key in ['1','2','3','4','5']:
            self.widget_x[key].SetValue(x['values'][key])

        self.textctrlPECy = wx.TextCtrl(self, value=y['label'], style=wx.TE_READONLY|wx.TE_CENTER)
        self.textctrlPECy1 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.textctrlPECy2 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.textctrlPECy3 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.textctrlPECy4 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.textctrlPECy5 = wx.TextCtrl(self, style=wx.TE_CENTER)
        self.widget_y = {'1':self.textctrlPECy1, '2':self.textctrlPECy2, '3':self.textctrlPECy3, '4':self.textctrlPECy4, '5':self.textctrlPECy5}
        for key in ['1','2','3','4','5']:
            self.widget_y[key].SetValue(y['values'][key])

        sizer1 = wx.GridSizer(6,2,5,5)
        sizer1.AddMany([
            (self.textctrlPECx,0,wx.EXPAND),
            (self.textctrlPECy,0,wx.EXPAND),
            (self.textctrlPECx1,0,wx.EXPAND),
            (self.textctrlPECy1,0,wx.EXPAND),
            (self.textctrlPECx2,0,wx.EXPAND),
            (self.textctrlPECy2,0,wx.EXPAND),
            (self.textctrlPECx3,0,wx.EXPAND),
            (self.textctrlPECy3,0,wx.EXPAND),
            (self.textctrlPECx4,0,wx.EXPAND),
            (self.textctrlPECy4,0,wx.EXPAND),
            (self.textctrlPECx5,0,wx.EXPAND),
            (self.textctrlPECy5,0,wx.EXPAND)
            ])

        buttonOK = wx.Button(self, label='OK', size=(50,-1))
        buttonCancel = wx.Button(self, label='Cancel', size=(50,-1))
        buttonApply = wx.Button(self, label='Apply', size=(50,-1))

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.AddMany([(buttonApply,0),(buttonOK,0),(buttonCancel,0)])

        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer3.AddMany([
            (sizer1,0,wx.CENTER|wx.TOP,10),
            (wx.StaticLine(self,style=wx.LI_HORIZONTAL),0,wx.EXPAND|wx.ALL,10),
            (sizer2,0,wx.ALIGN_RIGHT|wx.RIGHT,10)
            ])

        self.canvas = wplt.PlotCanvas(self)
        self.canvas.SetFont(canvas_font)
        self.graph = wplt.PlotGraphics([wplt.PolyLine([])], xLabel=self.x['label'], yLabel=self.y['label'])
        self.canvas.Draw(self.graph)
        self.RegressionPlot()

        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.AddMany([((20,-1)),(sizer3,0),((20,-1)),(self.canvas,1,wx.EXPAND|wx.ALL,10)])

        self.SetSizer(sizer4)

        self.Bind(wx.EVT_BUTTON, self.Apply, buttonApply)
        self.Bind(wx.EVT_BUTTON, self.OK, buttonOK)
        self.Bind(wx.EVT_BUTTON, self.Cancel, buttonCancel)

    def RegressionPlot(self):
        try:
            result = PropertyRegression(list(self.x['values'].values()), list(self.y['values'].values()))
            if not result == False:
                X_e, Y_e, slope, intercept, r_value = result
                polyobject = []
                polyobject.append(wplt.PolyMarker(np.append([X_e], [Y_e], axis=0).transpose(), marker='cross', colour='blue'))
                polyobject.append(wplt.PolyLine([[X_e[0], X_e[0]*slope+intercept],[X_e[-1], X_e[-1]*slope+intercept]], colour='red', style=wx.PENSTYLE_SHORT_DASH))
                self.graph.title = 'R-squared : {}'.format(round(r_value**2,4))
                self.graph.objects = polyobject
                self.canvas.Draw(self.graph)

        except Exception as err:
            wx.MessageBox(str(err),'Fit error',wx.OK)

    def SaveData(self):
        k = 0
        for key in self.widget_x.keys():
            if isnumber(self.widget_x[key].GetValue()) == True and isnumber(self.widget_y[key].GetValue()) == True:                
                self.x['values'][key] = self.widget_x[key].GetValue()
                self.y['values'][key] = self.widget_y[key].GetValue()
                k += 1
            else:
                self.widget_x[key].SetValue('')
                self.widget_y[key].SetValue('')
                self.x['values'][key] = ''
                self.y['values'][key] = ''
        if k >= 2:
            self.x['flag'] = True
            self.y['flag'] = True
        else:
            self.x['flag'] = False
            self.y['flag'] = False

    def Apply(self, event):
        self.SaveData()
        self.RegressionPlot()
                                 
    def OK(self, event):
        self.SaveData()
        self.EndModal(True)

    def Cancel(self, event):
        self.EndModal(True)


