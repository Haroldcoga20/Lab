from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Paciente:
    id: int
    nombreCompleto: str
    edad: int
    unidadEdad: str
    genero: str
    dni: Optional[str] = None
    telefono: Optional[str] = None
    fechaCreacion: Optional[datetime] = None

    @classmethod
    def from_tuple(cls, t):
        return cls(
            id=t[0],
            nombreCompleto=t[1],
            edad=t[2],
            unidadEdad=t[3],
            genero=t[4],
            dni=t[5],
            telefono=t[6],
            fechaCreacion=t[7]
        )
