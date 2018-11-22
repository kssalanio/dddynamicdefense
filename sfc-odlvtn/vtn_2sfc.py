"""
instantiate an SDN-created VTN using REST calls to the ODL-VTN API.

creates a VTN where destination port 80 redirects to component [f1]
    and destination port 25 to component [f2] before being routed to
    the interface going to the gateway.

"""

from vtn_2sfc.py import *

print('set debugging PUT request')
e = 'config/vtn-static-topology:vtn-static-topology/static-edge-ports'
d = '{"static-edge-ports": {"static-edge-port": [ {"port": "openflow:3:3"}, {"port": "openflow:3:4"}, {"port": "openflow:4:3"}, {"port": "openflow:4:4"}]}}'
sendToController(data=d,edge=e,request='PUT')

print('** CREATE VTN vtn1')
e = 'operations/vtn:update-vtn'
d ='{"input":{"tenant-name":"vtn1","update-mode":"CREATE","operation":"SET","description":"creating vtn","idle-timeout":300,"hard-timeout":0}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE BRIDGE vbr')
e = 'operations/vtn-vbridge:update-vbridge'
d = '{"input":{"update-mode":"CREATE","operation":"SET","description":"creating vbr","tenant-name":"vtn1","bridge-name":"vbr1"}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE if1')
e = 'operations/vtn-vinterface:update-vinterface'
d = '{"input":{"update-mode":"CREATE","operation":"SET","description":"Creating vbrif1 interface","tenant-name":"vtn1","bridge-name":"vbr1","interface-name":"if1"}}'
sendToController(data=d,edge=e,request='POST')

print('** MAP if1 to s1-eth2')
e = 'operations/vtn-port-map:set-port-map'
d = '{"input":{"vlan-id":0,"tenant-name":"vtn1","bridge-name":"vbr1","interface-name":"if1","node":"openflow:1","port-name":"s1-eth2"}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE if2')
e = 'operations/vtn-vinterface:update-vinterface'
d = '{"input":{"update-mode":"CREATE","operation":"SET","description":"Creating vbrif2 interface","tenant-name":"vtn1","bridge-name":"vbr1","interface-name":"if2"}}'
sendToController(data=d,edge=e,request='POST')

print('** MAP if2 to s2-eth2')
e = 'operations/vtn-port-map:set-port-map'
d = '{"input":{"vlan-id":0,"tenant-name":"vtn1","bridge-name":"vbr1","interface-name":"if2","node":"openflow:2","port-name":"s2-eth2"}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE if 3')
e = 'operations/vtn-vinterface:update-vinterface'
d = '{"input":{"update-mode":"CREATE","operation":"SET","description":"Creating vbrif3 interface","tenant-name":"vtn1","bridge-name":"vbr1","interface-name":"if3"}}'
sendToController(data=d,edge=e,request='POST')

print('** MAP if3 to s2-eth3')
e = 'operations/vtn-port-map:set-port-map'
d = '{"input":{"vlan-id":0,"tenant-name":"vtn1","bridge-name":"vbr1","interface-name":"if3","node":"openflow:2","port-name":"s2-eth3"}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE vterminal vt_srvc1_1 and its IF')
e = 'operations/vtn-vterminal:update-vterminal'
d = '{"input":{"update-mode":"CREATE","operation":"SET","tenant-name":"vtn1","terminal-name":"vt_srvc1_1","description":"Creating vterminal"}}'
sendToController(data=d,edge=e,request='POST')

e = 'operations/vtn-vinterface:update-vinterface'
d = '{"input":{"update-mode":"CREATE","operation":"SET","description":"Creating vterminal IF","enabled":"true","tenant-name":"vtn1","terminal-name":"vt_srvc1_1","interface-name":"IF"}}'
sendToController(data=d,edge=e,request='POST')

print('** MAP vt_srvc1_1 to s3-eth3')
e = 'operations/vtn-port-map:set-port-map'
d = '{"input":{"tenant-name":"vtn1","terminal-name":"vt_srvc1_1","interface-name":"IF","node":"openflow:3","port-name":"s3-eth3"}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE vterminal vt_srvc1_2 and its IF')
e = 'operations/vtn-vterminal:update-vterminal'
d = '{"input":{"update-mode":"CREATE","operation":"SET","tenant-name":"vtn1","terminal-name":"vt_srvc1_2","description":"Creating vterminal"}}'
sendToController(data=d,edge=e,request='POST')

e = 'operations/vtn-vinterface:update-vinterface'
d = '{"input":{"update-mode":"CREATE","operation":"SET","description":"Creating vterminal IF","enabled":"true","tenant-name":"vtn1","terminal-name":"vt_srvc1_2","interface-name":"IF"}}'
sendToController(data=d,edge=e,request='POST')

print('** MAP vt_srvc1_2 to s4-eth3')
e = 'operations/vtn-port-map:set-port-map'
d = '{"input":{"tenant-name":"vtn1","terminal-name":"vt_srvc1_2","interface-name":"IF","node":"openflow:4","port-name":"s4-eth3"}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE FLOW cond_1 and cond_any')
e = 'operations/vtn-flow-condition:set-flow-condition'
d = '{"input":{"operation":"SET","present":"false","name":"cond_1","vtn-flow-match":[{"index":1,"vtn-ether-match":{},"vtn-inet-match":{"source-network":"10.0.0.2/32","destination-network":"10.0.0.4/32"}}]}}'
sendToController(data=d,edge=e,request='POST')

e = 'operations/vtn-flow-condition:set-flow-condition'
d = '{"input":{"operation":"SET","present":"false","name":"cond_any","vtn-flow-match":[{"index":1}]}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE ACTION redirects vt_srvc1_2 to bridge1-IF2')
e = 'operations/vtn-flow-filter:set-flow-filter'
d = '{"input":{"output":"false","tenant-name":"vtn1","terminal-name":"vt_srvc1_2","interface-name":"IF","vtn-flow-filter":[{"condition":"cond_any","index":10,"vtn-redirect-filter":{"redirect-destination":{"bridge-name":"vbr1","interface-name":"if2"},"output":"true"}}]}}'
sendToController(data=d,edge=e,request='POST')

print('** CREATE ACTION redirects Bridge1-IF1 to vt_srvc1_1')
e = 'operations/vtn-flow-filter:set-flow-filter'
d = '{"input":{"output":"false","tenant-name":"vtn1","bridge-name":"vbr1","interface-name":"if1","vtn-flow-filter":[{"condition":"cond_1","index":10,"vtn-redirect-filter":{"redirect-destination":{"terminal-name":"vt_srvc1_1","interface-name":"IF"},"output":"true"}}]}}'
sendToController(data=d,edge=e,request='POST')
