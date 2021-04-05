import pandas as pd
import numpy as np
import time

rng = np.random.default_rng()
live_columns = ['Game','Period','Away','Home','Current Total','Live Total','PPM Last N','PPM Game','Live Spread','Margin Last N']

def process_incoming():
    df = pd.DataFrame()
    while True:
        tdf = pd.DataFrame(rng.integers(0, 10, size=(10, 10)), columns=live_columns)
        if not tdf['Game'].iloc[0] in df.index:
            df = df.append(tdf, ignore_index=False, sort=False)
        else:
            df.update(tdf, overwrite=True)
        print(df)
        time.sleep(4)

process_incoming()