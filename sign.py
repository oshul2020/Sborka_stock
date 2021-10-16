# -*- coding: utf-8 -*-

from pathlib import Path, PurePath
from PIL import Image, ImageDraw, ImageFont
import time
from treepoem import generate_barcode
from Sborka import config, parser
from urllib.parse import unquote

class SignFile:
	def __init__(self):
		self.path = None
		self.signTime = None
		self.comment = None

def _getmtime(entry):
	return entry.stat().st_mtime

def signBox(mode, height, text, number, backgroundColor):
	x = margin = 15
	p = (height * 20) // 100
	
	#options={'spaceratio':1, 'barratio':1, 'width':3, 'height': (height - p) * 0.006,}
	options={'barratio':1, 'width':2.2, 'height': (height) * 0.006,}
	barCode = generate_barcode(barcode_type=config.barType, data=number, options=options)
	barCode = barCode.convert('CMYK')
	barW, barH = barCode.size
	
	font = ImageFont.truetype(config.fontPath, height - p)
	width = margin + barW + margin + font.getsize(text)[0]
	img = Image.new(mode, (width, height), color=backgroundColor)
	draw = ImageDraw.Draw(img)
	img.paste(barCode,(x,p//2))
	x += barW + margin
	draw.text((x, 0), text=text, font=font, fill=~backgroundColor)	
	
	return img.convert("L") #to grayscale
	
def signFile(file, size, add2Name):
	print(file)
	img = Image.open(file)
	p = parser.Name(file.name)
	barText = p.getOrder()
	
	saveName = file.name
	
	if add2Name:
		saveName = f'{file.stem}_{add2Name}{file.suffix}'
		
	savePath = Path(config.signDir, saveName)
	signHMM = size
	w, h = img.size
	resX, resY = img.info['dpi']
	signH = round((signHMM * resX) / 25.4)	

	if img.mode == 'CMYK':
		backgroundColor = 0x000000
	else:
		backgroundColor = 0xFFFFFF
			
	if w < h:
		sgn = signBox(img.mode, signH, saveName, barText, backgroundColor)	
		sgnW, sgnH = sgn.size
		i = Image.new(img.mode, (w, h + signH * 2), color=backgroundColor)
		i.paste(img, (0, signH))
		i.paste(sgn, (0,0))	
		i.paste(sgn.transpose(Image.ROTATE_180), (w - sgnW, i.size[1] - sgnH))	
	
	else:
		sgn = signBox(img.mode, signH, saveName, barText, backgroundColor)	
		sgnW, sgnH = sgn.size
		i = Image.new(img.mode, (w + signH * 2, h), color=backgroundColor)
		i.paste(img, (signH, 0))
		i.paste(sgn.transpose(Image.ROTATE_90), (w + sgnH, h - sgnW))	
		i.paste(sgn.transpose(Image.ROTATE_270), (0, 0))	
	
	#del i.tag_v2[34377]
	#del i.tag_v2[33723]
	#del i.tag_v2[700]
		
	i.save(str(savePath), compression='tiff_deflate', dpi=img.info['dpi'])
	return savePath
		
def shira():
	try:
		walk = Path(config.shiraDir)
		found = walk.glob('**/*')
		result = [file for file in found if file.is_file()]
		return sorted(result, key=_getmtime, reverse=True)
	except Exception as e:
		return e
		
def perform(files, add2Name):
	result = []
	
	for file in files:
		start = time. time()
		f = Path(unquote(unquote(file)))
		sFile = SignFile()
		sFile.path = f
		try:
			newFile = signFile(f, config.signSizeMM, add2Name)		
			sFile.path = newFile
			end = time.time()
			sFile.signTime = f'{end-start:.2f} сек.'
		except Exception as e:
			sFile.comment = e
			#return e
				
		result.append(sFile)
		
	
	
	
	
	
	
	
	return result
	#return f'{end-start:.2f} сек.'
	

#	img.thumbnail(thumbSize)
#	img.save(thumb, 'jpeg')	

	

if __name__ == "__main__":
	get()