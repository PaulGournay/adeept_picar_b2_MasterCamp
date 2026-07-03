import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor
from gpiozero import DistanceSensor
from smooth_motor import SmoothMotor
from servo import Servo

# ==========================================
# 0. CONFIGURATION DU SERVEUR WEB ET VARIABLES GLOBALES
# ==========================================
app = Flask(__name__)
global_debug_frame = None

etat_robot = "REPOS"
compteur_fleches = 0
confirmations_vue = 0

def generate_video_stream():
    global global_debug_frame
    while True:
        if global_debug_frame is None:
            time.sleep(0.1)
            continue

        ret, buffer = cv2.imencode('.jpg', global_debug_frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>Vision Robot OpenCV</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="background-color: #222; color: white; text-align: center; font-family: sans-serif; margin-top: 20px;">
            <h1>Contrôle & Vision du Robot</h1>
            <img src="/video_feed" style="border: 2px solid white; border-radius: 10px; max-width: 100%; height: auto;" />
            <br><br>
            <a href="/action_relancer" style="background-color: #4CAF50; color: white; padding: 15px 32px; text-decoration: none; display: inline-block; font-size: 20px; border-radius: 8px; font-weight: bold; margin: 10px;">▶ RELANCER MISSION</a>
            <a href="/action_stop" style="background-color: #f44336; color: white; padding: 15px 32px; text-decoration: none; display: inline-block; font-size: 20px; border-radius: 8px; font-weight: bold; margin: 10px;">⏹ STOP</a>
        </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/action_relancer')
def action_relancer():
    global etat_robot, compteur_fleches
    etat_robot = "RECHERCHE"
    compteur_fleches = 0
    print("Action Web : Mission relancée depuis le début !")
    return redirect('/')

@app.route('/action_stop')
def action_stop():
    global etat_robot
    etat_robot = "REPOS"
    print("Action Web : Arrêt d'urgence du robot !")
    return redirect('/')

def run_flask_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ==========================================
# 1. INITIALISATION DU MATÉRIEL (HARDWARE)
# ==========================================
print("Initialisation des moteurs et servos...")
i2c = busio.I2C(SCL, SDA)
pwm_motor = PCA9685(i2c, address=0x5f)
pwm_motor.frequency = 50

direction = Servo(pwm_motor, 0, center=96, step=4)
cam1 = Servo(pwm_motor, 1, center=90, step=4)
cam2 = Servo(pwm_motor, 2, center=90, step=4)
cam1.angle = 0
cam2.angle = 10

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14
m = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1], pwm_motor.channels[MOTOR_M1_IN2])
m.decay_mode = motor.SLOW_DECAY
propulsion = SmoothMotor(m, 3)

# Initialisation du Capteur de Distance (Ultrasons)
Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr, max_distance=2)

def checkdist():
    return sensor.distance * 100  # Retourne la distance en cm

DISTANCE_OBSTACLE_CM = 15 # La distance critique avant de faire marche arrière

