import tkinter
from tkinter import ttk


def format_battletag(*args) -> None:
    orig_tag = battletag.get()
    converted_tag.set(orig_tag.replace('#', '-'))
root = tkinter.Tk()
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)


battletag = tkinter.StringVar()
converted_tag = tkinter.StringVar()
battletag_entry = ttk.Entry(mainframe, width=7, textvariable=battletag)
battletag_entry.grid(column=2, row=1, sticky=(tkinter.W, tkinter.E))
ttk.Label(mainframe, textvariable=converted_tag).grid(column=2, row=2, sticky=(tkinter.W, tkinter.E))
ttk.Button(mainframe, text="Convert Battletag", command=format_battletag).grid(column=3, row=3, sticky=tkinter.W)

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

battletag_entry.focus()
root.bind('<Return>', format_battletag)
root.mainloop()
