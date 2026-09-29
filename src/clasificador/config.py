"""Módulo de configuración para el clasificador de cinta transportadora."""

import os
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class AppConfig:
    # Parámetros de conexión y streaming de video
    video_url: str = field(
        default_factory=lambda: os.getenv("VIDEO_URL", "http://192.168.100.160:4747/video")
    )
    esp32_ip: str = field(
        default_factory=lambda: os.getenv("ESP32_IP", "127.0.0.1")
    )
    esp32_port: int = field(
        default_factory=lambda: int(os.getenv("ESP32_PORT", "8888"))
    )

    # =========================================================================
    # PROTOCOLO DE ENVÍO DE DATOS: Cambia entre "udp" y "http" en una sola línea
    # =========================================================================
    comm_protocol: str = field(
        default_factory=lambda: os.getenv("COMM_PROTOCOL", "udp").lower()
    )
    http_endpoint: str = field(
        default_factory=lambda: os.getenv("HTTP_ENDPOINT", "/clasificar")
    )
    http_timeout: float = 1.0

    # Parámetros del tracker de cinta
    tracker_max_dist: int = 120
    tracker_max_perdido: int = 15
    tracker_max_trayectoria: int = 12
    tracker_max_votos: int = 10
    tiempo_estabilizacion_arranque: float = 1.5

    # Parámetros de ROI (porcentajes respecto al tamaño del frame)
    roi_x_pct: float = 0.05
    roi_y_pct: float = 0.15
    roi_w_pct: float = 0.90
    roi_h_pct: float = 0.70

    # Línea de disparo de izquierda a derecha (L -> R)
    linea_trigger_pct: float = 0.55

    # Filtros de área y relación de aspecto para contornos
    area_min: float = 1500.0
    area_max: float = 45000.0
    aspect_ratio_min: float = 0.2
    aspect_ratio_max: float = 5.0

    # Dimensiones de ventana para visualización
    window_name: str = "Control de Calidad - Cinta Transportadora"
    window_width: int = 960
    window_height: int = 720


# Colores BGR para visualización en OpenCV
COLORES_BGR: Dict[str, Tuple[int, int, int]] = {
    "R": (0, 0, 255),       # Rojo
    "G": (0, 255, 0),       # Verde
    "B": (255, 0, 0),       # Azul
    "S": (255, 255, 0),     # Comodín / Otro color (Cian en HUD)
}

# Nombres legibles de las clases clasificadas
NOMBRES_CLASES: Dict[str, str] = {
    "R": "ROJO",
    "G": "VERDE",
    "B": "AZUL",
    "S": "COMODIN (OTRO)",
}
