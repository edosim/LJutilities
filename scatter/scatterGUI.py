import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from idlelib.tooltip import Hovertip
from ctypes import windll
####
if __name__=="__main__":
    # Direct import
    import loadBasisSets as BS
    import fitRetrieval as FR
else:
    #Relative import
    from . import loadBasisSets as BS
    from . import fitRetrieval as FR
###

#fix blurry text
windll.shcore.SetProcessDpiAwareness(1)

### Format constants ###
FONT_SIZE = 9
TITLE_FONT_SIZE = 20

MAIN_FRAME_PADDING = 10
RIGHT_FRAME_PADDING_Y = 15
RIGHT_FRAME_PADDING_X = 20
SETTING_FRAMES_PADDING_Y = 5
SETTING_FRAMES_PADDING_X = 0

WINDOW_COLOR = "#F0F0F0"
ACCENT_COLOR = '#D9D9D9'
MAIN_BUTTON_FONT = ('Helvetica', 9, 'bold')
MAIN_BUTTON_COLOR = "#dddddd"#"#ced1d7"
INFO_ICON_SUBSAMPLE = 2


## mpl rcParams
rcParams = {'figure.dpi':200,
            'font.family':'Arial',
            'font.size': 10.0,
            'legend.fontsize': 'medium', #equal to font.size
            'axes.labelsize':'medium',
            'legend.handletextpad': 0.8,
            'legend.labelspacing': 0.5,
            'lines.linewidth': 1.5,
            'lines.markersize': 3
            }

###
#This will color the border blue
#Use to check frame shape
#highlightbackground="blue", highlightthickness=0

### --------Custom widgets---------
class CustomHovertip(Hovertip):
    """Created with copilot"""
    def __init__(self, anchor_widget, text, hover_delay=1000):
        super().__init__(anchor_widget, text, hover_delay)
        self.widget = anchor_widget  # Ensure the widget attribute is set
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.showtip(event)

    def on_leave(self, event):
        self.hidetip()

    def showtip(self, event):
        if self.tipwindow or not self.text:
            return
        x = event.x_root
        y = event.y_root + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font = ('Helvetica',FONT_SIZE))
        label.pack(ipadx=1)
        tw.update_idletasks()  # Ensure the tooltip is drawn so we can get its width
        tooltip_width = tw.winfo_width()
        x = x - tooltip_width - 10  # Adjust the -10 to add some padding
        tw.wm_geometry("+%d+%d" % (x, y))
#-------------------------------------#

