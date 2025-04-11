import numpy as np

MASS_ELECTRON = 0.51099895e6 # eV
LIGHTSPEED = 299792458e-9 #m/ns
XE_EBE = 12.131 #xenon


def calibration(t,s,t0,E0):
    """Parametrised 1/2 m v**2"""
    return (0.5* MASS_ELECTRON/(LIGHTSPEED**2)) * (s/(t-t0))**2 - E0

def jacobian(intensity,TOF,t0):
    return intensity * ((TOF-t0)**3)

def tof2eKE(spectrum,cal_params):
    """Converts TOF to eKE and applies Jacobian"""
    spectrum[1] = jacobian(spectrum[1],spectrum[0],cal_params[1])
    spectrum[0] = calibration(spectrum[0],*cal_params)
    return spectrum

def multiple_gaussians(x, *params):
    """amp, ctr, fwhm"""
    y = np.zeros_like(x)
    for i in range(0, len(params), 3):
        amp = params[i]
        ctr = params[i+1]
        fwhm = params[i+2] 
        wid = fwhm * 0.60056
        y = y + amp * np.exp( -((x - ctr)/wid)**2)
    return y


def SP_curve(x, wavelength, phi, offset):
    L = 1.0 #mm, distance from skimmer
    R = 0.01 #mm, radius of jet
    true_eKE = 3*1239.8/wavelength - XE_EBE

    return true_eKE - offset - phi * (np.log((2*L+x)/x)/np.log((2*L+2*x-R)/R))
