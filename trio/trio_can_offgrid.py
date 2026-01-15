# CAN comms for TRIO-HP/3AC/1KDC/20KW/BI for off-grid use

import can
import struct
import time
import subprocess

# CAN + Phoenix addressing

CAN_IF = "can0"
BITRATE = 125000


# Broadcast for all-device messages 
# Multicast and peer-to-peer not implemented

DEVICE_NUMBER = 0x0A # For broadcast
TARGET        = 0x3F # Target address for broadcast
SOURCE        = 0xF0 # Default

# Commands

READ_COMMAND  = 0x23
WRITE_COMMAND = 0x24


# payload bytes

READINESS_OFF = 0xA1
READINESS_ON  = 0xA0
MODE_OFFGRID  = 0xA2


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

# Operational readiness
def set_operational_off():
    send(WRITE_COMMAND, bytes([0x11, 0x10, 0,0,0,0,0,READINESS_OFF]))
	
def set_operational_on():
    send(WRITE_COMMAND, bytes([0x11, 0x10, 0,0,0,0,0,READINESS_ON]))

def set_mode_offgrid():
    send(WRITE_COMMAND, bytes([0x21, 0x10, 0,0,0,0,0, MODE_OFFGRID]))
  
def set_dc_voltage(volts):
    val = int(volts * 1000) # milliVolts
    send(WRITE_COMMAND, bytes([0x11, 0x01, 0,0] + list(val.to_bytes(4, 'big'))))

def set_dc_current(amps):
    val = int(amps * 1000) # milliAmps
    send(WRITE_COMMAND, bytes([0x11, 0x02, 0,0] + list(val.to_bytes(4, 'big'))))


if __name__ == "__main__":
    config()
    time.sleep(2)
    print("TRIO-HP BI Off-Grid Setup")
    
    set_operational_off()
    set_dc_voltage(200)
    set_dc_current(1)
    set_mode_offgrid()
    set_operational_on()
   
    # This serves as keep-alive. TRIO power off if no CAN message from controller for 10 seconds.
    while True:
        send(READ_COMMAND, bytes([0x01, 0x01, 0,0,0,0,0,0])) #Reading system information
        time.sleep(2) 


