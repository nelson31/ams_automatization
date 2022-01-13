import ipaddress
import sys
import os
import subprocess


ansible_required = """---
- name: AMS
  hosts: all
  become: true

  tasks:
    - name: Install aptitude using apt
      apt: name=aptitude state=latest update_cache=yes force_apt_get=yes

    - name: Install required system packages
      apt: name={{ item }} state=latest update_cache=yes
      loop: [ 'apt-transport-https', 'ca-certificates', 'curl', 'software-properties-common', 'python3-pip', 'virtualenv', 'python3-setuptools']

    - name: Add Docker GPG apt Key
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present

    - name: Add Docker Repository
      apt_repository:
        repo: deb https://download.docker.com/linux/ubuntu bionic stable
        state: present

    - name: Update apt and install docker-ce
      apt: update_cache=yes name=docker-ce state=latest
      
    - name: Install Docker Module for Python
      pip:
        name: docker
        
    - name: Install docker-compose
      apt:
        name: docker-compose
        
    - name: Change VM.max_map_count
      command: sudo sysctl -w vm.max_map_count=262144

    - name: Copy docker-compose file
      copy:
        src: './templates/docker-compose.yml'
        dest: '/home/'
        mode: 0666
"""

ansible_elk_configfiles = """
    - name: Copy ELK config files
      copy:
        src: './templates/configs/'
        dest: '/home/configs/'
        mode: 0666
"""

ansible_alertmanager_configfiles = """
    - name: Copy alertmanager config file
      copy:
        src: './templates/alertmanager/'
        dest: '/home/alertmanager/'
        mode: 0666

"""

ansible_prometheus_configfiles = """
    - name: Copy prometheus config file
      copy:
        src: './templates/prometheus/'
        dest: '/home/prometheus/'
        mode: 0666
"""

ansible_build_docker_compose = """
    - name: build container with docker-compose
      community.docker.docker_compose:
        project_src: "/home/"
      register: options
      
    - name: Sleep for 10 seconds
      wait_for:
        timeout: 10

"""

ansible_elk_config = """
    - name: change elastic bootstrap password
      command: docker exec -it home_elk_1 bash -c 'echo "password_change_me" | /opt/elasticsearch/bin/elasticsearch-keystore add "bootstrap.password" -x'
        
    - name: Change ownership of elasticsearch.keystore
      community.docker.docker_container_exec:
        container: home_elk_1
        command: chmod a+wr /etc/elasticsearch/elasticsearch.keystore    
    
    - name: restart elasticsearch
      community.docker.docker_container_exec:
        container: home_elk_1
        command: service elasticsearch restart
        
    - name: wait for elastisearch to be up
      wait_for_connection:
        delay: 30
        sleep: 1     
        
    - name: change elastic user password
      command:
        argv:
          - docker
          - exec
          - -it
          - home_elk_1
          - bash
          - -c 
          - |
            curl -uelastic:"password_change_me" -XPUT -H 'Content-Type: application/json' 'http://localhost:9200/_xpack/security/user/elastic/_password/' -d '{ "password":"password_change_me" }'
          
    - name: change kibana_system user password
      command:
        argv:
          - docker
          - exec
          - -it
          - home_elk_1
          - bash
          - -c 
          - |
            curl -uelastic:"password_change_me" -XPUT -H 'Content-Type: application/json' 'http://localhost:9200/_xpack/security/user/kibana_system/_password/' -d '{ "password":"password_change_me" }'
    
    - name: restart elasticsearch
      community.docker.docker_container_exec:
        container: home_elk_1
        command: service elasticsearch restart
        
    - name: restart kibana
      community.docker.docker_container_exec:
        container: home_elk_1
        command: service kibana restart

"""

ansible_mini_httpd = """
    - name: Install mini-httpd
      apt:
        name: mini-httpd

    - name: Copy Web platform files
      copy:
        src: './AMSWebPlatform/'
        dest: '/home/AMSWebPlatform/'
        mode: 0666

    - name: Inicialize Web platform
      command: sudo mini_httpd -p 80 -d /home/AMSWebPlatform
"""


compose_required = """version: '3'

services:
"""

compose_elk = """
        elk:
                image: sebp/elk
                ports:
                        - "5601:5601"
                        - "9200:9200"
                        - "5044:5044"
                volumes:
                        - ./configs/elasticsearch.yml:/etc/elasticsearch/elasticsearch.yml
                        - ./configs/kibana.yml:/opt/kibana/config/kibana.yml
                        - ./configs/02-beats-input.conf:/etc/logstash/conf.d/02-beats-input.conf
                        - ./configs/30-output.conf:/etc/logstash/conf.d/30-output.conf
"""

compose_prometheus = """
        prometheus:
                image: prom/prometheus:latest
                command: --web.enable-lifecycle --config.file=/etc/prometheus/prometheus.yml
                ports:
                        - "9090:9090"
                volumes:
                        - ./prometheus:/etc/prometheus
                        - prometheus-data:/prometheus
                networks:
                        - prometheus-grafana
"""

compose_grafana = """
        grafana:
                image: grafana/grafana-oss:latest
                ports:
                        - "3000:3000"
                user: '104'
                networks:
                        - prometheus-grafana
"""

compose_alertmanager = """
        alertmanager:
                image: prom/alertmanager:latest
                restart: unless-stopped
                command: --config.file=/config/alertmanager.yml --log.level=debug
                ports:
                        - "9093:9093"
                volumes:
                        - ./alertmanager:/config
                        - alertmanager-data:/data
                networks:
                        - prometheus-grafana
            
"""

