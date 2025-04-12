import tkinter as tk
from tkinter import ttk

import streaming.streamingGUI as strg
import scatter.scatterGUI as scag

app = tk.Tk()
app.geometry("+60+60")


### Format constants ###
FONT_SIZE = 9
TITLE_FONT_SIZE = 20
SUBTITLE_FONT_SIZE = 16
###


def _on_tab_changed(event):
    event.widget.update_idletasks()

    tab = event.widget.nametowidget(event.widget.select())
    event.widget.configure(height=tab.winfo_reqheight(),
                           width=tab.winfo_reqwidth())

#Style of notebook tab labels
style = ttk.Style()
style.configure('TNotebook.Tab', font=('Helvetica', FONT_SIZE,), padding=[20, 5])


# Create and pack a notebook
notebook = ttk.Notebook(app,style='TNotebook')
notebook.pack(pady=10, expand=True)

# Create and pack frames
scatterFrame = scag.scatterGUI(notebook)
streamingFrame = strg.streamingGUI(notebook)

scatterFrame.pack(fill='both', expand=True)
streamingFrame.pack(fill='both', expand=True)

# add frames to notebook

notebook.add(streamingFrame, text='Streaming')
notebook.add(scatterFrame, text='Scatter')

# Bind resize upon tab change
notebook.bind("<<NotebookTabChanged>>", _on_tab_changed)

# Window settings
app.geometry("+60+60")
app.wm_title("UV LJ Utilities")

# Mainloop
app.mainloop()