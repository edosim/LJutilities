# LJutilities

A desktop toolkit for determining the streaming potential and vacuum-level offset from a series of xenon photoelectron spectra recorded in the liquid-jet photoelectron spectrometer at the Ultrafast Laser Facility, University College London.

## Streaming potential and vacuum-level offset

The streaming potential of a liquid jet shifts the measured kinetic energy of photoelectrons created in and near the liquid jet. Additionally, the presence of a liquid jet in the interaction chamber of the spectrometer causes water molecules to adsorb onto the walls of the chamber, shifting the local vacuum level. These two phenomena must be accounted for when processing liquid-jet photoelectron spectra in order to obtain accurate electron kinetic energies (eKE).

The streaming potential $\phi_{\mathrm{str}}$ and vacuum-level offset $V_0$ are determined by measuring a series of xenon photoelectron spectra while the liquid jet is translated at set distances from the interaction region along the interaction-region/detector axis:


```math
\mathrm{eKE}_{\mathrm{obs}}(x) = \mathrm{eKE}_{\mathrm{true}} - \phi_{\mathrm{str}} \frac{\ln\left(\displaystyle\frac{2\mathrm{L}+x}{x}\right)} {\ln\left(\displaystyle\frac{2(\mathrm{L}+x)-r}{r}\right)} - V_0,
```

where $\mathrm{eKE}_{\mathrm{obs}}(x)$ is the peak eKE when the jet is translated by a distance $x$ away from the interaction region, $\mathrm{eKE}_{\mathrm{true}}$ is the field-free eKE; $\mathrm{L}$ is the distance between the ionisation point and the skimmer and $r$ is the radius of the jet (1.0 mm and 0.01 mm, set in ``streaming/SPfunctions.py``).

## Getting started

Requires Python 3.11 + and `numpy`, `scipy`, `matplotlib`, `pyyaml` (`tkinter` comes with Python).

```bash
git clone https://github.com/edosim/LJutilities.git
cd LJutilities
pip install numpy scipy matplotlib pyyaml
python main.py
```

## Workflow

![Streaming potential tab of LJutilities](docs/gui.png)

1. **Input parameters**. Input the time-of-flight (TOF) to eKE conversion parameters and the wavelength used in the experiment. Note that the calibration parameters must be input before loading files, and the wavelength can be changed before any spectrum is fit.

2. **Load data**. Choose data folder (see [Data Format](#data-format) below), set the date, the file indices, and the jet positions. The "**V**" button fills in the file indices following the first one automatically. Spectra can be loaded (and deleted) individually or all at once. 

3. **Fit spectra**. Select a spectrum from the summary at the bottom of the window. A red background indicates that the spectrum has not yet been fit. Clicking on a spectrum displays the spectrum at the top. Here, clicking and dragging on the plot defines the fitting limits (blue lines) so that only the rising edge and the peak are fit with a Gaussian. Clicking “Fit” fits a Gaussian to the spectrum within the fitting limits; the background of the corresponding spectrum turns green in the bottom panel and the peak position is plotted in the right plot. “Previous” and “Next” can be clicked to switch between spectra.

4. **Streaming potential**. After at least three peak positions have been determined the equation in [Streaming potential and vacuum-level offset](#streaming-potential-and-vacuum-level-offset) is fit to the data and $\phi_{\mathrm{str}}$ and $V_0$ are displayed under the plot.

5. **Save results** . Click on save results to create a yaml file that includes $\phi_{\mathrm{str}}$, $V_0$, the folder path, date, file indices, liquid jet positions, peak eKEs, calibration parameters and wavelength.

## Repository structure

```
LJutilities/
├── main.py                  # Main window with one tab per utility
├── streaming/
│   ├── streamingGUI.py      # Streaming potential tab (GUI, loading, fitting, saving)
│   ├── SPfunctions.py       # Calibration, Jacobian, peak finding, fitting functions
│   ├── load_settings.py     # Reads settings.yaml
│   └── settings.yaml        # Default settings (folder, date, positions, calibration parameters, wavelength)
├── icons/                   # Button icons
├── docs/                    # Images for README
├── data/                    # Example data
└── LICENSE
```




## Data format
```
data/
└── 191224/                      # date folder (DDMMYY)
    └── 191224ag/                # date and file index
        ├── 191224ag.xml         # acquisition metadata
        └── 191224ag_SignalBack.txt   # TOF spectrum: columns = TOF (ns), intensity
```

The data in the folder `data/191224` is an example data set which works with the default positions, calibration parameters and wavelength.



## License
 
MIT. See [LICENSE](LICENSE).