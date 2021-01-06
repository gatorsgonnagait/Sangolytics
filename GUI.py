import tkinter as tk
from tkinter import ttk
import pandas as pd
import threading
import Constants as c
import queue
import time

class GUI(threading.Thread):
    def __init__(self, version):
        self.version = version
        self.q = queue.Queue()

        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        try:
            self.start()
        except KeyboardInterrupt:
            self.join()

        self.box = None
        self.root = None
        self.df = pd.DataFrame(columns=c.live_columns)
        self.player_df = pd.DataFrame(columns=c.player_columns)
        #window = tk.Toplevel(self.root)
        #tk.Label(window, text="Sangolytics", font=("Arial", 20)).grid(row=0, columnspan=3)
        self.list_box = ttk.Treeview()


    def run(self):

        self.root = tk.Tk()
        self.root.withdraw()
        #self.list_box = self.create_box(columns=c.live_columns)
        #self.process_incoming()
        self.root.mainloop()


    def process_incoming(self):
        print('process team stats')
        while True:
            while not self.q.empty():
                try:
                    tdf = self.q.get()
                    if tdf.empty:
                        continue

                    if not tdf['Game'].iloc[0] in self.df.index:
                        self.df = self.df.append(tdf, ignore_index=False, sort=False)
                    else:
                        self.df.update(tdf, overwrite=True)

                    time.sleep(.5)
                except self.q.empty():
                    pass
            time.sleep(2)
            self.fill_box(df=self.df)

    def process_players(self, player_q, box):
        print('process players stats')
        while True:
            try:
                tdf = player_q.get()
                if tdf.empty:
                    continue


                time.sleep(.5)
            except player_q.empty():
                continue
            time.sleep(2)
            self.fill_players(df=tdf, box=box)

    def create_box(self, columns):
        print('create box')
        window = tk.Toplevel(self.root)
        tk.Label(window, text="Sangolytics", font=("Arial", 20)).grid(row=0, columnspan=3)
        listBox = ttk.Treeview(window, columns=columns, show='headings')
        for col in columns:
            listBox.heading(col, text=col)
        listBox.grid(row=1, column=0, columnspan=2)
        tk.Button(window, text="Close", width=15, command=self.root.quit).grid(row=4, column=1)
        self.list_box = listBox
        #return listBox

    def create_player_box(self, columns, game):
        print('create player box')
        window = tk.Toplevel(self.root)
        tk.Label(window, text=game, font=("Arial", 20)).grid(row=0, columnspan=3)
        listBox = ttk.Treeview(window, columns=columns, show='headings')
        for col in columns:
            listBox.heading(col, text=col)
        listBox.grid(row=1, column=0, columnspan=2)
        tk.Button(window, text="Close", width=15, command=self.root.quit).grid(row=4, column=1)
        return listBox


    def fill_box(self, df):
        self.list_box.delete(*self.list_box.get_children())
        for row in df.values.tolist():
            self.list_box.insert('', 'end', values=row)
        self.list_box.delete()

    def fill_players(self, df, box):
        box.delete(*box.get_children())
        for row in df.values.tolist():
            box.insert('', 'end', values=row)
        box.delete()



# def fill_box(list_box, df):
#     for row in df.index:
#         print(row)
#         list_box.insert('', "end", values=df.loc[row])

if __name__ == '__main__':

    gui = GUI(version='cbb')
    df = pd.read_csv('datatest.csv', index_col=['index'])
    print(df.loc['tenn auburn'])
    columns = df.columns.tolist()

    gui.create_box(columns=columns)
    t1 = threading.Thread(target=gui.process_incoming)
    t1.start()
    print('test2')
    print(gui.list_box)
    gui.fill_box(df=df)


    # df2 = pd.read_csv('datatest2.csv')
    # gui.root = gui.create_box(df=df)
    # fill_box(list_box=gui.root, df=df2)


# one windows with df of all games
# for nba, window for each game with all the current players on the floor
# call the gamecast functions for nba

# create original 