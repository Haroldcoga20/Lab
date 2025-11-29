from dataclasses import dataclass
from typing import Optional

@dataclass
class PerfilExamen:
    id: int
    nombre: str
    categoria: str
    precioEstandar: float

    @classmethod
    def from_tuple(cls, t):
        return cls(
            id=t[0],
            nombre=t[1],
            categoria=t[2],
            precioEstandar=float(t[3]) if t[3] is not None else 0.0
        )
