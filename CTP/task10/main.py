import smbus
import time
import threading
from time import sleep
import busio
from board import SCL, SDA
from gpiozero import DistanceSensor, InputDevice, TonalBuzzer
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo, motor
import warnings
import ledmanager 
# Import de tes classes personnalisées
from smooth_motor import SmoothMotor
from ledmanager import Adeept_SPI_LedPixel  # Assure-toi d'avoir sauvegardé ta classe dans adeept_led.py

# Masque les avertissements inutiles de gpiozero
warnings.filterwarnings("ignore")

# Configuration des capteurs de ligne / lumière
line_pin_left = 22
line_pin_middle = 27
line_pin_right = 17

left = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right = InputDevice(pin=line_pin_left)

# Initialisation du Bandeau LED (14 LEDs)
led_strip = Adeept_SPI_LedPixel(count=14, sequence='GRB')

# Initialisation du Buzzer
tb = TonalBuzzer(18)

# Moteur
MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14

i2c = busio.I2C(SCL, SDA)
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

m = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1], pwm_motor.channels[MOTOR_M1_IN2])
m.decay_mode = (motor.SLOW_DECAY)

robot_motor = SmoothMotor(m, 4)

# Capteur Ultrason
Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr, max_distance=2)

def checkdist():
    return (sensor.distance) * 100 # Unité: cm

# Variables Globales d'état
running = True
status = 0
steering = 0
hazard_lights = False

def set_angle(ID, angle):
    servo_angle = servo.Servo(pwm_motor.channels[ID], min_pulse=500, max_pulse=2400, actuation_range=180)
    servo_angle.angle = angle

def led_task():
    global hazard_lights, steering, running
    x = 0
    N = 20
    led_strip.set_all_led_color(0, 0, 0) # Éteint tout au démarrage

    while running:
        # Priorité aux feux de détresse (Clignotement utilisant tes méthodes)
        if hazard_lights:
            x += 1
            x %= N
            if x < N/2:
                led_strip.Feux_détresse_on()
            else:
                led_strip.Feux_détresse_off()
            sleep(0.05)
            continue

        s = steering
        if robot_motor.speed > 0:
            s *= -1

        if s == 0:
            x = 0
            # Blanc léger pour indiquer la marche avant
            led_strip.set_all_led_color(50, 50, 50) 
        elif s == 1: # Clignotant Droit (Ex: LEDs 4 à 7)
            x += 1
            x %= N
            if x < N/2:
                led_strip.set_all_led_color(0, 0, 0)
                for i in range(4, 8): 
                    led_strip.set_led_color_data(i, 255, 100, 0) # Orange
                led_strip.show()
            else:
                led_strip.set_all_led_color(0, 0, 0)
        elif s == -1: # Clignotant Gauche (Ex: LEDs 0 à 3)
            x += 1
            x %= N
            if x < N/2:
                led_strip.set_all_led_color(0, 0, 0)
                for i in range(0, 4): 
                    led_strip.set_led_color_data(i, 255, 100, 0) # Orange
                led_strip.show()
            else:
                led_strip.set_all_led_color(0, 0, 0)
        sleep(0.05)

def handle_obstacle():
    """Gère la séquence d'arrêt, de recul et de reprise lors d'un obstacle."""
    global hazard_lights, status
    print("\n[!] Obstacle détecté ! Arrêt et feux de détresse.")
    hazard_lights = True
    
    # 1. Arrêt du robot et attente de 1 seconde
    robot_motor.accelerate_to(0, 1, acceleration=10)
    for _ in range(20): # 20 * 0.05s = 1s
        if status == 0: return # Interruption manuelle 'A'
        robot_motor.update_speed()
        sleep(0.05)
        
    # 2. Recul du robot d'environ 30 cm avec Bip Bip
    print("[!] Recul en cours...")
    robot_motor.accelerate_to(30, -1, acceleration=5)
    set_angle(0, 90) # Garde les roues droites en reculant
    
    # Durée estimée pour 30cm: ~3 secondes (à ajuster)
    for i in range(60): 
        if status == 0: break # Interruption manuelle 'A'
        robot_motor.update_speed()
        # Bip bip intermittent
        if i % 10 == 0:
            tb.play("B4")
        elif i % 10 == 5:
            tb.stop()
        sleep(0.05)
        
    tb.stop()
    if status == 0: return
    
    # 3. Arrêt pendant 2 secondes avant reprise
    print("[!] Pause de 2 secondes...")
    hazard_lights = False
    led_strip.Feux_détresse_off() # S'assure que les feux sont bien éteints
    robot_motor.accelerate_to(0, 1, acceleration=10)
    
    for _ in range(40): # 40 * 0.05s = 2s
        if status == 0: return # Interruption manuelle 'A'
        robot_motor.update_speed()
        sleep(0.05)
        
    print("[!] Reprise du suivi de lumière.")

class ADS7830(object):
    def __init__(self):
        self.cmd = 0x84
        self.bus=smbus.SMBus(1)
        self.address = 0x48 # 0x48 is the default i2c address for ADS7830 Module.   

    def analogRead(self, chn): # ADS7830 has 8 ADC input pins, chn:0,1,2,3,4,5,6,7
        value = self.bus.read_byte_data(self.address, self.cmd|(((chn<<2 | chn>>1)&0x07)<<4))
        return value


def background_task():
    global running, steering, status

    while running:
        if status == 1:
            # Vérification de l'obstacle en priorité absolue
            if checkdist() <= 20:
                handle_obstacle()
                continue # Passe l'itération pour ne pas écraser la séquence

            robot_motor.accelerate_to(30, 1, acceleration = 2)

        else:
            # Si le robot est à l'arrêt manuel (A)
            robot_motor.accelerate_to(0, 1, acceleration = 10)
            
        robot_motor.update_speed()
        sleep(0.05)


def light_direction_task():
    global running

    adc = ADS7830()
    previous_angle = 0
    servo_ = servo.Servo(pwm_motor.channels[0], min_pulse=500, max_pulse=2400,actuation_range=180)

    while running:
        if status != 1:
            continue
            
        adc_value = adc.analogRead(1)
        target_angle = 180 - ((adc_value / 255) * 180)

        if target_angle < 20: target_angle = 20
        elif target_angle > 160: target_angle = 160

        if not (-10 <= previous_angle - target_angle <= 10):
            previous_angle = target_angle
            servo_.angle = target_angle
        
        sleep(0.05)



if __name__ == "__main__":
    bg_thread = threading.Thread(target=background_task, daemon=True)
    bg_thread.start()

    light_thread = threading.Thread(target=led_task, daemon=True)
    light_thread.start()

    light_direction_thread = threading.Thread(target=light_direction_task, daemon=True)
    light_direction_thread.start()
    
    print("=== DÉMARRAGE ROBOT : TÂCHE 10 ===")
    print("- Entrez 'M' pour lancer la marche avant.")
    print("- Entrez 'A' pour l'arrêt immédiat.\n")
    
    try:
        while True:
            choice = input("Commande (M/A) : ").strip().upper()
            if choice == 'M':
                status = 1
            elif choice == 'A':
                status = 0
                robot_motor.stop() # Force l'arrêt immédiat matériellement
                tb.stop() # Coupe le buzzer
                led_strip.set_all_led_color(0, 0, 0) # Éteint les LEDs
    except KeyboardInterrupt:
        running = False
        robot_motor.stop()
        robot_motor.destroy()
        tb.stop()
        led_strip.led_close()
        print("\nSortie propre...")