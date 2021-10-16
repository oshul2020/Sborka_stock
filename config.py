# -*- coding: utf-8 -*-

import os
from wand.resource import limits
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

workDays = 3
thumbSize = 600, 600
barType = 'interleaved2of5'

signSizeMM = 7

logsOnPage = 50


if os.name == 'nt':
	workDir = 'sharedfolders/Work'
	shiraDir = 'sharedfolders/Design/Shira'
	signDir = 'sharedfolders/Design/Signed'
	fontPath = 'sharedfolders/Font/arial.ttf'
	dbPath = 'Sborka/stock/db/stock.db'
	dbCifraPath = 'sqlite:///Sborka/db/cifra_stock.db'
	dbWidePath = 'sqlite:///Sborka/db/wide_stock.db'
	dbBusPath = 'sqlite:///Sborka/db/bus.db'
else:
	workDir = '/sharedfolders/Work'
	shiraDir = '/sharedfolders/Design/Shira'
	signDir = '/sharedfolders/Design/Signed'
	#fontPath = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
	fontPath = '/home/alex/sborkaapp/Sborka/static/DINPro-Medium.otf'
	dbPath = '/var/db/stock.db'
	dbCifraPath = 'sqlite:////var/db/cifra_stock.db'
	dbWidePath = 'sqlite:////var/db/wide_stock.db'
	dbBusPath = 'sqlite:////var/db/bus.db'
	
if __name__ == "__main__":
	pass