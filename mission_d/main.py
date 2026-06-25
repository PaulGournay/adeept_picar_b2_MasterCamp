import cv2
import numpy as np

def processing_frame(frame):
    display_frame = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 1. Prétraitement et Masque
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((5, 5), np.uint8)
    clean_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    mirror_mask = cv2.flip(clean_mask, 1)
    cv2.imshow("Vue Robot (Masque)", clean_mask)

    # 2. Recherche des contours
    contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        surface = cv2.contourArea(contour)
        
        # --- NOUVEAU FILTRE : CALIBRAGE DE L'AIRE ---
        # On ignore catégoriquement toute forme qui n'est pas entre 35 000 et 45 000
        if not (30000 <= surface <= 45000): 
            continue
            
        perimetre = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimetre, True)
        
        nb_sommets = len(approx)
        
        # 3. Vérification : Est-ce une flèche ? (7 sommets)
        if nb_sommets == 7:
            # On dessine la forme validée en vert
            cv2.drawContours(display_frame, [approx], -1, (0, 255, 0), 3)
            
            # Affichage dans la console pour le debug (comme tu as fait)
            print(f"Surface de la flèche détectée : {surface}")
            
            # --- CALCUL DE LA DIRECTION ---
            x_coords = [point[0][0] for point in approx]
            print(f"Coordonnées X des sommets : {x_coords}")
            
            x_min = np.min(x_coords)
            x_max = np.max(x_coords)
            x_moyenne = int((x_min + x_max) / 2)
            
            h_frame = frame.shape[0]
            cv2.line(display_frame, (x_moyenne, 0), (x_moyenne, h_frame), (255, 0, 0), 2)
            
            # Comptage optimisé
            cote_gauche = sum(1 for x in x_coords if x < x_moyenne)
            cote_droit = sum(1 for x in x_coords if x > x_moyenne)
                    
            # 4. Déduction logique pour le Robot
            if cote_droit > cote_gauche:
                direction = "DROITE"
                couleur = (0, 255, 255) # Jaune
            else:
                direction = "GAUCHE"
                couleur = (255, 0, 255) # Rose
                
            # Affichage de l'ordre à l'écran
            cv2.putText(display_frame, f"ORDRE : TOURNER A {direction}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, couleur, 3)
            cv2.putText(display_frame, f"Surface: {int(surface)} | Sommets -> G: {cote_gauche} / D: {cote_droit}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Dessiner les 7 sommets en orange
            for point in approx:
                px, py = point[0]
                cv2.circle(display_frame, (px, py), 6, (0, 165, 255), -1)

        else:
            # L'objet a la bonne surface, mais pas 7 sommets (ex: un carré parfait de 40 000 px)
            # On le dessine en rouge pour que tu comprennes pourquoi il est rejeté
            cv2.drawContours(display_frame, [approx], -1, (0, 0, 255), 2)

    return display_frame
# --- BOUCLE PRINCIPALE ---
vidcap = cv2.VideoCapture(0)

if not vidcap.isOpened():
    print("Erreur : Impossible d'accéder à la caméra.")
    exit()

while True:
    ret, frame = vidcap.read()
    if not ret:
        break
        
    # On ajoute un léger flou initial comme ton camarade
    frame = cv2.GaussianBlur(frame, (5, 5), 0)
    
    processed = processing_frame(frame)
    cv2.imshow("Robot - Analyse", processed)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vidcap.release()
cv2.destroyAllWindows()