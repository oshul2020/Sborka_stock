# -*- coding: utf-8 -*-
from __future__ import with_statement
import locale
from flask import Flask, render_template, request, send_file, session, redirect
from flask_session import Session
from flask_mobility import Mobility
from Sborka import work, info, search, config, sign, formats, order
from tempfile import mkdtemp
from urllib.parse import unquote
from datetime import timedelta
import traceback

# Blueprints
from Sborka.cifra.api import app_cifra
from Sborka.wide.api import app_wide

locale.setlocale(locale.LC_ALL, '')
app = Flask(__name__)
Mobility(app)
app.register_blueprint(app_cifra)
app.register_blueprint(app_wide)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.permanent_session_lifetime = timedelta(minutes=15)
Session(app)


@app.route("/stock")
def timeout():
	return redirect('/wide')
	#return render_template('layout_timeout.html')


@app.route("/")
def get_index():
	
	order = session.get('order')
	return render_template('index.html', info=info, isOnline=order)

@app.route("/login", methods=['POST'])
def post_login():
	if request.method == "POST":
		session.clear()
		action = request.form.get("action")
		passw = request.form['passw']
		
		if action == 'login' and passw:
			try:
				session['order'] = order.Order(passw)
			except Exception as e:
				return render_template("error.html", info=e)		

	return redirect('/')
	
@app.route("/work")
def get_work():
	order = session.get('order')
	if order:
		order.loadSborkiSHF()
	
	works = work.load(order)

	'''
	for w in works:
		for q in w.qualities:
			for m_name, m in q.materials.items():
				for g in m.groups:
					print('\t{}'.format(g.name))
					for f in g.files:
						print('\t\t{}'.format(f.path.name))
	'''					

	return render_template("work.html", works=works, isOnline=order)

@app.route("/info", methods=["GET"])
def get_info():
	file = request.args.get('file')
	result = info.get(file)
	if isinstance(result, Exception):
		text = ' <br> '.join(traceback.format_exception(etype=type(result), value=result, tb=result.__traceback__))
		return 	render_template("error.html", info=text)	
	
	return render_template("info.html", info=result)	
	

@app.route("/thumb", methods=["GET"])
def get_thumb():
	file = unquote(request.args.get('file'))
	result = info.thumb(file)
	if isinstance(result, Exception):
		return 	render_template("error.html", info=result)	
	
	return send_file(result, mimetype='image/jpeg')
	
@app.route("/search", methods=["GET"])
def get_search():
	query = request.args.get('q')
	where = request.args.get('where')
	if where == 'work':
		searchDir = config.workDir
	else:
		searchDir = config.shiraDir

	result = search.get(query, searchDir)
	return 	render_template("search.html", data=result, dir=searchDir, where=where)

	
@app.route("/shira", methods=['GET'])
def get_shira():
	result = sign.shira()
	if isinstance(result, Exception):
		return 	render_template("error.html", info=result)	
	
	return 	render_template("sign.html", data=result)
	
	
@app.route("/sign", methods=['GET', 'POST'])
def post_sign():
	add = None
	
	files = request.form.getlist('files')
		
	if 'add' in request.form:	
		add = request.form['add']
	
	result = sign.perform(files, add)
	
	if isinstance(result, Exception):
		return 	render_template("error.html", info=result)	
	
	return render_template("sign_check.html", data=result)
	
	
@app.after_request
def after_request(response):
	"""Disable caching"""
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Expires"] = 0
	response.headers["Pragma"] = "no-cache"
	return response	

if __name__ == "__main__":
	app.run(host='0.0.0.0')
