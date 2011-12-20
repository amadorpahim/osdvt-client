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

import socket, ssl, pprint
import sys
import pygtk
import gtk
import gtk.glade
import gobject
import os
import subprocess
import socket
import fcntl
import struct
import time
from threading import Thread
pygtk.require("2.0")

#################################################
#################################################
#################################################
# New spice client (spicy) - "spice-gtk-tools" package.
spice_client = "/usr/bin/spicy"
# Old spice client (spicec) - "spice-client" package.
old_spice_client = "/usr/bin/spicec"
# VNC client.
vnc_client = "/usr/bin/vinagre"
# sudo is necessary to usb_redir
EnableSudo = True
#################################################
port = 6970
cacert = os.getenv('HOME')+"/osdvt/cacert.pem"
#################################################
#################################################
#################################################

DisableSpice = False
DisableVnc = False
if not os.path.isfile(spice_client):
	print "New spice client not found (%s). USB redirection will not work. Please, install spice-gtk-tools package. Trying old Client %s..." %(spice_client,old_spice_client)
	if os.path.isfile(old_spice_client):
		print "Ok, old Spice Client found (%s)." %(old_spice_client)
		spice_client = old_spice_client
	else:
		DisableSpice = True
		print "Old spice client not found (%s). You can't access your VMs through SPICE protocol." %(old_spice_client)

if not os.path.isfile(vnc_client):
	DisableVnc = True
	print "VNC client not found (%s). You can't access your VMs through VNC protocol." %(vnc_client)

if not EnableSudo:
	print "Sudo is disabled. 'spicy' client needs root rights to use USB redirection."

def quit(*args, **kwargs):
	global VarSaida
	VarSaida=False
	gtk.main_quit(*args, **kwargs)
	sys.exit()

