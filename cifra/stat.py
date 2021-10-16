from flask import get_template_attribute
from Sborka.cifra.entity import Material, Log, Size
from datetime import timedelta, datetime
from dateutil.relativedelta import *

class Stat:
	def __init__(self, db):
		self.__db = db
	
	def getDensityTable(self, material_id):
		material = self.__db.query(Material).get(material_id)
		materials = self.__db.query(Material).join(Size)	\
			.filter(Material.active,
					Material.category_id==material.category_id,
					Material.density_id==material.density_id,
					Material.title==material.title)	\
			.order_by(Size.width).all()
		
		
		today = datetime.now()
		yesterday = (today - timedelta(days=1)).date()
		
		dateFrom = today - timedelta(days=today.weekday(), weeks=1)
		week  = dateFrom.isocalendar()[1]
		dateTill = dateFrom + timedelta(weeks=1)
		month = today + relativedelta(months=-1)
		
		table_header = (yesterday.strftime('%d/%m'),
						f'{dateFrom.strftime("%d/%m")}-{dateTill.strftime("%d/%m")}',
						month.strftime('%B'),
						str(today.year),
						'всего')
		
		data = {}

		for m in materials:
			log_rows = self.__db.query(Log).filter(Log.material_id==m.id, Log.action==0).all()
			data[m] = [0,0,0,0,0] #writeoff [day,week,month,year,all]
			for log in log_rows:
				if log.time.date() == yesterday:
					data[m][0] += log.amount
				
				log_year, log_week, log_day  = log.time.isocalendar()	

				if log_week == week:
					data[m][1] += log.amount	
				
				if log.time.month == month.month:
					data[m][2] += log.amount
				
				if log_year == today.year:
					data[m][3] += log.amount					
				
				data[m][4] += log.amount	
		
		table = get_template_attribute('c_stat.html', 'stat_density_table')
		title = f'{material.category.title} {material.title} ({material.unit.title})'
		return table(title, data, table_header)	
		
	def getMaterialTable(self, material_id):
		data = {} #{month:[total, {week:total}]}
		material = self.__db.query(Material).get(material_id)
		start_year = datetime.now().replace(day=1, month=1)
		
		log_rows = self.__db.query(Log)	\
			.filter(Log.material_id==material_id, Log.action==0, Log.time >= start_year).all()	
		
		for log in log_rows:
			month =log.time.strftime('%B')
			week = log.time.isocalendar()[1]
			weekStart = log.time - timedelta(days=log.time.weekday())
			weekEnd = weekStart +  timedelta(days=6)
			name = f'{week}: ({weekStart.strftime("%d-%m-%y")} - {weekEnd.strftime("%d-%m-%y")})'
			
			data.setdefault(month, [0,{}])	
			data[month][0] += log.amount
			
			weeks = data[month][1]
			weeks.setdefault(name, 0)
			weeks[name] += log.amount
		
		table = get_template_attribute('c_stat.html', 'stat_material_table')
		title = f'{material.category.title} {material.title} {material.size} ({material.unit.title})'
		return table(title, data)		
		