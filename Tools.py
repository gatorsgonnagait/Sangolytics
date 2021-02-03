import Constants as c
from collections import Counter

def most_frequent(List):
	occurence_count = Counter(List)
	try:
		return occurence_count.most_common(1)[0][0]
	except IndexError:
		return None

def handle_duplicates(df, index):
	df = df.reset_index().drop_duplicates(keep='last', subset=[index])
	df.set_index(index, inplace=True)
	return df
