#import RPi.GPIO as GPIO
from gpiozero import PWMOutputDevice as PWM, LED
import time

# --- Attribution des broches GPIO pour les LED RGB des feux avant ---
# Feu gauche (Left)
Left_R = 19
Left_G = 0
Left_B = 13

# Feu droit (Right)
Right_R = 1
Right_G = 5
Right_B = 6

def setup():
  # Déclaration des variables en globales pour les rendre accessibles partout
  global L_R, L_G, L_B, R_R, R_G, R_B, L_1, L_2, L_3
  # Initialisation des LED RGB en PWM (Fréquence 2kHz)
  # Note : initial_value=1.0 car la logique est inversée (1.0 = Éteint au démarrage)
  L_R = PWM(pin=Left_R, initial_value=1.0, frequency=2000)
  L_G = PWM(pin=Left_G, initial_value=1.0, frequency=2000)
  L_B = PWM(pin=Left_B, initial_value=1.0, frequency=2000)
  R_R = PWM(pin=Right_R, initial_value=1.0, frequency=2000)
  R_G = PWM(pin=Right_G, initial_value=1.0, frequency=2000)
  R_B = PWM(pin=Right_B, initial_value=1.0, frequency=2000)
  # Initialisation des 3 LED standards de la HAL (Logique normale)
  L_1 = LED(9)
  L_2 = LED(25)
  L_3 = LED(11)
def loop():
  # Boucle principale d'écoute des commandes utilisateur
  while True:
    try:
      x = int(input("> "))
      # --- CODES 11 à 19 : Allumage des composants ---
      if x == 11:
        L_1.on()
      if x == 12:
        L_2.on()
      if x == 13:
        L_3.on()
      # Pour les feux RGB avant, la valeur 0.0 correspond à l'allumage (logique inversée)
      if x == 14:
        L_R.value = 0.0
      if x == 15:
        L_G.value = 0.0
      if x == 16:
        L_B.value = 0.0
      if x == 17:
        R_R.value = 0.0
      if x == 18:
        R_G.value = 0.0
      if x == 19:
        R_B.value = 0.0
      # --- CODES 21 à 29 : Extinction des composants ---
      if x == 21:
        L_1.off()
      if x == 22:
        L_2.off()
      if x == 23:
        L_3.off()
      # Pour les feux RGB avant, la valeur 1.0 correspond à l'extinction (logique inversée)
      if x == 24:
        L_R.value = 1.0
      if x == 25:
        L_G.value = 1.0
      if x == 26:
        L_B.value = 1.0
      if x == 27:
        R_R.value = 1.0
      if x == 28:
        R_G.value = 1.0
      if x == 29:
        R_B.value = 1.0
    except:
      pass # Ignore les erreurs de saisie (ex: si l'utilisateur tape une lettre)
def destroy():
  # Extinction et libération des ressources de toutes les broches GPIO
  L_1.stop()
  L_2.stop()
  L_3.stop()
  L_R.stop()
  L_G.stop()
  L_B.stop()
  R_R.stop()
  R_G.stop()
  R_B.stop()
if __name__ == "__main__":
  setup() # Configuration des entrées/sorties
  try:
    loop() # Lancement de la machine d'état
  except KeyboardInterrupt:
    destroy() # Sécurité : Exécuté en coupant le programme avec Ctrl+C