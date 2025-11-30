from dataclasses import dataclass
from typing import Optional

@dataclass
class Medico:
    id: int
    nombre: str
    especialidad: str
    telefono: Optional[str] = None
    tieneConvenio: bool = False

    @classmethod
    def from_tuple(cls, t):
        return cls(
            id=t[0],
            nombre=t[1],
            especialidad=t[2],
            telefono=t[3],
            tieneConvenio=bool(t[4])
        )
