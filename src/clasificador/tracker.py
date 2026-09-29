"""Módulo de seguimiento (tracking) de objetos en cinta transportadora (Izquierda a Derecha)."""

import time
from typing import Any, Dict, List, Set, Tuple
import numpy as np


class ConveyorTrackerLR:
    """Rastreador de centroides en 2D optimizado para flujo lineal unidireccional."""

    def __init__(self, max_dist: int = 120, max_perdido: int = 15, max_trayectoria: int = 12):
        self.next_id: int = 0
        self.max_dist: int = max_dist
        self.max_perdido: int = max_perdido
        self.max_trayectoria: int = max_trayectoria

        self.objetos: Dict[int, Tuple[int, int]] = {}
        self.trayectorias: Dict[int, List[Tuple[int, int, float]]] = {}
        self.desaparecido: Dict[int, int] = {}
        self.buffer_votos: Dict[int, List[str]] = {}
        self.ids_disparados: Set[int] = set()
        self.total_contados: int = 0

    def actualizar(self, candidatos: List[Dict[str, Any]]) -> List[Tuple[int, Dict[str, Any]]]:
        """Asocia detecciones actuales con objetos rastreados mediante distancia euclidiana mínima."""
        ahora = time.time()
        if len(candidatos) == 0:
            for oid in list(self.desaparecido.keys()):
                self.desaparecido[oid] += 1
                if self.desaparecido[oid] > self.max_perdido:
                    self.eliminar(oid)
            return []

        nuevos_pts = [(c["cx"], c["cy"]) for c in candidatos]

        if len(self.objetos) == 0:
            asignados = []
            for i, c in enumerate(candidatos):
                oid = self.registrar(nuevos_pts[i], c["color"], ahora)
                asignados.append((oid, c))
            return asignados

        obj_ids = list(self.objetos.keys())
        obj_coords = np.array(list(self.objetos.values()))
        nuevos_coords = np.array(nuevos_pts)

        # Matriz de distancias euclidianas entre centroides previos y nuevos
        D = np.linalg.norm(obj_coords[:, np.newaxis] - nuevos_coords[np.newaxis, :], axis=2)
        filas = D.min(axis=1).argsort()
        columnas = D.argmin(axis=1)[filas]

        filas_usadas = set()
        cols_usadas = set()
        asignados = []

        for f, c in zip(filas, columnas):
            if f in filas_usadas or c in cols_usadas:
                continue
            if D[f, c] > self.max_dist:
                continue

            oid = obj_ids[f]
            self.objetos[oid] = nuevos_pts[c]
            self.trayectorias[oid].append((nuevos_pts[c][0], nuevos_pts[c][1], ahora))
            if len(self.trayectorias[oid]) > self.max_trayectoria:
                self.trayectorias[oid].pop(0)

            self.desaparecido[oid] = 0
            filas_usadas.add(f)
            cols_usadas.add(c)
            asignados.append((oid, candidatos[c]))

        # Registrar nuevas piezas que entran a la cinta
        for c in range(len(nuevos_pts)):
            if c not in cols_usadas:
                oid = self.registrar(nuevos_pts[c], candidatos[c]["color"], ahora)
                asignados.append((oid, candidatos[c]))

        # Limpiar piezas que salieron del encuadre
        for f in range(len(obj_ids)):
            if f not in filas_usadas:
                oid = obj_ids[f]
                self.desaparecido[oid] += 1
                if self.desaparecido[oid] > self.max_perdido:
                    self.eliminar(oid)

        return asignados

    def registrar(self, pt: Tuple[int, int], color: str, t_stamp: float) -> int:
        """Registra un nuevo objeto en el tracker."""
        oid = self.next_id
        self.objetos[oid] = pt
        self.trayectorias[oid] = [(pt[0], pt[1], t_stamp)]
        self.desaparecido[oid] = 0
        self.buffer_votos[oid] = [color]
        self.next_id += 1
        return oid

    def eliminar(self, oid: int) -> None:
        """Elimina un objeto que ha salido del campo de visión."""
        self.objetos.pop(oid, None)
        self.trayectorias.pop(oid, None)
        self.desaparecido.pop(oid, None)
        self.buffer_votos.pop(oid, None)
        self.ids_disparados.discard(oid)
