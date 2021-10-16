from functools import wraps
import hashlib
import importlib
import json
from flask import Blueprint, render_template, request, redirect, session, flash, jsonify, get_template_attribute, g 
from sqlalchemy import create_engine, cast, Integer, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.serializer import loads, dumps
from datetime import date, timedelta, datetime
from flask_sqlalchemy import BaseQuery
from Sborka import config
from Sborka.wide.entity import Category, Log, Material, Request, Size, Sorder, Symbol, Unit, User
from Sborka.wide.entity import crudPost, get_active_materials, XYTable
from Sborka.wide.stat import Stat

app_wide = Blueprint('app_wide', __name__, template_folder='wide_templates')

Base = declarative_base()

engine = create_engine(config.dbWidePath, connect_args={'check_same_thread': False},echo=False)
Base.metadata.create_all(engine)
db = Session(engine)

actions = ('списание', 'получение', 'возврат', 'инвентаризация', 'заказ', 'подрядчик')

def clear_session():
	try:
		session.pop('wide_admin', None)
		session.pop('wide_user', None)
	except:
		pass

def admin_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if session.get('wide_admin') is None:
			return redirect('/wide')
			
		return f(*args, **kwargs)
	return decorated_function
	
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if session.get('wide_user') is None:
			return redirect('/wide/login')
			
		return f(*args, **kwargs)
	return decorated_function

@app_wide.route('/wide', methods=['GET', 'POST'])
def w_index():
	#return render_template('layout_timeout.html')
	#return render_template('layout_inventory.html')
	categories = db.query(Category).filter(Category.active).order_by(Category.sortby).all()
	return render_template('w_stock.html', categories=categories)

@app_wide.route('/wide/log', methods=['GET', 'POST'])
def w_log():
	query = BaseQuery(Log, db).order_by(Log.id.desc())
	if request.method == "GET":
		return render_template('w_log.html', paginate=query.paginate(1, config.logsOnPage),
				actions=actions, 
				categories = db.query(Category).order_by(Category.sortby).all(),
				users = db.query(User).all())

	action = request.form.get('action')
	user_id = request.form.get('user_id')
	category_id = request.form.get('category_id')
	material_title = request.form.get('material')
	material_id = request.form.get('material_id')
		
	if action:
		query = query.filter(Log.action==action)
	
	if user_id:
		query = query.filter(Log.user_id==user_id)
		
	if category_id:
		query = query.join(Material).filter(Material.category_id==category_id)
	
	if material_title:
		query = query.join(Material).filter(Material.title==material_title)
	
	if material_id:
		query = query.join(Material).filter(Material.id==material_id)	
		
	page = request.form.get('page', type=int)
	paginate= query.paginate(page, config.logsOnPage)
	table = get_template_attribute('w_log_table.html', 'table')
	return table(paginate, actions)


@app_wide.route("/wide/sorder", methods=["GET", "POST"])
def w_sorder():
	if request.method == "POST":
		if not 'wide_admin' in session:
			return ('!admin',400) 
				
		cmd = request.form.get('cmd')
		try:
			if cmd == 'close':
				order_id = request.form.get('order_id')
				o=db.query(Sorder).get(order_id)
				o.timeclose = datetime.now()
				o.status = 1
				o.user_id = session['wide_user'].id
				db.commit()
				orders = db.query(Sorder).order_by(Sorder.timeopen.desc()).all()
				table = get_template_attribute('w_sorder.html', 'table')
				return table(orders)
			
		except Exception as e:	
			flash('ошибка: заказ не закрыт', category='danger')
		
	else:	
		order_id = request.args.get('id')
		if order_id:
			order = db.query(Sorder).get(order_id)
			requests = db.query(Request) \
				.join(Material) \
				.join(Size) \
				.join(Category) \
				.filter(Request.sorder_id==order_id) \
				.order_by(Category.sortby, Material.symbol_id, Size.param_1) \
				.all()
			
			data = {}			
			for req in requests:
				data.setdefault(req.material.title, []).append(req)	
			
			return render_template('w_sorder_content.html', data=data, order=order)
		
	orders = db.query(Sorder).order_by(Sorder.timeopen.desc()).all()
	categories = db.query(Category).order_by(Category.sortby).all()
	return render_template('w_sorder.html', orders=orders, categories=categories)