# ==========================================
# 2. VISION (Flèches + Ligne Rouge + Centre)
# ==========================================
def analyze_frame(img):
    display_frame = img.copy()
    h, w = img.shape[:2]
    ordre_direction = None
    angle_suivi_ligne = None
    centre_fleche_x = None
    surface_fleche = None

    # --- A. DÉTECTION DE LA FLÈCHE ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((5, 5), np.uint8)
    clean_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        surface = cv2.contourArea(contour)

        if 15000 <= surface <= 65000:
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)

            if hull_area > 0:
                solidity = float(surface) / hull_area
                if not (0.45 <= solidity <= 0.85):
                    continue

            perimetre = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimetre, True)

            if len(approx) == 7:
                cv2.drawContours(display_frame, [approx], -1, (0, 255, 0), 3)
                x_coords = [point[0][0] for point in approx]
                x_moyenne = int((np.min(x_coords) + np.max(x_coords)) / 2)

                centre_fleche_x = x_moyenne
                surface_fleche = surface

                cv2.line(display_frame, (x_moyenne, 0), (x_moyenne, h), (255, 0, 0), 2)

                cote_gauche = sum(1 for x in x_coords if x < x_moyenne)
                cote_droit = sum(1 for x in x_coords if x > x_moyenne)

                if cote_droit > cote_gauche:
                    ordre_direction = "DROITE"
                else:
                    ordre_direction = "GAUCHE"

                cv2.putText(display_frame, f"FLECHE {ordre_direction} (Sol: {solidity:.2f})", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
                break

    # --- B. SUIVI DE LIGNE ROUGE ---
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 150, 150])
    upper_red = np.array([10, 255, 255])
    mask_red = cv2.inRange(img_hsv, lower_red, upper_red)

    points = []
    for y in range(0, h, 10):
        xs = np.where(mask_red[y, :] > 0)[0]
        if len(xs) > 0:
            cx = int(np.mean(xs))
            points.append(cx)
            cv2.circle(display_frame, (cx, y), 3, (0, 0, 255), -1)

    if len(points) > 0:
        moyenne_x = np.mean(points)
        deg = (moyenne_x * 90 / w) - 45
        angle_suivi_ligne = -1 * deg
        cv2.circle(display_frame, (int(moyenne_x), h // 2), 10, (0, 255, 0), -1)

    return ordre_direction, centre_fleche_x, surface_fleche, angle_suivi_ligne, display_frame

# ==========================================
# 3. LA MANŒUVRE DE CRÉNEAU
# ==========================================
def _avancer_jusqu_a_obstacle(t_max, distance_cm):
    """Fonction qui fait avancer le robot jusqu'à un obstacle ou un temps limite"""
    t_debut = time.time()
    while checkdist() > distance_cm:
        if (time.time() - t_debut) >= t_max:
            return False
        time.sleep(0.05)
    return True

def faire_creneau(direction_ordre):
    print(f"\n--- DÉBUT MANŒUVRE EN 6 ÉTAPES SACCADÉES VERS LA {direction_ordre} ---")
    propulsion.stop()
    time.sleep(0.5)


    VITESSE = 25
    ANGLE_MAX = 40

    angle_braquage = -ANGLE_MAX if direction_ordre == "DROITE" else ANGLE_MAX
    angle_inverse = ANGLE_MAX if direction_ordre == "DROITE" else -ANGLE_MAX

    # La fameuse boucle d'aller-retour rapide
    for i in range(6):
        # Braque dans le sens de la flèche et avance un coup sec
        direction.angle = angle_braquage
        propulsion.set_speed(speed=VITESSE, direction=1)
        time.sleep(0.40)

        # Contre-braque et recule un coup sec
        direction.angle = angle_inverse
        propulsion.set_speed(speed=VITESSE, direction=-1)
        time.sleep(0.40)

    # Dernier petit coup en avant pour finaliser le mouvement
    direction.angle = angle_braquage
    propulsion.set_speed(speed=VITESSE, direction=1)
    time.sleep(0.36)

    propulsion.stop()
    direction.angle = 0
    time.sleep(0.5)
    print("--- FIN MANŒUVRE ---\n")

# ==========================================
# 4. BOUCLE PRINCIPALE
# ==========================================
print("Démarrage du serveur web de Debug...")
server_thread = threading.Thread(target=run_flask_server, daemon=True)
server_thread.start()

print("Initialisation de Picamera2...")
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

propulsion.stop()
direction.angle = 0

print("\n" + "="*50)
print("🌐 LE ROBOT EST PRÊT ET EN ATTENTE !")
print("Clique sur le bouton vert 'RELANCER MISSION' sur la page Web pour qu'il démarre.")
print("="*50 + "\n")

try:
    while True:
        img = picam2.capture_array()
        h, w = img.shape[:2]

        ordre, centre_fleche_x, surface_fleche, angle_ligne, frame_dessinee = analyze_frame(img)

        # --- Affichage sur le retour vidéo ---
        dist_actuelle = checkdist()
        cv2.putText(frame_dessinee, f"ETAT: {etat_robot} | FLECHES: {compteur_fleches}/3", (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame_dessinee, f"Obstacle: {dist_actuelle:.0f} cm", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if surface_fleche is not None:
            cv2.putText(frame_dessinee, f"Dist Fleche: {int(surface_fleche)}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        global_debug_frame = frame_dessinee

        # --- MACHINE À ÉTATS ---

        # 🛡️ LE BOUCLIER ANTI-COLLISION (Le réflexe de survie !)
        if dist_actuelle < DISTANCE_OBSTACLE_CM and etat_robot in ["RECHERCHE", "CENTRAGE", "SUIVI_LIGNE"]:
            print(f"⚠️ MUR DÉTECTÉ TROP PRÈS ({dist_actuelle:.0f} cm) ! Marche arrière de sécurité.")
            etat_robot = "EVITEMENT_MUR"

        if etat_robot == "EVITEMENT_MUR":
            # 1. On coupe tout
            propulsion.stop()
            time.sleep(0.3)

            # 2. On met les roues droites et on recule
            direction.angle = 0
            time.sleep(0.2)
            propulsion.set_speed(speed=25, direction=-1) # -1 = Reculer
            time.sleep(1.5) # On recule d'une bonne distance pendant 1,5s
            propulsion.stop()
            time.sleep(0.3)

            # 3. On reprend la mission où on l'avait laissée
            print("Dégagement terminé. Reprise de la mission.")
            if compteur_fleches >= 3:
                etat_robot = "SUIVI_LIGNE"
            else:
                etat_robot = "RECHERCHE"
                confirmations_vue = 0

        elif etat_robot == "RECHERCHE":
            if ordre is not None:
                confirmations_vue += 1
                print(f"Flèche potentielle repérée... ({confirmations_vue}/3)")

                if confirmations_vue >= 3:
                    print(f"Flèche {ordre} CONFIRMÉE ! Je recule pour prendre de l'élan...")
                    propulsion.stop()
                    direction.angle = 0
                    time.sleep(0.3)
                    propulsion.set_speed(25, -1)
                    time.sleep(1.0)
                    propulsion.stop()
                    time.sleep(0.2)

                    etat_robot = "CENTRAGE"
                    direction_a_prendre = ordre
                    confirmations_vue = 0
            else:
                confirmations_vue = 0
                direction.angle = 0
                propulsion.set_speed(20, 1)

        elif etat_robot == "CENTRAGE":
            if centre_fleche_x is not None:
                erreur = centre_fleche_x - (w / 2)
                deg_centrage = (centre_fleche_x * 70 / w) - 35
                direction.angle = -1 * deg_centrage

                if 50000 <= surface_fleche <= 60000:
                    if abs(erreur) < 40:
                        confirmations_vue += 1
                        if confirmations_vue >= 3:
                            propulsion.stop()
                            print(f"Position parfaite confirmée ! Lancement du créneau.")
                            etat_robot = "MANOEUVRE"
                            confirmations_vue = 0
                        else:
                            propulsion.stop()
                    else:
                        confirmations_vue = 0
                        propulsion.set_speed(15, 1)

                elif surface_fleche < 50000:
                    confirmations_vue = 0
                    propulsion.set_speed(20, 1)

                else:
                    if abs(erreur) < 40:
                        confirmations_vue += 1
                        if confirmations_vue >= 3:
                            propulsion.stop()
                            print("Flèche très proche MAIS bien centrée ! Lancement.")
                            etat_robot = "MANOEUVRE"
                            confirmations_vue = 0
                    else:
                        print("Trop proche et MAL CENTRÉ ! Je recule pour réessayer...")
                        propulsion.stop()
                        direction.angle = 0
                        time.sleep(0.3)
                        propulsion.set_speed(25, -1)
                        time.sleep(1.2)
                        propulsion.stop()
                        confirmations_vue = 0

            else:
                propulsion.set_speed(15, 1)

        elif etat_robot == "MANOEUVRE":
            compteur_fleches += 1
            print(f"Flèche validée ! (Total: {compteur_fleches}/3).")

            faire_creneau(direction_a_prendre)

            if compteur_fleches >= 3:
                print("🎯 Objectif atteint : 3 flèches ! Passage en mode SUIVI DE LIGNE ROUGE.")
                etat_robot = "SUIVI_LIGNE"
            else:
                print(f"Reprise de la recherche (Encore {3 - compteur_fleches} flèche(s) à trouver).")
                etat_robot = "RECHERCHE"

                direction.angle = 0
                propulsion.set_speed(25, 1)
                _avancer_jusqu_a_obstacle(t_max=1.5, distance_cm=DISTANCE_OBSTACLE_CM)
                propulsion.stop()

        elif etat_robot == "SUIVI_LIGNE":
            cam2.angle = -20
            if angle_ligne is not None:
                direction.angle = angle_ligne
                propulsion.set_speed(50, 1)
            else:
                propulsion.stop()

        elif etat_robot == "REPOS":
            propulsion.stop()

        propulsion.update_speed()

except KeyboardInterrupt:
    print("\nArrêt d'urgence demandé (Ctrl+C).")

finally:
    print("Mise en sécurité du matériel...")
    propulsion.stop()
    direction.angle = 0
    picam2.stop()
    print("Terminé.")