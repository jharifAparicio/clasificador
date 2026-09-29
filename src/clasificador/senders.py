"""Módulo de comunicación agnóstica para el envío de datos de clasificación (UDP, HTTP, etc.)."""

import json
import socket
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseSender(ABC):
    """Interfaz base para transmisores de datos de clasificación."""

    @abstractmethod
    def enviar(self, comando: str) -> bool:
        """Envía el comando/etiqueta de color al destino configurado."""
        pass

    def close(self) -> None:
        """Libera sockets o conexiones si aplica."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class UDPSender(BaseSender):
    """Envío de comandos mediante datagramas UDP a microcontrolador o receptor."""

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._init_socket()

    def _init_socket(self) -> None:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as e:
            print(f"[UDP ERROR] No se pudo inicializar el socket UDP: {e}")
            self._sock = None

    def enviar(self, comando: str) -> bool:
        if self._sock is None:
            self._init_socket()
            if self._sock is None:
                return False

        try:
            self._sock.sendto(comando.encode("utf-8"), (self.ip, self.port))
            print("\n=======================================================")
            print(f">>> [TRIGGER CINTA (L->R) UDP] -> {self.ip}:{self.port} | PIEZA: '{comando}' <<<")
            print("=======================================================\n")
            return True
        except Exception as e:
            print(f"[UDP ERROR] al enviar a {self.ip}:{self.port}: {e}")
            return False

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None


class HTTPSender(BaseSender):
    """Envío de comandos mediante peticiones HTTP POST (REST API) con timeout seguro."""

    def __init__(self, url: str, timeout: float = 1.0):
        self.url = url
        self.timeout = timeout

    @classmethod
    def from_host_port(
        cls, ip: str, port: int, endpoint: str = "/clasificar", timeout: float = 1.0
    ) -> "HTTPSender":
        endpoint_clean = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        url = f"http://{ip}:{port}{endpoint_clean}"
        return cls(url=url, timeout=timeout)

    def enviar(self, comando: str) -> bool:
        payload = json.dumps({"color": comando, "comando": comando}).encode("utf-8")
        req = urllib.request.Request(
            url=self.url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ClasificadorVision/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status = response.status
                print("\n=======================================================")
                print(f">>> [TRIGGER CINTA (L->R) HTTP] -> {self.url} (Status: {status}) | PIEZA: '{comando}' <<<")
                print("=======================================================\n")
                return 200 <= status < 300
        except urllib.error.HTTPError as e:
            print(f"[HTTP ERROR] Respuesta del servidor {self.url}: {e.code} - {e.reason}")
            return False
        except urllib.error.URLError as e:
            print(f"[HTTP ERROR] No se pudo conectar a {self.url}: {e.reason}")
            return False
        except Exception as e:
            print(f"[HTTP ERROR] Error inesperado enviando a {self.url}: {e}")
            return False


class ConsoleSender(BaseSender):
    """Emisor simulado que imprime en terminal para pruebas locales."""

    def enviar(self, comando: str) -> bool:
        print("\n=======================================================")
        print(f">>> [TRIGGER CINTA (L->R) CONSOLA] | PIEZA: '{comando}' <<<")
        print("=======================================================\n")
        return True


def create_sender(
    protocol: str = "udp",
    ip: str = "127.0.0.1",
    port: int = 8888,
    http_endpoint: str = "/clasificar",
    http_timeout: float = 1.0,
    **kwargs: Any,
) -> BaseSender:
    """Factory para crear el emisor adecuado según el protocolo ('udp', 'http', 'console').

    Permite cambiar entre protocolos cambiando simplemente el parámetro `protocol`.
    """
    protocolo_limpio = protocol.strip().lower()

    if protocolo_limpio == "udp":
        return UDPSender(ip=ip, port=port)
    elif protocolo_limpio == "http":
        return HTTPSender.from_host_port(
            ip=ip, port=port, endpoint=http_endpoint, timeout=http_timeout
        )
    elif protocolo_limpio in ("console", "consola", "mock"):
        return ConsoleSender()
    else:
        raise ValueError(
            f"Protocolo desconocido: '{protocol}'. Protocolos soportados: 'udp', 'http', 'console'"
        )