@app_wide.route("/wide/login", methods=["GET", "POST"])
def w_login():
	clear_session()
	if request.method == "POST":
		passw = request.form.get('password')
		hash = hashlib.md5(passw.encode('utf-8')).hexdigest()
		try:
			user = db.query(User).filter(User.hash == hash).one()
			session['wide_user'] = user
			if user.admin:
				session['wide_admin'] = user
			return redirect('/wide')	
					
		except Exception as e:	
			flash('ошибка: пользователь не определен', category='danger')
			return render_template('w_login.html')	
	else:
		return render_template('w_login.html')

@app_wide.route("/wide/logout")
def w_logout():
	clear_session()
	return redirect("/wide")	
	
@app_wide.route('/wide/jdata', methods=['POST'])
def w_jdata():
	cmd = request.form.get('cmd')
	if cmd == 'category':
		data = {}
		category_id = request.form.get('category_id')
		childs = request.form.getlist('childs[]')	
		if 'size' in childs:
			sizes = db.query(Size).filter(Size.category_id==category_id).order_by(Size.param_1).all()
			data['size'] = [size.serialize for size in sizes]
		
		if 'symbol' in childs:	
			symbols = db.query(Symbol).filter(Symbol.category_id==category_id).order_by(Symbol.title).all()
			data['symbol'] = [symbol.serialize for symbol in symbols]
		
		if 'material' in childs:
			materials = db.query(Material) \
				.join(Material.category) \
				.join(Material.size) \
				.join(Material.symbol) \
				.filter(Material.category_id==category_id) \
				.order_by(Category.sortby, Symbol.id, Size.param_1)		
			data['material'] = [material.serialize for material in materials]
			
		return jsonify(data)
	
	if cmd == 'info':
		entity = request.form.get('entity')
		id = request.form.get('id')
		lib = importlib.import_module('Sborka.wide.entity')
		Entity = getattr(lib, entity)
		return	jsonify(db.query(Entity).get(id).serialize) 

	if cmd == 'orders_material':
		material_id = request.form.get('material_id')
		result = db.query(Sorder, Request).join(Request)	\
			.filter(Request.material_id==material_id, Sorder.status==0).all()
		
		return jsonify([{'Sorder':r.Sorder.serialize, 'Request':r.Request.serialize} for r in result])
	
@app_wide.route('/wide/data', methods=['GET', 'POST'])
def w_data():
	cmd = request.form.get('cmd')	
	if cmd == 'symbols_category':
		category_id = request.form.get('category_id')
		table = get_template_attribute('w_symbol.html', 'table')
		return table(db.query(Symbol).filter(Symbol.category_id==category_id).all())
	
	if cmd == 'sizes_category':
		category_id = request.form.get('category_id')
		table = get_template_attribute('w_size.html', 'table')
		return table(db.query(Size).filter(Size.category_id==category_id).order_by(Size.param_1).all())	
		
	if cmd == 'materials_category':
		category_id = request.form.get('category_id')
		table = get_template_attribute('w_material.html', 'table')
		materials = db.query(Material) \
			.join(Material.symbol) \
			.join(Material.size) \
			.filter(Material.category_id==category_id) \
			.order_by(Symbol.id, Size.param_1) \
			.all()
		return table(materials)	
	
	if cmd == 'requests_order':
		order_id = request.form.get('order_id')
		order = db.query(Sorder).get(order_id)
		table = get_template_attribute('w_sorder.html', 'infoTable')
		requests = db.query(Request) \
			.join(Material) \
			.filter(Request.sorder_id==order_id) \
			.order_by(Material.symbol_id) \
			.all()
		return table(requests, order)		
		
	if cmd == 'stock':
		category_id = request.form.get('category_id')
		data = get_active_materials(db, category_id)	
		table = get_template_attribute('w_stock.html', 'table')
		f = get_template_attribute('w_base.html', 'flashed')
		return jsonify((table(data),f()))
		
	if cmd == 'orders_category':	
		category_id = request.form.get('category_id')
		orders = db.query(Sorder) \
			.join(Request)	\
			.join(Material)	\
			.filter(Material.category_id==category_id)	\
			.order_by(Sorder.timeopen.desc())
			
		table = get_template_attribute('w_sorder.html', 'table')
		return table(orders.all())	
		
	if cmd == 'orders_materialtitle':	
		title = request.form.get('material_title')
		orders = db.query(Sorder) \
			.join(Request)	\
			.join(Material)	\
			.filter(Material.title==title)	\
			.order_by(Sorder.timeopen.desc())
			
		table = get_template_attribute('w_sorder.html', 'table')
		return table(orders.all())		
		
	if cmd == 'orders_material':	
		material_id = request.form.get('material_id')
		orders = db.query(Sorder) \
			.join(Request)	\
			.join(Material)	\
			.filter(Material.id==material_id)	\
			.order_by(Sorder.timeopen.desc())
			
		table = get_template_attribute('w_sorder.html', 'table')
		return table(orders.all())			
	
	return 'error'	

