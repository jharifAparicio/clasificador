"""Paquete clasificador de visión computacional para cinta transportadora."""

from clasificador.config import AppConfig, COLORES_BGR, NOMBRES_CLASES
from clasificador.main import main, run_pipeline
from clasificador.segmentation import segmentar_cubos
from clasificador.senders import BaseSender, ConsoleSender, HTTPSender, UDPSender, create_sender
from clasificador.tracker import ConveyorTrackerLR

__all__ = [
    "AppConfig",
    "COLORES_BGR",
    "NOMBRES_CLASES",
    "ConveyorTrackerLR",
    "BaseSender",
    "UDPSender",
    "HTTPSender",
    "ConsoleSender",
    "create_sender",
    "segmentar_cubos",
    "run_pipeline",
    "main",
]
