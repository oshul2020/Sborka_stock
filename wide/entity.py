from sqlalchemy import Table, Column, Integer, DateTime, String, MetaData, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship
from flask import flash
import importlib, datetime

Base = declarative_base()



class Category(Base):
	__tablename__ = 'category'
	id = Column('category_id', Integer, primary_key=True)
	title = Column('category_title', String)
	active = Column('category_active', Integer)
	sortby = Column('category_sortby', Integer)
	
	@property
	def serialize(self):
		return {'id': self.id, 'title': self.title}
 
class Size(Base):
	__tablename__ = 'size'
	id = Column('size_id', Integer, primary_key=True)
	title = Column('size_title', String)
	param_1 = Column('size_p1', Integer)
	param_2 = Column('size_p2', Integer)
	category_id = Column('category_id', Integer, ForeignKey('category'))
	category = relationship('Category')
	
	@property
	def serialize(self):
		return {'id': self.id, 'title': self.title}
		
	def __repr__(self):
		return self.title		

class Symbol(Base):
	__tablename__ = 'symbol'
	id = Column('symbol_id', Integer, primary_key=True)
	title = Column('symbol_title', String)
	category_id = Column('category_id', Integer, ForeignKey('category'))
	category = relationship('Category')
	material = relationship('Material')
	
	@property
	def serialize(self):
		return {'id': self.id, 'title': self.title}
		
	def __repr__(self):
		return self.title

class Unit(Base):
	__tablename__ = 'unit'
	id = Column('unit_id', Integer, primary_key=True)
	title = Column('unit_title', String)
	
	@property
	def serialize(self):
		return {'id': self.id, 'title': self.title}
		
	def __repr__(self):
		return self.title	
	
class User(Base):
	__tablename__ = 'user'
	id = Column('user_id', Integer, primary_key=True)
	title = Column('user_title', String)
	hash = Column('user_hash', String)
	admin = Column('user_admin', Integer)
	
	@property
	def serialize(self):
		return {'id': self.id, 'title': self.title}
		
	def __repr__(self):
		names = self.title.split()
		if len(names) == 1:
			return self.title
		
		return f'{names[1]} {names[0][0]}.'	

class Material(Base):
	__tablename__ = 'material'
	id = Column('material_id', Integer, primary_key=True)
	title = Column('material_title', String)
	info = Column('material_info', String)
	amount = Column('material_amount', Integer)
	minimal = Column('material_minimal', Integer)
	active = Column('material_active', Integer)
	capacity = Column('material_capacity', Integer)
	category_id = Column('category_id', Integer, ForeignKey('category'))
	symbol_id = Column('symbol_id', Integer, ForeignKey('symbol'))
	size_id = Column('size_id', Integer, ForeignKey('size'))
	unit_id = Column('unit_id', Integer, ForeignKey('unit'))
	category = relationship('Category')
	size = relationship('Size')
	unit = relationship('Unit')
	symbol = relationship('Symbol')
	
	@property
	def size_title(self):
		return self.size.title
		
	@property
	def symbol_title(self):
		return self.symbol.title	
	
	@property
	def serialize(self):
		return {
			'id': self.id, 'title': self.title, 'active': self.active, 'amount': self.amount, 'info': self.info, 
			'minimal': self.minimal, 'capacity': self.capacity,	'symbol': self.symbol.serialize,		
			'unit': self.unit.serialize, 'size': self.size.serialize, 'category': self.category.serialize
		}
		
	@property
	def htmlAttr(self):
		return (f'_id="{self.id}" title="{self.title}" category="{self.category_id}" '
				f'symbol="{self.symbol_id}" size="{self.size_id}" unit="{self.unit_id}" '
				f'active="{self.active}" minimal="{self.minimal}" capacity="{self.capacity}" '
				f'amount="{self.amount}" info="{self.info}" '	
				)

