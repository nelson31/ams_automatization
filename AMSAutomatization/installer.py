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
from flask import Flask, request, url_for, redirect, render_template, make_response, send_from_directory, current_app
#from dotenv import load_dotenv

app = Flask(__name__)


# IP do servidor de HTTP
http_ip = "localhost"
# Porta do servidor HTTP
http_port = 5601

varslog = """---
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
channel_name: 'name_channel'

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
	
	# obter selecao elk
	elk = request.form.get('elk')
	password = ""
	if(elk):
		print("elk: on")
		password = request.form.get('password')
		print(password)
		tagsOn = tagsOn + ",elk"
	else: print("elk: off")
	
	# obter selecao prometheus
	prometheus = request.form.get('prometheus')
	if(prometheus):
		print("prometheus: on")
		tagsOn = tagsOn + ",prometheus"
	else: print("prometheus: off")
	
	# obter selecao alertmanager
	alertmanager = request.form.get('alertmanager')
	url = ""
	channel = ""
	if(alertmanager):
		url = request.form.get('url')
		channel = request.form.get('channel')
		print(url)
		print(channel)
		print("alertmanager: on")
		if("prometheus" not in tagsOn):
			tagsOn = tagsOn + ",prometheus"
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
	path = os.path.join(os.path.dirname(__file__),"ansible/group_vars/all.yml")

	print(path)

	# subtituir variaveis de input
	logsvars = varslog.replace("password", password)
	logsvars = logsvars.replace("name_channel", channel)
	logsvars = logsvars.replace("url", url)
	
	print(logsvars)

	# criar ficheiro de logs
	yml_file = open(path, "w")

	yml_file.write(logsvars)

	yml_file.close()

	# criar ficheiro hosts

	hostvar = "[vm]\n" + ip_host +"\n\n"

	hosts_file = open(os.path.join(os.path.dirname(__file__),"ansible/hosts.inv"), "w")

	hosts_file.write(hostvar)

	hosts_file.close()

	# criar comando ansible

	subprocess.run("cat ansible/playbook.yml")
	
	#ansiblepath = os.path.join(os.path.dirname(__file__),"ansible/playbook.yml")
	#commandAnsible = "cd ansible && sudo ansible-playbook " + ansiblepath + " --tags \"" + tagsOn + "\""
	#print(commandAnsible)
	#subprocess.run(commandAnsible)

	return render_template("install.html")


if __name__ == '__main__':

	app.run(host='0.0.0.0', port=http_port, debug=True)


