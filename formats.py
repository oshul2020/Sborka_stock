from wand.image import Image as WImage
from PIL import Image as PImage 
from PIL import ImageCms
from pathlib import Path
from io import BytesIO, TextIOWrapper
from collections import namedtuple
import zipfile
from rdflib import Graph, Namespace, URIRef, Literal

PImage.MAX_IMAGE_PIXELS = None

class SImageError(Exception): pass

xmp = Namespace("http://ns.adobe.com/xap/1.0/")
cdr = Namespace("http://namespace.corel.com/cdr/metadata/1.0/")
cdrInfo = Namespace("http://namespace.corel.com/cdr/metadata/1.0/fileinfo/")
inFill = Namespace("http://namespace.corel.com/cdr/metadata/1.0/fillInfo/")
inOtl = Namespace ("http://namespace.corel.com/cdr/metadata/1.0/outlineInfo/")
inObj = Namespace("http://namespace.corel.com/cdr/metadata/1.0/objectInfo/")
sub = URIRef('')

Data = namedtuple('Data', ['name', 'data'])
Size = namedtuple('Size', ['width', 'height'])

class SImage(object):
	def __init__(self, path, engine):
		self.path = path
		self.dimention = ()
		self.dpi = 0
		self.format = None
		self.mode = None
		self.layers = 0
		self.engine = engine
		self.info = []
		if engine == 'PILL':
			self.image = PImage.open(self.path)
			self.mode = self.image.mode
			self.layers = self.image.tell() + 1
		elif engine == 'Wand':
			self.image = WImage(filename=self.path)
			self.dpi = self.image.resolution[0]
			self.mode = self.image.colorspace
			self.layers = len(self.image.sequence)
		else:
			self.image = None
		
		
	
	@staticmethod
	def factory(path):
		suffix = path.suffix.lower()
		if suffix == ".tif":
			return TIFImage(path, 'PILL')
		if suffix == ".pdf":
			return PDFImage(path, 'Wand')
		if suffix == ".cdr":
			return CDRImage(path)
		if suffix == ".eps":
			return EPSImage(path, 'PILL')
		if suffix == ".psd":
			return PSDImage(path, 'Wand')			

		raise SImageError('формат не поддерживается')
	
	def getThumb(self, size):
		img_io = BytesIO()
		if self.engine == 'PILL':
			self.image.thumbnail(size)
			self.image.save(img_io, 'jpeg')	
			
		elif self.engine == 'Wand':
			image = self.image
			if len(self.image.sequence) > 1:
				image = WImage(image=self.image.sequence[0])	
			
			image.format = 'jpeg'
			image.transform(resize=f'{size[0]}x{size[1]}')
			image.save(file=img_io)
		
		img_io.seek(0)
		return img_io	
		
	def getInfo(self):
		w,h = self.image.size
		
		if self.dpi == 0: 
			self.dpi = self.image.info['dpi'][0]
			

		x = round((float(w) * 25.4) / self.dpi)
		y = round((float(h) * 25.4) / self.dpi)
		self.dimention = Size(x, y)
		
		self.info.append(Data(name='размер', data=f'{x}x{y} mm'))
		self.info.append(Data(name='пиксели', data=f'{w}x{h} ({self.dpi} dpi)'))
		self.info.append(Data(name='формат', data=self.image.format))
		self.info.append(Data(name='палитра', data=self.mode))
		self.info.append(Data(name='страниц', data=self.layers))	

		try: #PILL
			for inf in self.image.info:
				if inf == 'icc_profile':
					f = io.BytesIO(self.image.info['icc_profile'])
					profile = ImageCms.ImageCmsProfile(f)
					self.info.append(Data(name='профиль', data=ImageCms.getProfileName(profile)))
					continue
					
				self.info.append(Data(name=inf, data=self.image.info[inf]))		
		except:
			pass

		try: #Wand
			for data in self.image.metadata:
				self.info.append(Data(name=data, data=self.image.metadata[data]))
		except:
			pass		

class PSDImage(SImage):
	def __init__(self, path, engine):
		SImage.__init__(self, path, engine)
		
class EPSImage(SImage):
	def __init__(self, path, engine):
		SImage.__init__(self, path, engine)
		
	def getInfo(self):
		self.dpi = 72
		super(EPSImage, self).getInfo()

		return self.info

