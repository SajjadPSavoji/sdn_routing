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

def MyRandom():
	return np.random.uniform()*4+1

def save_weights(weights):
	with open("weights.config", "w") as f:
		json.dump(weights,f) 

c0 = RemoteController( 'c0', ip='127.0.0.1', port=6633 )

# 5
num_runs = 2
# 6
num_net_up = 2

switches = ['s1', 's2', 's3', 's4']
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
		bw = random.randint(0, 4) + 1
		topo.addLink('h1', 's1', bw=bw, use_htb=True, cls=TCLink)
		bw = random.randint(0, 4) + 1
		topo.addLink('h2', 's2', bw=bw, use_htb=True, cls=TCLink)
		bw = random.randint(0, 4) + 1
		topo.addLink('h3', 's3', bw=bw, use_htb=True, cls=TCLink)
		bw = random.randint(0, 4) + 1
		topo.addLink('h4', 's3', bw=bw, use_htb=True, cls=TCLink)
		bw = random.randint(0, 4) + 1
		topo.addLink('h5', 's4', bw=bw, use_htb=True, cls=TCLink)
		bw = random.randint(0, 4) + 1
		topo.addLink('h6', 's4', bw=bw, use_htb=True, cls=TCLink)
		bw = random.randint(0, 4) + 1
		topo.addLink('h7', 's4', bw=bw, use_htb=True, cls=TCLink)

		bw = random.randint(0, 4) + 1
		topo.addLink('s1', 's2', bw=bw, use_htb=True, cls=TCLink)
		bw = random.randint(0, 4) + 1
		topo.addLink('s2', 's3', bw=bw, use_htb=True, cls=TCLink)
		# topo.addLink('s1', 's3')
		bw = random.randint(0, 4) + 1
		topo.addLink('s3', 's4', bw=bw, use_htb=True, cls=TCLink)
		# topo.addLink('s2', 's4')


		net = Mininet(topo=topo, controller=c0)
		net.start()

		time.sleep(2)
		net.pingAll()

		# CLI(net)  # Bring up the mininet CLI
		net.stop()	