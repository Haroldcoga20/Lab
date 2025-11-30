from dataclasses import dataclass
from typing import Optional

@dataclass
class RangoReferencia:
    id: int
    analitoId: int
    unidadEdad: str
    genero: Optional[str] = 'Ambos'
    edadMin: Optional[int] = 0
    edadMax: Optional[int] = 120
    valorMin: Optional[float] = None
    valorMax: Optional[float] = None
    referenciaVisualEspecifica: Optional[str] = None
    textoInterpretacion: Optional[str] = None
    panicoMin: Optional[float] = None
    panicoMax: Optional[float] = None

    @classmethod
    def from_tuple(cls, t):
        return cls(
            id=t[0],
            analitoId=t[1],
            genero=t[2],
            edadMin=t[3],
            edadMax=t[4],
            valorMin=float(t[5]) if t[5] is not None else None,
            valorMax=float(t[6]) if t[6] is not None else None,
            referenciaVisualEspecifica=t[7],
            unidadEdad=t[8],
            textoInterpretacion=t[9],
            panicoMin=float(t[10]) if t[10] is not None else None,
            panicoMax=float(t[11]) if t[11] is not None else None
        )
