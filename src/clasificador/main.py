"""Punto de entrada principal para el sistema de visión y clasificación de piezas."""

import sys
import time
from typing import Optional
import cv2

from clasificador.config import AppConfig
from clasificador.segmentation import segmentar_cubos
from clasificador.senders import BaseSender, create_sender
from clasificador.tracker import ConveyorTrackerLR
from clasificador.visualizer import dibujar_elementos


def run_pipeline(
    config: Optional[AppConfig] = None,
    sender: Optional[BaseSender] = None,
) -> None:
    """Ejecuta el ciclo principal de captura, tracking, clasificación y control.

    Args:
        config: Configuración de la aplicación (por defecto lee AppConfig).
        sender: Emisor de datos (UDP, HTTP, etc.). Si es None, se crea automáticamente
                a partir de config.comm_protocol ('udp' o 'http').
    """
    if config is None:
        config = AppConfig()

    if sender is None:
        # Crea el emisor según el protocolo configurado ("udp" o "http")
        sender = create_sender(
            protocol=config.comm_protocol,
            ip=config.esp32_ip,
            port=config.esp32_port,
            http_endpoint=config.http_endpoint,
            http_timeout=config.http_timeout,
        )

    print("==================================================")
    print("[INICIO] Flujo Cinta L->R | Descarte Cinta Negra")
    print(f"[CAMARA VIDEO_URL] {config.video_url}")
    print(f"[EMISOR {config.comm_protocol.upper()}] Destino: {config.esp32_ip}:{config.esp32_port}")
    print("==================================================")

    tracker = ConveyorTrackerLR(
        max_dist=config.tracker_max_dist,
        max_perdido=config.tracker_max_perdido,
        max_trayectoria=config.tracker_max_trayectoria,
    )
    cap = cv2.VideoCapture(config.video_url)

    cv2.namedWindow(config.window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(config.window_name, config.window_width, config.window_height)

    fps_historico = 0.0
    t_arranque = time.time()

    try:
        while True:
            t_inicio = time.time()
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.2)
                cap.open(config.video_url)
                continue

            h_img, w_img, _ = frame.shape

            # 1. ROI de la cinta útil
            rx = int(w_img * config.roi_x_pct)
            ry = int(h_img * config.roi_y_pct)
            rw = int(w_img * config.roi_w_pct)
            rh = int(h_img * config.roi_h_pct)
            roi_rect = (rx, ry, rw, rh)

            # 2. Línea de cruce (Trigger)
            linea_x = int(w_img * config.linea_trigger_pct)

            # 3. Procesamiento y detección cromática
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            candidatos = segmentar_cubos(
                hsv=hsv,
                roi_rect=roi_rect,
                area_min=config.area_min,
                area_max=config.area_max,
                aspect_ratio_min=config.aspect_ratio_min,
                aspect_ratio_max=config.aspect_ratio_max,
            )

            # 4. Seguimiento temporal de centroides
            objetos_activos = tracker.actualizar(candidatos)

            # 5. Evaluación de cruce y estabilización de votación de color
            for oid, data in objetos_activos:
                color = data["color"]

                tracker.buffer_votos.setdefault(oid, []).append(color)
                if len(tracker.buffer_votos[oid]) > config.tracker_max_votos:
                    tracker.buffer_votos[oid].pop(0)

                trayectoria = tracker.trayectorias[oid]
                if len(trayectoria) >= 2 and oid not in tracker.ids_disparados:
                    x_prev = trayectoria[-2][0]
                    x_curr = trayectoria[-1][0]

                    # Transición evaluada de izquierda a derecha sobre la vertical
                    if x_prev <= linea_x and x_curr >= linea_x:
                        votos = tracker.buffer_votos[oid]
                        color_confirmado = max(set(votos), key=votos.count)

                        tracker.ids_disparados.add(oid)
                        tracker.total_contados += 1

                        if (time.time() - t_arranque) > config.tiempo_estabilizacion_arranque:
                            sender.enviar(color_confirmado)

            # 6. Cálculo de métricas de rendimiento (FPS y latencia)
            ms_frame = (time.time() - t_inicio) * 1000.0
            fps_instantaneo = 1000.0 / ms_frame if ms_frame > 0 else 0.0
            fps_historico = 0.9 * fps_historico + 0.1 * fps_instantaneo

            # 7. Renderizado visual
            dibujar_elementos(
                frame=frame,
                objetos_activos=objetos_activos,
                ids_disparados=tracker.ids_disparados,
                roi_rect=roi_rect,
                linea_x=linea_x,
                total_contados=tracker.total_contados,
                fps=fps_historico,
                latencia_ms=ms_frame,
            )

            cv2.imshow(config.window_name, frame)

            if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        sender.close()


def main() -> None:
    """Función de arranque estándar."""
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n[OK] Finalizado por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
