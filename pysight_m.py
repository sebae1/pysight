import wx
import numpy as np
import _thread
import wx.lib.plot as wplt
import pyvisa
import csv
import pickle
import pathlib
import os
import usb
import usb.backend
import usb.backend.libusb1
import webbrowser
from about_dialog_m import AboutDialog
from calibration_dialog_m import CalibrationDialog
from curves_m import *
from post_process_m import *

libusb = os.path.join(str(pathlib.Path(__file__).absolute().parent), 'libusb-1.0.dll')
backend = usb.backend.libusb1.get_backend(libusb)
dev = usb.core.find(backend=backend)

savedir = os.environ['USERPROFILE'] + '\\Documents\\PySight'
autocal = os.environ['USERPROFILE'] + '\\Documents\\PySight\\cal.bin'

class PySight(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, title='PySight', size=(1500,800))
        if not os.path.isdir(savedir): # No save directory
            os.makedirs(savedir)

        self.BACKGROUNDCOLOR = '#fdfdfe'
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(self.BACKGROUNDCOLOR)
        self.channel_list = ('CHANNEL1','CHANNEL2','CHANNEL3','CHANNEL4')
        self.order = {'0':[1, ''], '1':[10**3, 'm'], '2':[10**6, '\mu'], '3':[10**9, 'n']}
        self.path = str(pathlib.Path(__file__).parent)
        self.SetIcon(wx.Icon(self.path+'\icons\PySight.ico'))
        self.Maximize(True)        
        self.Menu()
        self.Canvas()
        self.Process()

        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.AddMany([
            (self.sizer_menu,0,wx.EXPAND|wx.ALL, 10),
            (wx.StaticLine(self.panel),0,wx.EXPAND),
            (self.canvas,1,wx.EXPAND|wx.ALL, 10)
            ])
        
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.AddMany([
            (sizer_1,1,wx.EXPAND),
            (wx.StaticLine(self.panel,style=wx.LI_VERTICAL),0,wx.EXPAND),
            (self.sizer_process,0,wx.EXPAND)
            ])

        self.panel.SetSizer(sizer_2)

        #### INITIALIZING ####
        self.Menubar()
        self.ChannelRefresh()
        self.ModeRefresh()
        self.PlotRefresh()
        self.eventBind()        
        self.widgets = (self.checkboxCh1,
                self.checkboxCh2,
                self.checkboxCh3,
                self.checkboxCh4,
                self.spinNmax,
                self.checkboxLive,
                self.buttonPP,
                self.buttonP,
                self.buttonN,
                self.buttonNN,
                self.buttonAcq,
                self.buttonClear,
                self.comboLaser,
                self.comboPlasma,
                self.comboLaserB,
                self.buttonEnergy,
                self.buttonEnergyB,
                self.buttonPressure,
                self.textctrlCL1,
                self.textctrlCL2,
                self.textctrlOPL1,
                self.textctrlOPL2)
        self.Initializing()

        
    '''
    sizer_menu:O0  |  sizer_process
    ---------------|  0
    canvas:000000  |  0
    ---------------|  0
    toolbar:00000  |  0
    '''

    ##### LAYOUT START #####

    def Menubar(self):
        MenuFile = wx.Menu()
        self.ItemSave = wx.MenuItem(MenuFile,-1,'Save')
        self.ItemSave.SetBitmap(wx.Image(self.path+'\icons\save.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.ItemQuit = wx.MenuItem(MenuFile,-1,'Quit')
        self.ItemQuit.SetBitmap(wx.Image(self.path+'\icons\quit.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        MenuFile.Append(self.ItemSave)
        MenuFile.AppendSeparator()
        MenuFile.Append(self.ItemQuit)

        MenuOsc = wx.Menu()
        self.ItemAddress = wx.MenuItem(MenuOsc,-1,'Address')
        self.ItemAddress.SetBitmap(wx.Image(self.path+'\icons\setting.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        MenuOsc.Append(self.ItemAddress)

        MenuHelp = wx.Menu()
        self.ItemAbout = wx.MenuItem(MenuHelp,-1,'About')
        self.ItemAbout.SetBitmap(wx.Image(self.path+'\icons\\about.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        self.ItemGithub = wx.MenuItem(MenuHelp,-1,'Visit Github')
        self.ItemGithub.SetBitmap(wx.Image(self.path+'\icons\\git.png',wx.BITMAP_TYPE_PNG).ConvertToBitmap())
        MenuHelp.Append(self.ItemAbout)
        MenuHelp.Append(self.ItemGithub)

        menubar = wx.MenuBar()
        menubar.Append(MenuFile,'File')
        menubar.Append(MenuOsc,'Oscilloscope')
        menubar.Append(MenuHelp,'Help')
        self.SetMenuBar(menubar)

    def Menu(self):
        self.checkboxCh1 = wx.CheckBox(self.panel, label='Ch.1')
        self.checkboxCh2 = wx.CheckBox(self.panel, label='Ch.2')
        self.checkboxCh3 = wx.CheckBox(self.panel, label='Ch.3')
        self.checkboxCh4 = wx.CheckBox(self.panel, label='Ch.4')
        self.statictextNmax = wx.StaticText(self.panel, label='#  ')
        self.spinNmax = wx.SpinCtrl(self.panel, min=1, max=1000, initial=1, size=(50,-1))
        self.checkboxLive = wx.CheckBox(self.panel, label='Live')
        self.buttonPP = wx.Button(self.panel, label='<<', size=(30,-1))
        self.buttonP = wx.Button(self.panel, label='<', size=(30,-1))
        self.textctrlN = wx.TextCtrl(self.panel, value='0', style=wx.TE_READONLY|wx.TE_CENTER, size=(60,-1))
        self.statictextSlash = wx.StaticText(self.panel, label='/', style=wx.ALIGN_CENTER, size=(20,-1))
        self.textctrlNmax = wx.TextCtrl(self.panel, value='0', style=wx.TE_READONLY|wx.TE_CENTER, size=(60,-1))
        self.buttonN = wx.Button(self.panel, label='>', size=(30,-1))
        self.buttonNN = wx.Button(self.panel, label='>>', size=(30,-1))
        self.buttonAcq = wx.Button(self.panel, label='Acq.', size=(50,-1))
        self.buttonStop = wx.Button(self.panel, label='Stop', size=(50,-1))
        self.buttonStop.Enable(False)
        self.buttonClear = wx.Button(self.panel, label='Clear', size=(50,-1))
        
        self.sizer_menu_upper = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_menu_upper.AddMany([
            (self.checkboxCh1, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.checkboxCh2, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.checkboxCh3, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.checkboxCh4, 0, wx.ALIGN_CENTER_VERTICAL),
            ((20,-1), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.statictextNmax, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.spinNmax, 0, wx.ALIGN_CENTER_VERTICAL),
            ((20,-1), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.checkboxLive, 0, wx.ALIGN_CENTER_VERTICAL),
            ((20,-1), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.buttonPP, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.buttonP, 0, wx.ALIGN_CENTER_VERTICAL),
            ((10,-1), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlN, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.statictextSlash, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlNmax, 0, wx.ALIGN_CENTER_VERTICAL),
            ((10,-1), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.buttonN, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.buttonNN, 0, wx.ALIGN_CENTER_VERTICAL),
            ((20,-1), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.buttonAcq, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.buttonStop, 0, wx.ALIGN_CENTER_VERTICAL),
            ((20,-1), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.buttonClear, 0, wx.ALIGN_CENTER_VERTICAL)
            ])
        
        self.statictextAddress = wx.StaticText(self.panel, label='Address :')
        self.txtctrlAddress = wx.TextCtrl(self.panel, value='USB0::0x0957::0x17A0::MY53280162::0::INSTR', size=(270,-1))
        self.txtctrlAddress.Enable(False)
        self.sizer_menu_lower = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_menu_lower.AddMany([
            (self.statictextAddress, 0, wx.ALIGN_CENTER_VERTICAL),
            ((5,-1)),
            (self.txtctrlAddress, 0, wx.ALIGN_CENTER_VERTICAL)
            ])

        self.sizer_menu = wx.BoxSizer(wx.VERTICAL)
        self.sizer_menu.AddMany([
            (self.sizer_menu_upper),
            ((-1, 10)),
            (self.sizer_menu_lower)
            ])

    def Canvas(self):
        canvas_font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.canvas = wx.GridSizer(2,2,5,5)
        self.plot = {}
        self.plot['CHANNEL1'] = {}
        self.plot['CHANNEL2'] = {}
        self.plot['CHANNEL3'] = {}
        self.plot['CHANNEL4'] = {}
        self.DefaultObject = wplt.PolyMarker([[0,0]], marker='cross', size=3, colour='red')
        for val in self.plot.values():
            val['Canvas'] = wplt.PlotCanvas(self.panel)
            val['Canvas'].SetFont(canvas_font)
            self.canvas.Add(val['Canvas'],1,wx.EXPAND)
            val['Graphics'] = wplt.PlotGraphics([self.DefaultObject])
                                
    def Process(self):
        self.statictextLaser = wx.StaticText(self.panel, label='Laser A (source)', size=(100,-1))
        self.comboLaser = wx.ComboBox(self.panel, choices=['']+list(self.channel_list), style=wx.CB_READONLY, size=(100,-1))
        self.statictextPlasma = wx.StaticText(self.panel, label='Plasma', size=(100,-1))
        self.comboPlasma = wx.ComboBox(self.panel, choices=['']+list(self.channel_list), style=wx.CB_READONLY, size=(100,-1))
        self.statictextLaserB = wx.StaticText(self.panel, label='Laser B (trans.)', size=(100,-1))
        self.comboLaserB = wx.ComboBox(self.panel, choices=['']+list(self.channel_list), style=wx.CB_READONLY, size=(100,-1))
        self.sizer_channel = wx.FlexGridSizer(3, 3, 5, 5)
        self.sizer_channel.AddMany([
            (self.statictextLaser,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.comboLaser,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel),0,wx.ALIGN_CENTER_VERTICAL),
            (self.statictextLaserB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.comboLaserB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel),0,wx.ALIGN_CENTER_VERTICAL),
            (self.statictextPlasma,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.comboPlasma,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel),0,wx.ALIGN_CENTER_VERTICAL)
            ])
        self.sizer_channel.AddGrowableCol(2,0)

        self.statictextOPL1 = wx.StaticText(self.panel, label='OPL from laser to PD(laser) [m]')
        self.statictextOPL2 = wx.StaticText(self.panel, label='OPL from laser to PD(plasma) [m]')
        self.statictextCL1 = wx.StaticText(self.panel, label='Cable length from OSC. to PD(laser) [m]')
        self.statictextCL2 = wx.StaticText(self.panel, label='Cable length from OSC. to PD(plasma) [m]')
        self.textctrlOPL1 = wx.TextCtrl(self.panel, value='0', size=(50,-1))
        self.textctrlOPL2 = wx.TextCtrl(self.panel, value='0', size=(50,-1))
        self.textctrlCL1 = wx.TextCtrl(self.panel, value='0', size=(50,-1))
        self.textctrlCL2 = wx.TextCtrl(self.panel, value='0', size=(50,-1))
        self.sizer_length = wx.FlexGridSizer(4,2,5,5)
        self.sizer_length.AddMany([
            (self.statictextOPL1,0,wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlOPL1,0,wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
            (self.statictextOPL2,0,wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlOPL2,0,wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
            (self.statictextCL1,0,wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCL1,0,wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL),
            (self.statictextCL2,0,wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCL2,0,wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
            ])
        self.sizer_length.AddGrowableCol(1,0)
                
        self.statictextCurrent = wx.StaticText(self.panel, label='Current', style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.statictextAvg = wx.StaticText(self.panel, label='Avg.', style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.statictextStd = wx.StaticText(self.panel, label='Std.', style=wx.ALIGN_CENTRE_HORIZONTAL)

        self.statictextArrival = wx.StaticText(self.panel, label='Laser arrival', size=(70,-1))
        self.statictextArea = wx.StaticText(self.panel, label='Pulse area A', size=(70,-1))
        self.statictextAreaB = wx.StaticText(self.panel, label='Pulse area B', size=(70,-1))
        self.statictextDecay = wx.StaticText(self.panel, label='Decay time', size=(70,-1))

        self.buttonEnergy = wx.Button(self.panel, label='Pulse E. A', size=(70,-1))
        self.buttonEnergyB = wx.Button(self.panel, label='Pulse E. B', size=(70,-1))
        self.buttonPressure = wx.Button(self.panel, label='Pressure', size=(70,-1))

        self.textctrlCurrentArrival = wx.TextCtrl(self.panel, value='s', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlAvgArrival = wx.TextCtrl(self.panel, value='s', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlStdArrival = wx.TextCtrl(self.panel, value='s', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))

        self.textctrlCurrentArea = wx.TextCtrl(self.panel, value='Vs', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlAvgArea = wx.TextCtrl(self.panel, value='Vs', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlStdArea = wx.TextCtrl(self.panel, value='Vs', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))

        self.textctrlCurrentAreaB = wx.TextCtrl(self.panel, value='Vs', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlAvgAreaB = wx.TextCtrl(self.panel, value='Vs', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlStdAreaB = wx.TextCtrl(self.panel, value='Vs', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))

        self.textctrlCurrent = wx.TextCtrl(self.panel, value='s', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlAvg = wx.TextCtrl(self.panel, value='s', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlStd = wx.TextCtrl(self.panel, value='s', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))

        self.textctrlCurrentEnergy = wx.TextCtrl(self.panel, value='J', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlAvgEnergy = wx.TextCtrl(self.panel, value='J', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlStdEnergy = wx.TextCtrl(self.panel, value='J', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))

        self.textctrlCurrentEnergyB = wx.TextCtrl(self.panel, value='J', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlAvgEnergyB = wx.TextCtrl(self.panel, value='J', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlStdEnergyB = wx.TextCtrl(self.panel, value='J', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))

        self.textctrlCurrentPressure = wx.TextCtrl(self.panel, value='bara', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlAvgPressure = wx.TextCtrl(self.panel, value='bara', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))
        self.textctrlStdPressure = wx.TextCtrl(self.panel, value='bara', style=wx.TE_READONLY|wx.TE_RIGHT, size=(90,-1))

        self.sizer_result = wx.FlexGridSizer(9, 4, 5, 5)
        self.sizer_result.AddMany([
            (wx.StaticText(self.panel),0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.statictextCurrent,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.statictextAvg,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.statictextStd,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),

            (self.statictextArrival,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCurrentArrival,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlAvgArrival,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlStdArrival,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),

            (self.statictextArea,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCurrentArea,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlAvgArea,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlStdArea,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),

            (self.statictextAreaB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCurrentAreaB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlAvgAreaB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlStdAreaB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),

            (self.statictextDecay,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCurrent,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlAvg,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlStd,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),

            (wx.StaticText(self.panel),0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel),0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel),0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (wx.StaticText(self.panel),0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),

            (self.buttonEnergy,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCurrentEnergy,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlAvgEnergy,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlStdEnergy,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),

            (self.buttonEnergyB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCurrentEnergyB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlAvgEnergyB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlStdEnergyB,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),

            (self.buttonPressure,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlCurrentPressure,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlAvgPressure,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL),
            (self.textctrlStdPressure,0,wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)            
            ])
        self.sizer_result.AddGrowableCol(0,0)

        self.sizer_process = wx.BoxSizer(wx.VERTICAL)
        self.sizer_process.AddMany([
            (self.sizer_channel,0,wx.EXPAND|wx.ALL, 10),
            (self.sizer_length,0,wx.EXPAND|wx.ALL, 10),
            (self.sizer_result,0,wx.EXPAND|wx.ALL, 10)
            ])

    ##### LAYOUT END #####

    #### FUNCTION START ####

    def Initializing(self):        
        self.DataRefresh()
        self.PlotRefresh()
        self.cal_reference = {
            'area':{'values':{'1':'','2':'','3':'','4':'','5':''},'label':'Area [nVs]','flag':False},
            'energy':{'values':{'1':'','2':'','3':'','4':'','5':''},'label':'Energy [mJ]','flag':False},
            'area B':{'values':{'1':'','2':'','3':'','4':'','5':''},'label':'Area [nVs]','flag':False},
            'energy B':{'values':{'1':'','2':'','3':'','4':'','5':''},'label':'Energy [mJ]','flag':False},
            'decay time':{'values':{'1':'','2':'','3':'','4':'','5':''},'label':'Decay time [ns]','flag':False},
            'pressure':{'values':{'1':'','2':'','3':'','4':'','5':''},'label':'Pressure [bara]','flag':False},
            }
        if os.path.isfile(autocal):
            f = open(autocal, 'rb')
            self.cal_reference = pickle.load(f)
            f.close()
        for widget in self.widgets:
            widget.Enable(True)
        self.buttonStop.Enable(False)

    def ChannelRefresh(self):
        self.channel_on = []
        i = 0
        for chan in [self.checkboxCh1, self.checkboxCh2, self.checkboxCh3, self.checkboxCh4]:
            i += 1
            if chan.GetValue() == True:
                self.channel_on.append('CHANNEL{}'.format(i))

    def ModeRefresh(self):
        pass

    def PlotRefresh(self):
        for chan in self.channel_list:           
            self.plot[chan]['Graphics'].objects = [self.DefaultObject]
            self.plot[chan]['Graphics'].title = chan
            self.plot[chan]['Graphics'].xLabel = 'NO DATA'
            self.plot[chan]['Graphics'].yLabel = 'NO DATA'
            
        widgets = [self.textctrlCurrentArrival, self.textctrlAvgArrival, self.textctrlStdArrival,
                   self.textctrlCurrentArea, self.textctrlAvgArea, self.textctrlStdArea,
                   self.textctrlCurrentAreaB, self.textctrlAvgAreaB, self.textctrlStdAreaB,
                   self.textctrlCurrent, self.textctrlAvg, self.textctrlStd,
                   self.textctrlCurrentEnergy, self.textctrlAvgEnergy, self.textctrlStdEnergy,
                   self.textctrlCurrentEnergyB, self.textctrlAvgEnergyB, self.textctrlStdEnergyB,
                   self.textctrlCurrentPressure, self.textctrlAvgPressure, self.textctrlStdPressure]

        n = int(self.textctrlN.GetValue())

        for chan in self.channel_on:
            if len(self.t) < n or n == 0:
                break
            
            PolyObject = []

            t = self.t[n-1]
            V = self.V[chan][n-1]
            Vmin = np.amin(V)
            Vmax = np.amax(V)
            Vspan = Vmax-Vmin

            X_order, X_unit = GetOrder(t)
            Y_order, Y_unit = GetOrder(V)
            
            self.plot[chan]['Graphics'].xLabel = X_unit + 's'
            self.plot[chan]['Graphics'].yLabel = Y_unit + 'V'
            self.plot[chan]['Canvas'].xSpec = 'min'
            self.plot[chan]['Canvas'].ySpec = 'min'
            PolyObject.append(wplt.PolyLine(np.append([t*X_order],[V*Y_order],axis=0).transpose(), colour='black', width=1, style=wx.PENSTYLE_SOLID))
            
            if not n == 0 and len(self.laser_A['V']) >= n and self.comboLaser.GetValue() == chan:
                V_A = self.laser_A['V'][n-1]
                t0_A = np.array(self.laser_A['t0'])
                t0_A_order, t0_A_unit = GetOrder(t0_A[n-1])
                PolyObject.append(wplt.PolyLine(np.append([t*X_order],[V_A*Y_order],axis=0).transpose(), colour='blue', width=2, style=wx.PENSTYLE_SHORT_DASH))
                PolyObject.append(wplt.PolyLine([[t0_A[n-1]*X_order, (Vmin-Vspan*0.05)*Y_order],[t0_A[n-1]*X_order, (Vmax+Vspan*0.05)*Y_order]], colour='red', width=2, style=wx.PENSTYLE_SHORT_DASH))
                area_A = np.array(self.laser_A['area'])
                area_A_order, area_A_unit = GetOrder(area_A[n-1])
                self.textctrlCurrentArrival.SetValue(str(round(t0_A[n-1]*t0_A_order, 2)) + ' ' + t0_A_unit + 's')
                self.textctrlAvgArrival.SetValue(str(round(np.average(t0_A*t0_A_order), 2)) + ' ' + t0_A_unit +  's')
                self.textctrlStdArrival.SetValue(str(round(np.std(t0_A*t0_A_order), 2)) + ' ' + t0_A_unit +  's')                
                self.textctrlCurrentArea.SetValue(str(round(area_A[n-1]*area_A_order, 2)) + ' ' + area_A_unit + 'Vs')
                self.textctrlAvgArea.SetValue(str(round(np.average(area_A*area_A_order), 2)) + ' ' + area_A_unit +  'Vs')
                self.textctrlStdArea.SetValue(str(round(np.std(area_A*area_A_order), 2)) + ' ' + area_A_unit +  'Vs')
                widgets_laser = [self.textctrlCurrentArrival, self.textctrlAvgArrival, self.textctrlStdArrival,
                                 self.textctrlCurrentArea, self.textctrlAvgArea, self.textctrlStdArea]
                for widget_laser in widgets_laser:
                    widgets.remove(widget_laser)

            if not n == 0 and len(self.laser_B['V']) >= n and self.comboLaserB.GetValue() == chan:
                V_B = self.laser_B['V'][n-1]
                PolyObject.append(wplt.PolyLine(np.append([t*X_order],[V_B*Y_order],axis=0).transpose(), colour='blue', width=2, style=wx.PENSTYLE_SHORT_DASH))
                area_B = np.array(self.laser_B['area'])
                area_B_order, area_B_unit = GetOrder(area_B[-1])
                self.textctrlCurrentAreaB.SetValue(str(round(area_B[n-1]*area_B_order, 2)) + ' ' + area_B_unit + 'Vs')   
                self.textctrlAvgAreaB.SetValue(str(round(np.average(area_B*area_B_order), 2)) + ' ' + area_B_unit +  'Vs')
                self.textctrlStdAreaB.SetValue(str(round(np.std(area_B*area_B_order), 2)) + ' ' + area_B_unit +  'Vs')
                widgets_laser = [self.textctrlCurrentAreaB, self.textctrlAvgAreaB, self.textctrlStdAreaB]
                for widget_laser in widgets_laser:
                    widgets.remove(widget_laser)

            self.plot[chan]['Graphics'].objects = PolyObject
            self.plot[chan]['Canvas'].yAxis=((Vmin-Vspan*0.1)*Y_order, (Vmax+Vspan*0.1)*Y_order)

        if not n == 0 and len(self.energy_B) >= n:
            self.textctrlCurrentEnergyB.SetValue(str(round(self.energy_B[n-1], 2)) + ' mJ')   
            self.textctrlAvgEnergyB.SetValue(str(round(np.average(self.energy_B), 2)) + ' mJ')
            self.textctrlStdEnergyB.SetValue(str(round(np.std(self.energy_B), 2)) + ' mJ')
            for widget_energy in [self.textctrlCurrentEnergy, self.textctrlAvgEnergy, self.textctrlStdEnergy]:
                widgets.remove(widget_energy)

        if not n == 0 and len(self.plasma['V0']) >= n:
            chan_plasma = self.comboPlasma.GetValue()
            td = self.plasma['td'][n-1]
            V0 = self.plasma['V0'][n-1]
            
            t = self.t[n-1]
            V = self.V[chan_plasma][n-1]
            Vmin = np.amin(V)
            Vmax = np.amax(V)
            Vspan = Vmax-Vmin

            PolyObject = self.plot[chan_plasma]['Graphics'].objects
            PolyObject.append(wplt.PolyLine([[td*X_order, (Vmin-Vspan*0.05)*Y_order],[td*X_order, (Vmax+Vmax*0.05)*Y_order]], colour='red', width=2, style=wx.PENSTYLE_SHORT_DASH))
            PolyObject.append(wplt.PolyLine([[t[0]*X_order, V0*Y_order],[t[-1]*X_order, V0*Y_order]], colour='red', width=2, style=wx.PENSTYLE_SHORT_DASH))
            PolyObject.append(wplt.PolyLine([[t0_A[n-1]*X_order, (Vmin-Vspan*0.05)*Y_order],[t0_A[n-1]*X_order, (Vmax+Vmax*0.05)*Y_order]], colour='red', width=2, style=wx.PENSTYLE_SHORT_DASH))
            self.plot[chan_plasma]['Graphics'].objects = PolyObject
            
        if not n == 0 and len(self.energy_A) >= n:
            self.textctrlCurrentEnergy.SetValue(str(round(self.energy_A[n-1], 2)) + ' mJ')   
            self.textctrlAvgEnergy.SetValue(str(round(np.average(self.energy_A), 2)) + ' mJ')
            self.textctrlStdEnergy.SetValue(str(round(np.std(self.energy_A), 2)) + ' mJ')
            for widget_energy in [self.textctrlCurrentEnergy, self.textctrlAvgEnergy, self.textctrlStdEnergy]:
                widgets.remove(widget_energy)

        if not n == 0 and len(self.decay_time) >= n:
            self.textctrlCurrent.SetValue(str(round(self.decay_time[n-1]*X_order, 2)) + ' ' + X_unit + 's')
            self.textctrlAvg.SetValue(str(round(np.average(np.array(self.decay_time)*X_order), 2)) + ' ' + X_unit + 's')
            self.textctrlStd.SetValue(str(round(np.std(np.array(self.decay_time)*X_order), 2)) + ' ' + X_unit + 's')
            widgets_decay = [self.textctrlCurrent, self.textctrlAvg, self.textctrlStd]
            for widget_decay in widgets_decay:
                widgets.remove(widget_decay)

        if not n == 0 and len(self.pressure) >= n:
            self.textctrlCurrentPressure.SetValue(str(round(self.pressure[n-1]*area_order, 2)) + ' bara')   
            self.textctrlAvgPressure.SetValue(str(round(np.average(np.array(self.pressure)), 2)) + ' bara')
            self.textctrlStdPressure.SetValue(str(round(np.std(np.array(self.pressure)), 2)) + ' bara')
            for widget_pressure in [self.textctrlCurrentPressure, self.textctrlAvgPressure, self.textctrlStdPressure]:
                widgets.remove(widget_pressure)

        for widget in widgets:
            widget.SetValue('')

        for chan in self.channel_list:
            self.plot[chan]['Canvas'].Draw(self.plot[chan]['Graphics'])

    def DataRefresh(self):
        '''
        self.X_origin = [#, #, ..., #]
        self.X_increment = [#, #, ..., #]
        self.points = [#, #, ..., #]
        self.X = [[#, #, ..., #], ..., [#, #, ..., #]]
        self.t = [[#, #, ..., #], ..., [#, #, ..., #]]

        self.Y_origin = {'CHANNEL1':[#, #, ..., #], 'CHANNEL2':[#, #, ..., #], 'CHANNEL3':[#, #, ..., #], 'CHANNEL4':[#, #, ..., #]}
        self.Y_increment = {'CHANNEL1':[#, #, ..., #], 'CHANNEL2':[#, #, ..., #], 'CHANNEL3':[#, #, ..., #], 'CHANNEL4':[#, #, ..., #]}
        self.Y_reference = {'CHANNEL1':[#, #, ..., #], 'CHANNEL2':[#, #, ..., #], 'CHANNEL3':[#, #, ..., #], 'CHANNEL4':[#, #, ..., #]}
        self.Y = {'CHANNEL1':[[#, #, ..., #], ..., [#, #, ..., #]],
                  'CHANNEL2':[[#, #, ..., #], ..., [#, #, ..., #]],
                  'CHANNEL3':[[#, #, ..., #], ..., [#, #, ..., #]],
                  'CHANNEL4':[[#, #, ..., #], ..., [#, #, ..., #]]}
        self.V = {'CHANNEL1':[[#, #, ..., #], ..., [#, #, ..., #]],
                  'CHANNEL2':[[#, #, ..., #], ..., [#, #, ..., #]],
                  'CHANNEL3':[[#, #, ..., #], ..., [#, #, ..., #]],
                  'CHANNEL4':[[#, #, ..., #], ..., [#, #, ..., #]]}

        self.laser_A = {'V':[[#, #, ..., #], ..., [#, #, ..., #]],
                        't0':[#, #, ..., #],
                        'V0':[#, #, ..., #],
                        'area':[#, #, ..., #]}
        self.laser_B = {'V':[[#, #, ..., #], ..., [#, #, ..., #]],
                        't0':[#, #, ..., #],
                        'V0':[#, #, ..., #],
                        'area':[#, #, ..., #]}
        self.plasma = {'V0':[#, #, ..., #],
                       'td':[#, #, ..., #]}

        self.decay_time = [#, #, ..., #]
        self.energy_A = [#, #, ..., #]
        self.energy_B = [#, #, ..., #]
        self.pressure = [#, #, ..., #]
        '''

        self.X_origin = []
        self.X_increment = []
        self.points = []
        self.X = []
        self.t = []

        self.Y_origin = {'CHANNEL1':[],'CHANNEL2':[],'CHANNEL3':[],'CHANNEL4':[]}
        self.Y_increment = {'CHANNEL1':[],'CHANNEL2':[],'CHANNEL3':[],'CHANNEL4':[]}
        self.Y_reference = {'CHANNEL1':[],'CHANNEL2':[],'CHANNEL3':[],'CHANNEL4':[]}
        self.Y = {'CHANNEL1':[],'CHANNEL2':[],'CHANNEL3':[],'CHANNEL4':[]}
        self.V = {'CHANNEL1':[],'CHANNEL2':[],'CHANNEL3':[],'CHANNEL4':[]}

        self.laser_A = {'V':[],'t0':[],'V0':[],'area':[]}
        self.laser_B = {'V':[],'t0':[],'V0':[],'area':[]}
        self.plasma = {'V0':[],'td':[]}
        
        self.decay_time = []
        self.energy_A = []
        self.energy_B = []
        self.pressure = []

        self.textctrlN.SetValue('0')
        self.textctrlNmax.SetValue('0')

    def AcquireData(self):
        try:
            for widget in self.widgets:
                widget.Enable(False)
            self.buttonStop.Enable(True)

            self.DataRefresh()
            self.rm = pyvisa.ResourceManager()
            self.MSO_X3104A = self.rm.open_resource(self.txtctrlAddress.GetValue())
            self.MSO_X3104A.timeout = 20_000
            self.MSO_X3104A.write(':ACQuire:MODE %s' % 'RTIMe')
            self.MSO_X3104A.write(':ACQuire:TYPE %s' % 'NORMal')

            if self.checkboxLive.GetValue() == True: # Live Mode
                i = 0
                self.stop = 0
                while self.stop == 0:                
                    if len(self.X_origin) >= 30:
                        i -= 1
                        for data in [self.X_origin, self.X_increment, self.points, self.X, self.t]: del(data[0])
                        for data in [self.Y_origin, self.Y_increment, self.Y_reference, self.Y, self.V]:
                            for chan in self.channel_on: del(data[chan][0])
                        if len(self.laser_A['V']) >= 30:
                            for key in self.laser_A: del(self.laser_A[key][0])
                        if len(self.laser_B['V']) >= 30:
                            for key in self.laser_B: del(self.laser_B[key][0])
                        if len(self.plasma) >= 30:
                            del(self.plasma[0])
                        for data in [self.decay_time, self.energy_A, self.energy_B, self.pressure]:
                            if len(data) >= 30:
                                del(data[0])
                    i += 1
                    self.textctrlN.SetValue(str(i))
                    self.textctrlNmax.SetValue(str(i))
                    self.AcquireCommand(self.channel_on)

            else: # Normal Mode
                nmax = int(self.spinNmax.GetValue())
                self.textctrlNmax.SetValue(str(nmax))
                for n in range(nmax):
                    self.textctrlN.SetValue(str(n+1))
                    self.AcquireCommand(self.channel_on)
         
            self.MSO_X3104A.close()
            self.rm.close()

            for widget in self.widgets:
                widget.Enable(True)
            self.buttonStop.Enable(False)
            self.ModeRefresh()

        except pyvisa.errors.VisaIOError as err:
            self.Initializing()
            wx.MessageBox(str(err),'Connection failed',wx.OK)
        
        except Exception as err:
            self.Initializing()
            wx.MessageBox(str(err),'Acquisition failed',wx.OK)
        


    def AcquireCommand(self, CHANNELS):        
        self.MSO_X3104A.write(':DIGitize {}'.format(','.join(CHANNELS)))
        self.MSO_X3104A.write(':WAVeform:SOURce %s' % CHANNELS[0])
        self.MSO_X3104A.write(':WAVeform:POINts:MODE %s' % ('NORMal'))
        X_inc = self.MSO_X3104A.query_ascii_values(':WAVeform:XINCrement?')[0]
        X_ori = self.MSO_X3104A.query_ascii_values(':WAVeform:XORigin?')[0]
        p = int(self.MSO_X3104A.query_ascii_values(':WAVeform:POINts?')[0])
        X = list(range(1, p+1))
        t = Calibration(X, X_ori, X_inc)
        self.X_increment.append(X_inc)
        self.X_origin.append(X_ori)    
        self.points.append(p)
        self.X.append(X)
        self.t.append(t)
        
        k = 0
        for chan in CHANNELS:
            self.MSO_X3104A.write(':WAVeform:SOURce %s' % chan)
            self.MSO_X3104A.write(':WAVeform:FORMat %s' % ('BYTE'))
            Y_inc = self.MSO_X3104A.query_ascii_values(':WAVeform:YINCrement?')[0]
            Y_ori = self.MSO_X3104A.query_ascii_values(':WAVeform:YORigin?')[0]
            Y_ref = self.MSO_X3104A.query_ascii_values(':WAVeform:YREFerence?')[0]
            Y = self.MSO_X3104A.query_binary_values(':WAVeform:DATA?','B',False)
            V = Calibration(Y, Y_ori, Y_inc, Y_ref)
            self.Y_increment[chan].append(Y_inc)
            self.Y_origin[chan].append(Y_ori)
            self.Y_reference[chan].append(Y_ref)
            self.Y[chan].append(Y)
            self.V[chan].append(V)

            # Post processing
            if self.comboLaser.GetValue() == chan:
                k += 1
                popt = GetLaserPopt(X, Y)
                Y = GaussianFunc(X, *popt)
                X0 = popt[1]
                Y0 = popt[3]
                area = np.sqrt(2)*popt[0]*np.abs(popt[2])*np.sqrt(np.pi)*X_inc*Y_inc
                V_A = Calibration(Y, Y_ori, Y_inc, Y_ref)
                t0 = Calibration(X0, X_ori, X_inc)
                V0 = Calibration(Y0, Y_ori, Y_inc, Y_ref)
                self.laser_A['V'].append(V_A)
                self.laser_A['t0'].append(t0)
                self.laser_A['V0'].append(V0)
                self.laser_A['area'].append(area)
                # Energy conversion
                X_ref = self.cal_reference['area']['values'].values()
                Y_ref = self.cal_reference['energy']['values'].values()
                result = PropertyRegression(list(X_ref), list(Y_ref))
                if not result == False:
                    X_e, Y_e, slope, intercept, r_value = result
                    self.energy_A.append(area*10**9*slope+intercept) # [mJ]

            if self.comboLaserB.GetValue() == chan:
                popt = GetLaserPopt(X, Y)
                Y = GaussianFunc(X, *popt)
                X0 = popt[1]
                Y0 = popt[3]
                area_B = np.sqrt(2)*popt[0]*np.abs(popt[2])*np.sqrt(np.pi)*X_inc*Y_inc
                V_A = Calibration(Y, Y_ori, Y_inc, Y_ref)
                t0 = Calibration(X0, X_ori, X_inc)
                V0 = Calibration(Y0, Y_ori, Y_inc, Y_ref)
                self.laser_B['V'].append(V_A)
                self.laser_B['t0'].append(t0)
                self.laser_B['V0'].append(V0)
                self.laser_B['area'].append(area_B)
                # Energy conversion
                X_ref = self.cal_reference['area B']['values'].values()
                Y_ref = self.cal_reference['energy B']['values'].values()
                result = PropertyRegression(list(X_ref), list(Y_ref))
                if not result == False:
                    X_e, Y_e, slope, intercept, r_value = result
                    self.energy_B.append(np.array(area_B)*10**9*slope+intercept) # [mJ]

            if self.comboPlasma.GetValue() == chan:
                k += 1
                Xd, Y0 = DecayTime(X, Y)
                td = Calibration(Xd, X_ori, X_inc)
                V0 = Calibration(Y0, Y_ori, Y_inc, Y_ref)
                self.plasma['td'].append(td)
                self.plasma['V0'].append(V0)

            if k == 2:
                x1 = float(self.textctrlOPL1.GetValue())
                x2 = float(self.textctrlCL1.GetValue())
                y1 = float(self.textctrlOPL2.GetValue())
                y2 = float(self.textctrlCL2.GetValue())
                length = ((y1-x1)/3+(y2-x2)/2)/10**8
                tdd = self.plasma['td'][-1]-self.laser_A['t0'][-1] + length
                self.decay_time.append(tdd)

                X_ref = self.cal_reference['decay time']['values'].values()
                Y_ref = self.cal_reference['pressure']['values'].values()
                result = PropertyRegression(list(X_ref), list(Y_ref))
                if not result == False:
                    X_e, Y_e, slope, intercept, r_value = result
                    self.pressure.append(tdd*10**9*slope+intercept)

        self.PlotRefresh()
                
    def eventBind(self):
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.Bind(wx.EVT_MENU, self.OnQuit, self.ItemQuit)
        self.Bind(wx.EVT_MENU, self.OnSave, self.ItemSave)
        self.Bind(wx.EVT_MENU, self.OnAdd, self.ItemAddress)
        self.Bind(wx.EVT_MENU, self.OnAbout, self.ItemAbout)
        self.Bind(wx.EVT_MENU, self.OnGithub, self.ItemGithub)
        self.Bind(wx.EVT_CHECKBOX, self.OnLive, self.checkboxLive)
        for checkboxCh in [self.checkboxCh1, self.checkboxCh2, self.checkboxCh3, self.checkboxCh4]:
            self.Bind(wx.EVT_CHECKBOX, self.OnChannel, checkboxCh)
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.buttonClear)
        self.Bind(wx.EVT_BUTTON, self.OnPP, self.buttonPP)
        self.Bind(wx.EVT_BUTTON, self.OnP, self.buttonP)
        self.Bind(wx.EVT_BUTTON, self.OnN, self.buttonN)
        self.Bind(wx.EVT_BUTTON, self.OnNN, self.buttonNN)
        self.Bind(wx.EVT_BUTTON, self.OnAcq, self.buttonAcq)
        self.Bind(wx.EVT_BUTTON, self.OnStop, self.buttonStop)
        self.Bind(wx.EVT_BUTTON, self.OnCalEnergy, self.buttonEnergy)
        self.Bind(wx.EVT_BUTTON, self.OnCalEnergyB, self.buttonEnergyB)
        self.Bind(wx.EVT_BUTTON, self.OnCalPressure, self.buttonPressure)

    def OnQuit(self, event):
        dial = wx.MessageDialog(None,"Are you sure to quit?","Quit",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        returnvalue = dial.ShowModal()
        if returnvalue == wx.ID_YES:
            self.Destroy()

    def OnSave(self, event):
        try:
            if len(self.t) == 0:
                wx.MessageBox('No data exists','Save error',wx.OK)
                return

            dial = wx.FileDialog(None, "Save here", "", "", "CSV files (*.txt)|*.txt", wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
            if dial.ShowModal() == wx.ID_CANCEL:
                pass
            else:
                path = dial.GetPath()
                path_t = path[:-4] + '_t' + path[-4:]
                path_V = path[:-4] + '_V' + path[-4:]

                n = 0
                csvfile = open(path_t, "w", newline="")
                csvwriter = csv.writer(csvfile)
                for i in self.t:
                    n += 1
                    csvwriter.writerow(['Time[s]-' + str(n)] + list(i))
                csvfile.close()

                for chan in self.channel_on:
                    n = 0
                    fname_chan = '('+chan+')'
                    path_Vc = path_V[:-4] + fname_chan + path_V[-4:]
                    csvfile = open(path_Vc, "w", newline="")
                    csvwriter = csv.writer(csvfile)
                    for i in self.V[chan]:
                        n += 1
                        csvwriter.writerow(['Voltage[V]-' + str(n)] + list(i))
                    csvfile.close()

                # processed data
                group = [self.laser_A['area'], self.laser_B['area'], self.decay_time, self.energy_A, self.energy_B]
                label = ['Area(A)[Vs]', 'Area(B)[Vs]', 'Decay time[s]', 'Energy(A)[mJ]', 'Energy(B)[mJ]']
                path_p = path[:-4] + '_p' + path[-4:]
                csvfile = open(path_p, "w", newline="")
                csvwriter = csv.writer(csvfile)
                for i in range(5):
                    if not len(group[i]) == 0:
                        csvwriter.writerow([label[i]]+group[i])
                csvfile.close()

        except Exception as err:
            wx.MessageBox(str(err),'Save error',wx.OK)

    def OnAdd(self, event):
        dlg = wx.TextEntryDialog(self, "Enter VISA address", "Oscilloscope-Address")
        dlg.SetValue(self.txtctrlAddress.GetValue())
        if dlg.ShowModal() == wx.ID_OK:
            self.txtctrlAddress.SetValue(dlg.GetValue())
        dlg.Destroy()

    def OnAbout(self, event):
        dlg = AboutDialog()
        dlg.ShowModal()

    def OnGithub(self, event):
        webbrowser.open('https://github.com/sebae1/pysight')

    def OnLive(self, event):
        self.ModeRefresh()

    def OnChannel(self, event):
        self.ChannelRefresh()

    def OnClear(self, event):
        self.DataRefresh()
        self.PlotRefresh()

    def OnPP(self, event):
        n = int(self.textctrlN.GetValue())
        if n-10 <= 0: n = 1
        else: n -= 10
        self.textctrlN.SetValue(str(n))
        self.PlotRefresh()

    def OnP(self, event):
        n = int(self.textctrlN.GetValue())
        if n-1 <= 0: n = 1
        else: n -= 1
        self.textctrlN.SetValue(str(n))
        self.PlotRefresh()

    def OnN(self, event):
        n = int(self.textctrlN.GetValue())
        nmax = int(self.textctrlNmax.GetValue())
        if n+1 >= nmax: n = nmax
        else: n += 1
        self.textctrlN.SetValue(str(n))
        self.PlotRefresh()

    def OnNN(self, event):
        n = int(self.textctrlN.GetValue())
        nmax = int(self.textctrlNmax.GetValue())
        if n+10 >= nmax: n = nmax
        else: n += 10
        self.textctrlN.SetValue(str(n))
        self.PlotRefresh()

    def OnAcq(self, event):
        _thread.start_new_thread(self.AcquireData, ())

    def OnStop(self, event):
        self.stop = 1

    def OnCalEnergy(self, event):
        dlg = CalibrationDialog(None, 'Pulse Energy Calibration (A)', self.cal_reference['area'], self.cal_reference['energy'])
        if dlg.ShowModal() == True:
            self.cal_reference['area'] = dlg.x
            self.cal_reference['energy'] = dlg.y
            f = open(autocal, 'wb')
            pickle.dump(self.cal_reference, f)
            f.close()
        dlg.Destroy()
        self.PlotRefresh()

    def OnCalEnergyB(self, event):
        dlg = CalibrationDialog(None, 'Pulse Energy Calibration (B)', self.cal_reference['area B'], self.cal_reference['energy B'])
        if dlg.ShowModal() == True:
            self.cal_reference['area B'] = dlg.x
            self.cal_reference['energy B'] = dlg.y
            f = open(autocal, 'wb')
            pickle.dump(self.cal_reference, f)
            f.close()
        dlg.Destroy()
        self.PlotRefresh()

    def OnCalPressure(self, event):
        dlg = CalibrationDialog(None, 'Pressure Calibration', self.cal_reference['decay time'], self.cal_reference['pressure'])
        if dlg.ShowModal() == True:
            self.cal_reference['decay time'] = dlg.x
            self.cal_reference['pressure'] = dlg.y
            f = open(autocal, 'wb')
            pickle.dump(self.cal_reference, f)
            f.close()
        dlg.Destroy()
        self.PlotRefresh()

    #### FUNCTION END #####  


if __name__ == '__main__':
    app = wx.App()
    frame = PySight()
    frame.Show(True)
    app.MainLoop()

