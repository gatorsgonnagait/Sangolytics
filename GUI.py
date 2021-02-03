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
        self.game_box = ttk.Treeview()
        self.player_box_dict = {}
        self.score_by_quarter_dict = {}
        self.score_by_quarter_on = {}
        self.players_on = {}
        self.player_queue_dict = {}
        self.game_row = {}
        self.id_to_names = {}
        self.names_to_ids = {}
        self.n = 3
        self.n_entry = None
        self.live_columns = ['Game','Period','Away','Home','Current Total','Live Total','PPM Last N','PPM Game','Live Spread','Margin Last N']
        self.n_label = None
        self.window = None
        self.combo_box = None
        self.force_continue = {}



    def run(self):
        self.root = tk.Tk()
        #self.window = tk.Toplevel()
        self.root.withdraw()
        self.root.mainloop()


    def process_incoming(self):
        while self.is_alive():
            df = pd.DataFrame()
            while self.is_alive() and not self.q.empty():
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
            try:
                self.fill_box(df=df)
            except RuntimeError:
                return


    def process_players(self, id):
        player_q = self.player_queue_dict[id]
        while self.is_alive() and self.players_on[id]:
            try:
                tdf = player_q.get()
                if tdf.empty:
                    continue

                time.sleep(.5)
            except player_q.empty():
                continue
            time.sleep(2)
            try:
                self.fill_players(df=tdf, box=self.player_box_dict[id])
            except KeyError:
                pass


    def submit_n(self):
        try:
            self.n = round(float(self.n_entry.get()))
            self.game_box.heading('PPM Last N', text='PPM Last ' + str(self.n))
            self.game_box.heading('Margin Last N', text='Margin Last ' + str(self.n))
            self.n_label = tk.Label(self.window, text='Last ' + str(self.n) + ' Minutes').grid(row=4, column=0)
            for game_id in self.force_continue.keys():
                self.force_continue[game_id] = True
        except ValueError:
            self.n = 3


    def open_score_by_quarter(self,id):
        player_box = self.create_score_by_quarter_box(columns=list(map(str.capitalize, c.score_by_quarter)), id=id)
        self.score_by_quarter_dict[id] = player_box
        self.score_by_quarter_on[id] = True
        self.force_continue[id] = True


    def open_players(self,id):
        player_box = self.create_player_box(columns=c.player_columns, id=id)
        self.players_on[id] = True
        self.player_box_dict[id] = player_box
        self.force_continue[id] = True
        t2 = threading.Thread(target=self.process_players, args=[id])
        try:
            t2.start()
        except (KeyboardInterrupt, SystemExit):
            t2.join()
            sys.exit()


    def open_player_box(self):
        highlighted = self.combo_box.get()
        try:
            if not self.names_to_ids[highlighted] in self.player_box_dict.keys():
                self.open_players(id=self.names_to_ids[highlighted])
        except KeyError:
            pass

    def open_score_by_quarter_box(self):
        highlighted = self.combo_box.get()
        try:
            if not self.names_to_ids[highlighted] in self.score_by_quarter_dict.keys():
                self.open_score_by_quarter(id=self.names_to_ids[highlighted])
        except KeyError:
            pass


    def close_player_box(self, window, id):
        window.destroy()
        self.player_box_dict.pop(id, None)
        self.players_on[id] = False


    def close_score_by_quarter(self, window, id):
        window.destroy()
        self.score_by_quarter_dict.pop(id, None)
        self.score_by_quarter_on[id] = False


    def create_box(self):
        self.window = tk.Toplevel(self.root, width=950, height=600)
        label = tk.Label(self.window, text="Sangolytics", font=("Arial", 15), justify='center')
        label.grid(row=0, columnspan=7)

        game_box = ttk.Treeview(self.window, columns=self.live_columns, show='headings', height=20)

        for col in self.live_columns:
            if col == 'PPM Last N':
                game_box.heading(col, text='PPM Last '+str(self.n))
            elif col == 'Margin Last N':
                game_box.heading(col, text='Margin Last '+str(self.n))
            else:
                game_box.heading(col, text=col)
            if col == 'Game':
                game_box.column(col, minwidth=200, width=350, stretch=True)
            elif col == 'Period':
                game_box.column(col, minwidth=130, width=130, stretch=True)
            else:
                game_box.column(col, minwidth=100, width=100, stretch=True, anchor=tk.CENTER)

        game_box.grid(row=1, column=0, columnspan=7)
        self.n_label = tk.Label(self.window, text='Last '+str(self.n)+' Minutes').grid(row=4, column=0)
        self.n_entry = tk.Entry(self.window)
        self.n_entry.grid(row=4, column=1)
        tk.Button(self.window, text='Change N',command=self.submit_n).grid(row=4, column=2)

        self.combo_box = ttk.Combobox(self.window, textvariable='Select game', values=None, width=40)
        self.combo_box.grid(row=4, column=4)
        self.combo_box.set('Select game')
        tk.Button(self.window, text='Score by Q', command=self.open_score_by_quarter_box).grid(row=4, column=6)
        if self.version == 'nba':
            tk.Button(self.window, text='Open Players', command=self.open_player_box).grid(row=4, column=5)

        self.window.protocol("WM_DELETE_WINDOW", self.root.quit)
        self.game_box = game_box


    def create_player_box(self, columns, id):
        window = tk.Toplevel(self.window, width=950)
        label = tk.Label(window, text=self.id_to_names[id], font=("Arial", 15), justify='center')
        label.grid(row=0, columnspan=3)
        listBox = ttk.Treeview(window, columns=columns, show='headings')
        for col in columns:
            listBox.heading(col, text=col)
            if col == 'Player':
                listBox.column(col, minwidth=100, width=100, stretch=True)
            elif col == 'Team':
                listBox.column(col, minwidth=150, width=150, stretch=True)
            else:
                listBox.column(col, minwidth=100, width=100, stretch=True,anchor=tk.CENTER)
        listBox.grid(row=1, column=0, columnspan=2)
        window.protocol("WM_DELETE_WINDOW", lambda: self.close_player_box(window=window, id=id))
        return listBox


    def create_score_by_quarter_box(self, columns, id):
        window = tk.Toplevel(self.window, width=950, height=500)
        label = tk.Label(window, text=self.id_to_names[id], font=("Arial", 15), justify='center')
        label.grid(row=0, columnspan=10)
        listBox = ttk.Treeview(window, columns=columns, show='headings', height=20)
        listBox.grid(row=1, column=0, columnspan=10)
        for col in columns:
            listBox.heading(col, text=col)
            if col == 'Player':
                listBox.column(col, minwidth=170, width=170, stretch=True)
            elif col == 'Team':
                listBox.column(col, minwidth=170, width=170, stretch=True)
            else:
                listBox.column(col, minwidth=100, width=100, stretch=True,anchor=tk.CENTER)

        window.protocol("WM_DELETE_WINDOW", lambda: self.close_score_by_quarter(window=window, id=id))

        return listBox


    def fill_box(self, df):
        for i, row in enumerate(df.values.tolist()):
            if self.game_box.exists(item=row[0]):
                self.game_box.focus(row[0])
                for j in range(1, len(c.live_columns)):
                    self.game_box.set(row[0], column=j, value=row[j])
            else:
                self.game_box.insert('', index=i, iid=row[0], values=row)


    def fill_players(self, df, box):
        # initial fill
        if len(box.get_children()) < 10:
            for i, player in enumerate(df.index):
                box.insert('', index=i, iid=player, values=df.loc[player].to_list())

        else:
            df2 = df.copy()
            for i, player in enumerate(box.get_children()):
                box.focus(player)
                if player in df.index:
                    for j, col in enumerate(c.player_columns[1:], start=1):
                        box.set(player, column=j, value=df2.at[player, col])
                    df2.drop([player], inplace=True)

                else:
                    new_player = df2.first_valid_index()
                    box.delete(player)
                    box.insert('', index=i, iid=new_player, values=df2.loc[new_player].to_list())
                    df2 = df2.iloc[1:]


    def fill_score_by_quarter(self, df, box):
        cols = ['points', '1st', '2nd', '3rd', '4th']
        #for player in df.index:
        for i in range(len(df)):
            player = df['player'].iloc[i]
            if box.exists(player):
                for j, col in enumerate(cols, start=2):
                   # if j == 2: print(df)
                   # print(j, col, df[col].iloc[i])
                    q_points = df[col].iloc[i]
                    box.set(player, column=j, value=q_points)

            else:
                if df['site'].iloc[i] == 1:
                    position = 'end'
                else:
                    position = 0
                box.insert('', index=position, iid=player, values=df.iloc[i].to_list())
