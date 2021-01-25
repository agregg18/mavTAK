#!/usr/bin/env python3

from pymavlink import mavutil
import CoT
import argparse
import math

params = {
    "uid": "MAVLink-UAS",
    "identity": "friend",
    "dimtype": "",
    "how": "m-g", # machine-GPS
    "lat": 0.0,
    "lon": 0.0, 
    "hae": 0.0,
    "ce": 9999999.0,
    "le": 9999999.0,
    "course": 0.0,
    "speed": 0.0,
    "remarks": ""
}

MAVDIMTYPE = {
    0: "A-C",     #MAV_TYPE_GENERIC
    1: "A-M-F-Q", #MAV_TYPE_FIXED_WING
    2: "A-M-H-Q", #MAV_TYPE_QUADROTOR
    3: "A-M-H-Q", #MAV_TYPE_COAXIAL
    4: "A-M-H-Q", #MAV_TYPE_HELICOPTER
    5: "G-E", #MAV_TYPE_ANTENNA_TRACKER
    6: "G-U-C-V-U", #MAV_TYPE_GCS
    7: "A-M-L", #MAV_TYPE_AIRSHIP
    8: "A-M-L", #MAV_TYPE_FREE_BALLOON
    9: "A-W", #MAV_TYPE_ROCKET
    10: "G-E-V", #MAV_TYPE_GROUND_ROVER
    11: "S", #MAV_TYPE_SURFACE_BOAT
    12: "U-W-V", #MAV_TYPE_SUBMARINE
    13: "M-H-Q", #MAV_TYPE_HEXAROTOR
    14: "M-H-Q", #MAV_TYPE_OCTOROTOR
    15: "M-H-Q", #MAV_TYPE_TRICOPTER
    16: "M-F-Q", #MAV_TYPE_FLAPPING_WING
    17: "A-M-L", #MAV_TYPE_KITE -- Technically a kite is not lighter than air
    18: "", #MAV_TYPE_ONBOARD_CONTROLLER
    19: "M-F-Q", #MAV_TYPE_VTOL_DUOROTOR
    20: "M-F-Q", #MAV_TYPE_VTOL_QUADROTOR
    21: "M-F-Q", #MAV_TYPE_VTOL_TILTROTOR
    22: "M-F-Q", #MAV_TYPE_VTOL_RESERVED2
    23: "M-F-Q", #MAV_TYPE_VTOL_RESERVED3
    24: "M-F-Q", #MAV_TYPE_VTOL_RESERVED4
    25: "M-F-Q", #MAV_TYPE_VTOL_RESERVED5
    26: "", #MAV_TYPE_GIMBAL
    27: "", #MAV_TYPE_ADSB
    28: "A", #MAV_TYPE_PARAFOIL
    29: "", #MAV_TYPE_DODECAROTOR
    30: "", #MAV_TYPE_CAMERA
    31: "", #MAV_TYPE_CHARGING_STATION
    32: "", #MAV_TYPE_FLARM
    33: "", #MAV_TYPE_SERVO
    34: "", #MAV_TYPE_ODID
    35: "", #MAV_TYPE_DECAROTOR
}

def get_mavlink(m):
    # Get position, heading, and velocity
    msg = m.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
    if not msg:
        return
    if msg.get_type() == "BAD_DATA":
        if mavutil.all_printable(msg.data):
            sys.stdout.write(msg.data)
            sys.stdout.flush()
    else:
        #Message is valid
        params['lat'] = msg.lat/10000000
        params['lon'] = msg.lon/10000000
        params['hae'] = msg.alt/1000 # TODO: Convert to HAE from MSL
        params['course'] = msg.hdg/100 # TODO: Check mag/true
        params['speed'] = math.sqrt((msg.vx)**2 + (msg.vy)**2)/100

    # Get battery remaining
    msg = m.recv_match(type='SYS_STATUS', blocking=False)
    if not msg:
        return
    if msg.get_type() == "BAD_DATA":
        if mavutil.all_printable(msg.data):
            sys.stdout.write(msg.data)
            sys.stdout.flush()
    else:
        #Message is valid
        params['remarks'] = 'Battery Remaining: ' + str(msg.battery_remaining) + '%'
     
#    TODO: Get Current Mission Point and request the current route?
#    msg = m.recv_match(type='MISSION_CURRENT', blocking=False)
#    if not msg:
#        return
#    if msg.get_type() == "BAD_DATA":
#        if mavutil.all_printable(msg.data):
#            sys.stdout.write(msg.data)
#            sys.stdout.flush()
#    else:
#        #Message is valid
#        #print("Got a message with id %u and fields %s" % (msg.get_msgId(), msg.get_fieldnames()))
#        print (msg.seq)
  
if __name__ == '__main__':
    cot = CoT.CursorOnTarget()

    parser = argparse.ArgumentParser()
    parser.add_argument("--MAVaddr", help="address to listen on for MAVLink", default="localhost")
    parser.add_argument("--MAVport", help="port to listen on for MAVLink", type=int, default=14445)
    parser.add_argument("--TAKproto", help="protocol to send CoT to TAK: tcp, udp or broadcast", default="broadcast")
    parser.add_argument("--TAKaddr", help="address to send CoT to TAK")
    parser.add_argument("--TAKport", help="port", type=int, default=4242)
    parser.add_argument("--debug", help="debug output", action="store_true")
    args = parser.parse_args()
                                                                                   
    MAVaddr = args.MAVaddr or 'locahost'
    MAVport = args.MAVport or 14445

    print('Waiting for first heartbeat from MAVLink on %s:%d' % (MAVaddr, MAVport))
    mav = mavutil.mavlink_connection('udpin:' + MAVaddr + ':' + str(MAVport))
    mav.wait_heartbeat()
    print("Received heartbeat from system (system %u type %u)" % (mav.target_system, mav.mav_type))
    
    #Set the Battle Dimension and Type from the mav_type
    params['dimtype'] = MAVDIMTYPE[mav.mav_type];

    sender = None 
    if args.TAKproto.lower() == 'udp':
        TAKaddr = args.TAKaddr or 'locahost'
        TAKport = args.TAKport or 4242
        print('sending via udp to %s:%d' % (TAKaddr, TAKport))
        sender = cot.send_udp
    elif args.TAKproto.lower() == 'tcp':
        TAKaddr = args.TAKaddr or 'locahost'
        TAKport = args.TAKport or 4242
        print('sending via tcp to %s:%d' % (TAKaddr, TAKport))
        sender = cot.send_tcp
    elif args.TAKproto.lower() == 'broadcast':
        TAKaddr = args.TAKaddr or '192.168.1.255'
        TAKport = args.TAKport or 4242
        print('sending via broadcast to %s:%d' % (TAKaddr, TAKport))
        sender = cot.send_broadcast

    while True:
        get_mavlink(mav)
        cot_xml = cot.atoms(params)   
        #print(cot_xml)
        if sender is not None:
            sender(TAKaddr, TAKport, cot_xml)
        #time.sleep(0.1)