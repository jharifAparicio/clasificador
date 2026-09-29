import socket

PORT = 8888
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))

print(f"[DUMMY ESP32] Escuchando datagramas UDP en el puerto {PORT}...")

contadores = {'R': 0, 'G': 0, 'B': 0}
bloques_5 = {'R': 0, 'G': 0, 'B': 0}

while True:
    data, addr = sock.recvfrom(1024)
    cmd = data.decode('utf-8').strip()
    
    if cmd in ['R', 'G', 'B']:
        contadores[cmd] += 1
        print(f"[RECIBIDO de {addr[0]}] Pieza {cmd} | Conteo: {contadores[cmd]}")
        if contadores[cmd] >= 5:
            contadores[cmd] = 0
            bloques_5[cmd] += 1
            print(f"  >>> ¡BLOQUE DE 5 COMPLETADO para {cmd}! Total bloques: {bloques_5[cmd]}")
    elif cmd == 'S':
        print(f"[RECIBIDO de {addr[0]}] ¡¡¡COMODÍN DETECTADO -> PARO DE EMERGENCIA DE MOTOR!!!")
    elif cmd == 'U':
        print(f"[RECIBIDO de {addr[0]}] Objeto desconocido / Ruido descartado (No suma)")