from dataclasses import dataclass
from typing import Optional

@dataclass
class Analito:
    id: int
    nombre: str
    tipoDato: str
    categoria: str
    unidad: Optional[str] = None
    metodo: Optional[str] = None
    tipoMuestra: Optional[str] = None
    valorRefMin: Optional[float] = None
    valorRefMax: Optional[float] = None
    referenciaVisual: Optional[str] = None
    subtituloReporte: Optional[str] = None
    formula: Optional[str] = None
    esCalculado: bool = False
    abreviatura: Optional[str] = None

    @classmethod
    def from_tuple(cls, t):
        # Maps a pyodbc Row (tuple) to the Analito object.
        # Assumes order: id, nombre, unidad, categoria, metodo, tipoMuestra, tipoDato,
        # valorRefMin, valorRefMax, referenciaVisual, subtituloReporte, formula, esCalculado, abreviatura
        return cls(
            id=t[0],
            nombre=t[1],
            unidad=t[2],
            categoria=t[3],
            metodo=t[4],
            tipoMuestra=t[5],
            tipoDato=t[6],
            valorRefMin=float(t[7]) if t[7] is not None else None,
            valorRefMax=float(t[8]) if t[8] is not None else None,
            referenciaVisual=t[9],
            subtituloReporte=t[10],
            formula=t[11],
            esCalculado=bool(t[12]),
            abreviatura=t[13]
        )
