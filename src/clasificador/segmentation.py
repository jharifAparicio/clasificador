"""Módulo de segmentación cromática y filtrado morfológico de piezas en cinta."""

from typing import Any, Dict, List, Tuple
import cv2
import numpy as np


def segmentar_cubos(
    hsv: np.ndarray,
    roi_rect: Tuple[int, int, int, int],
    area_min: float = 1500.0,
    area_max: float = 45000.0,
    aspect_ratio_min: float = 0.2,
    aspect_ratio_max: float = 5.0,
) -> List[Dict[str, Any]]:
    """Segmenta objetos según máscaras HSV en una ROI y descarta el fondo/cinta negra.

    Retorna una lista de candidatos detectados con sus centroides, bbox, color y contorno.
    """
    rx, ry, rw, rh = roi_rect
    kernel = np.ones((5, 5), np.uint8)

    # 1. Máscaras para colores primarios
    # Rojo (rangos en los dos extremos del matiz H)
    m_r1 = cv2.inRange(hsv, np.array([0, 80, 70]), np.array([10, 255, 255]))
    m_r2 = cv2.inRange(hsv, np.array([168, 80, 70]), np.array([179, 255, 255]))
    mask_r = cv2.bitwise_or(m_r1, m_r2)

    # Verde
    mask_g = cv2.inRange(hsv, np.array([36, 60, 50]), np.array([86, 255, 255]))

    # Azul
    mask_b = cv2.inRange(hsv, np.array([96, 95, 60]), np.array([135, 255, 255]))

    # Unión de los colores primarios conocidos
    mask_rgb = cv2.bitwise_or(mask_r, cv2.bitwise_or(mask_g, mask_b))

    # 2. Filtro anti-cinta negra:
    # La banda de goma tiene brillo (V) muy bajo. Al exigir V >= 65 y S >= 50
    # se descartan tanto el negro de la cinta como grises o reflejos metálicos opacos.
    mask_no_negro = cv2.inRange(hsv, np.array([0, 50, 65]), np.array([179, 255, 255]))

    # 3. Comodín 'S': Cualquier objeto sobre la cinta que NO sea negro ni R/G/B
    mask_comodin = cv2.bitwise_and(mask_no_negro, cv2.bitwise_not(mask_rgb))

    mascaras = {
        "R": mask_r,
        "G": mask_g,
        "B": mask_b,
        "S": mask_comodin,
    }

    candidatos: List[Dict[str, Any]] = []

    for color_key, mask in mascaras.items():
        # Aislar exclusivamente en la zona útil de la cinta
        mask_roi = np.zeros_like(mask)
        mask_roi[ry : ry + rh, rx : rx + rw] = mask[ry : ry + rh, rx : rx + rw]

        # Operaciones morfológicas para eliminar ruido y cerrar contornos
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_OPEN, kernel, iterations=1)
        mask_roi = cv2.morphologyEx(mask_roi, cv2.MORPH_CLOSE, kernel, iterations=2)

        contornos, _ = cv2.findContours(mask_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contornos:
            area = cv2.contourArea(cnt)
            # Área mínima y máxima para descartar manchas o la cinta entera
            if area_min < area < area_max:
                x, y, w, h_box = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / h_box if h_box > 0 else 0

                # Relación dimensional esperada para cubos / prismas
                if aspect_ratio_min < aspect_ratio < aspect_ratio_max:
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        candidatos.append({
                            "cx": cx,
                            "cy": cy,
                            "color": color_key,
                            "bbox": (x, y, w, h_box),
                            "contour": cnt,
                        })

    return candidatos
