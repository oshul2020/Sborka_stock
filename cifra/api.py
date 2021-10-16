from functools import wraps
import hashlib
import importlib
import json
from flask import Blueprint, render_template, request, redirect, session, flash, jsonify, get_template_attribute, g 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from Sborka.cifra.entity import Category, User, Unit, Size, Material, Density, Log
from Sborka.cifra.entity import crudPost, get_active_materials
from sqlalchemy.ext.serializer import loads, dumps
from datetime import date, timedelta, datetime
from flask_sqlalchemy import BaseQuery
from Sborka.cifra.stat import Stat

from Sborka import config

cifra_actions = ('списание', 'получение', 'возврат', 'инвентаризация', 'заказ', 'подрядчик')
cifra_process = ('печать','постпечать','дополнительно',)

app_cifra = Blueprint('app_cifra', __name__, template_folder='cifra_templates')
Base = declarative_base()

engine = create_engine(config.dbCifraPath, connect_args={'check_same_thread': False},echo=False)
Base.metadata.create_all(engine)
db = Session(engine)

@app_cifra.before_request
def inject_process():
	pass

def admin_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if session.get('cifra_admin') is None:
			return redirect('/cifra')
			
		return f(*args, **kwargs)
	return decorated_function
	
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if session.get('cifra_user') is None:
			return redirect('/cifra/login')
			
		return f(*args, **kwargs)
	return decorated_function

@app_cifra.route('/cifra', methods=['GET', 'POST'])
def c_index():
	#return render_template('layout_timeout.html')
	process = request.args.get('process')
	if process:
		categories = db.query(Category) \
			.filter(Category.process==process, Category.active)\
			.order_by(Category.sortby) \
			.all()
			
		mainFrame = get_template_attribute('c_stock.html', 'tab')
		return mainFrame(categories)	
	
	categories = db.query(Category) \
			.filter(Category.process==0, Category.active)\
			.order_by(Category.sortby) \
			.all()
			
	return render_template('c_stock.html', categories=categories, processes=cifra_process)


@app_cifra.route('/cifra/log', methods=['GET', 'POST'])
def c_log():
	query = BaseQuery(Log, db).order_by(Log.id.desc())
	
	if request.method == "GET":
		return render_template('c_log.html', 
			paginate=query.paginate(1, config.logsOnPage),
			actions=cifra_actions, processes=cifra_process,	
			users = db.query(User).filter(User.title!='admin').all())

	action_id = request.form.get('action_id')
	user_id = request.form.get('user_id')
	filter = request.form.get('filter')
	
	if action_id and action_id != '-1':
		query = query.filter(Log.action==action_id)
	
	if user_id and user_id != '0':
		query = query.filter(Log.user_id==user_id)

	if filter:
		process_id = request.form.get('process_id')
		query = query.join(Material).join(Category).filter(Category.process==process_id)		
			
		if filter == 'category':
			category_id = request.form.get('category_id')
			query = query.filter(Category.id==category_id)			
		
		if filter == 'density':
			category_id = request.form.get('category_id')
			density_id = request.form.get('density_id')
			material = request.form.get('material_title')
			query = query.filter(Category.id==category_id,
				Material.density_id==density_id, Material.title==material)	
		
		if filter == 'material':
			material_id = request.form.get('material_id')
			query = query.filter(Log.material_id==material_id)				
	
	page = request.form.get('page', type=int)
	paginate= query.paginate(page, config.logsOnPage)
	table = get_template_attribute('c_log_table.html', 'table')
	return table(paginate, cifra_actions)
		
	
@app_cifra.route("/cifra/login", methods=["GET", "POST"])
def c_login():
	session.clear()
	
	if request.method == "POST":
		passw = request.form.get('password')
		hash = hashlib.md5(passw.encode('utf-8')).hexdigest()
		try:
			user = db.query(User).filter(User.hash == hash).one()
			session['cifra_user'] = user
			if user.admin:
				session['cifra_admin'] = user
				
			return redirect('/cifra')	
					
		except Exception as e:	
			flash('ошибка', category='danger')
		
			return render_template('c_login.html')	
			
	else:
		return render_template('c_login.html')

@app_cifra.route("/cifra/logout")
def c_logout():
    session.clear()
    return redirect("/cifra")

@app_cifra.route('/cifra/stock', methods=['GET', 'POST'])
def c_stock():
	if request.method == "POST":
		if not 'cifra_user' in session:
			flash('необходимо войти на склад', category='danger')
			f = get_template_attribute('c_base.html', 'flashed')
			return (f(), 400) 	
		
		try:
			cmd = request.form.get('cmd')
			id = request.form.get('id')
			amount = request.form.get('amount')
			material = db.query(Material).get(id)
			log = Log()
			
			if cmd == 'writeOff':
				material.amount = Material.amount - amount
				message = 'списание выполнено'
				log.action = 0
			
			elif cmd == 'add':
				material.amount = Material.amount + amount
				message = 'материал принят'	
				log.action = 1
				
			elif cmd == 'update':
				material.amount = amount
				message = 'количество изменено'	
				log.action = 3
	
			log.amount = amount
			log.user_id = session['cifra_user'].id
			log.time = datetime.now()
			log.material_id = material.id
			log.info = request.form.get('info')
			
			db.add(log)
			db.commit()
			flash(message, category='success')
			
			category_id = request.form.get('category_id')
			data = get_active_materials(db, category_id)	
			table = get_template_attribute('c_stock.html', 'new_table')
			f = get_template_attribute('c_base.html', 'flashed')
			return jsonify((table(data),f()))
			
		except Exception as e:	
			db.rollback()
			#flash(f'ошибка: ({e.orig})', category='danger')
			flash(f'ошибка: ({e})', category='danger')	
			f = get_template_attribute('c_base.html', 'flashed')
			return (f(), 400) 	
			
	return redirect('/cifra')
	
