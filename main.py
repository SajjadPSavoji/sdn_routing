# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An OpenFlow 1.0 L2 learning switch implementation.
"""


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.topology.api import get_switch, get_link, get_host
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches

import json
def load_wights():
	with open('weights.config') as f:
		return json.load(f)


class SimpleSwitch(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(SimpleSwitch, self).__init__(*args, **kwargs)
		self.mac_to_port = {}
		self.topology_api_app = self

		self.datapath_list = []
		self.switches = []

		self.adjacency = {} #map[sw1][sw2] -> port
		self.mymac = {} 
		self.weights = {} #map[sw1][sw2] -> w12


	def get_min(self, distances, remining_nodes):
		min = float('inf')
		min_node = None

		for node in remining_nodes:
			if distances[node] < min:
				min = distances[node]
				min_node = node

		return min_node

	def dijkestra(self, src,dst):
		distances = {}
		prev = {}

		#init table
		for dpid in self.switches:
			distances[dpid] = float('inf')
			prev[dpid] = None	
		distances[src] = 0

		# print 'initial distances', distances


		remaining_nodes = set(self.switches[::])
		while len(remaining_nodes)>0:
			# print 'len remaining nodes ', len(remaining_nodes)
			node = self.get_min(distances, remaining_nodes)
			# print 'selected node', node
			remaining_nodes.remove(node)
			for r_node in remaining_nodes:
				if r_node in self.adjacency[node]:
					if distances[node] + self.weights[node][r_node] < distances[r_node]:
						distances[r_node] = distances[node] + self.weights[node][r_node]
						prev[r_node] = node

		#back track in path
		path = []
		# print 'before loop kiri'
		x = dst
		path.append(x)
		while (not prev[x] == src) and (not prev[x] is None):
			x = prev[x]
			path.append(x)
		# print 'after loop kiri'
		path.append(src)
		# print 'path= ', path[::-1]

		return self.adjacency[src][x]

	def add_flow(self, datapath, in_port, dst, src, actions):
		ofproto = datapath.ofproto

		match = datapath.ofproto_parser.OFPMatch(
			in_port=in_port,
			dl_dst=haddr_to_bin(dst), dl_src=haddr_to_bin(src))

		mod = datapath.ofproto_parser.OFPFlowMod(
			datapath=datapath, match=match, cookie=0,
			command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
			priority=ofproto.OFP_DEFAULT_PRIORITY,
			flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
		datapath.send_msg(mod)

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto

		pkt = packet.Packet(msg.data)
		eth = pkt.get_protocol(ethernet.ethernet)

		if eth.ethertype == ether_types.ETH_TYPE_LLDP:
			# ignore lldp packet
			return
		dst = eth.dst
		src = eth.src

		dpid = datapath.id
		self.mac_to_port.setdefault(dpid, {})


		# learn a mac address to avoid FLOOD next time.
		self.mac_to_port[dpid][src] = msg.in_port
		# print 'mac to port', self.mac_to_port

		if not src in self.mymac:
			self.mymac[src] = (dpid, msg.in_port)

		if dst in self.mymac and self.mymac[dst][0] == dpid:
			print '_______ONE HUP__________'
			# self.logger.info("packet in %s %s %s %s", dpid, src, dst, msg.in_port)
			# print 'my mac', self.mymac
			out_port = self.mymac[dst][1]
		elif dst in self.mymac:
			print '___________ perform dijkestra ___________'
			# self.logger.info("packet in %s %s %s %s", dpid, src, dst, msg.in_port)
			# print 'my mac', self.mymac
			# sw_src = self.mymac[src][0]
			sw_src = dpid
			sw_dst = self.mymac[dst][0]
			# print 'sw_srd: ', sw_src, 'sw_dst:', sw_dst
			# print '*********befor dij'
			out_port = self.dijkestra(sw_src, sw_dst)
			# print '*********after dij'
			# print 'dij out port', out_port

		else:
			out_port = ofproto.OFPP_FLOOD

		actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

		# install a flow to avoid packet_in next time
		if out_port != ofproto.OFPP_FLOOD:
			self.add_flow(datapath, msg.in_port, dst, src, actions)

		data = None
		if msg.buffer_id == ofproto.OFP_NO_BUFFER:
			data = msg.data

		out = datapath.ofproto_parser.OFPPacketOut(
			datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
			actions=actions, data=data)
		datapath.send_msg(out)

	@set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
	def _port_status_handler(self, ev):
		msg = ev.msg
		reason = msg.reason
		port_no = msg.desc.port_no

		ofproto = msg.datapath.ofproto
		if reason == ofproto.OFPPR_ADD:
			self.logger.info("port added %s", port_no)
		elif reason == ofproto.OFPPR_DELETE:
			self.logger.info("port deleted %s", port_no)
		elif reason == ofproto.OFPPR_MODIFY:
			self.logger.info("port modified %s", port_no)
		else:
			self.logger.info("Illeagal port state %s %s", port_no, reason)


	@set_ev_cls(event.EventSwitchEnter)
	def get_topology_data(self, ev):
		print 'entered event.EvnetSwitchEnter'
		temp_dict = load_wights()
		print 'temp_dict', temp_dict
		self.weights = {}
		for key1 in temp_dict:
			self.weights[int(key1)] = {}
			for key2 in temp_dict[key1]:
				self.weights[int(key1)][int(key2)] = float(temp_dict[key1][key2])
			
		switch_list = get_switch(self.topology_api_app, None)
		switches=[switch.dp.id for switch in switch_list]
		self.switches = [switch.dp.id for switch in switch_list]
		self.datapath_list=[switch.dp for switch in switch_list]
		links_list = get_link(self.topology_api_app, None)
		srcs = [link.src for link in links_list]
		mylinks=[(link.src.dpid,link.dst.dpid,link.src.port_no,link.dst.port_no) for link in links_list]
		print 'my links', mylinks
		for s1,s2,port1,port2 in mylinks:
			# check if keys(s1 and s2 are valid)
			if not s1 in self.adjacency:
				self.adjacency[s1] = {}
			if not s2 in self.adjacency:
				self.adjacency[s2] = {}

			if not s1 in self.weights:
				self.weights[s1] = {}
			if not s2 in self.weights:
				self.weights[s2]={}

			self.adjacency[s1][s2]=port1
			self.adjacency[s2][s1]=port2

			#@TODO add real costs to self.weights
			if (not s1 in self.weights) or (not s2 in self.weights[s1]):
				self.weights[s1][s2]=1
			if (not s2 in self.weights) or (not s1 in self.weights[s2]):
				self.weights[s2][s1]=1

		print 'switches = ', self.switches
		print 'adjecency = ', self.adjacency
		print 'weights = ', self.weights