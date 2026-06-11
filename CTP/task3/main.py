#!/usr/bin/env/python3

import time
from board import SCL, SDA
import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685

# Initialisation du bus I2C (SCL = Horloge, SDA = Données)
i2c = busio.I2C(SCL, SDA)

# Initialisation de la carte PCA9685 à l'adresse I2C 0x5f
pca = PCA9685(i2c, address=0x5f)

# Configuration de la fréquence PWM à 50 Hz (fréquence standard pour les servomoteurs)
pca.frequency = 50

# The pulse range is 750 - 2250 by default. This range typically gives 135 degrees of
# range, but the default is to use 180 degrees. You can specify the expected range if you wish:
# servo7 = servo.Servo(pca.channels[7], actuation_range=135)

# Fonction pour appliquer un angle à un servomoteur spécifique
def set_angle(ID, angle):
    # Configuration du servo sur le canal "ID" avec ajustement des impulsions mini/maxi (500 à 2400 µs)
    servo_angle = servo.Servo(pca.channels[ID], min_pulse=500, max_pulse=2400, actuation_range=180)
    # Application de l'angle demandé
    servo_angle.angle = angle

if __name__ == "__main__":
    # Boucle infinie pour le contrôle manuel via la console
    while True:
        # Demande des paramètres à l'utilisateur
        servo_id = int(input("servo id > "))
        angle = int(input("angle > "))
        
        # Validation de sécurité : l'angle doit être entre 0 et 180°, et le canal entre 0 et 15
        if angle >= 0 and angle <= 180 and servo_id >= 0 and servo_id <= 15:
            set_angle(servo_id, angle)