@app_cifra.route('/cifra/user', methods=['GET', 'POST'])
@admin_required	
def c_user():
	if request.method == "POST":
		cmd = request.form.get('cmd')
		crudPost(db, request, 'User')

		mainFrame = get_template_attribute('c_user.html', 'mainFrame')
		return mainFrame(db.query(User).all())
	
	return render_template('c_user.html', users = db.query(User).all())

@app_cifra.route('/cifra/category', methods=['GET', 'POST'])
@admin_required		
def c_category():
	if request.method == "POST":	
		crudPost(db, request, 'Category')
		mainFrame = get_template_attribute('c_category.html', 'mainFrame')
		return mainFrame(db.query(Category).order_by(Category.process, Category.sortby).all(), cifra_process)
		
	return render_template('c_category.html', 
		categories = db.query(Category).order_by(Category.process, Category.sortby).all(), 
			processes=cifra_process)

@app_cifra.route('/cifra/density', methods=['GET', 'POST'])
@admin_required		
def c_density():
	if request.method == "POST":	
		crudPost(db, request, 'Density')
		mainFrame = get_template_attribute('c_density.html', 'mainFrame')
		return mainFrame(db.query(Density).order_by(Density.density).all())
		
	return render_template('c_density.html', densities = db.query(Density).order_by(Density.density).all())	
	
@app_cifra.route('/cifra/unit', methods=['GET', 'POST'])
@admin_required		
def c_unit():
	if request.method == "POST":	
		crudPost(db, request, 'Unit')
		mainFrame = get_template_attribute('c_unit.html', 'mainFrame')
		return mainFrame(db.query(Unit).all())
		
	return render_template('c_unit.html', units = db.query(Unit).all())

@app_cifra.route('/cifra/size', methods=['GET', 'POST'])
@admin_required		
def c_size():
	if request.method == "POST":	
		crudPost(db, request, 'Size')
		mainFrame = get_template_attribute('c_size.html', 'mainFrame')
		return mainFrame(db.query(Size).order_by(Size.width).all())
		
	return render_template('c_size.html', sizes = db.query(Size).order_by(Size.width).all())

@app_cifra.route('/cifra/stat', methods=['GET', 'POST'])
def c_stat():
	if request.method == "GET":
		pass
	
	cmd = request.form.get('cmd')	
	material_id = request.form.get('material_id')
	if cmd == 'density':
		return Stat(db).getDensityTable(material_id)

	if cmd == 'material':
		return Stat(db).getMaterialTable(material_id)
	
	return 'stat'	
	
@app_cifra.route('/cifra/material', methods=['GET', 'POST'])
@admin_required		
def c_material():
	if request.method == "POST":
		crudPost(db, request, 'Material')
		mainFrame = get_template_attribute('c_material.html', 'mainFrame')
		return mainFrame(db.query(Material).all())
	
	return render_template('c_material.html', materials = db.query(Material).all(),
				categories = db.query(Category).filter(Category.active).order_by(Category.process).all(), 
				densities = db.query(Density).order_by(Density.density).all(),
				sizes = db.query(Size).order_by(Size.width).all(),
				units = db.query(Unit).all())

@app_cifra.route('/cifra/data', methods=['GET', 'POST'])
def c_data():
	if request.method == "GET":
		cmd = request.args.get('cmd')
		if cmd == 'materials':
			category_id = request.args.get('category_id')
			data = get_active_materials(db, category_id)
			table = get_template_attribute('c_stock.html', 'new_table')
			return table(data, category_id)
		
		elif cmd == 'info':
			entity = request.args.get('entity')
			id = request.args.get('id')
			lib = importlib.import_module('Sborka.cifra.entity')
			Entity = getattr(lib, entity)
			return  jsonify(db.query(Entity).get(id).serialize) 
	
	cmd = request.form.get('cmd')	
	if cmd == 'categories_process':
		process_id = request.form.get('process_id')
		categories = db.query(Category).filter(Category.active).order_by(Category.sortby)
		if process_id:
			categories = categories.filter(Category.process==process_id)		
		categories = categories.all()
		return	jsonify(tuple(cat.serialize for cat in categories))	

	if cmd == 'densities_category':
		category_id = request.form.get('category_id')
		materials = db.query(Material).join(Material.density) \
				.filter(Material.category_id==category_id).order_by(Density.density)
		return json.dumps({m.title: m.density_id for m in materials})	

	if cmd == 'sizes_density_category':	
		category_id = request.form.get('category_id')
		density_id = request.form.get('density_id')
		title = request.form.get('title')
		materials = db.query(Material).join(Material.size) \
			.filter(Material.category_id==category_id, 
					Material.density_id==density_id,
					Material.title==title)	\
			.order_by(Size.width)
		return json.dumps({repr(m.size): m.size.id for m in materials})		

	if cmd == 'material':	
		category_id = request.form.get('category_id')
		density_id = request.form.get('density_id')
		size_id = request.form.get('size_id')
		title = request.form.get('title')
		try:
			material = db.query(Material) \
				.filter(Material.category_id==category_id, 
						Material.density_id==density_id,
						Material.size_id==size_id,
						Material.title==title).one()
			return jsonify(material.serialize)
		except:	
			return 'error', 404 
		
	return redirect('/cifra')		
	
			
@app_cifra.route('/cifra/test', methods=['GET', 'POST'])
def c_test():
			
	return 'test'