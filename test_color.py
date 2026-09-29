import os
import time
import cv2
import numpy as np
from ultralytics import YOLO

VIDEO_URL = os.getenv("VIDEO_URL", "http://192.168.100.160:4747/video")

def clasificar_color_en_mascara(hsv_img, mask_binaria):
    total_pixeles = cv2.countNonZero(mask_binaria)
    
    # 1. Filtro de tamaño mínimo (ruido)
    if total_pixeles < 800:
        return 'U', 0.0, "Area muy pequeña"

    # 2. Filtro de saturación y brillo medios dentro del objeto segmentado
    s_vals = hsv_img[:, :, 1][mask_binaria > 0]
    v_vals = hsv_img[:, :, 2][mask_binaria > 0]
    sat_media = np.mean(s_vals)
    val_medio = np.mean(v_vals)

    if sat_media < 65 or val_medio < 40:
        return 'U', 0.0, f"Sin color vivo (S={sat_media:.1f}, V={val_medio:.1f})"

    # 3. Máscaras HSV calibradas para los 4 colores
    # Rojo: cubre extremos 0-10 y 165-179
    m_r1 = cv2.inRange(hsv_img, np.array([0, 80, 60]), np.array([10, 255, 255]))
    m_r2 = cv2.inRange(hsv_img, np.array([165, 80, 60]), np.array([179, 255, 255]))
    count_r = cv2.countNonZero((m_r1 | m_r2) & mask_binaria)

    # Verde
    m_g = cv2.inRange(hsv_img, np.array([36, 70, 50]), np.array([85, 255, 255]))
    count_g = cv2.countNonZero(m_g & mask_binaria)

    # Azul
    m_b = cv2.inRange(hsv_img, np.array([95, 70, 50]), np.array([135, 255, 255]))
    count_b = cv2.countNonZero(m_b & mask_binaria)

    # Amarillo (Comodín / Paro)
    m_y = cv2.inRange(hsv_img, np.array([18, 80, 70]), np.array([34, 255, 255]))
    count_y = cv2.countNonZero(m_y & mask_binaria)

    conteos = {'R': count_r, 'G': count_g, 'B': count_b, 'S': count_y}
    mejor = max(conteos, key=conteos.get)
    pureza = conteos[mejor] / total_pixeles

    # Al menos el 40% de los píxeles del bloque deben coincidir con el color ganador
    if pureza >= 0.40:
        nombres = {'R': 'ROJO', 'G': 'VERDE', 'B': 'AZUL', 'S': 'AMARILLO (STOP)'}
        return mejor, pureza, nombres[mejor]
    
    return 'U', pureza, "Color no coincide (Descartado)"

def main():
    print("[IA] Cargando modelo YOLOv8n-seg...")
    model = YOLO("yolov8n-seg.pt")

    print(f"[VIDEO] Conectando a {VIDEO_URL}...")
    cap = cv2.VideoCapture(VIDEO_URL)

    print("---------------------------------------------------------------")
    print("Coloca un bloque (Rojo, Verde, Azul, Amarillo o cualquier otro)")
    print("frente a la cámara. Presiona Ctrl+C en la terminal para salir.")
    print("---------------------------------------------------------------")

    ultimo_print = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.5)
            cap.open(VIDEO_URL)
            continue

        h, w, _ = frame.shape
        # Inferencia con YOLO sobre el cuadro completo
        results = model(frame, conf=0.35, verbose=False)

        for result in results:
            if result.masks is not None:
                for mask in result.masks.data:
                    mask_np = mask.cpu().numpy()
                    mask_resized = cv2.resize(mask_np, (w, h))
                    mask_bin = (mask_resized > 0.5).astype(np.uint8) * 255

                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    cmd, pureza, detalle = clasificar_color_en_mascara(hsv, mask_bin)

                    ahora = time.time()
                    # Imprimir como máximo cada 0.6 segundos para no saturar la consola
                    if ahora - ultimo_print > 0.6:
                        print(f"[DETECTADO] Comando: '{cmd}' | Pureza: {pureza*100:.1f}% | Info: {detalle}")
                        ultimo_print = ahora

        time.sleep(0.03)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[OK] Calibración finalizada.")