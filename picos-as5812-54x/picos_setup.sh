#!/bin/bash 

# change the switch operating mode to ovs
sudo sed -i 's/^picos_start\=xorpplus/picos_start\=ovs/' /etc/picos/picos_start.conf

# restart picos 
sudo /etc/init.d/picos restart

# create ovs bridge
ovs-vsctl add-br br0 --set bridge br0 datapath_type=pica8

# double check bridge settings
ovs-ofctl show br0 
ovs-vsctl show 

# associate openflow datapath to controller 
ovs-vsctl set-controller br0 tcp:192.168.2.115:6633

# set the default openflow version 
ovs-vsctl set bridge br0 protocols=OpenFlow13

# add physical ports to the bridge 
ovs-vsctl add-port br0 te-1/1/1
ovs-vsctl add-port br0 te-1/1/2
ovs-vsctl add-port br0 te-1/1/3
ovs-vsctl add-port br0 te-1/1/4 
