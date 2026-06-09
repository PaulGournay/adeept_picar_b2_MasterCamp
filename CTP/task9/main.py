import os
import sys
import time
import threading
from time import sleep
import busio
from board import SCL, SDA
from gpiozero import DistanceSensor
from adafruit_pca9685 import PCA9685
import warnings

# Masque les avertissements inutiles de gpiozero
warnings.filterwarnings("ignore")

# --- IMPORTS DE TES CLASSES ---
from ledmanager import Adeept_SPI_LedPixel
from smooth_motor import SmoothMotor

# ==========================================
# 1. INITIALISATION DU MATÉRIEL
# ==========================================
Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr, max_distance=2)

i2c = busio.I2C(SCL, SDA)
pwm_motor = PCA9685(i2c, address=0x5f)
pwm_motor.frequency = 50

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14

robot_motor = SmoothMotor(MOTOR_M1_IN1, MOTOR_M1_IN2)
leds_robot = Adeept_SPI_LedPixel(count=14, bright=255)

# Variables globales
running = True
motorOn = False
detresse_active = False

# ==========================================
# 2. FONCTION FILTRE DU CAPTEUR
# ==========================================
def get_distance_filtree():
    """Filtre les fausses lectures (bugs) à 0cm du capteur HC-SR04"""
    mesures = []
    for _ in range(3):
        dist = sensor.distance * 100
        if dist > 2.0:  # Ignore les bugs physiques
            mesures.append(dist)
        sleep(0.01)
    if len(mesures) > 0:
        return sum(mesures) / len(mesures)
    return 200.0 # Voie libre par défaut en cas d'erreur

# ==========================================
# 3. BOUCLE EN ARRIÈRE-PLAN (MOTEUR + SÉCURITÉ)
# ==========================================
def background_task():
    global motorOn, detresse_active
    
    leds_robot.set_all_led_color(0, 0, 0)
    
    while running:
        if motorOn:
            distance = get_distance_filtree()
            # Affichage de contrôle (s'efface tout seul)
            print(f"Distance: {distance:.1f} cm | Vitesse: {robot_motor.speed}%   ", end="\r")
            
            # --- CONDITION DE L'OBSTACLE ---
            if distance < 20:
                print(f"\n[OBSTACLE] à {distance:.1f} cm ! Début de la décélération...")
                motorOn = False
                
                # ORDRE DE DÉCÉLÉRATION (Cible = 0)
                robot_motor.accelerate_to(0, 1) 
                
                leds_robot.Feux_détresse_on()
                detresse_active = True

        # --- APPLICATION DE LA PENTE DE VITESSE ---
        # Même si motorOn est passé à False, update_speed continue 
        # de tourner et va baisser la vitesse doucement jusqu'à 0.
        robot_motor.update_speed()
        
        sleep(0.05)

# ==========================================
# 4. PROGRAMME PRINCIPAL (CLAVIER)
# ==========================================
if __name__ == '__main__':
    # Déclaration des variables d'état du programme
    running = True
    motorOn = False
    detresse_active = False

    # --- 1er Process : Définition du Thread en arrière-plan ---
    def background_task():
        global motorOn, detresse_active
        
        # S'assure que les LED sont éteintes au départ
        leds_robot.set_all_led_color(0, 0, 0)
        
        while running:
            if motorOn:
                distance = get_distance_filtree()
                
                # --- CONDITION DE L'OBSTACLE ---
                if distance < 20:
                    print(f"\n[OBSTACLE] à {distance:.1f} cm ! Début de la décélération...")
                    motorOn = False
                    
                    # ORDRE DE DÉCÉLÉRATION (Cible = 0)
                    robot_motor.accelerate_to(0, 1) 
                    
                    leds_robot.Feux_détresse_on()
                    detresse_active = True

            # --- APPLICATION DE LA PENTE DE VITESSE ---
            robot_motor.update_speed()
            
            sleep(0.05)

    # Lancement du 1er Process (Thread)
    bg_thread = threading.Thread(target=background_task, daemon=True)
    bg_thread.start()


    # --- 2ème Process : Boucle principale (Clavier) ---
    print("\n=== CONTRÔLE DU ROBOT ===")
    print("M -> Marche avant")
    print("A -> Arrêt manuel")
    print("Ctrl+C -> Quitter")

    try:
        while running:
            choice = input("\nCommande (M/A) : ").strip().upper()

            if choice == 'A':
                # Arrêt IMMÉDIAT (Consigne 2)
                print("Arrêt manuel immédiat et extinction des feux.")
                motorOn = False
                robot_motor.stop()
                leds_robot.set_all_led_color(0, 0, 0) # Extinction des LED
                detresse_active = False

            elif choice == 'M':
                # Démarrage Progressif (Consignes 1 & 4)
                dist = get_distance_filtree()
                if dist < 20:
                    print(f"Démarrage impossible, obstacle toujours présent ({dist:.1f} cm)")
                else:
                    if detresse_active:
                        print("Voie libre, extinction des feux de détresse.")
                        leds_robot.Feux_détresse_off()
                        detresse_active = False

                    print("Démarrage progressif vers 50% de puissance...")
                    motorOn = True
                    robot_motor.accelerate_to(50, 1)

    except KeyboardInterrupt:
        print("\nArrêt du programme demandé...")
    finally:
        running = False
        sleep(0.2)
        robot_motor.destroy()
        leds_robot.set_all_led_color(0, 0, 0)
        print("Robot éteint.")