@app_wide.route('/wide/category', methods=['GET', 'POST'])
@admin_required		
def w_category():
	if request.method == "POST":	
		crudPost(db, request, 'Category')
		mainFrame = get_template_attribute('w_category.html', 'mainFrame')
		return mainFrame(db.query(Category).order_by(Category.sortby).all())
		
	return render_template('w_category.html', 
		categories = db.query(Category).order_by(Category.sortby).all())

@app_wide.route('/wide/material', methods=['GET', 'POST'])
@admin_required	
def w_material():
	materials = db.query(Material) \
			.join(Material.category) \
			.join(Material.size) \
			.join(Material.symbol) \
			.order_by(Category.sortby, Symbol.id, Size.param_1) 

	if request.method == "POST":
		crudPost(db, request, 'Material')
		filter = request.form.get('category_filter')
		if filter:
			materials = materials.filter(Material.category_id == filter)
			
		table = get_template_attribute('w_material.html', 'table')
		f = get_template_attribute('w_base.html', 'flashed')
		return jsonify((table(materials.all()),f()))
	
	c = db.query(Category).order_by(Category.sortby).all()
	return render_template('w_material.html', 
		materials = materials.all(), 
		categories = db.query(Category).order_by(Category.sortby).all(),
		units = db.query(Unit).all()
	)		

@app_wide.route('/wide/stock', methods=['GET', 'POST'])
def w_stock():
	if request.method == "POST":
		if not 'wide_user' in session:
			return ('!user',400)	
		
		try:
			message = ''
			alert = ''
			cmd = request.form.get('cmd')
			id = request.form.get('id')
			amount = request.form.get('amount')
			info = request.form.get('info')
			material = db.query(Material).get(id)
			sorder_id = request.form.get('sorder_id')
			
			log = Log()
			log.stock = material.amount
			log.amount = amount
			log.user_id = session['wide_user'].id
			log.time = datetime.now()
			log.material_id = material.id
			
			if cmd == 'order':
				r = Request()
				r.material = material
				r.amount = amount
				r.result = 0
				r.timeopen = datetime.now()
				r.user_id = session['wide_user'].id
				message = 'материал добавлен в список заявок'
				
				if info:
					r.comment = info
				db.add(r)
			
			elif cmd == 'writeOff':
				material.amount = Material.amount - amount
				message = 'списание выполнено'
				if material.amount == 0:
					alert = 'На складе больше нет данного материала. Может сделать заявку?'
					
				log.action = 0
				if info:
					log.info = info
				db.add(log)
			
			elif cmd == 'add':
				if not 'wide_admin' in session:
					return ('!admin',400)	
					
				material.amount = Material.amount + amount
				message = 'материал принят'	
				log.action = 1
				db.add(log)
				if sorder_id:
					r = db.query(Request).filter(Request.sorder_id==sorder_id, Request.material_id==id).one()
					r.result = Request.result + amount
					r.timeclose = datetime.now()
					#r.user_id = session['wide_user'].id
					log.info = f'Заказ №{sorder_id}'
					if info:
						r.comment = Request.comment + '; ' + info
				
			elif cmd == 'update':
				if not 'wide_admin' in session:
					return ('!admin',400)	
				material.amount = amount
				message = 'количество изменено'	
				log.action = 3
				if info:
					log.info = info
				db.add(log)
				
			else:
				return (cmd,400)	
			
			
			db.commit()
			flash(message, category='success')
			
			category_id = request.form.get('category_id')
			data = get_active_materials(db, category_id)	
			table = get_template_attribute('w_stock.html', 'table')
			f = get_template_attribute('w_base.html', 'flashed')
			return jsonify((table(data),f(),alert))
			
		except Exception as e:	
			db.rollback()
			#flash(f'ошибка: ({e.orig})', category='danger')
			flash(f'ошибка: ({e})', category='danger')	
			f = get_template_attribute('w_base.html', 'flashed')
			return (f(), 400)	
			
	return redirect('/wide')	


