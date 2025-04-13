import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.widgets import SpanSelector
import matplotlib.figure as mplfigure
import matplotlib as mpl
import numpy as np
from scipy.optimize import curve_fit
import yaml
from ctypes import windll

import time

if __name__=="__main__":
    # Direct import
    from SPfunctions import *
    from load_settings import *
else:
    #Relative import
    from .SPfunctions import * 
    from .load_settings import *


#fix blurry text
windll.shcore.SetProcessDpiAwareness(1)

### Format constants ###
FONT_SIZE = 9
TITLE_FONT_SIZE = 20
SUBTITLE_FONT_SIZE = 16
LARGE_FONT_SIZE = 14
MAIN_FRAME_PADDING = 20
LEFT_FRAME_PADDING = 7.5
RF_PADY = 7.5
RF_PADX = 7.5
SETTINGS_FRAME_PADDING = 5

WINDOW_COLOR = "#F0F0F0"
ACCENT_COLOR = '#D9D9D9'
MAIN_BUTTON_FONT = ('Helvetica', 9, 'bold')
MAIN_BUTTON_COLOR = "#dddddd"#"#ced1d7"
ICON_SUBSAMPLE = 2

#extra
ALPHABET = list("abcdefghijklmnopqrstuvwxyz")
alphabet_mesh = np.meshgrid(ALPHABET,ALPHABET)[0]
ALL_FINDICES = np.char.add(alphabet_mesh.T, alphabet_mesh).flatten()

MAX_NUM_DATA = 10 # Maximum possible number of spectra to upload (10 is reccomended)
# if MAX_NUM_DATA>10 errors will arise in summaryFrame as only 10 plots are displayed --> maybe find fix later
if not isinstance(MAX_NUM_DATA, int) or MAX_NUM_DATA < 1 or MAX_NUM_DATA > 10:
    raise ValueError("The value of MAX_NUM_DATA must be of type int and between 1 and 10.")

#Plot constants
FIG_WID = 2.5
XS_EKE = np.arange(0,5,0.002)
XS_POS = np.arange(0,2.0,.01)

#UNICODE
phistr = u'\u03D5' 
tickstr = u'\u2713'
zerosubstr = u'\u2080'

# COLORS
BLACK = "#565656"

#### MPL rcParams ######
rcParams = {'figure.dpi':200,
            'font.family':'Arial',
            'font.size':5.0,
            'legend.fontsize': 6, 
            'axes.labelsize':'medium', #equal to font.size
            'legend.handletextpad': 0.3,
            'legend.labelspacing': 0.3,
            'lines.linewidth': 1,
            'lines.markersize': 3
            }

###
#This will color the border red
#Use to check frame shape
# highlightbackground="red", highlightthickness=0