class photoelectronSpectrum:
    """Includes all info about spectrum
    e.g. file path, file name, data, fit result and so on
    this makes it easier to access instead of assigning these to frames"""
    def __init__(self,master):
        # when initiating program
        #Root window (to access variables)
        self.master = master

        # Data
        self.spectrum = None
        # Plot
        self.filePath = ''
        #Guesses
        self.gaussTypeSelection = ("S","B")
        self.gaussTypes = [tk.StringVar(value = self.gaussTypeSelection[0]) for _ in range(3)]
        self.guessAmps = None
        self.guessCentres = None
        self.guessFWHMs = None
        #Photon options
        self.wavelength = tk.StringVar(self.master)
        self.wavelength.trace_add('write', self.updatePhotonEnergy)
        self.numberOfPhotons = tk.StringVar(self.master,value = '1')
        self.numberOfPhotons.trace_add('write', self.updatePhotonEnergy)
        self.photonEnergyStr = ""
        self.photonEnergyValue = ""
        # Binding energies
        #----string lists
        #Fit results
        self.fitResult = np.array(())
        #Retrieval
        self.xs                 = np.arange(0.01,5.01,0.01)
        self.num_surface        = 20
        self.num_bulk           = 0
        self.crossSectionSetInd = None
        self.thresholdInd       = None
        self.surfInd            = None
        self.min_eKE            = None

    def fitRaw(self):
        self.min_eKE = min(self.spectrum[0])

        self.p0,_ = self.getInitialGuess()

        self.itpData = FR.interpolateData(self.spectrum, min_eKE = self.min_eKE, xs = self.xs)
        self.fitResult,covar = FR.retrieveRawFit(self.itpData[0],self.itpData[1],self.p0)
        print(self.fitResult)
        self.x_above_cutoff = self.itpData[0]

        self.fitfunc = None #Remove scattering function from previous fit 

        self.drawFit(rawFit = True)

        self.updateFitResults()
        self.updateBindingEnergies()


    def retrieve(self):
        self.crossSectionSetInd = self.retrievalSettingsFrame.crossSectionSet_combobox.current()
        self.thresholdInd       = self.retrievalSettingsFrame.thresholdValue_combobox.current()
        self.surfInd            = self.retrievalSettingsFrame.surfValue_combobox.current()
        self.min_eKE            = min(self.spectrum[0])

        self.p0, self.gaussTypesResult = self.getInitialGuess()

        self.itpData = FR.interpolateData(self.spectrum, min_eKE = self.min_eKE, xs = self.xs)
        self.fitfunc = FR.setupFitFunc(self.gaussTypesResult, self.crossSectionSetInd, self.thresholdInd, self.surfInd, self.min_eKE)
        self.fitResult,covar = FR.retrieveFit(self.fitfunc,self.xs,self.itpData[1],self.p0,
                                              bounds = ((0,-np.inf,0)*len(self.p0[0::3]),
                                                        (np.inf,np.inf,np.inf)*len(self.p0[0::3])))
        print(self.fitResult)
        self.x_above_cutoff = self.itpData[0]

        self.drawFit()

        self.updateFitResults()
        self.updateBindingEnergies()

    def updateFitResults(self):
        #Update values of fit peaks
        for ind in range(0,len(self.fitResult[0::3])):
            self.ampStrings[ind].set(f"{self.fitResult[3*ind]:.2}")
            self.centreStrings[ind].set(f"{self.fitResult[3*ind+1]:.2f}")
            self.FWHMStrings[ind].set(f"{self.fitResult[3*ind+2]:.2f}")
        for ind,gaussType in enumerate(self.gaussTypesResult):
            self.gaussTypeStrings[ind].set(gaussType)
        #Delete old values if not overwritten
        for ind in range(len(self.fitResult[0::3]),3):
            self.ampStrings[ind].set("")
            self.centreStrings[ind].set("")
            self.FWHMStrings[ind].set("")
            self.gaussTypeStrings[ind].set("")


    def getInitialGuess(self):
        initialGuess = []
        gaussTypes = []
        for gaussType,amp,centre,FWHM in zip(self.gaussTypes,self.guessAmps,self.guessCentres,self.guessFWHMs):
            if all((gaussType.get(),amp.get(),centre.get(),FWHM.get())):
                gaussTypes.append(gaussType.get())
                initialGuess.append(float(amp.get()))
                initialGuess.append(float(centre.get()))
                initialGuess.append(float(FWHM.get()))
        print(initialGuess)
        return initialGuess, gaussTypes
    
    def drawFit(self, rawFit = False):
        """Plots image on the canvas """
        fig, ax = self.master.plotFrame.fig, self.master.plotFrame.ax

        canvas,fitLine, retrievedLine = self.master.plotFrame.canvas,self.master.plotFrame.fitLine,self.master.plotFrame.retrievedLine
        
        #Remove existing lines
        if fitLine:       
            fitLine.remove()
            self.master.plotFrame.fitLine = None # It seems like remove just detaches it from the axes (?)
        if retrievedLine:  retrievedLine.remove()
        if self.master.plotFrame.retrievedGaussians:
            for G in self.master.plotFrame.retrievedGaussians:
                G.remove()
        self.master.plotFrame.retrievedGaussians = []

        # Add new lines
        if not rawFit:
            self.master.plotFrame.fitLine, = ax.plot(self.x_above_cutoff, self.fitfunc.f(self.xs, *self.fitResult),lw=.5,c='k')
        self.master.plotFrame.retrievedLine, = ax.plot(self.x_above_cutoff, FR.multiple_gaussians(self.x_above_cutoff, *self.fitResult), 'k--',lw=.5)
        for i in range(0,len(self.fitResult),3):
            G, = ax.plot(self.x_above_cutoff,FR.multiple_gaussians(self.x_above_cutoff,*self.fitResult[i:i+3]),'r--',lw=0.5)
            self.master.plotFrame.retrievedGaussians.append(G)
        canvas.draw()

    def drawGuess(self):
        fig, ax = self.master.plotFrame.fig, self.master.plotFrame.ax
    
        if self.master.plotFrame.guessFitLine:
            self.master.plotFrame.guessFitLine.remove()
            self.master.plotFrame.guessFitLine = None
            self.master.plotFrame.guessRetrievedLine.remove()
            self.master.plotFrame.guessRetrievedLine = None

        else:
            self.crossSectionSetInd = self.retrievalSettingsFrame.crossSectionSet_combobox.current()
            self.thresholdInd       = self.retrievalSettingsFrame.thresholdValue_combobox.current()
            self.surfInd            = self.retrievalSettingsFrame.surfValue_combobox.current()
            self.min_eKE            = 0

            self.p0, gaussTypes = self.getInitialGuess()
            self.fitfunc = FR.setupFitFunc(gaussTypes, self.crossSectionSetInd, self.thresholdInd, self.surfInd, self.min_eKE)

            self.master.plotFrame.guessFitLine, = ax.plot(self.xs, self.fitfunc.f(self.xs, *self.p0),lw=.5,c='r')
            self.master.plotFrame.guessRetrievedLine, = ax.plot(self.xs, FR.multiple_gaussians(self.xs, *self.p0), 'r--',lw=.5)
            
        ax.relim()
        ax.autoscale(axis='y')
        self.master.plotFrame.canvas.draw()

    def drawGraph(self):
        if self.filePath:
            self.spectrum = np.genfromtxt(self.filePath,delimiter = '\t').T
            self.itpData = FR.interpolateData(self.spectrum, min_eKE = min(self.spectrum[0]), xs = self.xs)

            #Get axis
            ax = self.master.plotFrame.ax
            #Clear all lines
            for line in ax.lines:
                line.remove()

            ax.plot(self.itpData[0],self.itpData[1],lw=1,c='tab:blue')

            #Remove reference to lines
            self.master.plotFrame.fitLine = None
            self.master.plotFrame.retrievedLine = None
            self.master.plotFrame.guessFitLine = None
            self.master.plotFrame.guessRetrievedLine = None
            self.master.plotFrame.retrievedGaussians = None
            
            #Set xlims and draw
            self.master.plotFrame.ax.set_xlim(-.5,5)
            self.master.plotFrame.canvas.draw()

    def updatePhotonEnergy(self,*args):
        wavelengthValue = self.wavelength.get()
        numberOfPhotonsValue = int(self.numberOfPhotons.get())
        try:
            self.photonEnergyValue = numberOfPhotonsValue * 1239.8/float(wavelengthValue)
            photonEnergyStr = f"{self.photonEnergyValue:.2f}"
        except:
            photonEnergyStr = ""

        self.photonOptionsFrame.photonEnergyString_label.config(text = photonEnergyStr)
        self.updateBindingEnergies()

    def updateBindingEnergies(self):
        if self.photonEnergyValue and any(self.fitResult):
            #Update values of fit peaks
            for ind in range(0,len(self.fitResult[0::3])):
                self.eBEStrings[ind].set(f"{self.photonEnergyValue - self.fitResult[3*ind+1]:.2f}")
            #Delete old values if not overwritten
            for ind in range(len(self.fitResult[0::3]),3):
                self.eBEStrings[ind].set("")