@app_wide.route('/wide/request', methods=['GET', 'POST'])
def w_request():
	requests = db.query(Request).filter(Request.sorder_id==0)

	if request.method == "POST":
		try:
			message = ''
			cmd = request.form.get('cmd')
			if cmd == 'order_create':
				if not 'wide_admin' in session:
					return ('!admin',400)
				
				o = Sorder()
				o.timeopen = datetime.now()
				o.user_id = session['wide_user'].id
				o.status = 0
				db.add(o)
				db.commit()
				db.query(Request).filter(Request.sorder_id==0).update({Request.sorder_id: o.id})
				db.commit()
				flash(f'заказ {o.id} создан', category='success')
				return('200')
			
			elif cmd == 'reset_order':
				if not 'wide_admin' in session:
					return ('!admin',400)
				id = request.form.get('request_id')
				r = db.query(Request).get(id)
				if r.result != 0:
					return ('заявка уже получена',400)
				r.sorder_id = 0
				db.commit()
				flash('заявка удалена из заказа', category='success')
				return('200')
			
			elif cmd == 'delete':
				if not 'wide_admin' in session:
					return ('!admin',400)
				
				message = 'запись удалена'	
				id = request.form.get('id')
				r = db.query(Request).get(id)
				db.delete(r)
			
			elif cmd == 'update':
				if not 'wide_user' in session:
					return ('вход на склад не выполнен',400)	
				
				message = 'количество изменено'		
				id = request.form.get('id')
				amount = request.form.get('amount')
				r = db.query(Request).get(id)
				r.amount = amount
				r.user_id = session['wide_user'].id
				r.timeopen = datetime.now()
				
			db.commit()
				
			flash(message, category='success')
			table = get_template_attribute('w_request.html', 'table')
			f = get_template_attribute('w_base.html', 'flashed')
			return jsonify((table(requests.all()),f()))
		
		except Exception as e:	
			db.rollback()
			flash(f'ошибка: ({e.orig})', category='danger')
			#flash(f'ошибка: ({e})', category='danger')	
			f = get_template_attribute('w_base.html', 'flashed')
			return (f(), 400)			
		
	return render_template('w_request.html', requests=requests.all())
	
	

@app_wide.route('/wide/size', methods=['GET', 'POST'])
@admin_required	
def w_size():
	if request.method == "POST":
		crudPost(db, request, 'Size')
		sizes = db.query(Size)
		filter = request.form.get('category_filter')
		if filter:
			sizes = sizes.filter(Size.category_id == filter).order_by(Size.param_1)
			
		table = get_template_attribute('w_size.html', 'table')
		f = get_template_attribute('w_base.html', 'flashed')
		return jsonify((table(sizes.all()),f()))
	
	s = db.query(Size).order_by(Size.category_id, Size.param_1).all()
	c = db.query(Category).order_by(Category.sortby).all()
	return render_template('w_size.html', sizes = s, categories = c)		
		
