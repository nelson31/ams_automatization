#!/usr/bin/python3

"""
Aplicacao que serve para ajudar na automatização da instalação do Advanced Monitorization Solution (AMS)
Copyright (c) 2022 Universidade do Minho
Projeto de Informática 2021/22
Desenvolvido por: Grupo 3 da Accenture
"""

import subprocess
import os, sys, datetime
#import requests
import json, socket
from time import sleep
from flask import Flask, request, url_for, redirect, render_template, make_response, send_from_directory, current_app, session
#from dotenv import load_dotenv

app = Flask(__name__)


# IP do servidor de HTTP
http_ip = "localhost"
# Porta do servidor HTTP
http_port = 8080


'''
Funcao usada para proceder ao tratamento das operacoes relativas ao path /
'''
@app.route('/', methods=['GET','POST'])
def home():
	
	
	return render_template("home.html")

@app.route('/installed', methods=['GET','POST'])
def installing():

	# criar comando ansible
	
	ansiblepath = os.path.join(os.path.dirname(__file__),"ansible/playbook.yml")
	commandAnsible = "sudo ansible-playbook " + ansiblepath + " --tags \"" + session['tagsOn'] + "\" -i ansible/hosts.inv"
	print(commandAnsible)
	#subprocess.run(commandAnsible, shell=True)
	
	logvars = session['varslog']
	if(session['elk']):
		if(len(session['password'])>0):
			logvars = logvars.replace(session['password'], "secret")
	if(session['alertmanager']):
		logvars = logvars.replace(session['url'], "secret")
	
	print(logvars)
	yml_file = open(session['path'], "w")

	yml_file.write(logvars)

	yml_file.close()

	return render_template("installed.html")

@app.route('/installing', methods=['GET','POST'])
def install():


	
	template = """---
#provisioning
common_shell: /bin/bash
common_member_of: sudo

#docker_compose
docker_compose_dir: /home

#kube-state-metrics
ip_kube_state_metrics: ipKube

#node-exporter
ips_node_exporter: ipsNode

#Hooks slack
hooks_slack: 'url'

#Channel name
channel_name: 'name_channel'

#Pass do elasticsearch
pass_elasticsearch: "password"

"""
	
	varslog = str(template)

	# obter ip do host
	ip_host = request.form['ip_host']
	print(ip_host)

	tagsOn = "common"
	
	# obter selecao webapp
	webapp = request.form.get('webapp')
	if(webapp):
		print("webapp: on")
		tagsOn = tagsOn + ",webapp"
	else: print("webapp: off")
	
	#logsvars = ""
	
	# obter selecao elk
	elk = request.form.get('elk')
	
	if(elk):
		print("elk: on")
		password = request.form.get('password')
		print(password)
		varslog = varslog.replace("password", password)
		tagsOn = tagsOn + ",elk"
	else: print("elk: off")
	
	# obter selecao prometheus
	prometheus = request.form.get('prometheus')
	kubeStateMetrics = ""
	nodeExporter = ""
	listNode = []
	listNodePort = ""
	if(prometheus):
		print("prometheus: on")
		kubeStateMetrics = request.form.get('kubeStateMetrics')
		kubeStateMetrics = "['" + kubeStateMetrics + ":8080']"
		print(kubeStateMetrics)
		nodeExporter= request.form.get('nodeExporter')
		print(nodeExporter)
		listNode = nodeExporter.split(',')
		print(listNode)
		i = 0
		if(listNode[0] != ''):
			listNodePort = "["
			for x in listNode:
				if i>0:
					listNodePort +=","
				listNodePort += "'" + x + ":9100'"
				i=1
			listNodePort += "]"
		else: 
			listNodePort = "[]"

		print(listNodePort)

		varslog = varslog.replace("ipKube", kubeStateMetrics)
		varslog = varslog.replace("ipsNode", listNodePort)
		tagsOn = tagsOn + ",prometheus"
	else: print("prometheus: off")
	
	# obter selecao alertmanager
	alertmanager = request.form.get('alertmanager')
	channel = ""
	if(alertmanager):
		url = request.form.get('url')
		channel = request.form.get('channel')
		print(url)
		print(channel)
		print("alertmanager: on")
		if("prometheus" not in tagsOn):
			tagsOn = tagsOn + ",prometheus"
		
		varslog = varslog.replace("name_channel", channel)
		varslog = varslog.replace("url", url)
		tagsOn = tagsOn + ",alertmanager"
	else: print("alertmanager: off")
	
	# obter selecao grafana
	grafana = request.form.get('grafana')
	if(grafana):
		print("grafana: on")
		if(",prometheus" not in tagsOn):
			tagsOn = tagsOn + ",prometheus"
		tagsOn = tagsOn + ",grafana"
	else: print("grafana: off")

	# path para o ficheiro var_logs
	path = os.path.join(os.path.dirname(__file__),"ansible\\group_vars\\all.yml")

	session['path'] = path
	if(session['elk']):
		session['password'] = password
	session['url'] = url
	session['tagsOn'] = tagsOn
	session['elk'] = elk
	session['alertmanager'] = alertmanager
	session['varslog'] = varslog


	print(path)

	# subtituir variaveis de input
	
	print(varslog)

	# criar ficheiro de logs
	yml_file = open(path, "w")

	yml_file.write(varslog)

	yml_file.close()

	# criar ficheiro hosts

	hostvar = "[vm]\n" + ip_host +"\n\n"

	hosts_file = open(os.path.join(os.path.dirname(__file__),"ansible/hosts.inv"), "w")

	hosts_file.write(hostvar)

	hosts_file.close()

	return render_template("installing.html")


if __name__ == '__main__':

	app.secret_key = "amsAutomatization"

	app.run(host='0.0.0.0', port=http_port, debug=True)


