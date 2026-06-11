import time
import threading
from time import sleep
import busio
from board import SCL, SDA
from gpiozero import DistanceSensor
from adafruit_pca9685 import PCA9685
import warnings
from adafruit_motor import servo
from board import SCL, SDA
import busio
from adafruit_motor import motor
from adafruit_motor import servo
from gpiozero import InputDevice
from gpiozero import PWMOutputDevice as PWM

from smooth_motor import SmoothMotor

line_pin_left = 22
line_pin_middle = 27
line_pin_right = 17

left = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right = InputDevice(pin=line_pin_left)

# Masque les avertissements inutiles de gpiozero
warnings.filterwarnings("ignore")

# Feu gauche (Left)
Left_R = 13
Left_G = 19
Left_B = 0

# Feu droit (Right)
Right_R = 1
Right_G = 5
Right_B = 6

L_R = PWM(pin=Left_R, initial_value=1.0, frequency=2000)
L_G = PWM(pin=Left_G, initial_value=1.0, frequency=2000)
L_B = PWM(pin=Left_B, initial_value=1.0, frequency=2000)
R_R = PWM(pin=Right_R, initial_value=1.0, frequency=2000)
R_G = PWM(pin=Right_G, initial_value=1.0, frequency=2000)
R_B = PWM(pin=Right_B, initial_value=1.0, frequency=2000)

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14

#def setup():
i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
#  pwm_motor.channels[7].duty_cycle = 0xFFFF
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

m = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2])
m.decay_mode = (motor.SLOW_DECAY)

robot_motor = SmoothMotor(m, 4)

Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr,max_distance=2) # Maximum detection distance 2m.

# Get the distance of ultrasonic detection.
def checkdist():
    return (sensor.distance) *100 # Unit: cm

running = True
status = 0
steering = 0

def set_angle(ID, angle):
    servo_angle = servo.Servo(pwm_motor.channels[ID], min_pulse=500, max_pulse=2400,actuation_range=180)
    servo_angle.angle = angle

def led_task():
    x = 0
    N = 20
    L_B.value = 1.0
    R_B.value = 1.0
    R_G.value = 1.0
    R_R.value = 1.0
    L_G.value = 1.0
    L_R.value = 1.0

    while running:
        s = steering

        if robot_motor.speed > 0:
            s *= -1

        if s == 0:
            x = 0
            R_G.value = 1.0
            R_R.value = 1.0
            L_G.value = 1.0
            L_R.value = 1.0
        if s == 1:
            x += 1
            x %= N
            if x < N/2:
                R_G.value = 1.0
                R_R.value = 1.0
                L_G.value = 1.0
                L_R.value = 1.0
            else:
                R_G.value = 0.0
                R_R.value = 0.0
                L_G.value = 1.0
                L_R.value = 1.0
        if s == -1:
            x += 1
            x %= N
            if x < N/2:
                R_G.value = 1.0
                R_R.value = 1.0
                L_G.value = 1.0
                L_R.value = 1.0
            else:
                R_G.value = 1.0
                R_R.value = 1.0
                L_G.value = 0.0
                L_R.value = 0.0
        sleep(0.05)


def background_task():
    global running
    global steering
    global status

    while running:
        if status == 1:
            status_right = right.value
            status_middle = middle.value
            status_left = left.value
            # print('left: %d   middle: %d   right: %d' %(status_right,status_middle,status_left))
            if status_left == 1 and status_middle == 1 and status_right == 0:
                set_angle(0, 75)
                steering = -1
            if status_left == 1 and status_middle == 0 and status_right == 0:
                set_angle(0, 55)
                steering = -1
            if status_left == 0 and status_middle == 1 and status_right == 1:
                set_angle(0, 105)
                steering = 1
            if status_left == 0 and status_middle == 0 and status_right == 1:
                set_angle(0, 125)
                steering = 1
            if status_left == 0 and status_middle == 1 and status_left == 0:
                set_angle(0, 90)
                steering = 0
            if status_right == 1 and status_middle == 1 and status_left == 1:
                set_angle(0, 90)
                steering = 0
            if status_right == 0 and status_middle == 0 and status_left == 0:
                robot_motor.accelerate_to(30, -1, acceleration = 2)
                if -4 < robot_motor.speed < 4:
                    if steering == 0:
                        set_angle(0, 90)
                    if steering == 1:
                        set_angle(0, 75)
                    if steering == -1:
                        set_angle(0, 105)
            else:
                robot_motor.accelerate_to(40, 1, acceleration = 5)
            
            if checkdist() <= 20:
                status = 0
        else:
            robot_motor.accelerate_to(0, 1, acceleration = 2)
        robot_motor.update_speed()
        sleep(0.05)

if __name__ == "__main__":
    bg_thread = threading.Thread(target=background_task, daemon=True)
    bg_thread.start()

    light_thread = threading.Thread(target=led_task, daemon=True)
    light_thread.start()
    try:
        while True:
            choice = input("\nCommande (M/A) : ").strip().upper()
            if choice == 'M':
                status = 1
            if choice == 'A':
                status = 0
    except KeyboardInterrupt:
        running = False
        robot_motor.stop()
        robot_motor.destroy()
        print("Exit")


