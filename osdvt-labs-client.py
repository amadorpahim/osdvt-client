#!/usr/bin/env python
# This program is a VDI solution using the SPICE Protocol
# Copyright (C) 2010  Universidade de Caxias do Sul
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# long with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import fcntl
import struct
import socket
import ssl
import sys
import subprocess
import time
from dialog import Dialog

#################################################
#################################################
#################################################
Server = "osdvtserver.example.com"
ServerPort = 6970
LocalInterface = "em1"
#################################################
EnableShutdown = False
# New spice client (spicy) - "spice-gtk-tools" package.
spice_client = "/usr/bin/spicy"
# Old spice client (spicec) - "spice-client" package.
old_spice_client = "/usr/bin/spicec"
# VNC client.
vnc_client = "/usr/bin/vinagre"
# sudo is necessary to usb_redir
EnableSudo = True
#################################################
cacert = os.getenv('HOME')+"/osdvt/cacert.pem"
#################################################
#################################################
#################################################

if not os.path.isfile(spice_client):
        print "New spice client not found (%s). USB redirection will not work. Please, install spice-gtk-tools package. Trying old Client %s..." %(spice_client,old_spice_client)
        if os.path.isfile(old_spice_client):
                print "Ok, old Spice Client found (%s)." %(old_spice_client)
                spice_client = old_spice_client
        else:  
                print "Old spice client not found (%s). You can't access your VMs through SPICE protocol." %(old_spice_client)

if not os.path.isfile(vnc_client):
        print "VNC client not found (%s). You can't access your VMs through VNC protocol." %(vnc_client)

if not EnableSudo:
        print "Sudo is disabled. 'spicy' client needs root rights to use USB redirection."

class Principal:
	def get_ip_address(self, ifname):
    		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    		return socket.inet_ntoa(fcntl.ioctl(
        		s.fileno(),
        		0x8915,  # SIOCGIFADDR
        		struct.pack('256s', ifname[:15])
    		)[20:24])


	def auth(self, ip):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ssl_sock = ssl.wrap_socket(s,
		                           ca_certs=cacert,
		                           cert_reqs=ssl.CERT_REQUIRED)
	
		ssl_sock.connect((Server, ServerPort))
		ssl_sock.write("AUTH IP "+ip)
		data = ssl_sock.read()
		ssl_sock.close()
		s.close()
		return data

	def procurar(self, ip, token):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ssl_sock = ssl.wrap_socket(s,
		                           ca_certs=cacert,
		                           cert_reqs=ssl.CERT_REQUIRED)
		ssl_sock.connect((Server, ServerPort))
		ssl_sock.write("SEARCH IP "+ip+" "+token) 
		data = ssl_sock.read()
		ssl_sock.close()
		s.close()
	
		return data

	def status(self, vm, token):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	        ssl_sock = ssl.wrap_socket(s,
	        	ca_certs=cacert,
	        	cert_reqs=ssl.CERT_REQUIRED)

                ssl_sock.connect((Server, ServerPort))
		ssl_sock.write( "STATUS IP " + vm + " " + token)
	
		data = ssl_sock.read()
		ssl_sock.close()
		s.close()
		if data == "True":
			return "OK: Running."
		else:
			return "ERR: Stopped."

	def ligar(self, vm, token):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ssl_sock = ssl.wrap_socket(s,
			ca_certs=cacert,
 			cert_reqs=ssl.CERT_REQUIRED)

		ssl_sock.connect((Server, ServerPort))
		ssl_sock.write( "START IP " + vm + " " + token)
		data = ssl_sock.read()
		ssl_sock.close()
		s.close()
		return data

	def conectar(self, vm, token):
            	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ssl_sock = ssl.wrap_socket(s,
                        ca_certs=cacert,
                        cert_reqs=ssl.CERT_REQUIRED)

                ssl_sock.connect((Server, ServerPort))
                ssl_sock.write( "CONNECT IP " + vm + " " + token)

		data = ssl_sock.read()
                ssl_sock.close()
		s.close()

                if data.split()[0] != "ERR":
                        cmnd = []

			if EnableSudo:
				cmnd.append("sudo")

                        if data.split().__len__() is 3 and data.split()[2] == "0" or data.split().__len__() is 2:
				cmnd.append(spice_client)
				cmnd.append("-h")
				cmnd.append("%s" % (Server))
				cmnd.append("-p")
				cmnd.append("%s" % (data.split()[0]))
				cmnd.append("-w")
				cmnd.append("%s" % (data.split()[1]))
				cmnd.append("-f")
			elif data.split().__len__() is 3 and data.split()[2] == "1":
				cmnd.append(vnc_client)
				cmnd.append("%s:%s" % (Server,int(data.split()[0])%5900))
				cmnd.append("-f")

                        subprocess.call(cmnd)

def main():
	while True:
		vms = Principal()
		ip = vms.get_ip_address(LocalInterface)
		result = vms.auth(ip)
		token = result.split()[1]
		result = vms.procurar(ip, token)
		varcontrole = ""
		window = Dialog()

		if result.split()[0] == "ERR:":
			varcontrole = window.yesno("VM not found. Refresh?")
			if varcontrole != 0:
				sys.exit(1)
		else:
	
			if len(result.split()) > 1:
				lista_vms = [(r, '') for r in result.split(' ')]
                                status, vm = window.menu("VM List", choices=lista_vms)
				if status != 0:
                                	sys.exit(1)
			
			else:
				vm = result.split()[0]

			result = vms.status(vm, token)
			if result.split()[0] == "ERR:":
				result = vms.ligar(vm, token)

			result = vms.conectar(vm, token)	
			time.sleep(1)

			if EnableShutdown:
				shutdown = []

				if EnableSudo:
					shutdown.append("sudo")

				shutdown.append("shutdown")
				shutdown.append("-h")
				shutdown.append("now")

				subprocess.call(shutdown)
                                sys.exit(1)


if __name__ == "__main__":
	main()