class streamingPotential:
    """All about streaming potential stuff"""
    def __init__(self,master):
        self.master = master

        self.fit_params = np.array(())

        #Parameters
        self.cal_params_strings = [tk.StringVar(self.master,value=_) for _ in DEFAULT_CAL_PARAMS]
        self.wavelength_string = tk.StringVar(self.master,value=DEFAULT_WAVELENGTH)
        if DEFAULT_FOLDER:
            self.folder_path = DEFAULT_FOLDER

        #Data
        self.date = tk.StringVar(self.master,value=DEFAULT_DATE)
        
        self.file_indices = [tk.StringVar(self.master) for _ in range(MAX_NUM_DATA)]
        # Create a list of strings with len MAX_NUM_DATA. If len(DEFAULT_POSITIONS) is grater than MAX_NUM_DATA
        # it will be cutoff, otherwise empty strings will be appended
        position_strings = DEFAULT_POSITIONS[:MAX_NUM_DATA] + ["" for _ in range(MAX_NUM_DATA-len(DEFAULT_POSITIONS[:MAX_NUM_DATA]))]
        self.positions_strings = [tk.StringVar(self.master,value=value) for value in position_strings]

        self.loaded_confirm_labels = []
        self.spectra = np.empty((MAX_NUM_DATA),dtype=np.ndarray)

    @property
    def cal_params(self):
        try:
            return [float(p.get()) for p in self.cal_params_strings]
        except ValueError:
            # display message
            return None

    @property
    def wavelength(self):
        try:
            return float(self.wavelength_string.get())
        except ValueError:
            # display message
            return None

    #Data functions
    def autofill_indices(self):
        start_index = self.file_indices[0].get()
        try:
            start = np.where(ALL_FINDICES==start_index)[0][0] # output is tuple of array. I want integer
        except IndexError:
            return
        for i in range(1,MAX_NUM_DATA):
            #Check if there are positions
            try:
                float(self.positions_strings[i].get())
                self.file_indices[i].set(ALL_FINDICES[start+i])
            except ValueError:
                break

    def load_all_files(self):
        for ind in range(len(self.file_indices)):
            self.load_file(ind)

    def load_file(self,ind):
        #Get date from entry
        date = self.date.get()
        #Get file index
        findex = self.file_indices[ind].get()
        try:
            data = np.genfromtxt(self.folder_path+"\\"+date+findex+f"\\{date}{findex}_SignalBack.txt").T
        except FileNotFoundError:
            return
        try:
            pos = self.positions_strings[ind].get()
            pos = float(pos)
        except ValueError:
            return
        #Convert to eKE and apply Jacobian
        data = tof2eKE(data,self.cal_params)
        #Normalise to height between 2.5 and 5 eV
        data[1]/=max(data[1][np.logical_and(data[0]>2.5,data[0]<5)])
        #Store spectrum
        self.spectra[ind] = SPspectrum(data,pos,self.folder_path,date,findex)
        #Plot spectrum
        self.master.summaryFrame.plot_summary_spectrum(ind)
        #If active in summary plot, redraw
        if ind == self.master.rightFrame.fittingFrame.display_ind:
            self.master.rightFrame.fittingFrame.plot_fit_spectrum(ind)
        #Replot results plot if changed
        if ind in self.master.rightFrame.resultsFrame.plotted_indices:
            self.master.rightFrame.resultsFrame.plot_positions()
        #Update tick in GUI
        self.loaded_confirm_labels[ind].config(text=tickstr)

    # Save result
    def save_result(self):
        ## find better way!! maybe yaml??
        """Saves a tab-delimited txt file with results and enough
        informatin to reproduce the results
        - SP
        - V0
        - dates
        - folders
        - filenames,
        - positions, 
        - eKEs
        - calibration parameters
        - wavelength
        - ...
        """
        # Get positions and kinetic_energies and file name details.
        # These should already be attributes of streamingPotential
        # You must change resultsFrame.plot_positions()
        positions = []
        kinetic_energies = []
        dates = []
        folders = []
        findices = []
        for i,spectrum in enumerate(self.spectra):
            if isinstance(spectrum,SPspectrum) and len(spectrum.fit_params)>0:
                positions.append(spectrum.position)
                kinetic_energies.append(float(spectrum.fit_params[1]))
                dates.append(spectrum.date)
                folders.append(spectrum.folder)
                findices.append(spectrum.findex)

        # if dates and folders are all the same just save the string
        if len(set(dates)) == 1:
            dates=dates[0]
        if len(set(folders)) == 1:
            folders=folders[0]

        resultsDic = {
            'Streaming potential': float(self.fit_params[0]),
            'Vacuum level offset': float(self.fit_params[1]),
            'Dates': dates,
            'Folders': folders,
            'Filenames': findices,
            'Positions': positions,
            'eKEs': kinetic_energies,
            'Calibration parameters':self.cal_params, #be careful as it gets them from entry
            'Wavelength': self.wavelength, # same
        }

        print(resultsDic)

        filename = tk.filedialog.asksaveasfile(mode='w',
                                                initialfile = 'SP_result.yaml',
                                                defaultextension=".yaml",
                                                filetypes=[("YAML source file","*.yaml"),("All Files","*.*")])
        print(filename.name)
        with open(filename.name, 'w') as file:
            yaml.dump(resultsDic,file,sort_keys=False)

class SPspectrum:
    def __init__(self,data,position,folder,date,findex):
        self.data = data #Signal vs eKE
        # self.TOFdata = TOFdata #Signal vs TOF
        self.fit_params = np.array([]) #fit params
        self.position = position #distance from jet
        self.folder = folder # of file
        self.date = date # of file
        self.findex = findex # index of file e.g. "aa"

        self.fit_limits= [0,5]

    def fit_spectrum(self):

        fittableData = self.data[:,np.logical_and(self.data[0]>=self.fit_limits[0],self.data[0]<=self.fit_limits[1])]
        self.fit_params, _ = curve_fit(multiple_gaussians,*fittableData, p0 = [1,self.fit_limits[0]+.02,1])
        print(self.fit_params)


