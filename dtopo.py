from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink  # So we can rate limit links
from mininet.cli import CLI  # So we can bring up the Mininet CLI
from mininet.node import RemoteController #remote controller

c0 = RemoteController( 'c0', ip='127.0.0.1', port=6633 )

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
topo.addLink('h1', 's1')
topo.addLink('h2', 's2')
topo.addLink('h3', 's3')
topo.addLink('h4', 's3')
topo.addLink('h5', 's4')
topo.addLink('h6', 's4')
topo.addLink('h7', 's4')

topo.addLink('s1', 's2')
topo.addLink('s2', 's3')
topo.addLink('s3', 's1')
topo.addLink('s3', 's4')
topo.addLink('s2', 's4')

# topo.addLink("h1", "s1", bw=20.0, delay='10ms', use_htb=True)
net = Mininet(topo=topo, controller=c0)
net.start()
CLI(net)  # Bring up the mininet CLI
net.stop()