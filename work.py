# -*- coding: utf-8 -*-

import locale
from pathlib import Path
from datetime import datetime, timedelta
from Sborka import config, parser
from collections import defaultdict 

#exclusions = ('grommet', 'gotovo', 'готово', 'ночная', 'Ночь', 'рез', 'ZundRez', 'rez', '/plot', 'day', 'night', 'Night')
exclusions = ('cifra', 'grommet', 'ночная', 'Ночь', 'рез', 'ZundRez', 'rez', '/plot', 'day', 'night', 'Night', 'ДЕНЬ')
ready = ('готово', )

test = ('256416', '256176', '256234', '256320')

locale.setlocale(locale.LC_ALL, '')

class DayWork:
	def __init__(self):
		self.date = ''
		self.qualities = []
		self.amount = 0
		self.ready = 0
	
	def addQuality(self, quality):
		self.qualities.append(quality)
		self.amount += quality.amount

class Quality:
	def __init__(self, name):
		self.name = name
		self.materials = {}
		self.amount = 0
		self.totalSize = 0

	def getMaterial(self, name):
		if name in self.materials:
			return self.materials[name]
		
		material = Material(name)
		self.materials[name] = material
		return material
		
class Material:
	def __init__(self, name):
		self.name = name
		self.groups = []
		self.description = ''
		
	def addGroup(self, group):
		self.groups.append(group)
	
	def getGroup(self, groupName):
		for group in self.groups:
			if group.name == groupName:
				return group
		return None
	
	def getSize(self):
		totalSize = 0
		for group in self.groups:
			totalSize += group.totalSize
		
		return totalSize

	def getAmount(self):
		amount = 0
		for group in self.groups:
			amount += group.getAmount()
		
		return amount
	
		
class Group:
	def __init__(self, name):
		self.name = name
		self.order = None
		self.orderStatus = True
		self.isPrintToday = None
		self.files = []
		self.totalSize = 0
			
	def addFile(self, file):
		self.files.append(file)
		w,h = file.dimention
		self.totalSize += w * h * file.copies
		
	def getAmount(self):
		return len(self.files)
		
class File:
	def __init__(self, path):
		self.path = path
		self.copies = 0
		self.dimention = None

def get_files(date, works, order):
	month = date.strftime("%B").lower()
	day = f'{date.day:0>2}'
	
	workPath = Path(config.workDir, month, day)

	if not workPath.exists():
		return
	
	dayWork = DayWork()
	dayWork.date = f'{day} {month}'
	dateNow = datetime.now()
	
	now = f'({dateNow.day:0>2}_{dateNow.month:0>2})'
	
	subdirs = [d for d in workPath.iterdir() if d.is_dir()]
	
	for dir in subdirs:
		rdir = str(dir.relative_to(workPath))
		
		if [e for e in exclusions if e in rdir]:
			continue
		
		quality = Quality(rdir)
				
		files = [f for f in dir.rglob('*.*')]

		amount = 0
		
		for file in sorted(files, reverse=True):		
			rfile = file.relative_to(dir)
			strFile = str(rfile)
			if [e for e in exclusions if e in strFile]:
				continue
				
			if [e for e in ready if e in strFile]:	
				dayWork.ready += 1
				continue

			materialName = parser.getMaterial(file.stem)
			material = quality.getMaterial(materialName)
			material.description = parser.MATERIALS[materialName]
		
			groupName = str(rfile.parent)
			
			if groupName == '.':	#sborka = 1 file
				group = Group(groupName)
				group.order = parser.getGroup(file.stem)
				material.addGroup(group)
			
			else:
				group = material.getGroup(groupName)
				if not group:	
					group = Group(groupName)
					group.order = parser.getGroup(groupName)
					material.addGroup(group)
				
				
			
			if order:
				group.orderStatus = group.order in order.sborkiSHF
				
			group.isPrintToday = parser.getDateComplete(file.stem) == now

			f = File(file)
			f.copies = parser.getCopies(file.stem)
			f.dimention = parser.getDimentions(file.stem)
			quality.totalSize  += parser.getSize(file.stem) * f.copies
			group.addFile(f)
			quality.amount += 1
			
		if quality.materials:
			dayWork.addQuality(quality)
		
	if dayWork.qualities:
		works.append(dayWork)						
				

def load(order):
	data = []
	
	for single_date in (datetime.now() - timedelta(n) for n in reversed(range(config.workDays))):
		get_files(single_date, data, order)
		
	return data

if __name__ == "__main__":
	load()