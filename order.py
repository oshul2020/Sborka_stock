# -*- coding: utf-8 -*-

import requests
import re

HOST = 'https://sborka.ua/adm/'
headers = {	'User-Agent'    	: 	'Mozilla/5.0',  						
				'Authorization' 	: 	'Basic YWRtaW46bGtBYzdUS3NaWVow',		#admin:AXIPrm-iTSn@	
				'Connection'		:	'Keep-Alive'}				

class OrderError(Exception): pass	

class Order(object):
	def __init__(self, user):
		self.sborkiSHF = []
		self.session = requests.Session()
		r = self.session.get(HOST, headers=headers)
				
		if r.status_code != requests.codes.ok:
			raise OrderError('Not loggin in to admin area')
			
		payload = {'pass_worker'  : user}
		r = self.session.post(HOST,headers=headers,data=payload)	

		if r.status_code != requests.codes.found:
			raise ValueError('User not loggin', r.status_code)
	
			
	def close(self):
		self.session.get(HOST+'login.php?logout=logout&logoutpic.x=54&logoutpic.y=15', headers=headers)

	def get(self, url):	
		r = self.session.get(HOST+url, headers=headers)
		
		if r.status_code != requests.codes.ok:
			raise ValueError('Request error: ', r.status_code)
    
		return r

	def loadSborkiSHF(self):
		r = self.get('sborki_print_shf.php')
		start = r.text.find('<table')
		end = r.text.find('</table>')
		table = r.text[start:end]
		sborki = re.findall(r'value="\d{6}">', table)
		self.sborkiSHF = [s[7:-2] for s in sborki]
					

if __name__ == '__main__':
	o = Order('nesi4')
	o.loadSborkiSHF()
	out = open('d:/sborki.txt', 'w')
	out.write('\n'.join(o.sborkiSHF))
	out.close()