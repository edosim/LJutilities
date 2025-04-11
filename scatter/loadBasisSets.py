import numpy as np
import h5py

cpath = r"C:/Users/Edoardo/"
cpath = r"C:/Users/edoar/"

results1b = r"OneDrive - University College London\PhD\Scattering code\SOPs and so\Results\240917"
results2 = r"OneDrive - University College London\PhD\Scattering code\SOPs and so\Results\240403"
results4 = r"OneDrive - University College London\PhD\Scattering code\SOPs and so\Results\240425"
results5 = r"OneDrive - University College London\PhD\Scattering code\SOPs and so\Results\240509"

fileDic = {
    "a": 0.0,
    "b": 0.1,
    "c": 0.2,
    "d": 0.3,
    "e": 0.5,
    "f": 0.8,
    "g": 1.0,
    "h": 1.5,
    "i": 2.0,
}
concAmps = [0.0,0.1,0.2,0.5,1.0,2.0,5.0,10.0,20.0,50.0,100.0]
E0s = list(fileDic.values())
crossSectionSets = ['1b (III)','2 (IV)','4 (I)','5 (II)']

#Guide for indices of basisSets (E0 amp)
indexGuide = []
for E0 in fileDic.values():
    indices = []
    for amp in concAmps:
        indices.append((E0, amp))
    indexGuide.append(indices)
indexGuide = np.array(indexGuide)
#indexGuide.shape

print("Loading basis sets...")
h5File = h5py.File('basisSets.hdf5', 'r')
allBasisSets = h5File['allBasisSets']
allBasisSetsUnnorm = h5File['allBasisSetsUnnorm']
print("Basis sets loaded")
