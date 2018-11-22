#!/usr/bin/python

"""
This example shows how to add an interface (for example a real
hardware interface) to a network after the network is created.
#TODO: run OVS switches with STP for controller to work in “looped” topologies
"""

import re
import sys

from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.link import Intf
from mininet.topolib import TreeTopo
from mininet.util import quietRun
from mininet.node import OVSController, RemoteController
from mininet.topo import Topo


class TestTopo( Topo ):
    "Test topology with a two switches and two hosts"

    def build( self ):
        # Create two hosts.
        # h1 = self.addHost('h1')
        # h2 = self.addHost('h2')
        h1 = self.addHost('h1', ip='10.158.55.11/24',
                          defaultRoute='via 10.158.55.1')
        h2 = self.addHost('h2', ip='10.158.55.12/24',
                          defaultRoute='via 10.158.55.1')

        # Create a switch
        s1 = self.addSwitch('s1', failMode="secure")
        s2 = self.addSwitch('s2', failMode="secure")
        s3 = self.addSwitch('s3', failMode="secure")

        # Add links between the switch and each host
        self.addLink( s3, h1 )
        self.addLink( s3, h2 )

        self.addLink(s1, s3)
        self.addLink(s2, s3)


def checkIntf( intf ):
    "Make sure intf exists and is not configured."
    config = quietRun( 'ifconfig %s 2>/dev/null' % intf, shell=True )
    if not config:
        error( 'Error:', intf, 'does not exist!\n' )
        exit( 1 )
    ips = re.findall( r'\d+\.\d+\.\d+\.\d+', config )
    if ips:
        error( 'Error:', intf, 'has an IP address,'
               'and is probably in use!\n' )
        exit( 1 )

if __name__ == '__main__':
    setLogLevel( 'info' )

    info( '*** Creating network\n' )
    topo = TestTopo()
    #net = Mininet( topo=topo, controller = OVSController )
    #net = Mininet(topo=topo, controller=lambda name: RemoteController(name, defaultIP='<controllerIP>', listenPort=6633))
    net = Mininet(topo=topo, controller=None)
    net.addController("c0",
                      controller=RemoteController,
                      ip='192.168.161.205',
                      port=6633)

    # switch1 = net.switches[ 0 ]
    # switch2 = net.switches[1]
    # switch3 = net.switches[2]
    switch1 = net.get("s1")
    switch2 = net.get("s2")
    switch3 = net.get("s3")

    info('switch1: ', switch1.name, '\n')
    info('switch2: ', switch2.name, '\n')
    info('switch3: ', switch3.name, '\n')

    # info( '*** Adding hardware interface', intfName, 'to switch',
    #       switch.name, '\n' )
    Intf("br-svc1", node=switch1)
    Intf("br-svc2", node=switch2)
    #Intf("br-svc1", node=switch2)
    #Intf("br-svc2", node=switch1)
    Intf("enp3s0", node=switch3)

    info( '*** Note: you may need to reconfigure the interfaces for '
          'the Mininet hosts:\n', net.hosts, '\n' )

    net.start()
    CLI( net )
    net.stop()