class scatterGUI(tk.Frame):
    def __init__(self,master):
        super().__init__(master)
        self.root = self.winfo_toplevel()

        #Initialise UVspectrum
        self.UVspectrum = photoelectronSpectrum(self)

        #'i' image
        self.infoIcon_image = tk.PhotoImage(file=r"Icons\info_20dp_5F6368_FILL0_wght400_GRAD0_opsz20.png")
        self.infoIcon_image=self.infoIcon_image.subsample(INFO_ICON_SUBSAMPLE)
        #Font settings
        widgetFont = tk.font.Font(family="Helvetica",size=FONT_SIZE)
        self.option_add("*Font", widgetFont)

        #Configure grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)

        self.rowconfigure(0, weight=3)
        self.rowconfigure(1, weight=6)

        #Create and place frames
        # self.titleFrame = titleFrame(self)
        self.fileInfoFrame = fileInfoFrame(self)
        self.plotFrame = plotFrame(self)
        self.rightFrame = rightFrame(self)

        # self.titleFrame.grid(row=0,column=0,columnspan=3,padx=10,pady=10,sticky='nswe')
        self.fileInfoFrame.grid(row=0,column=1,padx=MAIN_FRAME_PADDING,pady=10,sticky='nswe')
        self.plotFrame.grid(row=1,column=1,padx=MAIN_FRAME_PADDING,pady=10,sticky='nswe')
        self.rightFrame.grid(row=0,column=2,rowspan=2,padx=(MAIN_FRAME_PADDING,0),pady=0,sticky='nswe')

        #Add reference to self.settingsFrame to UVspectrum
        self.UVspectrum.settingsFrame = self.settingsFrame

    def open_file(self):
        """Command for dropdown menu, which provides path of data to display."""
        ftypes = [('text files','*.txt'),('comma delimited files','*.csv'),('all files','*.*')]
        dlg = tk.filedialog.Open(self,filetypes=ftypes)
        filePath = dlg.show()
        self.UVspectrum.filePath = filePath
        fileName = filePath.split("/")[-1]
        self.UVspectrum.fileName = fileName
        self.fileInfoFrame.fileNameLabel.config(text=fileName)
        self.UVspectrum.drawGraph()