class streamingGUI(tk.Frame):
    def __init__(self,master):
        super().__init__(master)

        #Initialise streaming potential
        self.streamingPotential = streamingPotential(self)

        #Font settings
        widgetFont = tk.font.Font(family="Helvetica",size=FONT_SIZE)
        self.option_add("*Font", widgetFont)
        # Symbols/icons
        self.saveIcon_image = tk.PhotoImage(file=r"icons\save_20dp_000000_FILL0_wght400_GRAD0_opsz20.png")
        self.saveIcon_image=self.saveIcon_image.subsample(ICON_SUBSAMPLE)

        #Configure grid
        # self.columnconfigure(0, weight=1)
        # self.rowconfigure(0, weight=3)

        #Create and place frames
        self.leftFrame = leftFrame(self)
        self.rightFrame = rightFrame(self)
        self.leftFrame.grid(row=0,column=0,padx=(0,MAIN_FRAME_PADDING),pady=0,sticky='nswe')
        self.rightFrame.grid(row=0,column=2,padx=MAIN_FRAME_PADDING,pady=0,sticky='nswe')


    def open_file(self):
        """Opens file dialog to select folder with data."""
        self.streamingPotential.folder_path = tk.filedialog.askdirectory()
        self.master.dataFrame.folder_label.config(text = self.streamingPotential.folder_path)






class leftFrame(tk.Frame):
    """This only contains settings frame but helps with padding"""
    def __init__(self,master):
        super().__init__(master,highlightbackground="red", highlightthickness=0,bg=ACCENT_COLOR)
        self.master = master

        #Create (sub)frames
        # self.titleFrame = titleFrame(self,master)
        # self.titleFrame.grid(row=0,column=0,columnspan=2,pady=LEFT_FRAME_PADDING)

        self.settingsFrame = settingsFrame(self,master)
        self.settingsFrame.grid(row=0,column=0,padx=MAIN_FRAME_PADDING,pady=LEFT_FRAME_PADDING)

        # Make attributes of master for easier access
        self.master.settingsFrame = self.settingsFrame


class rightFrame(tk.Frame):
    def __init__(self,master):
        super().__init__(master,highlightbackground="red", highlightthickness=0)
        self.master = master

        #Configure grid
        # self.rowconfigure(0, weight=3)
        # self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        #Create (sub)frames
        self.fittingFrame = fittingFrame(self,master)
        self.summaryFrame = summaryFrame(self,master)
        self.resultsFrame = resultsFrame(self,master)
        self.resultPanelFrame = resultPanelFrame(self,master)

        self.fittingFrame.grid(row=0,column=0,pady=RF_PADY,padx=RF_PADX,sticky='se')
        self.summaryFrame.grid(row=1,column=0,pady=RF_PADY,padx=RF_PADX,sticky='ne')
        self.resultsFrame.grid(row=0,column=1,pady=RF_PADY,padx=RF_PADX,sticky='sw')
        self.resultPanelFrame.grid(row=1,column=1,pady=RF_PADY,padx=RF_PADX,sticky='nsew') #only this is nsew because i want it to expand

        #make attributes of master for easier access
        self.master.fittingFrame = self.fittingFrame
        self.master.summaryFrame = self.summaryFrame
        self.master.resultsFrame = self.resultsFrame
        self.master.resultPanelFrame = self.resultPanelFrame

class titleFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent

        label = tk.Label(self, font=('Helvetica', TITLE_FONT_SIZE),height = 2,text="Streaming potential")
        label.pack(pady=10)

class settingsFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,highlightbackground="red", highlightthickness=0,bg = ACCENT_COLOR)
        self.master = master 
        self.parent = parent

        #Configure grid
        # self.rowconfigure(0, weight=1)
        # self.rowconfigure(1, weight=4)

        #Create (sub)frames
        self.parametersFrame = parametersFrame(self,master)
        self.dataFrame = dataFrame(self,master)

        self.parametersFrame.grid(row=1,column=0,pady=SETTINGS_FRAME_PADDING)
        self.dataFrame.grid(row=0,column=0,pady=SETTINGS_FRAME_PADDING)

        # Make attributes of master for easier access
        self.master.parametersFrame = self.parametersFrame
        self.master.dataFrame = self.dataFrame

class parametersFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,highlightbackground="red", highlightthickness=0,bg = ACCENT_COLOR)
        self.master = master 
        self.parent = parent

        tk.Label(self,text='Parameters',font=('Helvetica', TITLE_FONT_SIZE,'bold'),bg=self['bg']).grid(row=0,column=0,columnspan=2,padx=10,pady=10, sticky = 'nswe')
        tk.Label(self,text="s / m",bg=self['bg']).grid(row=1,column=0,padx=5,pady=5,sticky='nse')
        tk.Label(self,text=f"t0 / ns",bg=self['bg']).grid(row=2,column=0,padx=5,pady=5,sticky='nse')
        tk.Label(self,text=f"E0 / eV",bg=self['bg']).grid(row=3,column=0,padx=5,pady=5,sticky='nse')
        tk.Label(self,text="Wavelength / nm",bg=self['bg']).grid(row=4,column=0,padx=5,pady=5,sticky='nse')

        tk.Entry(self,width=10,textvariable = self.master.streamingPotential.cal_params_strings[0]).grid(row=1,column=1,pady=5,padx=5,sticky='nsw')
        tk.Entry(self,width=10,textvariable = self.master.streamingPotential.cal_params_strings[1]).grid(row=2,column=1,pady=5,padx=5,sticky='nsw')
        tk.Entry(self,width=10,textvariable = self.master.streamingPotential.cal_params_strings[2]).grid(row=3,column=1,pady=5,padx=5,sticky='nsw')
        self.master.wavelength = tk.StringVar(self.master)
        tk.Entry(self,width=10,textvariable = self.master.streamingPotential.wavelength_string).grid(row=4,column=1,pady=5,padx=5,sticky='nsw')

class dataFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,bg=ACCENT_COLOR, highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent

        tk.Label(self, text='Data',font=('Helvetica', TITLE_FONT_SIZE,'bold'),bg=self['bg']).grid(row=0,column=0,columnspan=4,padx=10,pady=10, sticky = 'nswe')

        tk.Button(self,text="Folder",command = self.master.open_file,width=8).grid(row=1,column=0,columnspan=2,padx=5,pady=5,sticky='nse')
        self.folder_label = tk.Label(self,text="",width=25,anchor="e", justify=tk.RIGHT,bg=self['bg'])
        self.folder_label.grid(row=1,column=2,columnspan=4,padx=5,pady=5,sticky='nsw')
        if self.master.streamingPotential.folder_path:
            self.folder_label.config(text = self.master.streamingPotential.folder_path)

        tk.Label(self,text="Date ",bg=self['bg']).grid(row=2,column=0,columnspan=2,padx=5,pady=5,sticky='nse')
        tk.Entry(self,width=10,textvariable = self.master.streamingPotential.date).grid(row=2,column=2,columnspan=2,pady=5,padx=5,sticky='nsw')


        tk.Label(self,text="Index",bg=self['bg']).grid(row=3,column=1,padx=5,pady=5)
        for ind,index_string in enumerate(self.master.streamingPotential.file_indices):
            tk.Entry(self,width=10,textvariable = index_string).grid(row=4+ind,column=1,pady=5,padx=5,sticky='nsw')
        autofill_button = tk.Button(self,text = 'V',command=self.master.streamingPotential.autofill_indices)
        autofill_button.grid(row=4,column=0,padx=2.5,pady=5,sticky='nsew')

        tk.Label(self,text="Position / mm",bg=self['bg']).grid(row=3,column=2,padx=5,pady=5)
        for ind,position_string in enumerate(self.master.streamingPotential.positions_strings):
            tk.Entry(self,width=10,textvariable = position_string).grid(row=4+ind,column=2,pady=5,padx=5,sticky='nsw')

        #Load buttons
        tk.Button(self,text='Load all',command=self.master.streamingPotential.load_all_files,width=10).grid(row=3,column=3,pady=5,padx=5,sticky='nswe')
        for ind in range(MAX_NUM_DATA):
            tk.Button(self,text='Load',command=lambda ind=ind:self.master.streamingPotential.load_file(ind),width=10).grid(row=4+ind,column=3,pady=5,padx=5,sticky='nswe')
        #Loaded?
        for ind in range(MAX_NUM_DATA):
            label = tk.Label(self,text='X',bg=self['bg'])
            label.grid(row=4+ind,column=4,pady=5,padx=5,sticky='nswe')
            self.master.streamingPotential.loaded_confirm_labels.append(label)

class summaryFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent
        self.streamingPotential = master.streamingPotential
        self.rowconfigure(0, weight=1)

        # Update rcParams
        mpl.rcParams.update(rcParams)
        # Initialise figure
        self.fig = mplfigure.Figure(figsize=(FIG_WID,1),dpi=200)
        self.fig.patch.set_color(WINDOW_COLOR)
        self.canvas=FigureCanvasTkAgg(self.fig, master=self)  
        self.canvas.draw_idle()
        self.canvas.flush_events()
        self.canvas.get_tk_widget().grid(row=0, column=0)
        # self.canvas.get_tk_widget().config(highlightthickness=3, highlightbackground=BLACK)
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.15, wspace=0, hspace=0)

        axes = [self.fig.add_subplot(2, 5, i + 1) for i in range(10)]
        self.axes = np.array(axes).reshape(2, 5)
        #Toolbar
        # self.toolbarFrame=tk.Frame(master=self)
        # self.toolbarFrame.grid(row=1,column=0,padx=10,pady=5,sticky='nsw')
        # NavigationToolbar2Tk(self.canvas, self.toolbarFrame, pack_toolbar=True)
        # self.ax.format_coord = lambda x, y: "" #remove coordinates from toolbar

        for ax in self.axes.flatten():
            ax.tick_params(axis='both',which='both',bottom=False,left=False,labelbottom=False,labelleft=False)

        self.axes[0,0].set_ylabel("Photoelectron signal / a.u.",y=0)
        self.axes[1,2].set_xlabel("Electron kinetic energy / eV")

        self.ax_labels = []
        for ax in self.axes.flatten():
            ax.plot(-1,-1,c='k',alpha=.25)
            ax.plot(-1,-1,c='tab:red',alpha=.25)
            ax.set_xlim(2,3)
            ax.set_ylim(0,1.1)
            self.ax_labels.append((ax.text(0.05,0.85,f"",weight='bold',ha='left',va='center',transform=ax.transAxes),
                                  ax.text(0.5,0.5,f"",ha='center',va='center',transform=ax.transAxes)))
            

        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def plot_summary_spectrum(self,ind):
        spectrum = self.streamingPotential.spectra[ind]
        #Get axis
        ax = self.axes.flatten()[ind]
        #Update plot
        ax.get_lines()[0].set_data(*spectrum.data)
        #Update labels
        self.ax_labels[ind][0].set_text(f"{spectrum.findex}")
        self.ax_labels[ind][1].set_text(f"{spectrum.position:.2f} mm")
        #Set background to red (not yet fit)
        ax.set_facecolor((1,0,0,0.2))
        #Redraw canvas
        self.canvas.draw_idle()
        # self.canvas.flush_events()

    def update_fit_status(self,ind):
        #Get axis
        ax = self.axes.flatten()[ind]
        #Set background to green (fit done)
        ax.set_facecolor((0,0.68,0,0.2))
        #Redraw canvas
        self.canvas.draw_idle()
        self.canvas.flush_events()



    def on_click(self,event):
        """Select subplot"""
        if event.inaxes is not None:
            ax = event.inaxes
            ind = np.where(self.axes.flatten()==ax)[0][0]
            # add what happens on selection
            self.master.fittingFrame.plot_fit_spectrum(ind)

    def on_motion(self,event):
        """Change cursor to pointer on subplots"""
        if event.inaxes is not None:
            self.canvas.get_tk_widget().config(cursor="hand2")
        else:
            self.canvas.get_tk_widget().config(cursor="")


class fittingFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent
        self.streamingPotential = master.streamingPotential
        # Update rcParams
        mpl.rcParams.update(rcParams)
        # Initialise figure
        self.fig = mplfigure.Figure(figsize=(FIG_WID, FIG_WID*0.75), dpi=200)
        self.fig.patch.set_color(WINDOW_COLOR)
        self.canvas=FigureCanvasTkAgg(self.fig, master=self)  
        self.canvas.draw_idle()
        self.canvas.flush_events()
        self.canvas.get_tk_widget().grid(row=1, column=0,columnspan=2)
        self.fig.subplots_adjust(left=0.15, right=0.965, top=0.97, bottom=0.16, wspace=0, hspace=0)
        self.ax = self.fig.add_subplot(111)
        self.xlim_strings = [tk.StringVar(value=xlim) for xlim in DEFAULT_XLIMS]
        self.update_xlim()
        self.ax.set_ylim(0,1.1)
        self.ax.set_xlabel("Electron kinetic energy / eV")
        self.ax.set_ylabel("Photoelectron signal / a.u.")
        for xlim_string in self.xlim_strings:
            xlim_string.trace_add('write', self.update_xlim)
        #Initialise lines
        self.spectrum_line, = self.ax.plot(-1,-1,'k')
        self.fit_line, = self.ax.plot(-1,-1,'tab:red')
        #Top frame
        self.topFrame = tk.Frame(master=self)
        self.topFrame.grid(row=0,column=0,columnspan=2)
        tk.Button(self.topFrame,text='Previous',command=self.load_previous,width=20).grid(row=0,column=0,pady=5,padx=10,sticky='nswe')
        tk.Button(self.topFrame,text='Fit',command=self.fit_spectrum,width=20).grid(row=0,column=1,pady=5,padx=10,sticky='nswe')
        tk.Button(self.topFrame,text='Next',command=self.load_next,width=20).grid(row=0,column=2,pady=5,padx=10,sticky='nswe')
        #Toolbar
        self.toolbarFrame=tk.Frame(master=self,highlightbackground="red", highlightthickness=0)
        self.toolbarFrame.grid(row=2,column=0,padx=(105,10),pady=5,sticky='nsw')
        NavigationToolbar2Tk(self.canvas, self.toolbarFrame, pack_toolbar=True)
        self.ax.format_coord = lambda x, y: "" #remove coordinates from toolbar
        #Bottom frame
        self.bottomFrame=tk.Frame(master=self)
        self.bottomFrame.grid(row=2,column=1)
        tk.Label(self.bottomFrame,text='x lim').grid(row=0,column=5,padx=5,pady=5)
        tk.Entry(self.bottomFrame,textvariable=self.xlim_strings[0],width=8).grid(row=0,column=6,padx=5,pady=5)
        tk.Entry(self.bottomFrame,textvariable=self.xlim_strings[1],width=8).grid(row=0,column=7,padx=5,pady=5)

        #Data
        self.display_ind = -1
        self.fit_limits = [0,5]

        #### Span Selector ####
        self.span = SpanSelector(self.ax,
                            self.onselect,
                            "horizontal",
                            useblit=True,
                            props=dict(alpha=0, facecolor="tab:blue"),
                            interactive=True,
                            drag_from_anywhere=True
                        )
        self.canvas.mpl_connect('key_press_event', self.span)
        self.canvas.draw_idle()
        self.canvas.flush_events()

    def onselect(self,xmin,xmax):
        self.fit_limits = [xmin,xmax]

    def update_xlim(self,*args):
        try:
            self.ax.set_xlim([float(x.get()) for x in self.xlim_strings])
            self.canvas.draw_idle()
            # self.canvas.flush_events()
        except ValueError:
            return

    def plot_fit_spectrum(self,ind):
        """Plots spectrum with ind."""
        self.display_ind = ind
        self.update_xlim()

        spectrum = self.streamingPotential.spectra[ind]
        if isinstance(spectrum,SPspectrum):
            self.spectrum_line.set_data(spectrum.data[0],spectrum.data[1])
            if spectrum.fit_params.size != 0:
                self.draw_fit()
                self.span.extents = (spectrum.fit_limits)
            else:
               self.fit_line.set_data([-1],[-1])
        else: 
            pass
        self.canvas.draw_idle()
        # self.canvas.flush_events()
        
    def clear_plot(self):
        #Reset lines
        self.spectrum_line, = self.ax.plot(-1,-1,'k')
        self.fit_line, = self.ax.plot(-1,-1,'tab:red')
        #Reset ylim
        self.ax.set_ylim(0,1.1)
        self.update_xlim()
        self.display_ind = -1


    def load_previous(self):
        next_ind = self.display_ind-1
        if next_ind>=0:
            self.plot_fit_spectrum(next_ind)
        else:
            pass
    def load_next(self):
        next_ind = self.display_ind+1
        if next_ind<len(self.streamingPotential.spectra):
            self.plot_fit_spectrum(next_ind)
        else:
            pass

    def fit_spectrum(self):
        spectrum = self.streamingPotential.spectra[self.display_ind]
        spectrum.fit_limits = self.fit_limits.copy()
        spectrum.fit_spectrum()
        self.draw_fit()
    
    def draw_fit(self):
        spectrum = self.streamingPotential.spectra[self.display_ind]
        #Update fit line in fit frame
        self.fit_line.set_data(XS_EKE,multiple_gaussians(XS_EKE,*spectrum.fit_params))

        self.canvas.draw_idle()
        #Plot in results frame
        self.master.resultsFrame.plot_positions()
        #Update status in summary frame
        self.master.summaryFrame.update_fit_status(self.display_ind)


class resultsFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,highlightbackground="red", highlightthickness=0)
        self.master = master 
        self.parent = parent
        self.streamingPotential = master.streamingPotential
        # Update rcParams
        mpl.rcParams.update(rcParams)
        #Initialise figure
        self.fig = mplfigure.Figure(figsize=(FIG_WID, FIG_WID*0.75), dpi=200)
        self.fig.patch.set_color(WINDOW_COLOR)
        self.canvas=FigureCanvasTkAgg(self.fig, master=self)  
        self.canvas.draw_idle()
        self.canvas.flush_events()
        self.canvas.get_tk_widget().grid(row=0, column=0,columnspan=2)
        self.fig.subplots_adjust(left=0.15, right=0.965, top=0.97, bottom=0.16, wspace=0, hspace=0)
        self.ax = self.fig.add_subplot(111) 
        self.ax.set_xlim(0,2)
        self.ax.set_xlabel("Distance from jet / mm")
        self.ax.set_ylabel("Electron kinetic energy / eV")
        #to keep track of plotted spectra
        self.plotted_indices = []

        #Toolbar
        self.toolbarFrame=tk.Frame(master=self)
        self.toolbarFrame.grid(row=1,column=0,padx=(105,10),pady=5,sticky='nsw')
        NavigationToolbar2Tk(self.canvas, self.toolbarFrame, pack_toolbar=True)
        self.ax.format_coord = lambda x, y: "" #remove coordinates from toolbar
        # Bottom frame
        self.bottomFrame=tk.Frame(master=self,highlightbackground="red", highlightthickness=0)
        self.bottomFrame.grid(row=1,column=1)

    def plot_positions(self):
        """Change this function and StreamingPotential so that
        positions and kinetic energies are attributes of StreamingPotential"""
        self.ax.clear()
        self.ax.set_xlim(0,2)
        self.ax.set_xlabel("Distance from jet / mm")
        self.ax.set_ylabel("Electron kinetic energy / eV")

        self.positions = []
        self.kinetic_energies = []
        self.plotted_indices = []
        for i,spectrum in enumerate(self.streamingPotential.spectra):
            if isinstance(spectrum,SPspectrum) and len(spectrum.fit_params)>0:
                self.positions.append(spectrum.position)
                self.kinetic_energies.append(spectrum.fit_params[1])
                self.plotted_indices.append(i)
        self.ax.plot(self.positions,self.kinetic_energies,'ko')
        if len(self.positions)>=3:
            self.fit_positions()
        else:
            self.master.resultPanelFrame.phi_label.config(text=f"{phistr}")
            self.master.resultPanelFrame.offset_label.config(text=f"V{zerosubstr}")

        self.canvas.draw_idle()

    def fit_positions(self):
        SP_fit_func = lambda x, phi, offset: SP_curve(x, self.streamingPotential.wavelength, phi, offset)
        self.streamingPotential.fit_params,_ = curve_fit(SP_fit_func,self.positions,self.kinetic_energies,p0 = [.1,.1])
        true_eKE = 3*1239.8/self.streamingPotential.wavelength - XE_EBE

        if len(self.ax.get_lines())>1: # bad practice?
            self.ax.get_lines()[1].set_data(XS_POS,SP_fit_func(XS_POS,*self.streamingPotential.fit_params))
            self.ax.collections[0].set_segments([[(0, true_eKE - self.streamingPotential.fit_params[1]), (2.0, true_eKE - self.streamingPotential.fit_params[1])]])  # Update the hline ends
        else:
            self.ax.plot(XS_POS,SP_fit_func(XS_POS,*self.streamingPotential.fit_params),'tab:red')
            self.ax.hlines(true_eKE - self.streamingPotential.fit_params[1],0,2.0,'k',':')
        
        low_ylim = min(true_eKE - self.streamingPotential.fit_params[1]-0.05, min(self.kinetic_energies)-0.01)
        high_ylim = max(true_eKE - self.streamingPotential.fit_params[1]+0.05, max(self.kinetic_energies)+0.01)
        self.ax.set_ylim(low_ylim,high_ylim)
        self.master.resultPanelFrame.phi_label.config(text=f"{phistr} = {self.streamingPotential.fit_params[0]:.2f} eV")
        self.master.resultPanelFrame.offset_label.config(text=f"V{zerosubstr} = {self.streamingPotential.fit_params[1]:.2f} eV")

