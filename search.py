# -*- coding: utf-8 -*-

from pathlib import Path

def get(query, searchDir):
	walk = Path(searchDir)
	found = walk.glob('**/*')

	queries = query.split('+')
	queriesAmount = len(queries)

	result = []

	for item in found:
		if item.is_dir():
			continue

		matches = [q for q in queries if q in str(item)]
		if len(matches) == queriesAmount:
			result.append(item)

	return result
		

if __name__ == "__main__":
	get()
