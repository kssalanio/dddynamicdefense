#!/usr/bin/python

"""
Simple python function that formats and sends OpenDaylight VTN API calls

sendToController: REST API call to controller
resetDefaultConfig: deletes created VTN 'vtn1'
getVTNConfig: retrieve current VTN config
"""

import requests
import json

CONTROLLER_IP='<controller IP address>'
AUTH=('admin','admin')
HEADERS = {
    'content-type': 'application/json',
    'ipaddr': '{}'.format(CONTROLLER_IP),
}

def sendToController(data=None,request=None,edge=None,
                     auth=AUTH,headers=HEADERS):

    if request == 'POST':
        response = requests.post('http://{}:8181/restconf/{}'.format(CONTROLLER_IP,edge),
            headers=headers, data=data, auth=auth)

    elif request == 'GET':
        response = requests.get('http://{}:8181/restconf/{}'.format(CONTROLLER_IP,edge),
            headers=headers, data=data, auth=auth)

    elif request == 'PUT':
        response = requests.put('http://{}:8181/restconf/{}'.format(CONTROLLER_IP,edge),
            headers=headers, data=data, auth=auth)

    elif request == 'DELETE':
        response = requests.post('http://{}/restconf/{}'.format(CONTROLLER_IP,edge),
            headers=headers, data=data, auth=auth)

    else:
        'invalid HTTP request type'

    print(response)
    try:
        json_data = json.loads(response.text)
        print(json_data)
    except:
        pass

def resetDefaultConfig():
    e = 'operations/vtn:remove-vtn'
    d = '{"input":\
            {"tenant-name":"vtn1"}\
        }'
    sendToController(data=d,edge=e,request='POST')

    e = 'operations/vtn-flow-condition:remove-flow-condition'
    d = '{"input":\
            {"name":"cond_1"}\
        }'
    sendToController(data=d,edge=e,request='POST')

    e = 'operations/vtn-flow-condition:remove-flow-condition'
    d = '{"input":{"name":"cond_2"}}'
    sendToController(data=d,edge=e,request='POST')

    e = 'operations/vtn-flow-condition:remove-flow-condition'
    d = '{"input":{"name":"cond_any"}}'
    sendToController(data=d,edge=e,request='POST')

def getVTNConfig():
    e = 'operational/vtn:vtns'
    sendToController(edge=e,request='GET')