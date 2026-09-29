"""Script de prueba de integración completa del clasificador.

Ejecutar con:
    uv run python test_integration.py
"""

import http.server
import json
import socket
import threading
import time
import cv2
import numpy as np

from clasificador.config import AppConfig
from clasificador.segmentation import segmentar_cubos
from clasificador.senders import HTTPSender, UDPSender, create_sender
from clasificador.tracker import ConveyorTrackerLR


def test_udp_transmission():
    print("\n--- [TEST 1] Envío y recepción UDP ---")
    recibidos = []
    stop_event = threading.Event()
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind(("127.0.0.1", 8888))
    server_sock.settimeout(0.5)

    def udp_listener():
        while not stop_event.is_set():
            try:
                data, _ = server_sock.recvfrom(1024)
                recibidos.append(data.decode("utf-8"))
            except socket.timeout:
                continue

    t = threading.Thread(target=udp_listener, daemon=True)
    t.start()

    sender = create_sender("udp", ip="127.0.0.1", port=8888)
    assert isinstance(sender, UDPSender)
    sender.enviar("R")
    sender.enviar("G")
    sender.enviar("S")

    time.sleep(0.2)
    stop_event.set()
    server_sock.close()
    sender.close()

    assert recibidos == ["R", "G", "S"], f"Esperado ['R', 'G', 'S'], obtenido: {recibidos}"
    print(f"✔ OK: Se enviaron y recibieron correctamente los comandos UDP: {recibidos}")


def test_http_transmission():
    print("\n--- [TEST 2] Envío y recepción HTTP ---")
    peticiones_recibidas = []

    class MockHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            peticiones_recibidas.append(body)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        def log_message(self, *args):
            pass

    httpd = http.server.HTTPServer(("127.0.0.1", 8989), MockHandler)
    t = threading.Thread(target=httpd.handle_request, daemon=True)
    t.start()

    sender = create_sender("http", ip="127.0.0.1", port=8989, http_endpoint="/clasificar")
    assert isinstance(sender, HTTPSender)
    exito = sender.enviar("B")

    t.join(timeout=1.0)
    httpd.server_close()
    sender.close()

    assert exito is True
    assert len(peticiones_recibidas) == 1
    assert peticiones_recibidas[0]["color"] == "B"
    print(f"✔ OK: Se envió payload JSON por HTTP POST y se recibió con Status 200: {peticiones_recibidas[0]}")


def test_pipeline_tracking_trigger():
    print("\n--- [TEST 3] Visión, Segmentación y Cruce Trigger (L -> R) ---")
    config = AppConfig(tiempo_estabilizacion_arranque=0.0)
    tracker = ConveyorTrackerLR(
        max_dist=config.tracker_max_dist,
        max_perdido=config.tracker_max_perdido,
        max_trayectoria=config.tracker_max_trayectoria,
    )

    w_img, h_img = 640, 480
    linea_x = int(w_img * config.linea_trigger_pct)  # 352 px
    roi_rect = (
        int(w_img * config.roi_x_pct),
        int(h_img * config.roi_y_pct),
        int(w_img * config.roi_w_pct),
        int(h_img * config.roi_h_pct),
    )

    # Simular una pieza verde desplazándose de izquierda a derecha y cruzando la línea
    piezas_disparadas = []
    posiciones = [240, 310, 380]  # El último cruza los 352 px

    for x in posiciones:
        frame = np.zeros((h_img, w_img, 3), dtype=np.uint8)
        frame[200:250, x : x + 50] = [0, 255, 0]  # BGR Verde

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        candidatos = segmentar_cubos(hsv, roi_rect, area_min=100)
        objetos_activos = tracker.actualizar(candidatos)

        for oid, data in objetos_activos:
            color = data["color"]
            tracker.buffer_votos.setdefault(oid, []).append(color)
            trayectoria = tracker.trayectorias[oid]

            if len(trayectoria) >= 2 and oid not in tracker.ids_disparados:
                x_prev = trayectoria[-2][0]
                x_curr = trayectoria[-1][0]
                if x_prev <= linea_x and x_curr >= linea_x:
                    votos = tracker.buffer_votos[oid]
                    color_confirmado = max(set(votos), key=votos.count)
                    tracker.ids_disparados.add(oid)
                    tracker.total_contados += 1
                    piezas_disparadas.append(color_confirmado)

    assert piezas_disparadas == ["G"]
    print(f"✔ OK: Pieza Verde detectada, trackeada y trigger disparado al cruzar: {piezas_disparadas}")


def main():
    print("==================================================")
    print(" INICIANDO PRUEBAS DE INTEGRACIÓN DEL CLASIFICADOR")
    print("==================================================")
    test_udp_transmission()
    test_http_transmission()
    test_pipeline_tracking_trigger()
    print("\n==================================================")
    print("  ¡TODAS LAS PRUEBAS (3/3) PASARON EXITOSAMENTE!  ")
    print("==================================================")


if __name__ == "__main__":
    main()