@app_wide.route('/wide/symbol', methods=['GET', 'POST'])
@admin_required	
def w_symbol():
	if request.method == "POST":
		crudPost(db, request, 'Symbol')
		symbols = db.query(Symbol)
		filter = request.form.get('category_filter')
		if filter:
			symbols = symbols.filter(Symbol.category_id == filter)
			
		table = get_template_attribute('w_symbol.html', 'table')
		f = get_template_attribute('w_base.html', 'flashed')
		return jsonify((table(symbols.all()),f()))
	
	s = db.query(Symbol).all()
	c = db.query(Category).order_by(Category.sortby).all()
	return render_template('w_symbol.html', symbols = s, categories = c)	

@app_wide.route('/wide/unit', methods=['GET', 'POST'])
@admin_required	
def w_unit():
	if request.method == "POST":
		crudPost(db, request, 'Unit')

		mainFrame = get_template_attribute('w_unit.html', 'mainFrame')
		return mainFrame(db.query(Unit).all())
	
	return render_template('w_unit.html', units = db.query(Unit).all())	

@app_wide.route('/wide/user', methods=['GET', 'POST'])
@admin_required	
def w_user():
	if request.method == "POST":
		cmd = request.form.get('cmd')
		crudPost(db, request, 'User')

		mainFrame = get_template_attribute('w_user.html', 'mainFrame')
		return mainFrame(db.query(User).all())
	
	return render_template('w_user.html', users = db.query(User).all())		
	
@app_wide.route('/wide/all', methods=['GET', 'POST'])
@admin_required	
def w_all():
	data = {}
	categories = db.query(Category).order_by(Category.sortby).all()
	for category in categories:
		materials = db.query(Material) \
				.join(Material.symbol) \
				.join(Material.size) \
				.filter(Material.category_id==category.id)	\
				.order_by(Symbol.id, Size.param_1) \
				.all()
		m = {}
		for material in materials:
			m.setdefault(material.title, []).append(material)
		
		data.setdefault(category.title, []).append(m)
	
	return render_template('w_all.html', data=data)
	
@app_wide.route('/wide/stat', methods=['GET', 'POST'])
def w_stat():
	if request.method == "GET":
		if 'period' in request.args:
			period = request.args.get('period')
			res = Stat(db).getWriteOff(period)
			return render_template('w_report.html', materials=res[0], date=res[1])

	cmd = request.form.get('cmd')	
	material_id = request.form.get('material_id')
	if cmd == 'size':
		return Stat(db).getSizeTable(material_id)

	if cmd == 'material':
		return Stat(db).getMaterialTable(material_id)
	
	return 'stat'		

@app_wide.route('/wide/search', methods=['GET', 'POST'])
def w_search():
	text = request.form.get('text')
	if text:
		search = f'%{text}%'
			
		materials = db.query(Material)	\
			.join(Symbol)	\
			.join(Size)		\
			.filter(Material.active)	\
			.filter(or_(Material.title.like(search), Symbol.title.like(search), Size.title.like(search))) \
			.order_by(Symbol.id, Size.param_1) \
			.all()
		
		data = {}		
		f = get_template_attribute('w_base.html', 'flashed')
		
		if len(materials) == 0:
			flash(f'поиск: {text} нет результатов.', category='danger')
			return (f(), 400)		
			
		for material in materials:
			data.setdefault(material.title, []).append(material)	
		
		table = get_template_attribute('w_stock.html', 'table')
		flash(f'поиск: {text}', category='success')
		return jsonify((table(data),f()))	
			
		
	return ('!text', 400)			
	
@app_wide.route('/wide/order_template', methods=['GET', 'POST'])
#@admin_required	
def w_order_template():
	data = {}
	categories = db.query(Category).order_by(Category.sortby).all()
	print(categories)
	for category in categories:
		materials = db.query(Material) \
				.join(Material.symbol) \
				.join(Material.size) \
				.filter(Material.category_id==category.id)	\
				.order_by(Symbol.id, Size.param_1) \
				.all()
				
		m = {str(material.id): material for material in materials}
		data.setdefault(category.title, m)
	
	
	
	#t = XYTable('symbol_title', 'size_title', data['пленка'])
	
	return render_template('w_order_template.html', data=data, now=date.today().strftime("%d/%m/%Y"))
	#return 'test'