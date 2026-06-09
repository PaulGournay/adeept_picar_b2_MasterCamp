#!/usr/bin/env/python3

import time
from board import SCL, SDA
import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c, address=0x5f)

pca.frequency = 50

# The pulse range is 750 - 2250 by default. This range typically gives 135 degrees of
# range, but the default is to use 180 degrees. You can specify the expected range if you wish:
# servo7 = servo.Servo(pca.channels[7], actuation_range=135)
def set_angle(ID, angle):
    servo_angle = servo.Servo(pca.channels[ID], min_pulse=500, max_pulse=2400,actuation_range=180)
    servo_angle.angle = angle

if __name__ == "__main__":
    while True:
        servo_id = int(input("servo id > "))
        angle = int(input("angle > "))
        if angle >= 0 and angle <= 180 and servo_id >= 0 and servo_id <= 15:
            set_angle(servo_id, angle)

