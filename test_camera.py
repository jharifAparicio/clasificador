import os
import sys
import time
import cv2

# Cambia esta URL por la IP y puerto que te da la app de tu celular
DEFAULT_URL = "http://192.168.100.160:4747/video"
VIDEO_URL = os.getenv("VIDEO_URL", DEFAULT_URL)

print(f"[VIDEO] Conectando a: {VIDEO_URL}")
cap = cv2.VideoCapture(VIDEO_URL)

if not cap.isOpened():
    print("[ERROR] No se pudo abrir el stream de video.")
    print("Verifica que el móvil esté en la misma red Wi-Fi y la URL sea correcta.")
    sys.exit(1)

print("[OK] Stream conectado con éxito.")
print("Leyendo 30 cuadros para calcular resolución y rendimiento...")

frames_leidos = 0
inicio = time.time()

while frames_leidos < 30:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Falló la lectura de un cuadro.")
        break
    frames_leidos += 1

fin = time.time()
duracion = fin - inicio
fps = frames_leidos / duracion if duracion > 0 else 0

alto, ancho, canales = frame.shape
print("------------------------------------------")
print(f"[RESULTADO] Resolución: {ancho}x{alto} px")
print(f"[RESULTADO] Cuadros leídos: {frames_leidos}/30")
print(f"[RESULTADO] Velocidad promedio: {fps:.2f} FPS")
print("------------------------------------------")

cap.release()
print("[OK] Prueba de cámara completada.")