import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit

#####
import loadBasisSets as BS
# import fittingFunctions as FF



def interpolateData(data, min_eKE = 0, xs = np.arange(0.01,5.01,0.01)):
    """Interpolates data onto ```xs```"""
    data = np.asarray(data)
    itp = interp1d(data[0], data[1], bounds_error=False, fill_value=0.0)
    y_itp = itp(xs)
    x_above_cutoff = xs[xs>=min_eKE]
    y_above_cutoff = y_itp[-x_above_cutoff.shape[0]:]

    return np.asarray((x_above_cutoff,y_above_cutoff))

def setupFitFunc(gauss_types, crossSectionSetInd, thresholdInd, surfInd, min_eKE):
    """Creates fit function"""
    surf_bas = BS.allBasisSets[crossSectionSetInd,thresholdInd,surfInd]
    bulk_bas = BS.allBasisSets[crossSectionSetInd,thresholdInd,0]
    fitfunc = JetFitFunc(gauss_types, surf_bas, bulk_bas, min_eKE)
    return fitfunc


def retrieveFit(fitfunc,xs,y_above_cutoff,p0,**curve_fit_kwargs):
    """Fits data with scattering model"""
    fit,covar = curve_fit(fitfunc.f, xs, y_above_cutoff,
        p0 = p0,
        **curve_fit_kwargs
                )
    
    return fit,covar

def retrieveRawFit(x_above_cutoff,y_above_cutoff,p0,**curve_fit_kwargs):
    """Fits data with a sum of Gaussians"""
    fit,covar = curve_fit(multiple_gaussians, x_above_cutoff, y_above_cutoff,
        p0 = p0,
        **curve_fit_kwargs
                )
    
    return fit,covar


def multiple_gaussians(x, *params):
    """Returns a sum of Gaussians
    
    *params are a series of amplitude, mean and
    full width at half maximum (FWHM)
    """
    y = np.zeros_like(x)
    for i in range(0, len(params), 3):
        amp = params[i]
        ctr = params[i+1]
        FWHM = params[i+2] 
        wid = FWHM * 0.60056
        y = y + amp * np.exp( -((x - ctr)/wid)**2)
    return y


class JetFitFunc():
    def __init__(self, gauss_types, surf_bas, bulk_bas, min_eKE):
        self.gauss_types = gauss_types
        self.surf_bas = surf_bas
        self.bulk_bas = bulk_bas
        self.min_eKE = min_eKE

    def f(self, x, *params):
        y = np.zeros_like(x)
 
        for gauss_ind, param_ind in enumerate(range(0, len(params), 3)):
            if self.gauss_types[gauss_ind] == "S":
                basis = self.surf_bas
            elif self.gauss_types[gauss_ind] == "B":
                basis = self.bulk_bas
            else:
                raise ValueError(f'Only "S" or "B" allowed. "{self.gauss_types[gauss_ind]}" is not a valid input.')
                
            amp = params[param_ind]
            ctr = params[param_ind+1]
            wid = params[param_ind+2]*.60056
            y_tmp = amp * np.exp( -((x - ctr)/wid)**2)
            y += np.sum(basis.T * y_tmp, axis=1)
            
        
        x_above_cutoff = x[x>=self.min_eKE]
        y_above_cutoff = y[-x_above_cutoff.shape[0]:]
        
        return y_above_cutoff
    

