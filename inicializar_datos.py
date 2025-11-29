import pyodbc
from database import db

def cargar_datos_reales():
    print("🚀 Iniciando carga ordenada según TUS IMÁGENES...")
    
    # ==============================================================================
    # 1. HEMOGRAMA COMPLETO (Orden Exacto de tu imagen)
    # ==============================================================================
    analitos_hemo_completo = [
        # BLOQUE 1: GENERAL (Sin subtítulo visible o "General")
        {"nombre": "LEUCOCITOS",   "unidad": "10e3/uL", "cat": "Hematología", "sub": "General", "tipo": "Numerico", "min": 4.5, "max": 11.0, "ref": "4.5 - 11.0"},
        {"nombre": "HEMATIES",     "unidad": "10e6/uL", "cat": "Hematología", "sub": "General", "tipo": "Numerico", "min": 4.1, "max": 5.5,  "ref": "4.10 - 5.50"},
        {"nombre": "HEMOGLOBINA",  "unidad": "g/dL",    "cat": "Hematología", "sub": "General", "tipo": "Numerico", "min": 12.0, "max": 16.0, "ref": "12.00 - 16.00"},
        {"nombre": "HEMATOCRITO",  "unidad": "%",       "cat": "Hematología", "sub": "General", "tipo": "Numerico", "min": 36.0, "max": 48.0, "ref": "36.0 - 48.0"},
        {"nombre": "MCV",          "unidad": "fL",      "cat": "Hematología", "sub": "General", "tipo": "Numerico", "min": 80.0, "max": 100.0,"ref": "80.0 - 100.0"},
        {"nombre": "MCH",          "unidad": "pg",      "cat": "Hematología", "sub": "General", "tipo": "Numerico", "min": 26.0, "max": 34.0, "ref": "26.0 - 34.0"},
        {"nombre": "MCHC",         "unidad": "g/dL",    "cat": "Hematología", "sub": "General", "tipo": "Numerico", "min": 31.0, "max": 37.0, "ref": "31.0 - 37.0"},
        {"nombre": "PLAQUETAS",    "unidad": "10e3/uL", "cat": "Hematología", "sub": "General", "tipo": "Numerico", "min": 150,  "max": 350,   "ref": "150.0 - 350.0"},
        
        # BLOQUE 2: DIFERENCIACION (Subtítulo explícito)
        {"nombre": "SEGMENTADOS",    "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 37, "max": 72, "ref": "37.0 - 72.0"},
        {"nombre": "ABASTONADOS",    "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 0,  "max": 7,  "ref": "0 - 7"},
        {"nombre": "METAMIELOCITOS", "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 0,  "max": 0,  "ref": "0 - 0"},
        {"nombre": "MIELOCITOS",     "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 0,  "max": 0,  "ref": "0 - 0"},
        {"nombre": "LINFOCITOS",     "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 20, "max": 50, "ref": "20.0 - 50.0"},
        {"nombre": "MONOCITOS",      "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 0,  "max": 20, "ref": "0.0 - 20.0"},
        {"nombre": "EOSINOFILOS",    "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 0,  "max": 6,  "ref": "0.0 - 6.0"},
        {"nombre": "BASOFILOS",      "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 0,  "max": 2,  "ref": "0.0 - 2.0"},
        {"nombre": "BLASTOS",        "unidad": "%", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 0,  "max": 0,  "ref": "0 - 0"},
        {"nombre": "ERITROBLASTOS",  "unidad": "/100 WBCs", "cat": "Hematología", "sub": "DIFERENCIACION MANUAL", "tipo": "Numerico", "min": 0, "max": 0, "ref": "0 - 0"},
        
        # BLOQUE 3: CIERRE
        {"nombre": "OBSERVACIONES", "unidad": None, "cat": "General", "sub": "OBSERVACIONES", "tipo": "Texto", "min": None, "max": None, "ref": ""}
    ]

    # ==============================================================================
    # 2. PERFIL LIPÍDICO
    # ==============================================================================
    analitos_lipido = [
        {"nombre": "COLESTEROL",      "unidad": "mg/dL", "cat": "Química", "sub": "General", "tipo": "Numerico", "min": 0, "max": 200, "ref": "MENOR A 200"},
        {"nombre": "TRIGLICERIDOS",   "unidad": "mg/dL", "cat": "Química", "sub": "General", "tipo": "Numerico", "min": 0, "max": 160, "ref": "MENOR A 160"},
        {"nombre": "HDL COLESTEROL",  "unidad": "mg/dL", "cat": "Química", "sub": "General", "tipo": "Numerico", "min": 35, "max": 65, "ref": "H: 35-55 / M: 45-65"},
        {"nombre": "LDL COLESTEROL",  "unidad": "mg/dL", "cat": "Química", "sub": "General", "tipo": "Numerico", "min": 0, "max": 129, "ref": "MENOR A 129"},
        {"nombre": "VLDL COLESTEROL", "unidad": "mg/dL", "cat": "Química", "sub": "General", "tipo": "Numerico", "min": 10, "max": 50, "ref": "10 - 50"},
        {"nombre": "OBSERVACIONES", "unidad": None, "cat": "General", "sub": "OBSERVACIONES", "tipo": "Texto", "min": None, "max": None, "ref": ""}
    ]

    # --- FUNCIÓN DE CARGA ---
    def procesar_lista(lista_analitos):
        ids = []
        for a in lista_analitos:
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM Analitos WHERE nombre = ?", (a['nombre'],))
                row = cursor.fetchone()
                aid = None
                
                if not row:
                    print(f"   + Creando: {a['nombre']}")
                    db.agregar_analito({
                        'nombre': a['nombre'], 'unidad': a['unidad'], 'categoria': a['cat'],
                        'subtitulo': a['sub'], 'tipoDato': a['tipo'], 'metodo': "",
                        'min': a.get('min'), 'max': a.get('max'), 'refVisual': a['ref'],
                        'formula': None, 'esCalculado': 0
                    })
                    cursor.execute("SELECT @@IDENTITY")
                    aid = cursor.fetchone()[0]
                else:
                    aid = row[0]
                
                if aid: ids.append(aid)
                conn.close()
            except Exception as e:
                print(f"Error con {a['nombre']}: {e}")
        return ids

    # CREAR PERFILES CON ORDEN
    print("\n--- Cargando Hemograma ---")
    ids_hemo = procesar_lista(analitos_hemo_completo) 
    
    conn = db.get_connection()
    exists = conn.cursor().execute("SELECT COUNT(*) FROM PerfilesExamen WHERE nombre = 'HEMOGRAMA COMPLETO'").fetchone()[0]
    conn.close()
    
    if exists == 0:
        db.agregar_perfil("HEMOGRAMA COMPLETO", "Hematología", 25.00, ids_hemo) 
        print("✅ Perfil 'HEMOGRAMA COMPLETO' creado.")
    else:
        print("ℹ️ Perfil ya existe.")

    print("\n--- Cargando Perfil Lipídico ---")
    ids_lipido = procesar_lista(analitos_lipido)
    
    conn = db.get_connection()
    exists = conn.cursor().execute("SELECT COUNT(*) FROM PerfilesExamen WHERE nombre = 'PERFIL LIPIDICO'").fetchone()[0]
    conn.close()
    
    if exists == 0:
        db.agregar_perfil("PERFIL LIPIDICO", "Química", 40.00, ids_lipido)
        print("✅ Perfil 'PERFIL LIPIDICO' creado.")
    else:
        print("ℹ️ Perfil ya existe.")

if __name__ == "__main__":
    cargar_datos_reales()