class TIFImage(SImage):
	def __init__(self, path, engine):
		SImage.__init__(self, path, engine)
		
	def getInfo(self):
		super(TIFImage, self).getInfo()

		i = self.image

		if 258 in i.tag:
			self.info.append(Data(name='глубина цвета', data=i.tag[258]))	
		if 305 in i.tag:	
			self.info.append(Data(name='программа', data=i.tag[305][0]))		
		if 306 in i.tag:	
			self.info.append(Data(name='дата', data=i.tag[306][0]))
		self.info.append(Data(name='компрессия', data=i.info['compression']))
	
		return self.info
	

class CDRImage(SImage):
	def __init__(self, path, engine=None):
		SImage.__init__(self, path, engine)
		self.imageData = None
		
	def getInfo(self):
		archive = zipfile.ZipFile(self.path, 'r')
		item = archive.open('META-INF/metadata.xml')
		xmpFile = TextIOWrapper(item, encoding='utf8').read()
		archive.close()
		
		rdfStart = xmpFile.find('<rdf:RDF')
		rdfEnd = xmpFile.find('</rdf:RDF>')

		g = Graph()
		g.parse(data=xmpFile[rdfStart: rdfEnd + len('</rdf:RDF>')], format='xml')
		
		self.info.append(Data(name='Размер страницы', data=g.value(sub, cdrInfo.PageDimensions)))
		self.info.append(Data(name='Страниц', data=g.value(sub, cdrInfo.NumPages)))
		self.info.append(Data(name='Слои', data=g.value(sub, cdrInfo.NumLayers)))
		
		b = g.value(sub, cdrInfo.Objects)
		self.info.append(Data(name='Объектов', data=g.value(b, inObj.Total)))
		
		items = f'''{g.value(b, inObj.Bitmap)}/{g.value(b, inObj.Polygon)}/
		{g.value(b, inObj.Curve)}/{g.value(b, inObj.Rect)}/{g.value(b, inObj.Ellipse)}/
		{g.value(b, inObj.Text)}'''
		self.info.append(Data(name='Растр/Поли/Кривые/Прямоугольники/Эллипсы/Тексты', data=items))
		
		b = g.value(sub, cdrInfo.FillInfo)
		b = g.value(b, inFill.SpotColors)
		spots = [spot for spot in g.objects(b) if type(spot) == Literal]	
		if spots:	
			self.info.append(Data(name='Заливка Spots', data=', '.join(spots)))
		
		b = g.value(sub, cdrInfo.OutlineInfo)
		b = g.value(b, inOtl.SpotColors)
		spots = [spot for spot in g.objects(b) if type(spot) == Literal]		
		if spots:	
			self.info.append(Data(name='Контур Spots', data=', '.join(spots)))
		
		programm = f'{g.value(sub, cdr.ProductName)} ({g.value(sub, cdr.AppVersion)})'
		self.info.append(Data(name='Программа', data=programm))
		self.info.append(Data(name='Дата', data=g.value(sub, xmp.CreateDate)))
		
		return self.info
	
	def getThumb(self, size):
		if not self.imageData:
			archive = zipfile.ZipFile(self.path, 'r')
			self.imageData = archive.read('previews/thumbnail.png')
			archive.close()
		
		self.image = PImage.open(BytesIO(self.imageData))
		self.engine = 'PILL'
		return super(CDRImage, self).getThumb(size)	
		
		
class PDFImage(SImage):
	def __init__(self, path, engine):
		SImage.__init__(self, path, engine)

if __name__ == '__main__':
	#test
	tests = (
		'd:/Temp/Sborka/sharedfolders/Design/Shira/(13696-12658046).tif',
		'd:/Temp/Sborka/sharedfolders/Design/Shira/dolphin.eps',
		'd:/Temp/Sborka/sharedfolders/Design/Shira/ONYX Quality Evaluation.pdf',
		'd:/Temp/Sborka/sharedfolders/Design/Shira/test1.cdr',
		'd:/Temp/Sborka/sharedfolders/Design/Shira/dv081026.psd'
	)
	for file in tests:
		image = SImage.factory(Path(file))
		i = image.getInfo()
		t = image.getThumb((100,100))
		print(image.path.name)
		
	
	



	
	