import numpy as np
import matplotlib.pyplot as plt
from curves_m import GaussianFunc
from scipy.optimize import curve_fit
from scipy.stats import linregress

def LaserArrival(popt, plotting=False, k=0.1):
    # popt from GaussianFunc in curves_m
    # 0 < k < 1
    a, b, c, y0 = popt
    X0 = b-np.sqrt(-2*c**2 * np.log((k-1)/a*y0+k))
    if plotting == True:
        X = np.linspace(b-5*c, b+5*c, 100)
        Y = GaussianFunc(X, *popt)
        plt.plot(X,Y)
        plt.axvline(x=X0, linestyle='--')
        plt.show()
    return X0

def DecayTime(X, Y, plotting=False):
    Y = np.array(Y)
    Y0 = np.average(Y[:30])
    Yp = Y-Y0
    Ymax = Yp.max()
    imax = int(np.where(Yp == Ymax)[0][0])
    Yp2 = np.abs(Yp[imax:]-Ymax*np.exp(-1))
    id = int(np.where(Yp2 == Yp2.min())[0][0])
    id += imax
    Xd = X[id]
    if plotting == True:
        plt.plot(X,Y)
        plt.axvline(x=Xd, linestyle='--')
        plt.axhline(y=Y0, linestyle='--')
        plt.show()
    return Xd, Y0

def GetLaserPopt(X, Y):
    X = np.array(X)
    Y = np.array(Y)
    ai = Y.max()
    au = Y.max()*3
    al = 0
    i = np.where(Y == Y.max())[0][0]
    bi = X[i]
    bu = X.max()
    bl = X.min()
    ci = (X.max()-X.min())/2
    cu = X.max()-X.min()
    cl = 0
    y0i = np.average(Y)
    y0u = Y.max()
    y0l = Y.min()- y0i
    initial = [ai, bi, ci, y0i]
    limits = [[al, bl, cl, y0l],[au, bu, cu, y0u]]
    popt, pcov = curve_fit(GaussianFunc, X, Y, p0=initial, bounds=limits)
    return popt

def GetOrder(data):
    # data as array
    if data.max() < 10**(-9): order, unit = [10**12, 'p']
    elif data.max() < 10**(-6): order, unit = [10**9, 'n']
    elif data.max() < 10**(-3): order, unit = [10**6, u'\N{MICRO SIGN}']
    elif data.max() < 10**(0): order, unit = [10**3, 'm']
    else: order, unit = [10**0, '']
    return order, unit

def Calibration(value, origin, increment, reference=1):
    if type(value) == list:
        value = np.array(value)
    return origin + (value-reference)*increment

def PropertyRegression(X, Y):
    X_e = []
    Y_e = []
    k = 0
    for i in range(len(X)):
        if isnumber(X[i]) == True and isnumber(Y[i]) == True:
            k += 1
            X_e.append(float(X[i]))
            Y_e.append(float(Y[i]))
    if k >= 2:
        slope, intercept, r_value, p_value, std_err = linregress(X_e, Y_e)
        return (X_e, Y_e, slope, intercept, r_value)
    else:
        return False

def isnumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        
