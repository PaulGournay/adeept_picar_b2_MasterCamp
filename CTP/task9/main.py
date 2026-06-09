from gpiozero import DistanceSensor
from time import sleep
import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor
import threading
import sys
import os

import CTP.task9.ledmanager as ledmanager
from CTP.task9.ledmanager import Adeept_SPI_LedPixel
from smooth_motor import SmoothMotor
Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr,max_distance=2) # Maximum detection distance 2m.

# motor_EN_A: Pin7  |  motor_EN_B: Pin11
# motor_A:  Pin8,Pin10    |  motor_B: Pin13,Pin12

vitesse = 0

MOTOR_M1_IN1 =  15      #Define the positive pole of M1
MOTOR_M1_IN2 =  14      #Define the negative pole of M1

Dir_forward   = 0
Dir_backward  = 1

left_forward  = 1
left_backward = 0

right_forward = 0
right_backward= 1

pwn_A = 0
pwm_B = 0
  
def map(x,in_min,in_max,out_min,out_max):
  return (x - in_min)/(in_max - in_min) *(out_max - out_min) +out_min


#def setup():
i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
#  pwm_motor.channels[7].duty_cycle = 0xFFFF
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

motor1 = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2] )
motor1.decay_mode = (motor.SLOW_DECAY)
#  motorStop()


def motorStop():#Motor stops
    motor1.throttle = 0

def destroy():
  motorStop()
  pwm_motor.deinit()


def getToSpeed(goalSpeed, direction, duration):
    global vitesse                             # Utilisé par le fonction Motor
    if direction == -1:
        goalSpeed = -1 * goalSpeed
    delta = (goalSpeed - vitesse) / 100
    for i in range(100):
        vitesse += delta
        speed = map(vitesse, 0, 100, 0, 1.0)
        motor1.throttle = speed
        sleep(duration / 100)

# Get the distance of ultrasonic detection.
def checkdist():
    return (sensor.distance) *100 # Unit: cm



if __name__ == '__main__':
    running = True
    motorOn = False
    detresse_active = False

    # Initialisation des LEDs
    leds_robot = Adeept_SPI_LedPixel(count=14, bright=255)
    leds_robot.set_all_led_color(0, 0, 0)
    
    def movement_loop():
        global motorOn, detresse_active
        print("[Thread] Gestionnaire de mouvement et sécurité démarré.")
        
        while running:
            # 1. Gestion de la sécurité distance (Prioritaire)
            if motorOn:
                distance = checkdist()
                if distance > 20:
                    # Tout est OK -> On demande d'aller à 50% de vitesse en marche avant (1)
                    robot_motor.accelerate_to(50, 1)
                else:
                    # DANGER : Obstacle proche !
                    print(f"\n[ALERTE] Obstacle détecté à {distance:.1f} cm ! Arrêt d'urgence.")
                    motorOn = False
                    # Arrêt immédiat pour sécurité, pas de rampe lente ici !
                    robot_motor.set_speed_immediate(0, 1) 
                    leds_robot.Feux_détresse_on()
                    detresse_active = True
            else:
                # Si l'utilisateur a coupé manuellement ou si arrêt d'urgence
                # On s'assure que le moteur vise bien 0
                if not detresse_active: 
                    robot_motor.accelerate_to(0, 1)

            # 2. APPLICATION DE LA RAMPE SMOOTH
            # update_speed() modifie légèrement la vitesse à chaque cycle
            robot_motor.update_speed()
            
            # Fréquence de rafraîchissement de la rampe (20ms)
            sleep(0.02)

    # Lancement du thread en arrière-plan
    move_thread = threading.Thread(target=movement_loop, daemon=True)
    move_thread.start()

    print("Entrez 'M' pour démarrer, 'A' pour stopper.")
    
    try:
        while running:
            choice = input("Commande : ").strip().upper()
            
            if choice == 'A':
                print("Arrêt manuel demandé.")
                motorOn = False
                
            elif choice == 'M':
                if detresse_active:
                    print("Extinction des feux de détresse.")
                    leds_robot.Feux_détresse_off()
                    detresse_active = False
                print("Marche avant activée.")
                motorOn = True
                
    except KeyboardInterrupt:
        print("\nFermeture du programme...")
    finally:
        running = False
        sleep(0.2) # Laisser le temps au thread de finir proprement
        robot_motor.stop()
        pwm_motor.deinit()
        leds_robot.set_all_led_color(0, 0, 0)
        print("Robot éteint sécurisé.")