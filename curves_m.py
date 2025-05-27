import numpy as np

def GaussianFunc(x,a,b,c,y0): # Gaussian function
    return y0 + a*np.exp(-(x-b)**2/(2*c**2))