VarSaida = True
class Principal:

	def kill(self, func, cmb_main_vms):

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ssl_sock = ssl.wrap_socket(s,
			ca_certs=cacert,
 			cert_reqs=ssl.CERT_REQUIRED)

		ssl_sock.connect((self._server, self._port))
		ssl_sock.write( "KILL " + cmb_main_vms.get_active_text() + " " + self._token)
		ssl_sock.close()
		s.close()
	
	def ligar(self, func, cmb_main_vms):

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ssl_sock = ssl.wrap_socket(s,
			ca_certs=cacert,
 			cert_reqs=ssl.CERT_REQUIRED)

		ssl_sock.connect((self._server, self._port))
		ssl_sock.write( "START " + cmb_main_vms.get_active_text() + " " + self._token)
		ssl_sock.close()
		s.close()
	
	def conectar(self, func, cmb_main_vms, checkbutton1):

            	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ssl_sock = ssl.wrap_socket(s,
                        ca_certs=cacert,
                        cert_reqs=ssl.CERT_REQUIRED)

                ssl_sock.connect((self._server, self._port))
                ssl_sock.write( "CONNECT " + cmb_main_vms.get_active_text() + " " + self._token)

		data = ssl_sock.read()
                ssl_sock.close()
		s.close()

		if data.split()[0] != "ERR":
			cmnd = []

			if data.split().__len__() is 3:

				if data.split()[2] == "0":

					if EnableSudo:
						cmnd.append("sudo")
	
					cmnd.append(spice_client)
					cmnd.append("-h") 
					cmnd.append("%s" % (self._server)) 
					cmnd.append("-p") 
					cmnd.append("%s" % (data.split()[0])) 
					cmnd.append("-w") 
					cmnd.append("%s" % (data.split()[1])) 
		
					if checkbutton1.get_active():
						cmnd.append("-f")
	
				if data.split()[2] == "1":
					cmnd.append(vnc_client)
					cmnd.append("%s:%s" % (self._server,int(data.split()[0])%5900)) 

					if checkbutton1.get_active():
						cmnd.append("-f")
		
			else:
				cmnd.append(spice_client)
				cmnd.append("-h")
				cmnd.append("%s" % (self._server))
				cmnd.append("-p")
				cmnd.append("%s" % (data.split()[0]))
				cmnd.append("-w")
				cmnd.append("%s" % (data.split()[1]))

				if checkbutton1.get_active():
					cmnd.append("-f")
					
			subprocess.Popen(cmnd)

	def status(self, sta_main, cmb_main_vms, btn_main_start, btn_main_kill, btn_main_connect, btn_main_refresh,checkbutton1,lab_Smp,lab_Memory,lab_Video,lab_Bits,lab_Os):
		if cmb_main_vms.get_active_text() and cmb_main_vms.get_active_text() != "VM not found": 
			try:	
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		                ssl_sock = ssl.wrap_socket(s,
		                                           ca_certs=cacert,
		                                           cert_reqs=ssl.CERT_REQUIRED)
		
		                ssl_sock.connect((self._server, self._port))
				ssl_sock.write( "STATUS " + cmb_main_vms.get_active_text() + " " + self._token)
		
				data = ssl_sock.read()
				ssl_sock.close()
				s.close()

				btn_main_refresh.set_sensitive(True)
		
				if data.split()[0] == "ERR:":
					checkbutton1.set_sensitive(False)
					cmb_main_vms.set_sensitive(False)
					btn_main_refresh.set_sensitive(True)
					btn_main_start.set_sensitive(False)
					btn_main_kill.set_sensitive(False)
					btn_main_connect.set_sensitive(False)
					sta_main.push(0,"Server was restarted. Please click 'Refresh'.")
					

				else:
					if data.split()[0] == "True":
						status_vm = "Running"
	
						checkbutton1.set_sensitive(True)
						cmb_main_vms.set_sensitive(True)
						btn_main_refresh.set_sensitive(True)
	
						btn_main_start.set_sensitive(False)
						btn_main_kill.set_sensitive(True)

						if (data.split().__len__() == 1 or data.split()[3] == "SPICE") and DisableSpice is True:
							btn_main_connect.set_sensitive(False)
						elif data.split().__len__() > 1 and data.split()[3] == "VNC" and DisableVnc is True:
							btn_main_connect.set_sensitive(False)
						else:
							btn_main_connect.set_sensitive(True)
				
					else:
						status_vm = "Power off"
						checkbutton1.set_sensitive(True)
						cmb_main_vms.set_sensitive(True)
						btn_main_refresh.set_sensitive(True)

						btn_main_start.set_sensitive(True)
						btn_main_kill.set_sensitive(False)
						btn_main_connect.set_sensitive(False)
			
					if data.split().__len__() > 1:
						lab_Smp.set_text(data.split()[1])
						lab_Memory.set_text(data.split()[2])
						lab_Video.set_text(data.split()[3])
						lab_Bits.set_text(data.split()[4])
						lab_Os.set_text(data.split()[5])

					sta_main.push(0,cmb_main_vms.get_active_text()+" - "+status_vm)
			except:
				checkbutton1.set_sensitive(False)
				cmb_main_vms.set_sensitive(False)
				btn_main_refresh.set_sensitive(False)
				btn_main_start.set_sensitive(False)
				btn_main_kill.set_sensitive(False)
				btn_main_connect.set_sensitive(False)
				sta_main.push(0,"Connection lost.")

		else:
			checkbutton1.set_sensitive(False)
			btn_main_start.set_sensitive(False)
			btn_main_kill.set_sensitive(False)
			btn_main_connect.set_sensitive(False)


	
	def status2(self, sta_main, cmb_main_vms, btn_main_start, btn_main_kill, btn_main_connect, btn_main_refresh,checkbutton1,lab_Smp,lab_Memory,lab_Video,lab_Bits,lab_Os):
		global VarSaida
		while VarSaida:
			self.status(sta_main, cmb_main_vms, btn_main_start, btn_main_kill, btn_main_connect, btn_main_refresh,checkbutton1,lab_Smp,lab_Memory,lab_Video,lab_Bits,lab_Os)
			time.sleep(0.4)


	def auth(self, func, ent_auth_user, ent_auth_pass, ent_auth_server, window1, window2, sta_auth, sta_main, cmb_main_vms, btn_main_start, btn_main_kill, btn_main_connect, liststore, btn_main_refresh, checkbutton1,lab_Smp,lab_Memory,lab_Video,lab_Bits,lab_Os):
		try:
	                self._server=ent_auth_server.get_text()
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			ssl_sock = ssl.wrap_socket(s,
			                           ca_certs=cacert,
			                           cert_reqs=ssl.CERT_REQUIRED)
		
			ssl_sock.connect((self._server, self._port))
			ssl_sock.write("AUTH "+ent_auth_user.get_text()+" "+ent_auth_pass.get_text())
			data = ssl_sock.read()
			ssl_sock.close()
			s.close()
			if data.split()[0] == "OK:":
				window1.hide()
				window2.show()
				self._token = data.split()[1]
				self.procurar(self.procurar, ent_auth_user, cmb_main_vms, liststore)
				t = Thread(target=self.status2, kwargs=dict(sta_main=sta_main,cmb_main_vms=cmb_main_vms,btn_main_start=btn_main_start,btn_main_kill=btn_main_kill,btn_main_connect=btn_main_connect,btn_main_refresh=btn_main_refresh,checkbutton1=checkbutton1,lab_Smp=lab_Smp,lab_Memory=lab_Memory,lab_Video=lab_Video,lab_Bits=lab_Bits,lab_Os=lab_Os))
				t.start()
			else:
				sta_auth.push(0,data)
		except:
			sta_auth.push(0,"Can't connect.")

	def procurar(self, func, ent_auth_user, cmb_main_vms, liststore):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ssl_sock = ssl.wrap_socket(s,
		                           ca_certs=cacert,
		                           cert_reqs=ssl.CERT_REQUIRED)
		ssl_sock.connect((self._server, self._port))
		ssl_sock.write("SEARCH "+ent_auth_user.get_text()+" "+self._token) 
		data = ssl_sock.read()
		ssl_sock.close()
		s.close()
		
		liststore.clear()
		if data.split()[0] == "ERR:":
			liststore.append(["VM not found"])
		else:
		       	for entry in data.split():
		       		liststore.append([entry])

		cmb_main_vms.set_active(0)
		return cmb_main_vms

        def __init__(self):
		self._token = ""
		self._server = ""
		self._port = port
                gtk.gdk.threads_init()
                self.gladefile = os.getenv('HOME')+"/osdvt/osdvt-client.glade"
                self.wTree = gtk.glade.XML(self.gladefile)
                self.window1 = self.wTree.get_widget("window1")
                self.window2 = self.wTree.get_widget("window2")
                if (self.window1):
                        self.window1.connect("destroy", quit)
                if (self.window2):
                        self.window2.connect("destroy", quit)

		btn_auth_ok=self.wTree.get_widget("button1")
                btn_auth_cancel=self.wTree.get_widget("button2")
		ent_auth_user=self.wTree.get_widget("entry1")
                ent_auth_pass=self.wTree.get_widget("entry2")
                ent_auth_server=self.wTree.get_widget("entry3")
                sta_auth=self.wTree.get_widget("statusbar1")
                sta_main=self.wTree.get_widget("statusbar2")

		lab_Smp=self.wTree.get_widget("label7")
		lab_Memory=self.wTree.get_widget("label9")
		lab_Video=self.wTree.get_widget("label11")
		lab_Bits=self.wTree.get_widget("label13")
		lab_Os=self.wTree.get_widget("label15")
		
		btn_main_refresh=self.wTree.get_widget("button3")
		btn_main_start=self.wTree.get_widget("button4")
		btn_main_connect=self.wTree.get_widget("button5")
		btn_main_kill=self.wTree.get_widget("button6")
		checkbutton1=self.wTree.get_widget("checkbutton1")

		cmb_main_vms=self.wTree.get_widget("combobox1")
        	liststore = gtk.ListStore(gobject.TYPE_STRING)
        	cmb_main_vms.set_model(liststore)
        	cell = gtk.CellRendererText()
        	cmb_main_vms.pack_start(cell, True)
        	cmb_main_vms.add_attribute(cell, 'text', 0)


		btn_main_refresh.connect( "clicked", self.procurar, ent_auth_user, cmb_main_vms, liststore)
		btn_main_start.connect( "clicked", self.ligar, cmb_main_vms)
		btn_main_kill.connect( "clicked", self.kill, cmb_main_vms)
		btn_main_connect.connect( "clicked", self.conectar, cmb_main_vms, checkbutton1)

		
		btn_auth_ok.connect( "clicked", self.auth, ent_auth_user, ent_auth_pass, ent_auth_server, self.window1, self.window2, sta_auth, sta_main, cmb_main_vms, btn_main_start, btn_main_kill, btn_main_connect, liststore, btn_main_refresh, checkbutton1,lab_Smp,lab_Memory,lab_Video,lab_Bits,lab_Os)
		btn_auth_cancel.connect( "clicked", quit)


                self.window1.show()

if __name__ == "__main__":
        hwg = Principal()
        gtk.main()
