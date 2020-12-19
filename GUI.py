
import tkinter as tk
from tkinter import ttk
import pandas as pd

def fill_box(list_box, df):
    for row in df.values.tolist():
        list_box.insert("", "end", values=row)




def create_box(df):
    columns = df.columns.tolist()
    window = tk.Toplevel(root)
    tk.Label(window, text="Sangolytics", font=("Arial",20)).grid(row=0, columnspan=3)
    listBox = ttk.Treeview(window, columns=columns, show='headings')
    for col in columns:
        listBox.heading(col, text=col)
    listBox.grid(row=1, column=0, columnspan=2)
    tk.Button(window, text="Close", width=15, command=exit).grid(row=4, column=1)
    return listBox


def gui_driver():
    root = tk.Tk()
    root.withdraw()
    df = pd.read_csv('datatest.csv')

    box = create_box(df=df)
    fill_box(list_box=box, df=df)
    root.mainloop()

# one windows with df of all games
# for nba, window for each game with all the current players on the floor
# call the gamecast functions for nba