compose_volumes = """
volumes:
"""
prometheus_volume = """
        prometheus-data:
"""
alertmanager_volume = """
        alertmanager-data:
"""

compose_networks = """
networks:
        prometheus-grafana:
                driver: bridge

"""


installer_configs = {
    "hosts": -1,
    "password": -1,
    "elk": -1,
    "prometheus": -1,
    "alertmanager": -1,
    "grafana": -1,
    "webpage": -1
}


def main():

    #----------------------------Read config file---------------------------------------
    try:
      config_file = open(os.path.join(os.path.dirname(__file__),'conf.txt'), "r")
    except OSError:
      print("Could not open configuration file to read.")
      sys.exit()

    for line in config_file:
        parse_line(line.strip("\n"))

    complete = True
    for key in installer_configs.keys():
      if installer_configs[key] == -1:
        print("Missing configuration for \"" + key + "\" option.")
        complete = False

    if not complete:
      sys.exit()

    if(not installer_configs['elk'] and not installer_configs['prometheus'] and not installer_configs['alertmanager'] and not installer_configs['grafana']):
      print("Nothing to install. Goodbye.")
      sys.exit()


    #----------------------------Write ansible file---------------------------------------

    yml_file = open(os.path.join(os.path.dirname(__file__),'ams.yml'), "w")

    yml_file.write(ansible_required)

    if(installer_configs['elk']):
      yml_file.write(ansible_elk_configfiles)

    if(installer_configs['prometheus'] or installer_configs['alertmanager'] or installer_configs['graphana']):
      yml_file.write(ansible_prometheus_configfiles)

    if(installer_configs['alertmanager']):
      yml_file.write(ansible_alertmanager_configfiles)

    yml_file.write(ansible_build_docker_compose)

    if(installer_configs['elk']):
      yml_file.write(ansible_elk_config.replace("password_change_me", installer_configs['password']))

    if(installer_configs['webpage']):
      yml_file.write(ansible_mini_httpd)

    yml_file.close()
    
    #----------------------------Write docker compose file---------------------------------------

    compose_file = open(os.path.join(os.path.dirname(__file__),'templates/docker-compose.yml'), "w")

    compose_file.write(compose_required)

    if(installer_configs['elk']):
      compose_file.write(compose_elk)

    if(installer_configs['prometheus'] or installer_configs['alertmanager'] or installer_configs['graphana']):
      compose_file.write(compose_prometheus)

    if(installer_configs['alertmanager']):
      compose_file.write(compose_alertmanager)

    if(installer_configs['grafana']):
      compose_file.write(compose_grafana)

    compose_file.write(compose_volumes)

    if(installer_configs['prometheus'] or installer_configs['alertmanager'] or installer_configs['graphana']):
      compose_file.write(prometheus_volume)

    if(installer_configs['alertmanager']):
      compose_file.write(alertmanager_volume)

    if(installer_configs['prometheus'] or installer_configs['alertmanager'] or installer_configs['graphana']):
      compose_file.write(compose_networks)

    #----------------------------Write hosts file-------------------------------------------------

    hosts_file = open("/etc/ansible/hosts", "w")

    hosts_file.write(installer_configs['hosts'])

    
    #----------------------------Run ansible-------------------------------------------------------
    subprocess.run(["ansible-playbook", "./ams.yml"])





def parse_line(line):
    if line=="":
      return

    words = line.split(":", 1)

    if words[0] == "hosts":
      try:
        ip = ipaddress.ip_address(words[1])
        installer_configs['hosts'] = words[1]
      except ValueError:
        print("IP address is invalid.")
        sys.exit()
      except:
        print("Error parsing IP address")
        sys.exit()
      
    elif words[0] == "password":
      if len(words[1]) < 8:
        print("Password too small. Please make sure it is at least 8 characther long.")
        sys.exit()
      else:
        installer_configs['password'] = words[1]
    
    elif words[0] == "elk":
      if words[1].lower() == "yes":
        installer_configs['elk'] = True
      elif words[1].lower() == "no":
        installer_configs['elk'] = False
      else:
        print("Error parsing ELK install option. Make sure it is either \"yes\" or \"no\"")
        sys.exit()

    elif words[0] == "prometheus":
      if words[1].lower() == "yes":
        installer_configs['prometheus'] = True
      elif words[1].lower() == "no":
        installer_configs['prometheus'] = False
      else:
        print("Error parsing Prometheus install option. Make sure it is either \"yes\" or \"no\"")
        sys.exit()

    elif words[0] == "alertmanager":
      if words[1].lower() == "yes":
        installer_configs['alertmanager'] = True
      elif words[1].lower() == "no":
        installer_configs['alertmanager'] = False
      else:
        print("Error parsing AlertManager install option. Make sure it is either \"yes\" or \"no\"")
        sys.exit()

    elif words[0] == "grafana":
      if words[1].lower() == "yes":
        installer_configs['grafana'] = True
      elif words[1].lower() == "no":
        installer_configs['grafana'] = False
      else:
        print("Error parsing Grafana install option. Make sure it is either \"yes\" or \"no\"")
        sys.exit()

    elif words[0] == "webpage":
      if words[1].lower() == "yes":
        installer_configs['webpage'] = True
      elif words[1].lower() == "no":
        installer_configs['webpage'] = False
      else:
        print("Error parsing Webpage install option. Make sure it is either \"yes\" or \"no\"")
        sys.exit()
     
    else:
      print("Error parsing line \"" + line + "\"")
      sys.exit()


    

if __name__ == "__main__":
    main()