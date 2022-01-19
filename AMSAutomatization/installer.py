#!/usr/bin/python3

"""
Aplicacao que serve para ajudar na automatização da instalação do Advanced Monitorization Solution (AMS)
Copyright (c) 2022 Universidade do Minho
Projeto de Informática 2021/22
Desenvolvido por: Grupo 3 da Accenture
"""

import os, sys, datetime, logging
import requests
import jwt, json, socket
from werkzeug.utils import secure_filename
from flask import Flask, request, url_for, redirect, render_template, make_response, send_from_directory, current_app
from dotenv import load_dotenv

app = Flask(__name__)


# IP do servidor de HTTP
http_ip = socket.gethostbyname("http_container")
# Porta do servidor HTTP
http_port = 80







if __name__ == '__main__':

	# configuracao de log
	logging.basicConfig(filename=logname,
							filemode='a',
							format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
							datefmt='%H:%M:%S',
							level=logging.DEBUG)

	logging.info("Running HTTP Server")
	logger = logging.getLogger()
	# fim configuracao de log

	app.run(host='0.0.0.0', port=http_port, debug=True)