class Log(Base):
	__tablename__ = 'log'
	id = Column('log_id', Integer, primary_key=True)
	action = Column('log_action', Integer)
	amount = Column('log_amount', Integer)
	stock = Column('log_stock', Integer)
	time = Column('log_time', DateTime)
	material_id = Column('material_id', Integer, ForeignKey('material'))
	user_id = Column('user_id', Integer, ForeignKey('user'))
	info = Column('log_info', String)
	material = relationship('Material')
	user = relationship('User')				
				
def crudPost(db, request, className):
	columns = request.form.to_dict()
	id = columns.pop('id')
	cmd = columns.pop('cmd')
		
	lib = importlib.import_module('Sborka.wide.entity')
	Entity = getattr(lib, className)
	try:	
		if cmd == 'delete':
			entity = db.query(Entity).get(id)
			db.delete(entity)
			message = 'Запись удалена'
				
		else:
			if cmd == 'insert':	
				entity = Entity()
				db.add(entity)
				message = 'Запись добавлена'
		
			elif cmd == 'update':	
				entity = db.query(Entity).get(id)
				message = 'Запись изменена'
	
			for column, value in columns.items():
				setattr(entity, column, value)	
				
		db.commit()
		flash(message, category='success')
	
	except Exception as e:	
		#flash(e.orig, category='danger')
		flash(e, category='danger')
		db.rollback()

class Sorder(Base):
	__tablename__ = 'sorder'
	id = Column('sorder_id', Integer, primary_key=True)
	title = Column('sorder_title', String)
	timeopen = Column('sorder_timeopen', DateTime)
	timeclose = Column('sorder_timeclose', DateTime)
	comment = Column('sorder_comment', String)
	status = Column('sorder_status', Integer)
	user_id = Column('user_id', Integer, ForeignKey('user'))
	user = relationship('User')	
	
	@property
	def serialize(self):
		return {'id': self.id, 'title': self. __repr__()}
		
	def __repr__(self):
		return f'Заказ №{self.id}'

class Request(Base):
	__tablename__ = 'request'
	id = Column('request_id', Integer, primary_key=True)
	amount = Column('request_amount', Integer)
	result = Column('request_result', Integer)
	timeopen = Column('request_timeopen', DateTime)
	timeclose = Column('request_timeclose', DateTime)
	comment = Column('request_comment', String)
	material_id = Column('material_id', Integer, ForeignKey('material'))
	sorder_id = Column('sorder_id', Integer, ForeignKey('sorder'),default=0)
	user_id = Column('user_id', Integer, ForeignKey('user'))
	material = relationship('Material')	
	sorder = relationship('Sorder')	
	user = relationship('User')	
	
	@property
	def serialize(self):
		return {'id': self.id, 'amount': self.amount, 'result': self.result}
		
	@property
	def htmlAttr(self):
		return (f'_id="{self.id}" '
				f'title="({self.material.symbol.title}) {self.material.category.title} {self.material.title} {self.material.size.title}" '	
				f'unit="{self.material.unit.title}" stock="{self.material.amount}" '
				f'amount="{self.amount}"')	

def get_active_materials(db, category_id):
	materials = db.query(Material) \
			.join(Material.symbol) \
			.join(Material.size) \
			.filter(Material.category_id==category_id, Material.active) \
			.order_by(Symbol.id, Size.param_1) \
			.all()
			
	data = {}
	for material in materials:
		data.setdefault(material.title, []).append(material)
	
	return data	
	
class XYTable():
	x_header = []
	y_header = []
	array = None
		
	def __init__(self, x_name, y_name, data):
		for entity in data:
			x = getattr(entity, x_name)
			y = getattr(entity, y_name)
			if x not in self.x_header:
				self.x_header.append(x)
			if y not in self.y_header:
				self.y_header.append(y)	
				
		self.array = [ [ None for i in range(len(self.x_header)) ] for j in range(len(self.y_header)) ]	
		#print(self.x_header)
		#print(self.y_header)
		
		for entity in data:
			i = self.y_header.index(getattr(entity, y_name))
			j = self.x_header.index(getattr(entity, x_name))	
			#print(i,j)
			self.array[i][j] = entity
		
		#print(self.array)
			