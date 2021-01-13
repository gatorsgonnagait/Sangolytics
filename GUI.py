import tkinter as tk
from tkinter import ttk
import pandas as pd
import threading
import Constants as c
import queue
import time
import sys

class GUI(threading.Thread):
    def __init__(self, version):
        self.version = version
        self.q = queue.Queue()

        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        try:
            self.start()
        except (KeyboardInterrupt, SystemExit):
            self.join()
            sys.exit()

        self.box = None
        self.root = None
        self.df = pd.DataFrame(columns=c.live_columns)
        self.player_df = pd.DataFrame(columns=c.player_columns)
        self.list_box = ttk.Treeview()
        self.player_box_dict = {}
        self.game_row = {}
        self.game_set = set()


    def run(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.mainloop()


    def process_incoming(self):
        print('process team stats')
        while True:
            df = pd.DataFrame()
            while not self.q.empty():
                try:
                    tdf = self.q.get()
                    if tdf.empty:
                        continue

                    if not tdf['Game'].iloc[0] in df.index:
                        df = df.append(tdf, ignore_index=False, sort=False)
                    else:
                        df.update(tdf, overwrite=True)

                    time.sleep(.5)
                except self.q.empty():
                    pass
            time.sleep(2)
            self.fill_box(df=df)

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


    def create_player_box(self, columns, game):
        print('create player box')
        window = tk.Toplevel(self.root)
        tk.Label(window, text=game, font=("Arial", 20)).grid(row=0, columnspan=3)
        listBox = ttk.Treeview(window, columns=columns, show='headings')
        for col in columns:
            listBox.heading(col, text=col)
        listBox.grid(row=1, column=0, columnspan=2)
        tk.Button(window, text="Close", width=15, command=listBox.quit).grid(row=4, column=1)
        return listBox


    def fill_box(self, df):
        #live_columns = ['Game','Period','Current Total','Live Total','PPM Last N','PPM Game']
        for i, row in enumerate(df.values.tolist()):
            if self.list_box.exists(item=row[0]):
                self.list_box.focus(row[0])
                self.list_box.set(row[0], column=1, value=row[1])
                self.list_box.set(row[0], column=2, value=row[2])
                self.list_box.set(row[0], column=3, value=row[3])
                self.list_box.set(row[0], column=4, value=row[4])
                self.list_box.set(row[0], column=5, value=row[5])
            else:
                self.game_row[row[0]] = i
                self.list_box.insert('', index=i,iid=row[0], values=row)


        #self.list_box.delete()

    def fill_players(self, df, box):
        box.delete(*box.get_children())
        for row in df.values.tolist():
            box.insert('', 'end', values=row)
        box.delete()

    def open_players(self, game, id):
        player_box = self.create_player_box(columns=c.player_columns, game=game)
        self.player_box_dict[id] = player_box
        player_queue = queue.Queue()
        t2 = threading.Thread(target=self.process_players, args=[player_queue, player_box])
        try:
            t2.start()
        except KeyboardInterrupt:
            t2.join()


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