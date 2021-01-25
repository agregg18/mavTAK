#!/usr/bin/env python3

import time
import socket
import xml.etree.ElementTree as ET
import io

ID = {
    "pending": "p",
    "unknown": "u",
    "assumed-friend": "a",
    "friend": "f",
    "neutral": "n",
    "suspect": "s",
    "hostile": "h",
    "joker": "j",
    "faker": "f",
    "none": "o",
    "other": "x"
}

#Dimensions for reference only
DIM = {
    "space": "P",
    "air": "A",
    "land-unit": "G",
    "land-equipment": "G",
    "land-installation": "G",
    "sea-surface": "S",
    "sea-subsurface": "U",
    "subsurface": "U",
    "other": "X"
}

TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

class CursorOnTarget:

    def atoms(__self, unit):

        unit_id = ID[unit["identity"]] or ID["none"]
        cot_type = "a-" + unit_id
        if "dimtype" in unit:
          cot_type = cot_type + "-" + unit["dimtype"]
 
        if "uid" in unit:
            cot_id = unit["uid"]
        else:
            cot_id = uuid.uuid4().get_hex()

        zulu = time.strftime(TIME_FORMAT, time.gmtime())
        stale = time.strftime(TIME_FORMAT, time.gmtime(time.time() + 60))
        
        if "how" in unit:
            how = unit["how"]
        else:
            how = "m-g" # assume machine-GPS

        evt_attr = {
            "version": "2.0",
            "uid": cot_id,
             "time": zulu,
            "start": zulu,
            "stale": stale,
            "type": cot_type,
            "how": how,
            "type": cot_type
        }

        pt_attr = {
            "lat": str(unit["lat"]),
            "lon": str(unit["lon"]),
            "hae": str(unit["hae"]),
            "ce": str(unit["ce"]),
            "le": str(unit["le"])
        }
        
        track_attr = {
            "course": str(unit["course"]),
            "speed": str(unit["speed"]),
        } 

        cot = ET.Element('event', attrib=evt_attr)
        ET.SubElement(cot,'point', attrib=pt_attr)

        det = ET.SubElement(cot, 'detail')
        ET.SubElement(det, 'remarks').text = unit["remarks"]
        ET.SubElement(det, 'track', attrib=track_attr)
        
        cot_xml = ET.tostring(cot)
        
        return cot_xml

    def send_broadcast(__self, ip_address, port, cot_xml):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sent = sock.sendto(cot_xml, (ip_address, port))
        return sent
    
    def send_UDP(__self, ip_address, port, cot_xml):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sent = sock.sendto(cot_xml, (ip_address, port))
        return sent

    def send_TCP(__self, ip_address, port, cot_xml):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = sock.connect((ip_address, port))
        return sock.send(cot_xml)