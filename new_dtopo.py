from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink  # So we can rate limit links
from mininet.cli import CLI  # So we can bring up the Mininet CLI
from mininet.node import RemoteController #remote controller
import random
import time

import json
import numpy as np
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# create trace files
with open ('flowtable.trace', 'w') as f:
	pass
with open ('path.trace', 'w') as f:
	pass


class DataPacket(dict):
	def __init__(self, host, dest, rtt, time):
		self.host = host
		self.dest = dest
		self.rtt = rtt
		self.time = time


def MyRandom():
	return np.random.uniform()*4+1

def save_weights(weights):
	with open("weights.config", "w") as f:
		json.dump(weights,f) 

def draw_plot(history, index):
	fig, ax = plt.subplots()
	for i in range(num_hosts):
		y = []
		x = []
		if i != index:
			for data in history:
				if data.dest == i:
					y.append(data.rtt)
					x.append(float(data.time))
			
			if y != []:
				x, y = zip(*sorted(zip(x, y)))
				# ax.scatter(x, y, label=i+1)
				ax.plot(x, y, label=i+1)

	plt.title(str(index + 1))
	plt.xlabel('time s')	
	plt.ylabel('rtt ms')
	ax.legend()
	plt.savefig("./pics/plt" + str(index + 1) + ".png")
	plt.close() 

c0 = RemoteController( 'c0', ip='127.0.0.1', port=6633 )

# 5
num_runs = 5
# 6
num_net_up = 6
# num hosts
num_hosts = 7

history = [[] for i in range(num_hosts)]
switches = ['s1', 's2', 's3', 's4']
base_time = time.time()

for i in range(num_runs):
	for j in range(num_net_up):

		# all possible connections between switches
		mask = {}
		for s1 in switches:
			mask[s1] = {}
			for s2 in switches:
				mask[s1][s2] = False

		# costumize links mask
		mask['s1']['s2'] = True
		mask['s2']['s3'] = True
		mask['s3']['s4'] = True

		weights = {}
		bws = {}
		for i, s in enumerate(switches):
			weights[i+1] = {}
			bws[s] = {}
		for i in range(len(switches)):
			for j in range(i+1, len(switches)):
				if not mask[switches[i]][switches[j]]:
					continue
				rand = MyRandom()
				bws[switches[i]][switches[j]] = rand
				bws[switches[j]][switches[i]] = rand
				weights[i+1][j+1] = 1/rand
				weights[j+1][i+1] = 1/rand
		save_weights(weights)

		topo = Topo()  # Create an empty topology

		# Add hosts
		h1 = topo.addHost( 'h1' )
		h2 = topo.addHost( 'h2' )
		h3 = topo.addHost( 'h3' )
		h4 = topo.addHost( 'h4' )
		h5 = topo.addHost( 'h5' )
		h6 = topo.addHost( 'h6' )
		h7 = topo.addHost( 'h7' )

		# Add switches
		s1 = topo.addSwitch( 's1' )
		s2 = topo.addSwitch( 's2' )
		s3 = topo.addSwitch( 's3' )
		s4 = topo.addSwitch( 's4' )

		# Add links
		bw = MyRandom()
		topo.addLink('h1', 's1', bw=bw, use_htb=True, cls=TCLink)
		bw = MyRandom()
		topo.addLink('h2', 's2', bw=bw, use_htb=True, cls=TCLink)
		bw = MyRandom()
		topo.addLink('h3', 's3', bw=bw, use_htb=True, cls=TCLink)
		bw = MyRandom()
		topo.addLink('h4', 's3', bw=bw, use_htb=True, cls=TCLink)
		bw = MyRandom()
		topo.addLink('h5', 's4', bw=bw, use_htb=True, cls=TCLink)
		bw = MyRandom()
		topo.addLink('h6', 's4', bw=bw, use_htb=True, cls=TCLink)
		bw = MyRandom()
		topo.addLink('h7', 's4', bw=bw, use_htb=True, cls=TCLink)

		bw = weights[1][2]
		topo.addLink('s1', 's2', bw=bw, use_htb=True, cls=TCLink)
		bw = weights[2][3]
		topo.addLink('s2', 's3', bw=bw, use_htb=True, cls=TCLink)
		# topo.addLink('s1', 's3')
		bw = weights[3][4]
		topo.addLink('s3', 's4', bw=bw, use_htb=True, cls=TCLink)
		# topo.addLink('s2', 's4')


		net = Mininet(topo=topo, controller=c0)
		net.start()

		time.sleep(2)
		net.pingAll()
		
		# Getting hosts from network
		hosts = []
		for i in range(num_hosts):
			hosts.append(net.get('h'+str(i+1)))
		# print(hosts)

		# need to change links every 10 secs
		begin_time = time.time()
		while time.time() - begin_time < 10:

			# random destinations for every host
			rand_index = [0] * num_hosts
			for rand_dest in range(num_hosts):
				rand_index[rand_dest] = random.randint(0, 6)

			
			# need to change connections every 100 ms
			start_time = time.time()
			# seding tcp packets with size 100000 bytes for 100 ms
			while time.time() - start_time < 0.1:
				for host_num in range(num_hosts):
					log = hosts[host_num].cmd('hping3 -d 100000 -c 3', hosts[rand_index[host_num]].IP())
					log_split =  log.split()
					rtt = log_split[23]
					if (rtt[0:3] == 'rtt'):
						rtt_number = rtt[4:]
						history[host_num].append(DataPacket(host_num, rand_index[host_num], float(rtt_number)/ 2, float(time.time() - start_time)))
						
					# else:
					# 	print(log_split)

		# CLI(net)  # Bring up the mininet CLI
		net.stop()	

for i in range(num_hosts):
	print('creating plot #' + str(i+1))
	draw_plot(history[i], i)
