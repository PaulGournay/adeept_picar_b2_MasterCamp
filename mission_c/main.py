from gpiozero import DistanceSensor, InputDevice
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo, motor
import busio
from board import SCL, SDA
from time import sleep, time
import warnings
import statistics

from smooth_motor import SmoothMotor


i2c = busio.I2C(SCL, SDA)
pwm_motor = PCA9685(i2c, address=0x5f)
pwm_motor.frequency = 50

Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr, max_distance=2)

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14
m = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2])
m.decay_mode = (motor.SLOW_DECAY)
robot_motor = SmoothMotor(m, 3)
robot_motor.stop()

line_pin_left = 22
line_pin_middle = 27
line_pin_right = 17

left = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right = InputDevice(pin=line_pin_left)


def checkdist():
    return sensor.distance * 100 # cm

def checkdist_stable(n=5):
    readings = []
    for i in range(n):
        readings.append(sensor.distance * 100)
        sleep(0.02)
    # readings = [sensor.distance * 100 for _ in range(n)]
    # sleep(0.01)
    return statistics.median(readings)

servo_ch0 = servo.Servo(
    pwm_motor.channels[0],
    min_pulse=500,
    max_pulse=2400,
    actuation_range=180,
)

servo_ch1 = servo.Servo(
    pwm_motor.channels[1],
    min_pulse=500,
    max_pulse=2400,
    actuation_range=180,
)

servo_ch2 = servo.Servo(
    pwm_motor.channels[2],
    min_pulse=500,
    max_pulse=2400,
    actuation_range=180,
)

def set_angle_ch1(angle):
    servo_ch1.angle = angle

def ultrasonic_scan():
    r = []

    # gauche
    set_angle_ch1(170)
    sleep(1.5)
    r.append(checkdist_stable())

    # devant
    set_angle_ch1(90)
    sleep(1.5)
    r.append(checkdist_stable())

    # droite
    set_angle_ch1(10)
    sleep(1.5)
    r.append(checkdist_stable())

    return r


def maneuvre(direction, back_duration=1.5, stearing_duration=3, stearing_back=3):
    if direction == -1: # gauche
        angle = 130
    elif direction == 1: # droite
        angle = 50
    else:
        return


    servo_ch0.angle = 90+8
    robot_motor.set_speed(15, -1)
    sleep(back_duration)

    servo_ch0.angle = angle
    robot_motor.set_speed(20, 1)
    sleep(stearing_duration)

    servo_ch0.angle = 180 - angle + 8
    sleep(stearing_back)

    servo_ch0.angle = 90 + 8


if __name__ == "__main__":
    servo_ch0.angle = 90+8
    servo_ch1.angle = 90
    servo_ch2.angle = 90

    # jsp pourquoi mais ça prend du temps avant que le capteur donne des bonnes valeur, du coup
    # ce code est juste là pour temporiser
    for i in range(0, 100):
        checkdist()
        sleep(0.02)

    robot_motor.set_speed(20, 1)

    previous_directions = []
    rotate_timestamp = 0
    stearing = False

    while True:
        # capteur ligne noire (0: blanc, 1: noir)
        status_right = right.value
        status_middle = middle.value
        status_left = left.value
        print(status_right, status_middle, status_left)

        if status_right == 1:
            maneuvre(1, 1.5, 1.75, 0)
        elif status_left == 1:
            maneuvre(-1, 1.5, 1.75, 0)
        elif status_right == 1 and status_left == 1:
            # TODO: retourner en arrière? jsp
            pass
        else:
            servo_ch0.angle = 90+6

        dist = checkdist()
        print(dist)
        if (dist < 30 and stearing == False): # or dist < 20: # obstacle au milieu
            robot_motor.stop()
            scan = ultrasonic_scan()
            print(scan)
            set_angle_ch1(90)

            if scan[0] == scan[2] or (scan[0] > 160 and scan[2] > 160): # même distance à gauche et à droite (ou obstacle trop loins des deux côtés)
                if len(previous_directions) == 0:
                    previous_directions.append(-1)
                    maneuvre(-1, 1.5, 2.75, 0.3)
                elif previous_directions.count(-1) > previous_directions.count(1):
                    previous_directions.append(1)
                    maneuvre(1, 1.5, 2.75, 0.3)
                else:
                    previous_directions.append(-1)
                    maneuvre(-1, 1.5, 2.75, 0.3)

            elif scan[0] > scan[2]: # tourner à gauche
                previous_directions.append(-1)
                maneuvre(-1, 1.5, 2.75, 0.3)

            else: # tourner à droite
                previous_directions.append(1)
                maneuvre(1, 1.5, 2.75, 0.3)
