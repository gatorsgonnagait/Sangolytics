import Constants as c
from collections import Counter

def most_frequent(List):
	occurence_count = Counter(List)
	try:
		return occurence_count.most_common(1)[0][0]
	except IndexError:
		return None

def format_team_names(team_name):
	formatted_team = c.team_dict.get(team_name)
	if formatted_team:
		return formatted_team
	else:
		return team_name