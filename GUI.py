import tkinter as tk
from tkinter import ttk
import pandas as pd
import threading
import Constants as c
import queue


class GUI(threading.Thread):
    def __init__(self, version):
        self.version = version
        self.q = queue.Queue()
        threading.Thread.__init__(self)
        self.start()
        self.box = None
        self.root = None
        self.df = pd.DataFrame(columns=c.live_columns)


    def run(self):

        self.root = tk.Tk()
        self.root.withdraw()
        self.create_box(columns=c.live_columns)
        self.process_incoming()
        self.root.mainloop()
        #


    def process_incoming(self):
        """Handle all messages currently in the queue, if any."""

        while self.q.qsize():
            print('test')
            try:
                tdf = self.q.get()
                # Check contents of message and do whatever is needed. As a
                # simple test, print it (in real life, you would
                # suitably update the GUI's display in a richer fashion).
                print(tdf.to_frame().T)
                self.df.update(tdf.to_frame().T, overwrite=True)

            except self.q.empty():
                # just on general principles, although we don't
                # expect this branch to be taken in this case
                pass

        fill_box(self.root, df=self.df)

    def create_box(self, columns):
        window = tk.Toplevel(self.root)
        tk.Label(window, text="Sangolytics", font=("Arial", 20)).grid(row=0, columnspan=3)
        listBox = ttk.Treeview(window, columns=columns, show='headings')
        for col in columns:
            listBox.heading(col, text=col)
        listBox.grid(row=1, column=0, columnspan=2)
        tk.Button(window, text="Close", width=15, command=self.root.quit).grid(row=4, column=1)
        self.root = listBox




def fill_box(list_box, df):
    for row in df.values.tolist():
        list_box.insert("", "end", values=row)


if __name__ == '__main__':

    gui = GUI(version='cbb')
    df = pd.read_csv('datatest.csv')
    columns = df.columns.tolist()
    gui.create_box(columns=columns)
    t1 = threading.Thread(target=gui.process_incoming)
    t1.start()
    print('test')
    #print(gui.root)
    #fill_box(gui.root, df=df)


    # df2 = pd.read_csv('datatest2.csv')
    # gui.root = gui.create_box(df=df)
    # fill_box(list_box=gui.root, df=df2)




# one windows with df of all games
# for nba, window for each game with all the current players on the floor
# call the gamecast functions for nba

# create original 