class resultPanelFrame(tk.Frame):
    def __init__(self,parent,master):
        super().__init__(parent,
                         bg=ACCENT_COLOR,
                        #  relief='raised',
                         borderwidth=2,
                         highlightbackground="red",
                         highlightthickness=0
                         )
        self.master = master 
        self.parent = parent
        self.streamingPotential = self.master.streamingPotential

        #Divide frame into three rows each with its own frame/content
        self.columnconfigure(0, weight=1)
        
        # self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        #Top frame
        label=tk.Label(self, text='Results',font=('Helvetica', SUBTITLE_FONT_SIZE,'bold'),bg=self['bg'])
        label.grid(row=0,column=0,columnspan=4,padx=10,pady=10, sticky = 'nsw')
        # Middle frame
        self.middleFrame = tk.Frame(self,highlightbackground="red", highlightthickness=0,bg=self['bg'])
        self.middleFrame.grid(row=1,column=0,padx=5,pady=5,sticky='ns') 
        for n in range(2):
            self.middleFrame.columnconfigure(n, weight=1)
        self.middleFrame.rowconfigure(0, weight=1)
        self.phi_label = tk.Label(self.middleFrame,text = f"{phistr}",wid=14,font=('Helvetica', LARGE_FONT_SIZE),anchor='w',bg=self['bg'])
        self.phi_label.grid(row=0,column=0,padx=5,pady=5,sticky='nse')
        self.offset_label = tk.Label(self.middleFrame,text = f"V{zerosubstr}",wid=14,font=('Helvetica', LARGE_FONT_SIZE),anchor='w',bg=self['bg'])
        self.offset_label.grid(row=0,column=1,padx=5,pady=5,sticky='nsw')
        #Bottom frame
        self.bottomFrame = tk.Frame(self,highlightbackground="red", highlightthickness=0,bg=self['bg'])
        self.bottomFrame.grid(row=2,column=0,padx=5,pady=5,sticky='sw')
        #Save results
        label=tk.Label(self.bottomFrame,text='Save results',bg=self['bg'])
        label.grid(row=0,column=0,padx=5,pady=5, sticky = 'nswe')
        label=tk.Button(self.bottomFrame,command=self.streamingPotential.save_result, image=master.saveIcon_image)
        label.grid(row=0,column=1,padx=5,pady=5, sticky = 'nswe')
        #Save project
        label=tk.Label(self.bottomFrame,text='Save project',bg=self['bg'])
        label.grid(row=0,column=2,padx=5,pady=5, sticky = 'nswe')
        label=tk.Button(self.bottomFrame, image=master.saveIcon_image)
        label.grid(row=0,column=3,padx=5,pady=5, sticky = 'nswe')


if __name__ =="__main__":

    app = tk.Tk()
    streamingFrame = streamingGUI(app)
    streamingFrame.pack()

    app.geometry("+60+60")
    app.wm_title("Streaming")
    app.mainloop()