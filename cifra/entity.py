from sqlalchemy import Table, Column, Integer, DateTime, String, MetaData, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship
from flask import flash
import importlib

Base = declarative_base()

class Unit(Base):
	__tablename__ = 'unit'
	id = Column('unit_id', Integer, primary_key=True)
	title = Column('unit_title', String)
	
	@property
	def serialize(self):
		return {'id': self.id, 'title': self.title}
		
	def __repr__(self):
		return self.title
	
class Density(Base):
	__tablename__ = 'density'
	id = Column('density_id', Integer, primary_key=True)
	density = Column('density_density', Integer)
	
	def __repr__(self):
		if self.density == 0:
			return 'нет'
		return  f"{self.density} г/м\xb2" 

	@property
	def serialize(self):
		return {'id':self.id, 'title':self.__repr__(), 'density':self.density}			

class Size(Base):
	__tablename__ = 'size'
	id = Column('size_id', Integer, primary_key=True)
	title = Column('size_title', String)
	width = Column('size_width', Integer)
	height = Column('size_height', Integer)	
	
	def __repr__(self):
		if self.width == 0 and self.height == 0:
			return self.title
		elif self.title:
			return  f"{self.width} x {self.height} мм ({self.title})"
		return 	f"{self.width} x {self.height} мм"
		
	@property
	def serialize(self):
		return {'id':self.id, 'title':self.__repr__(), 'width':self.width, 'height':self.height}	
	
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

class Category(Base):
	__tablename__ = 'category'
	id = Column('category_id', Integer, primary_key=True)
	title = Column('category_title', String)
	process = Column('category_process', Integer)
	active = Column('category_active', Integer)
	sortby = Column('category_sortby', Integer)
	materials = relationship("Material")
	
	@property
	def serialize(self):
		return {'id': self.id, 'title': self.title}
	
class Material(Base):
	__tablename__ = 'material'
	id = Column('material_id', Integer, primary_key=True)
	title = Column('material_title', String)
	active = Column('material_active', Integer, default=0)
	amount = Column('material_amount', Integer, default=0)
	minimum = Column('material_minimum', Integer, default=1)
	category_id = Column('category_id', Integer, ForeignKey('category'))
	unit_id = Column('unit_id', Integer, ForeignKey('unit'))
	size_id = Column('size_id', Integer, ForeignKey('size'))
	density_id = Column('density_id', Integer, ForeignKey('density'))
	category = relationship('Category')
	size = relationship('Size')
	unit = relationship('Unit')
	density = relationship('Density')
	
	
	@property
	def serialize(self):
		return {
			'id': self.id, 'title': self.title, 'active': self.active, 'amount': self.amount,
			'unit': self.unit.serialize, 'size': self.size.serialize,
			'density': self.density.serialize, 'category': self.category.serialize
		}
	
	@property
	def part_serialize(self):
		return {
			'id': self.id, 'title':self.__repr__()
		}	
	
	def __repr__(self):
		return  f"{self.category.title} {self.title} {self.size}" 

class Log(Base):
	__tablename__ = 'log'
	id = Column('log_id', Integer, primary_key=True)
	title = Column('log_title', String)
	action = Column('log_action', Integer)
	amount = Column('log_amount', Integer)
	info = Column('log_info', String)
	time = Column('log_time', DateTime)
	material_id = Column('material_id', Integer, ForeignKey('material'))
	user_id = Column('user_id', Integer, ForeignKey('user'))
	material = relationship('Material')
	user = relationship('User')


def crudPost(db, request, className):
	columns = request.form.to_dict()
	id = columns.pop('id')
	cmd = columns.pop('cmd')
		
	lib = importlib.import_module('Sborka.cifra.entity')
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
		flash(e.orig, category='danger')
		db.rollback()	
		
def get_active_materials(db, category_id):
	materials = db.query(Material) \
	.join(Material.density, Material.size) \
	.filter(Material.category_id==category_id, Material.active) \
	.order_by(Density.density, Material.title, Size.width)	
			
	data = {}
	for material in materials:
		data.setdefault(material.title, []).append(material)
	
	return data			