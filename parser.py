#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re


MATERIALS_1 = ['plgl_p', 'plgl', 'plpr', 'plperf', 'plmat', 'g_orajet', 'a_orajet', 'pllegko',
			 'banlit510', 'banlit440', 'banlam', 'banset',
			 'city150', 'city200', 'blue',
			 'holst_s', 'holst_n',
			 'pvh1', 'pvh2', 'pvh3', 'pvh4', 'pvh5', 'pvh6', 'pvh8', 'pvh10',
			 'penocarton5',
			 'akril_t2', 'akril_t3', 'akril_m2', 'akril_m3',
			 'compozit',
			 'oboi_shtukaturka'
			]

			
MATERIALS = {	'plgl_p': 'Пленка глянцевая ARB (белая)',
				'plgl': 'Пленка глянцевая Ritrama (белая)',
				'plpr': 'Пленка прозрачная Ritrama',
				'plperf': 'Пленка перфорированная', 
				'plmat': 'Пленка матовая Ritrama (белая)',
				'g_orajet': 'Пленка Orajet (глянцевая)',
				'a_orajet': 'Пленка Orajet (автомобильная)',
				'n_orajet': 'Пленка Orajet (напольная)',
				'pllegko' : 'Пленка легкосъемная Ritrama',
				'banlit510' : 'Баннер литой 510 г/м2',
				'banlit440' : 'Баннер литой 440 г/м2',
				'banlam' : 'Баннер ламинированный',
				'banset' : 'Баннерная сетка',
				'city150': 'Бумага City-Light 150 г/м2',
				'city200': 'Бумага City-Light 200 г/м2',
				'blue': 'Бумага Blue-Back',
				'holst_s': 'Холст синтетический',
				'holst_n': 'Хост натуральный',
				'pvh1' : 'Лист ПВХ 1 мм',
				'pvh2' : 'Лист ПВХ 2 мм',
				'pvh3' : 'Лист ПВХ 3 мм',
				'pvh4' : 'Лист ПВХ 4 мм',
				'pvh5' : 'Лист ПВХ 5 мм', 
				'pvh6' : 'Лист ПВХ 6 мм', 
				'pvh8' : 'Лист ПВХ 8 мм',
				'pvh10': 'Лист ПВХ 10 мм',
				'penocarton5': 'Лист Пенокартона 5 мм',
				'akril_t2': 'Акрил прозрачный 2 мм',
				'akril_t3': 'Акрил прозрачный 3 мм',
				'akril_m2': 'Акрил молочный 2 мм',
				'akril_m3': 'Акрил молочный 3 мм',
				'compozit': 'Лист композита 3 мм',
				'composit3': 'Лист композита 3 мм',
				'vinyl_magnet': 'Магнит',
				'oboi_shtukaturka': 'Обои "Штукатурка"',
				'none': 'Материал не определен'
			}
			
def getMaterial(name):
	for material in MATERIALS:
		if material in name:
			return material

	return 'none'		
	#raise Exception(f'Материал не определен: {name}')		
	
def getQuality(name):
	search = re.search(r'\d{1,4}dpi', name)
	if search:
		return search.group(0)[:-3]
	

def getOrder(name):
	search = re.search(r'-\d{8}', name)
	if search:
		return search.group(0)[1:]
	
	raise Exception(f'Номер заказа не определен: {name}')

def getDateComplete(name):
	search = re.search(r'\([0-3][0-9]_[0-1][0-9]\)', name)
	if search:
		return search.group(0)
	
	return ''

def getDimentions(name):
	search = re.search(r'\d+x\d+', name)
	if search:
		values = search.group(0).split('x')
		return(int(values[0]), int(values[1]))
	
	return (0,0)
	
def getSize(name):
	w,h = getDimentions(name)
	return w * h
	
def getGroup(name):
	search = re.search(r'\d{6}[^0-9\)]', name)
	if search:
		return search.group(0)[:6]
				
	return None	
	
def getCopies(name):
	search = re.search(r'(?<!izdel)(?<!KS)(?<!NP)(?<!dia)_([0-9]|[0-9][0-9]|[0-9][0-9][0-9]|[0-9][0-9][0-9][0-9])_', name)
	if search:
		amount = search.group(0)[1:-1]
		return int(amount)

	search = re.search(r'_[0-9]*copies_', name)	
	if search:
		amount = search.group(0)[1:-7]
		return int(amount)

	return 1
		
if __name__ == "__main__":
	test = ('__253398 _(15563-12830303)banlit510_1_(11400x2400)_1080dpi_luvPerim_dia10_shag30_obr_KS_24_(15)_(15_05)_(15_05).tif',\
	        '253316_ZUND_1499x4011_3copies_g_orajet_720dpi_NP_(15_05).eps',\
			'Fotoba__(683-12902970)city200_20_(1200x800)_1440dpi_obr_KS_24_(28)_(09_06).tif',\
			'__256245_(PLOT)_(1743-12900519)plgl_100_(150x90)_1440dpi_plot1_izdel_1_KS_24_(29)_(09_06).pdf',\
			'__256245_(PLOT)_(1743-12900519)plgl_3_(150x90)_1440dpi_plot1_izdel_6_KS_24_(29)_(09_06).pdf',\
			'__256245_(PLOT)_(1743-12900519)plgl_(150x90)_1440dpi_plot1_izdel_7_KS_24_(29)_(09_06).pdf',\
			'__256245_(PLOT)_(1743-12900519)plgl_(150x90)_1440dpi_plot1_izdel_7_NP_3_KS_23(29)_34_(09_06).pdf',
			'__256245_(PLOT)_(1743-12900519)plgl_(150x90)_0dpi_plot1_izdel_7_NP_3_KS_23(29)_34_(09_06).pdf')
	
	for t in test:
		print(getMaterial(t))