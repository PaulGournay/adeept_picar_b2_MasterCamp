import time
import smbus
from gpiozero import DistanceSensor, InputDevice
import argparse


line_pin_left = 22
line_pin_middle = 27
line_pin_right = 17

left = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right = InputDevice(pin=line_pin_left)
Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr,max_distance=2) # Maximum detection distance 2m.

def lineDetect():
    status_right = right.value
    status_middle = middle.value
    status_left = left.value
    print('left: %d   middle: %d   right: %d' %(status_right,status_middle,status_left))
# Get the distance of ultrasonic detection.
def checkdist():
    return (sensor.distance) *100 # Unit: cm

class ADS7830(object):
    def __init__(self):
        self.cmd = 0x84
        self.bus=smbus.SMBus(1)
        self.address = 0x48 # 0x48 is the default i2c address for ADS7830 Module.   
        
    def analogRead(self, chn): # ADS7830 has 8 ADC input pins, chn:0,1,2,3,4,5,6,7
        value = self.bus.read_byte_data(self.address, self.cmd|(((chn<<2 | chn>>1)&0x07)<<4))
        return value
    
    

if __name__ == "__main__":
    adc = ADS7830()
    while True:
        adc_value = adc.analogRead(1)
        print(f"Light Tracking Value: {adc_value}")
        distance = checkdist()
        print("%.2f mm" %(distance*10))
        lineDetect()
        time.sleep(0.5)