class rightFrame(tk.Frame):
    """This only contains settings frame but helps with padding"""
    def __init__(self,master):
        super().__init__(master,highlightbackground="red", highlightthickness=0,bg=ACCENT_COLOR)
        self.master = master

        self.settingsFrame = settingsFrame(self,master)
        self.settingsFrame.grid(row=0,column=0,padx=RIGHT_FRAME_PADDING_X,pady=RIGHT_FRAME_PADDING_Y)

        # Make attributes of master for easier access
        self.master.settingsFrame = self.settingsFrame


class settingsFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,bg=ACCENT_COLOR,highlightbackground="red", highlightthickness=0)
        self.master = master
        self.parent = parent
        
        #Create (sub)frames
        self.retrievalSettingsFrame = retrievalSettingsFrame(self,master)
        self.fitGuessesFrame = fitGuessesFrame(self,master)
        self.photonOptionsFrame = photonOptionsFrame(self,master)
        self.fitResultsFrame = fitResultsFrame(self,master)
        self.retrieveFrame = retrieveFrame(self,master)


        # Place frames
        self.retrievalSettingsFrame.grid(row=0,column=0,padx=SETTING_FRAMES_PADDING_X,pady=SETTING_FRAMES_PADDING_Y)
        self.fitGuessesFrame.grid(row=1,column=0,padx=SETTING_FRAMES_PADDING_X,pady=SETTING_FRAMES_PADDING_Y)
        self.photonOptionsFrame.grid(row=2,column=0,padx=SETTING_FRAMES_PADDING_X,pady=SETTING_FRAMES_PADDING_Y)
        self.fitResultsFrame.grid(row=3,column=0,padx=SETTING_FRAMES_PADDING_X,pady=SETTING_FRAMES_PADDING_Y)
        self.retrieveFrame.grid(row=4,column=0,padx=SETTING_FRAMES_PADDING_X,pady=SETTING_FRAMES_PADDING_Y)

        #Add reference to (sub)frames to UVspectrum
        self.master.UVspectrum.retrievalSettingsFrame =  self.retrievalSettingsFrame 
        self.master.UVspectrum.fitGuessesFrame =         self.fitGuessesFrame 
        self.master.UVspectrum.photonOptionsFrame =      self.photonOptionsFrame 
        self.master.UVspectrum.fitResultsFrame =         self.fitResultsFrame 
        self.master.UVspectrum.retrieveFrame =           self.retrieveFrame

class retrieveFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,bg=ACCENT_COLOR,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent
        self.UVspectrum = master.UVspectrum

        #Retrieve button
        retrieve_button=tk.Button(self, text="Retrieve",height=2,width=20,
                                  font=MAIN_BUTTON_FONT, bg = MAIN_BUTTON_COLOR,
                                   command=self.UVspectrum.retrieve)
        retrieve_button.grid(row=0,column=0,sticky='nesw',padx=10,pady=10)

        #Plot guess button
        retrieve_button=tk.Button(self, text="Plot guess",height=2,width=20,
                                  font=MAIN_BUTTON_FONT,bg = MAIN_BUTTON_COLOR,
                                  command=self.UVspectrum.drawGuess)
        retrieve_button.grid(row=0,column=1,sticky='nesw',padx=10,pady=10)

        #Fit raw button
        retrieve_button=tk.Button(self, text="Raw fit",height=2,width=20,
                                  font=MAIN_BUTTON_FONT,bg = MAIN_BUTTON_COLOR,
                                  command=self.UVspectrum.fitRaw)
        retrieve_button.grid(row=1,column=0,sticky='nesw',padx=10,pady=10)

class fitResultsFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,bg=ACCENT_COLOR,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent
        self.UVspectrum = master.UVspectrum 

        #Fit results title
        self.fitResultsTitle_label=tk.Label(self, text='Fit results',font=('Helvetica', TITLE_FONT_SIZE,'bold'),bg=self['bg'])
        self.fitResultsTitle_label.grid(row=0,column=0,columnspan=5,padx=10,pady=10, sticky = 'nswe')

        #Fit results display
        gaussTypeTitle_label = tk.Label(self,text = 'Type',bg=self['bg'])
        gaussTypeTitle_label.grid(row=1,column=0,padx=5,pady=2)
        amplitudesTitle_label = tk.Label(self,text = 'Amplitude',bg=self['bg'])
        amplitudesTitle_label.grid(row=1,column=1,padx=5,pady=2)
        centresTitle_label = tk.Label(self,text = 'Centre / eV',bg=self['bg'])
        centresTitle_label.grid(row=1,column=2,padx=5,pady=0)
        FWHMsTitle_label = tk.Label(self,text = 'FWHM / eV',bg=self['bg'])
        FWHMsTitle_label.grid(row=1,column=3,padx=5,pady=0)
        eBEsTitle_label = tk.Label(self,text = 'eBE / eV',bg=self['bg'])
        eBEsTitle_label.grid(row=1,column=4,padx=5,pady=0)

        self.UVspectrum.gaussTypeStrings = []
        gaussTypeLabels = []
        self.UVspectrum.ampStrings = []
        ampLabels = []
        self.UVspectrum.centreStrings = []
        centreLabels = []
        self.UVspectrum.FWHMStrings = []
        FWHMLabels = []
        self.UVspectrum.eBEStrings = []
        eBELabels = []
        for ind in range(3):
            gaussType = tk.StringVar()
            self.UVspectrum.gaussTypeStrings.append(gaussType)
            gaussType_label=tk.Label(self, textvariable=gaussType,width=4,justify=tk.RIGHT,bg=self['bg'])
            gaussType_label.grid(row=2+ind, column=0,pady=5,padx=5)
            gaussTypeLabels.append(gaussType_label)

            amp = tk.StringVar()
            self.UVspectrum.ampStrings.append(amp)
            amp_label=tk.Label(self, textvariable=amp,width=10,justify=tk.RIGHT,bg=self['bg'])
            amp_label.grid(row=2+ind, column=1,pady=5,padx=5)
            ampLabels.append(amp_label)

            centre = tk.StringVar()
            self.UVspectrum.centreStrings.append(centre)
            centre_label=tk.Label(self, textvariable=centre,width=10,justify=tk.RIGHT,bg=self['bg'])
            centre_label.grid(row=2+ind, column=2,pady=5,padx=5)
            centreLabels.append(centre_label)

            FWHM = tk.StringVar()
            self.UVspectrum.FWHMStrings.append(FWHM)
            FWHM_label=tk.Label(self, textvariable=FWHM,width=10,justify=tk.RIGHT,bg=self['bg'])
            FWHM_label.grid(row=2+ind, column=3,pady=5,padx=5)
            FWHMLabels.append(FWHM_label)
            
            eBE = tk.StringVar()
            self.UVspectrum.eBEStrings.append(eBE)
            eBE_label=tk.Label(self, textvariable=eBE,width=10,justify=tk.RIGHT,bg=self['bg'])
            eBE_label.grid(row=2+ind, column=4,pady=5,padx=5)
            eBELabels.append(eBE_label)

class photonOptionsFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,bg=ACCENT_COLOR,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent 
        self.UVspectrum = master.UVspectrum 

        #Photon options title
        self.photonOptionsTitle_label=tk.Label(self, text='Photon options',font=('Helvetica', TITLE_FONT_SIZE,'bold'),bg=self['bg'])
        self.photonOptionsTitle_label.grid(row=0,column=0,columnspan=3,padx=10,pady=10, sticky = 'nswe')

        #Wavelength selection
        self.wavelengthTitle_label = tk.Label(self,text = 'Wavelength / nm',bg=self['bg'])
        self.wavelengthTitle_label.grid(row=1,column=0,padx=5,pady=5)
        self.wavelength_entry = tk.Entry(self,width=10,textvariable = self.UVspectrum.wavelength)
        self.wavelength_entry.grid(row=1,column=1,pady=5,padx=5,sticky='nsw')

        #Number of photon selection
        self.numberOfPhotonsTitle_label = tk.Label(self,text = 'n',bg=self['bg'])
        self.numberOfPhotonsTitle_label.grid(row=2,column=0,padx=5,pady=5)

        def validate_integer(value_if_allowed, action):
            """Checks if input in spinbox is a positive integer.
            From copilot"""
            if action != '1':  # If the action is not insertion, allow it
                return True
            try:
                value = int(value_if_allowed)
                if 0 < value: 
                    return True
                else:
                    return False
            except ValueError:
                return False
        self.numberOfPhotonsValidateCommand = (self.register(validate_integer), '%P', '%d')

        self.numberOfPhotons_entry=ttk.Spinbox(self, from_=1,to=5,increment = 1,width = 10,textvariable=self.UVspectrum.numberOfPhotons,
                                               validate='key', validatecommand=self.numberOfPhotonsValidateCommand)
        self.numberOfPhotons_entry.grid(row=2,column=1,pady=5,padx=5,sticky='nsw')

        #Photon energy display
    
        self.photonEnergyTitle_label=tk.Label(self,text="Photon energy / eV",bg=self['bg'])
        self.photonEnergyTitle_label.grid(row=3,column=0,pady=5,padx=5)
        self.photonEnergyString_label=tk.Label(self,width=10,text=self.UVspectrum.photonEnergyStr,bg=self['bg'])
        self.photonEnergyString_label.grid(row=3,column=1,pady=5,padx=5,sticky='nsw')

class fitGuessesFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,bg=ACCENT_COLOR,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent
        self.UVspectrum = master.UVspectrum

        #Fit parameters title
        fitParametersTitle_label=tk.Label(self, text='Fit parameters',font=('Helvetica', TITLE_FONT_SIZE,'bold'),bg=self['bg'])
        fitParametersTitle_label.grid(row=0,column=0,columnspan=4,padx=10,pady=10, sticky = 'nswe')

        #Surface/bulk selection
        gaussTypeTitle_label = tk.Label(self,text = 'Type',bg=self['bg'])
        gaussTypeTitle_label.grid(row=1,column=0,padx=10,pady=2)
        for i,gaussType in enumerate(self.UVspectrum.gaussTypes):
            surfValue_combobox = ttk.Combobox(self,textvariable=gaussType, values=self.UVspectrum.gaussTypeSelection,
                                              state='readonly',width=4)
            surfValue_combobox.grid(row=2+i,column=0,padx=2,pady=5)


        #Amplitudes
        amplitudesTitle_label = tk.Label(self,text = 'Amplitude',bg=self['bg'])
        amplitudesTitle_label.grid(row=1,column=1,padx=10,pady=2)
        amp1=tk.StringVar(value = 1)
        amp2=tk.StringVar()
        amp3=tk.StringVar()
        self.UVspectrum.guessAmps = (amp1,amp2,amp3)
        amp1_entry=tk.Entry(self, textvariable=amp1,width=14,justify=tk.RIGHT)
        amp2_entry=tk.Entry(self, textvariable=amp2,width=14,justify=tk.RIGHT)
        amp3_entry=tk.Entry(self, textvariable=amp3,width=14,justify=tk.RIGHT)
        amp1_entry.grid(row=2, column=1,pady=5,padx=5)
        amp2_entry.grid(row=3, column=1,pady=5,padx=5)
        amp3_entry.grid(row=4, column=1,pady=5,padx=5)
        
        #Centres
        centresTitle_label = tk.Label(self,text = 'Centre / eV',bg=self['bg'])
        centresTitle_label.grid(row=1,column=2,padx=10,pady=0)
        centre1=tk.StringVar(value = 1)
        centre2=tk.StringVar()
        centre3=tk.StringVar()
        self.UVspectrum.guessCentres  = (centre1,centre2,centre3)
        centre1_entry=tk.Entry(self, textvariable=centre1,width=14,justify=tk.RIGHT)
        centre2_entry=tk.Entry(self, textvariable=centre2,width=14,justify=tk.RIGHT)
        centre3_entry=tk.Entry(self, textvariable=centre3,width=14,justify=tk.RIGHT)
        centre1_entry.grid(row=2, column=2,pady=5,padx=5)
        centre2_entry.grid(row=3, column=2,pady=5,padx=5)
        centre3_entry.grid(row=4, column=2,pady=5,padx=5)

        FWHMsTitle_label = tk.Label(self,text = 'FWHM / eV',bg=self['bg'])
        FWHMsTitle_label.grid(row=1,column=3,padx=10,pady=0)
        FWHM1=tk.StringVar(value = 1)
        FWHM2=tk.StringVar()
        FWHM3=tk.StringVar()
        self.UVspectrum.guessFWHMs = (FWHM1,FWHM2,FWHM3)
        FWHM1_entry=tk.Entry(self, textvariable=FWHM1,width=14,justify=tk.RIGHT)
        FWHM2_entry=tk.Entry(self, textvariable=FWHM2,width=14,justify=tk.RIGHT)
        FWHM3_entry=tk.Entry(self, textvariable=FWHM3,width=14,justify=tk.RIGHT)
        FWHM1_entry.grid(row=2, column=3,pady=5,padx=5)
        FWHM2_entry.grid(row=3, column=3,pady=5,padx=5)
        FWHM3_entry.grid(row=4, column=3,pady=5,padx=5)

class retrievalSettingsFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,bg=ACCENT_COLOR,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent   

        #Fit settings title
        self.fitSettingsTitle_label=tk.Label(self, text='Retrieval settings',font=('Helvetica',TITLE_FONT_SIZE,'bold'),bg=self['bg'])
        self.fitSettingsTitle_label.grid(row=0,column=0,columnspan=3,padx=10,pady=10,sticky='nswe')

        #Surface gaussian amplitude
        self.surfValueTitle_label=tk.Label(self,text='Surface gaussian amplitude',anchor='e',bg=self['bg'])
        self.surfValueTitle_label.grid(row=1,column=0,padx=10,pady=2,sticky = 'e')
        self.surfValue = tk.StringVar(value = BS.concAmps[0])
        self.surfValue_combobox = ttk.Combobox(self,textvariable=self.surfValue,values=BS.concAmps,state='readonly')
        self.surfValue_combobox.grid(row=1,column=1,pady=2)
        self.infoIconSurfValue_label = tk.Label(self, image=master.infoIcon_image,bg=self['bg'])
        self.infoIconSurfValue_label.grid(row=1,column=2,padx=10,sticky='w')
        self.infoIconsurfValue_hover = CustomHovertip(self.infoIconSurfValue_label,'Concentration profiles are described as "A * g(x) + 1",\nwhere g(x) is a Gaussian and A is the height of the Gaussian')

        #Escape threshold value
        self.thresholdValueTitle_label=tk.Label(self,text='Escape threshold / eV',anchor='e',bg=self['bg'])
        self.thresholdValueTitle_label.grid(row=2,column=0,padx=10,pady=2,sticky = 'e')
        self.thresholdValue=tk.StringVar(value = BS.E0s[0])
        self.thresholdValue_combobox = ttk.Combobox(self,textvariable=self.thresholdValue,values=BS.E0s,state='readonly')
        self.thresholdValue_combobox.grid(row=2, column=1,pady=2)
        self.infoIconthresholdValue_label = tk.Label(self, image=master.infoIcon_image,bg=self['bg'])
        self.infoIconthresholdValue_label.grid(row=2,column=2,padx=10,sticky='w')
        self.infoIconthresholdValue_hover = CustomHovertip(self.infoIconthresholdValue_label,'Barrier electrons need to overcome to escape jet.\nAlso referred to as electron affinity of water at the surface')

        #Cross section set selection
        self.crossSectionSetTitle_label=tk.Label(self,text='Cross section set',anchor='e',bg=self['bg'])
        self.crossSectionSetTitle_label.grid(row=3,column=0,padx=10,pady=2,sticky = 'e')
        self.crossSectionSet = tk.StringVar(value = BS.crossSectionSets[0])
        self.crossSectionSet_combobox = ttk.Combobox(self,textvariable=self.crossSectionSet,values=BS.crossSectionSets,state='readonly')
        self.crossSectionSet_combobox.grid(row=3,column=1,pady=2)
        self.infoIconCrossSectionSet_label = tk.Label(self, image=master.infoIcon_image,bg=self['bg'])
        self.infoIconCrossSectionSet_label.grid(row=3,column=2,padx=10,sticky='w')
        self.infoIconCrossSectionSet_hover = CustomHovertip(self.infoIconCrossSectionSet_label,'Will come up with better naming system')


