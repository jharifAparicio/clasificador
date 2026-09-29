"""Módulo para el renderizado del HUD, marcadores y elementos visuales con OpenCV."""

from typing import Any, Dict, List, Set, Tuple
import cv2
import numpy as np

from clasificador.config import COLORES_BGR, NOMBRES_CLASES


def dibujar_elementos(
    frame: np.ndarray,
    objetos_activos: List[Tuple[int, Dict[str, Any]]],
    ids_disparados: Set[int],
    roi_rect: Tuple[int, int, int, int],
    linea_x: int,
    total_contados: int,
    fps: float,
    latencia_ms: float,
) -> None:
    """Dibuja sobre el frame los contornos, bounding boxes, línea de trigger y HUD superior."""
    rx, ry, rw, rh = roi_rect
    h_img, w_img, _ = frame.shape

    # 1. Dibujar objetos activos detectados y rastreados
    for oid, data in objetos_activos:
        color = data["color"]
        x, y, w, h = data["bbox"]
        cnt = data["contour"]

        color_bgr = COLORES_BGR.get(color, (255, 255, 255))
        es_disparado = oid in ids_disparados

        grosor = 2 if es_disparado else 1
        cv2.drawContours(frame, [cnt], -1, color_bgr, grosor)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color_bgr, grosor)

        estado_txt = "ENVIADO" if es_disparado else "EN TRANSITO"
        nombre_color = NOMBRES_CLASES.get(color, color)
        etiqueta = f"#{oid} {nombre_color} [{estado_txt}]"

        (tw, th), _ = cv2.getTextSize(etiqueta, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(frame, (x, max(0, y - 20)), (x + tw + 6, y), color_bgr, -1)
        cv2.putText(
            frame,
            etiqueta,
            (x + 3, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 0) if color == "S" else (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    # 2. Contorno visual de la ROI de la cinta
    cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (70, 70, 70), 1)

    # 3. Línea de disparo con flecha indicativa de sentido (L -> R)
    cv2.line(frame, (linea_x, ry), (linea_x, ry + rh), (0, 255, 255), 2)
    cv2.arrowedLine(
        frame,
        (linea_x - 40, ry + 25),
        (linea_x + 30, ry + 25),
        (0, 255, 255),
        2,
        tipLength=0.3,
    )
    cv2.putText(
        frame,
        "TRIGGER (L -> R)",
        (linea_x - 55, ry - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )

    # 4. Barra HUD superior
    cv2.rectangle(frame, (0, 0), (w_img, 32), (20, 20, 20), -1)
    hud = (
        f"FPS: {fps:.1f} | Latencia: {latencia_ms:.1f}ms | "
        f"Procesados: {total_contados} | En transito: {len(objetos_activos)}"
    )
    cv2.putText(
        frame,
        hud,
        (10, 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )
