#!/usr/bin/python3

"""
Aplicacao que serve para ajudar na automatização da instalação do Advanced Monitorization Solution (AMS)
Copyright (c) 2022 Universidade do Minho
Projeto de Informática 2021/22
Desenvolvido por: Grupo 3 da Accenture
"""

import os, sys, datetime
#import requests
import json, socket
from flask import Flask, request, url_for, redirect, render_template, make_response, send_from_directory, current_app
#from dotenv import load_dotenv

app = Flask(__name__)


# IP do servidor de HTTP
http_ip = "localhost"
# Porta do servidor HTTP
http_port = 8080

vars = """
---
#provisioning
common_shell: /bin/bash
common_member_of: sudo

#docker_compose
docker_compose_dir: /home

#kube-state-metrics
ip_kube_state_metrics: ['10.8.0.5:8080']

#node-exporter
ips_node_exporter: ['10.8.0.2:9100','10.8.1.2:9100','10.8.2.2:9100']

#Hooks slack
hooks_slack: 'url'

#Channel name
channel_name: 'channel_name'

#Pass do elasticsearch
pass_elasticsearch: "password"

"""

'''
Funcao usada para proceder ao tratamento das operacoes relativas ao path /
'''
@app.route('/', methods=['GET','POST'])
def home():
	
	
	return render_template("home.html")

@app.route('/install', methods=['GET','POST'])
def install():
	
	ip_host = request.form['ip_host']
	print(ip_host)
	webapp = request.form.get('webapp')
	if(webapp):
		print("webapp: on")
	else: print("webapp: off")
	
	elk = request.form.get('elk')
	if(elk):
		print("elk: on")
		password = request.form.get('password')
		print(password)
	else: print("elk: off")
	
	prometheus = request.form.get('prometheus')
	if(prometheus):
		print("prometheus: on")
	else: print("prometheus: off")
	
	alertmanager = request.form.get('alertmanager')
	if(alertmanager):
		url = request.form.get('url')
		channel = request.form.get('channel')
		print(url)
		print(channel)
		print("alertmanager: on")
	else: print("alertmanager: off")
	
	grafana = request.form.get('grafana')
	if(grafana):
		print("grafana: on")
	else: print("grafana: off")

	yml_file = open(os.path.join(os.path.dirname(__file__),'group_vars\\all.yml'), "w")

	vars.replace("password", password)
	vars.replace("ip_host", ip_host)
	vars.replace("channel", channel)
	vars.replace("url", url)

	yml_file.write(vars)


	
	return render_template("install.html")


if __name__ == '__main__':

	app.run(host='0.0.0.0', port=http_port, debug=True)


