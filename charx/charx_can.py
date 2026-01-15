# CAN comms for CHARX PS-M2/825DC/1000DC/30KW

import sys
import can
import struct
import subprocess
import time

# CAN + Phoenix addressing

CAN_IF = "can0"
BITRATE = 125000

# Broadcast for all-device messages 
# Multicast and peer-to-peer not implemented

DEVICE_NUMBER = 0x0A # For broadcast
TARGET        = 0x3F # Target address for broadcast
SOURCE        = 0xF0 # Default

# Commands

CMD_READINESS  = 0x1A
CMD_OUTPUT_V_I = 0x1C
CMD_SYSINFO    = 0x01

# CAN BUS INITIALIZATION
# needs root/sudo access, or configure this part on the OS

def config():
    subprocess.call(['ip', 'link', 'set', 'down', CAN_IF])
    subprocess.call(['ip', 'link', 'set', CAN_IF, 'type', 'can', 'bitrate', str(BITRATE), 'restart-ms', '1500'])
    subprocess.call(['ip', 'link', 'set', 'up', CAN_IF])
    
bus = can.interface.Bus(channel=CAN_IF, bustype="socketcan")


# Build 29-bit identifier per the manual
def phoenix_can_id(command):
    return ((DEVICE_NUMBER & 0x0F) << 22) | \
           ((command & 0x3F) << 16) | \
           ((TARGET & 0xFF) << 8) | \
           (SOURCE & 0xFF)


def send(command, payload_bytes):
    msg = can.Message(
        arbitration_id=phoenix_can_id(command),
        data=payload_bytes,
        is_extended_id=True
    )
    bus.send(msg)
    #print(msg)
    time.sleep(0.2)


# CHARX PS helpers

def set_operational_on():
    send(CMD_READINESS, bytes([0,0,0,0,0,0,0,0]))

def set_operational_off():
    send(CMD_READINESS, bytes([0x01,0,0,0,0,0,0,0]))

def set_output_v_i(voltage, current):
    v = voltage * 1000
    i = current * 1000
    send(CMD_OUTPUT_V_I, bytes( list(v.to_bytes(4, 'big')) + list(i.to_bytes(4, 'big')) ))

if __name__ == "__main__":

    config()
    time.sleep(2)

    print("CHARX PS minimal startup")

    set_operational_off()
    set_output_v_i(400, 10)
    set_operational_on()

    # This serves as keep-alive. CHARX power off if no CAN message from controller for 10 seconds.
    while True:
        send(CMD_SYSINFO, bytes([0,0,0,0,0,0,0,0])) #Reading system information
        time.sleep(2) 
