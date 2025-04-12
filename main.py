import tkinter as tk
from tkinter import ttk

import streaming.streamingGUI as strg
import scatter.scatterGUI as scag

app = tk.Tk()
app.geometry("+60+60")

# app = strg.streamingGUI()
# app.mainloop()
# notebook = ttk.Notebook(app)

# create a notebook
notebook = ttk.Notebook(app)
notebook.pack(pady=10, expand=True)

# create frames
frame1 = scag.scatterGUI(notebook)
frame2 = ttk.Frame(notebook, width=400, height=280)

frame1.pack(fill='both', expand=True)
frame2.pack(fill='both', expand=True)

# add frames to notebook

notebook.add(frame1, text='General Information')
notebook.add(frame2, text='Profile')

app.mainloop()