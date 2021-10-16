from flask import get_template_attribute
from Sborka.wide.entity import Category, Material, Log, Size
from datetime import timedelta, datetime
from dateutil.relativedelta import *
from sqlalchemy import extract

class Stat:
	def __init__(self, db):
		self.__db = db
	
	def getMaterialTable(self, material_id):
		m = self.__db.query(Material).get(material_id)
		ms = self.__db.query(Material).join(Size)	\
			.filter(Material.category_id==m.category_id,	Material.title==m.title)	\
			.order_by(Size.param_1).all()
		
		
		today = datetime.now()
		yesterday = (today - timedelta(days=1)).date()
		dateFrom = today - timedelta(days=today.weekday(), weeks=1)
		week  = dateFrom.isocalendar()[1]
		dateTill = dateFrom + timedelta(weeks=1)
		
		month_1 = today + relativedelta(months=-1)
		month_2 = today + relativedelta(months=-2)
		
		table_header = (yesterday.strftime('%d/%m'),
						f'{dateFrom.strftime("%d/%m")}-{dateTill.strftime("%d/%m")}',
						today.strftime('%B'), month_1.strftime('%B'), month_2.strftime('%B'),
						'всего за год')
		
		data = {}
		
		#print(type(Log.time))
		for m in ms:
			log_rows = self.__db.query(Log).filter(Log.material_id==m.id, Log.action==0, \
				extract('year', Log.time) == today.year).all()
				
			data[m] = [0,0,0,0,0,0] #writeoff [day,week,month_1,month_2,year]
			for log in log_rows:
				if log.time.date() == yesterday:
					data[m][0] += log.amount
				
				log_year, log_week, log_day  = log.time.isocalendar()	

				if log_week == week:
					data[m][1] += log.amount	
				
				if log.time.month == today.month:
					data[m][2] += log.amount
				
				if log.time.month == month_1.month:
					data[m][3] += log.amount
					
				if log.time.month == month_2.month:
					data[m][4] += log.amount	
				
				data[m][5] += log.amount					
				
					
		
		table = get_template_attribute('w_stat.html', 'stat_material_table')
		title = f'{m.category.title} {m.title} ({m.unit.title})'
		return table(title, data, table_header)	
		
	def getSizeTable(self, material_id):
		data = {} #{month:[total, {week:total}]}
		m = self.__db.query(Material).get(material_id)
		today = datetime.now()
		start_year = today.replace(day=1, month=1)
		
		log_rows = self.__db.query(Log)	\
			.filter(Log.material_id==m.id, Log.action==0,extract('year', Log.time) == today.year).all()	
		
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
		
		table = get_template_attribute('w_stat.html', 'stat_size_table')
		title = f'{m.category.title} {m.title} {m.size} ({m.unit.title})'
		return table(title, data)	

	def getWriteOff(self, period):
		data = {}
		now = datetime.now()
		t = None
		
		if period=='day':
			t = now.replace(hour=0, minute=0, second=0, microsecond=0)
			
		elif period=='work':	
			start = now.replace(hour=8, minute=0, second=0, microsecond=0)
			end = now.replace(hour=20, minute=0, second=0, microsecond=0)
			tonight = now.replace(hour=0, minute=0, second=0, microsecond=0)
			
			if start <= now < end:
				t = start
				
			elif tonight <= now < start:
				t = end - timedelta(days=1)
			else:	
				t = end
				
		elif period == 'week':	
			t = now - timedelta(days=now.weekday(), weeks=0)
			t = t.replace(hour=0, minute=0, second=0, microsecond=0)
		
		elif period == 'month':		
			t = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
				
		res = self.__db.query(Log, Material).join(Material).join(Category)	\
			.filter(Log.action==0,Log.time >= t)	\
			.order_by(Category.sortby) \
			.all()	
			
		for r in res:
			data.setdefault(r.Material.id, {'entity':r.Material, 'amount':0})
			data[r.Material.id]['amount'] += r.Log.amount
				
		return (data, t)	
		
		
		
		