class plotFrame(tk.Frame):
    def __init__(self,master):
        super().__init__(master,highlightbackground="red", highlightthickness=0)
        self.master = master
        # Update rcParams
        mpl.rcParams.update(rcParams)
        ### Initialise fig
        self.fig = plt.figure(figsize=(4, 3.2), dpi=200)
        self.canvas=FigureCanvasTkAgg(self.fig, master=self)  
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0)
        self.fig.subplots_adjust(left=0.17, right=0.965, top=0.97, bottom=0.16, wspace=0, hspace=0)
        self.fig.patch.set_color(WINDOW_COLOR)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Electron kinetic energy / eV")
        self.ax.set_ylabel("Photoelectron signal / a.u.")
        #Minor ticks
        self.ax.xaxis.set_minor_locator(AutoMinorLocator('auto'))
        self.ax.yaxis.set_minor_locator(AutoMinorLocator('auto'))

        # self.ax = None
        self.fitLine = None
        self.retrievedLine = None
        self.guessFitLine = None
        self.guessRetrievedLine = None
        self.retrievedGaussians = None
        
        ### Initialise toolbar
        self.toolbarFrame=tk.Frame(master=self)
        self.toolbarFrame.grid(row=1,column=0,)
        NavigationToolbar2Tk(self.canvas, self.toolbarFrame)

class titleFrame(tk.Frame):
    def __init__(self,master):
        super().__init__(master,highlightbackground="red", highlightthickness=0)
        label = tk.Label(self, font=('Helvetica', TITLE_FONT_SIZE),height = 2,text="Retrieval of ultraviolet photoelectron spectra")
        label.pack(pady=10)

class fileInfoFrame(tk.Frame):
    def __init__(self,master):
        super().__init__(master,bg=ACCENT_COLOR,highlightbackground="red", highlightthickness=0)
    
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.columnconfigure(2, weight=3)

        fileNameButton = tk.Button(self,text="Load file", command=master.open_file, width=10)
        fileNameButton.grid(row=0,column=0,padx=20,pady=10,sticky='e')
        self.fileNameLabel = tk.Label(self,text="", width=20,bg=self['bg'])
        self.fileNameLabel.grid(row=0,column=1,padx=10,pady=10,sticky='w')


if __name__ =="__main__":

    app = tk.Tk()
    scatterFrame = scatterGUI(app)
    scatterFrame.pack()

    rcParams = ['figure.dpi','font.family','font.size','legend.fontsize','axes.labelsize',
                'legend.handletextpad','legend.labelspacing','lines.linewidth','lines.markersize']
    for rcParam in rcParams:
        print(rcParam, mpl.rcParams[rcParam])
    app.geometry("+60+60")
    app.wm_title("Scatter")
    app.mainloop()



