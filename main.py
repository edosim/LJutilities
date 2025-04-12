import tkinter as tk
from tkinter import ttk

import streaming.streamingGUI as strg
import scatter.scatterGUI as scag

app = tk.Tk()
app.geometry("+60+60")

# app = strg.streamingGUI()
# app.mainloop()
# notebook = ttk.Notebook(app)

#Style of notebook tab labels
style = ttk.Style()
style.configure('TNotebook.Tab', font=('Helvetica', 10,), padding=[20, 5])


# create a notebook
notebook = ttk.Notebook(app,style='TNotebook')
notebook.pack(pady=10, expand=True)

# create frames
scatterFrame = scag.scatterGUI(notebook)
streamingFrame = strg.streamingGUI(notebook)

scatterFrame.pack(fill='both', expand=True)
streamingFrame.pack(fill='both', expand=True)

# add frames to notebook

notebook.add(streamingFrame, text='Streaming')
notebook.add(scatterFrame, text='Scatter')


##
# def update_menubar(event):
#     selected_tab = notebook.index(notebook.select())
#     menubar.entryconfig("Tab Info", label=f"Selected Tab: {selected_tab + 1}")


# notebook.bind("<<NotebookTabChanged>>", update_menubar)

app.mainloop()