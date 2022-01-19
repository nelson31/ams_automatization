#!/usr/bin/python3

"""
Aplicacao que serve para ajudar na automatização da instalação do Advanced Monitorization Solution (AMS)
Copyright (c) 2022 Universidade do Minho
Projeto de Informática 2021/22
Desenvolvido por: Grupo 3 da Accenture
"""

import os, sys, datetime
import requests
import json, socket
from flask import Flask, request, url_for, redirect, render_template, make_response, send_from_directory, current_app
from dotenv import load_dotenv

app = Flask(__name__)


# IP do servidor de HTTP
http_ip = "localhost"
# Porta do servidor HTTP
http_port = 80



'''
Funcao usada para proceder ao tratamento das operacoes relativas ao path /
'''
@app.route('/', methods=['GET','POST'])
def home():
	
	
	return render_template("home.html")



if __name__ == '__main__':

	app.run(host='0.0.0.0', port=http_port, debug=True)


