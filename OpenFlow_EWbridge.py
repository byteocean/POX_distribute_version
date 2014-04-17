import errno
import socket
import lib_ewbridge as ofpew

import Queue
import time
"""
Author: muzi
Date: 2014/4/12
TODO: handle the OpenFlow EWbridge messages

"""
#TODO:store the info.
network = {}
nodes = {}
ports = {}
links = {}
flow_paths = {}


def update_handler(data):
    #manipulate the messenge
    header = ofpew.ofpew_header(data[0:8])
    data = data[8:]
    print "update_handler"
    update_msg = ofpew.ofpew_update(data[0:8])
    data = data[8:]                  
    for x in xrange(update_msg.network_number):
        offset = 0
        network_view = ofpew.ofpew_network_view(data[0:16])
        network[x] = network_view               #store the network_view
        network_view.show()

        #offset = 16+network_view.node_number*28+network_veiw.link_number*48 +network_view.port_number*36 +network_view.flow_path_number*60
        offset = 16
        data = data[offset:]

        #we need to make sure the offset of network object.

        for i in xrange(network_view.node_number):
            #store the nodes of this network
            node_t =  ofpew.ofpew_node(data[(i-1)*28:i*28]) 
            #node_t.show()
            nodes[node_t.datapath_id] = node_t

        offset = 28*network_view.node_number
        data = data[offset:]

        for k in xrange(network_view.port_number):
            #store the ports of this network
            port_t =  ofpew.ofpew_port(data[(k-1)*36:k*36]) 
            #port_t.show()
            ports[port_t.port_id] = port_t

        offset = 36*network_view.port_number
        data = data[offset:]
        for j in xrange(network_view.link_number):
            #store the links of this network
            link_t =  ofpew.ofpew_link(data[(j-1)*48:j*48]) 
            #link_t.show()
            links[link_t.link_id] = link_t

        offset = 48*network_view.link_number
        data = data[offset:]
        for y in xrange(network_view.flow_path_number):
            #store the flwo_paths of this network
            flow_path_t =  ofpew.ofpew_flow_path(data[(y-1)*60:y*60]) 
            #flow_path_t.show()
            flow_paths[flow_path_t.flow_path_id] = flow_path_t

        offset = 60* network_view.flow_path_number
        data = data[offset:]

    return None

def notification_handler(data):
    print "***OFPEW_NOTIFICATION:"+data
    #TODO: DO something I don't know.
    return None

def down_handler(data):
    print "***OFPEW_DOWN.***"
    return None

def refresh_handler(data):
    #send the topo which is changed.
    network_number = 1
    node_number = 2
    port_number = 4
    link_number = 1
    flow_path_number = 1
    length = len(ofpew.ofpew_header())+len(ofpew.ofpew_update())+len(ofpew.ofpew_network_view())*network_number
            +len(ofpew.ofpew_node())*node_number+len(ofpew.ofpew_port())*port_number
            +len(ofpew.ofpew_link())*link_number+len(ofpew.ofpew_flow_path())*flow_path_number

    update_msg = ofpew.ofpew_update(network_number = network_number)
    network_msg = ofpew.ofpew_network_view(node_number = node_number, port_number = port_number,
                                        link_number = link_number,flow_path_number = flow_path_number)
    node_msg_1 = ofpew.ofpew_node(datapath_id = 1)
    node_msg_2 = ofpew.ofpew_node(datapath_id = 2)

    port_msg_1 = ofpew.ofpew_port(port_id = 1,node_id = 1)
    port_msg_2 = ofpew.ofpew_port(port_id = 2,node_id = 2)
    port_msg_3 = ofpew.ofpew_port(port_id = 3,node_id = 1)
    port_msg_4 = ofpew.ofpew_port(port_id = 4,node_id = 2)

    link_msg = ofpew.ofpew_link(link_id = 1,src_node_id = 1, src_port_id = 1,dst_node_id = 2, dst_port_id = 2)

    flow_path_msg = ofpew.ofpew_flow_path(flow_path_id = 1, src_in_port_id =3,src_node_id =1, src_out_port_id = 1,
                        dst_node_id = 2,dst_in_port_id = 2 ,dst_out_port_id = 4)
    header = ofpew.ofpew_header(type = 5, length =length)

    #we encapsulate the packet.
    msg = header/update_msg/network_msg/node_msg_1/node_msg_2/port_msg_1/port_msg_2/port_msg_3/port_msg_4/link_msg/flow_path_msg
    print "*****\n send update messages\n*****"
    msg.show()
    return msg
def hello_handler():
    print "OFPEW_HELLO"
    return None

def echo_handler():#send echo request.
    print "OFPEW_ECHO_REQUEST"
    msg = ofpew.ofpew_header(type = 2,length = 8)#send the ofpew_echo_request period.
    return msg
def echo_request_handler(data):
    print "OFPEW_ECHO_REPLY"
    msg = ofpew.ofpew_header(type = 3,length = 8)
    return msg

def echo_reply_handler(data):
    print "OFPEW_ECHO_REPLY"
    return None

def send_echo_handler():   
    if (int(time.time) % 5 )== 0:
        return echo_handler()

def vendor_handler(data):
    print "***OFPEW_VENDOR:"+data 
    return None

def error_handler(data):
    print "***OFPEW_ERROR:"+data
    return None

##################### manipulate the msg  ################################
def msg_handler(data):
    rmsg = ofpew.ofpew_header(data[0:8])
    body = data[8:]

    if rmsg.type == 0:
        #"OFPEW_HELLO"
        hello_handler()
        return refresh_handler(data)  #send the topo
        
    elif rmsg.type == 1:
        # "OFPEW_ERROR"
        return error_handler(data)
    elif rmsg.type == 2:
        # "OFPEW_ECHO_REQUEST"
        return echo_request_handler(data)
    
    elif rmsg.type == 3:
        # "OFPEW_ECHO_REPLY"
        #send echo request periodic.
        return echo_reply_handler(data)
    elif rmsg.type == 4:   
        #"OFPEW_VENDOR",
        return vendor_handler(data)

    elif rmsg.type == 5: 
        #"OFPEW_UPDATE"
        #read and store messenge.
        print "do something"
        return update_handler(data)

    elif rmsg.type == 6:
        #"OFPEW_NOTIFICATION"
        return notification_handler(data)

    elif rmsg.type == 7:
        #"OFPEW_REFRESH_VIEW"                 
        #ofpew_refresh_view  without any body. Just has a header. 
        #receive the refresh messenge and return new topo of update messenge by refresh_handler.
        return refresh_handler(data)  

    elif rmsg.type == 8:
        #"OFPEW_GOING_DOWN"
        return down_handler(data)    