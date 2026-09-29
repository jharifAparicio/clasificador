import sys
import numpy as np
import cv2
from ultralytics import YOLO

print(f"[OK] Python: {sys.version.split()[0]}")
print(f"[OK] OpenCV: {cv2.__version__}")
print(f"[OK] NumPy: {np.__version__}")

print("[...] Inicializando modelo YOLO...")
model = YOLO("yolov8n-seg.pt")
print("[OK] Modelo YOLOv8n-seg listo.")