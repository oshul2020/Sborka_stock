# -*- coding: utf-8 -*-

from pathlib import Path
from Sborka.config import thumbSize
from Sborka.formats import SImage

def get(file):
	try:	
		image = SImage.factory(Path(file))
		image.getInfo()
		return image
		
	except Exception as e:
		return e	
	
def thumb(file):
	print(file)
	try:	
		image = SImage.factory(Path(file))
		return image.getThumb(thumbSize)
	
	except Exception as e:
		return e	
	
if __name__ == "__main__":
	pass

