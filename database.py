import pyodbc
import threading
from datetime import datetime

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Connection Details
        self.driver = '{ODBC Driver 17 for SQL Server}'
        self.server = r'LAPTOP-3COEKCGP\SQLEXPRESS'
        self.database = 'LabDivinoNinoDB'
        self.trusted_connection = 'yes'

        self.connection_string = (
            f"DRIVER={self.driver};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"Trusted_Connection={self.trusted_connection};"
        )

        self.connection = None
        self._initialized = True

    def connect(self):
        """Establishes the database connection."""
        try:
            self.connection = pyodbc.connect(self.connection_string)
            print("Conexión a base de datos exitosa.")
            return True
        except Exception as e:
            print(f"Error conectando a la base de datos: {e}")
            self.connection = None
            return False

    def close(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
            print("Conexión cerrada.")
            self.connection = None

    def get_connection(self):
        """Returns the current connection, reconnecting if necessary."""
        if self.connection is None:
            self.connect()
        return self.connection

    def sanitize_input(self, value):
        """
        Sanitizes input data.
        Converts empty strings '' to None (NULL in SQL).
        """
        if value == '':
            return None
        return value

    # --- CRUD ANALITOS ---
    def get_all_analitos(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Analitos ORDER BY nombre")
        return cursor.fetchall()

    def upsert_analito(self, data):
        """
        Inserts or Updates an Analito.
        data: dict with keys matching fields + 'id' (optional for update).
        """
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        # Extract and sanitize
        nombre = data.get('nombre')
        unidad = self.sanitize_input(data.get('unidad'))
        categoria = data.get('categoria')
        metodo = self.sanitize_input(data.get('metodo'))
        tipoMuestra = self.sanitize_input(data.get('tipoMuestra'))
        tipoDato = data.get('tipoDato')
        val_min = float(data['valorRefMin']) if data.get('valorRefMin') else None
        val_max = float(data['valorRefMax']) if data.get('valorRefMax') else None
        visual = self.sanitize_input(data.get('referenciaVisual'))
        esCalculado = 1 if data.get('esCalculado') else 0
        formula = self.sanitize_input(data.get('formula'))

        if data.get('id'):
            # Update
            query = """
                UPDATE Analitos SET
                nombre=?, unidad=?, categoria=?, metodo=?, tipoMuestra=?, tipoDato=?,
                valorRefMin=?, valorRefMax=?, referenciaVisual=?, esCalculado=?, formula=?
                WHERE id=?
            """
            cursor.execute(query, (nombre, unidad, categoria, metodo, tipoMuestra, tipoDato,
                                   val_min, val_max, visual, esCalculado, formula, data['id']))
        else:
            # Insert
            query = """
                INSERT INTO Analitos (
                    nombre, unidad, categoria, metodo, tipoMuestra, tipoDato,
                    valorRefMin, valorRefMax, referenciaVisual, esCalculado, formula
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (nombre, unidad, categoria, metodo, tipoMuestra, tipoDato,
                                   val_min, val_max, visual, esCalculado, formula))
        conn.commit()

    # --- CRUD RANGOS ---
    def get_rangos_by_analito(self, analito_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM RangosReferencia WHERE analitoId = ?", analito_id)
        return cursor.fetchall()

    def add_rango(self, data):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO RangosReferencia (analitoId, genero, edadMin, edadMax, unidadEdad, valorMin, valorMax)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['analitoId'],
            data['genero'],
            int(data['edadMin']),
            int(data['edadMax']),
            data['unidadEdad'],
            float(data['valorMin']) if data.get('valorMin') else None,
            float(data['valorMax']) if data.get('valorMax') else None
        ))
        conn.commit()

    def delete_rango(self, rango_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM RangosReferencia WHERE id = ?", rango_id)
        conn.commit()

    # --- CRUD PERFILES ---
    def get_all_perfiles(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM PerfilesExamen ORDER BY nombre")
        return cursor.fetchall()

    def get_perfil_analitos(self, perfil_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.* FROM Analitos a
            JOIN DetallePerfilAnalito dpa ON a.id = dpa.analitoId
            WHERE dpa.perfilExamenId = ?
        """, perfil_id)
        return cursor.fetchall()

    def upsert_perfil(self, data, analito_ids):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        precio = float(data['precioEstandar']) if data.get('precioEstandar') else 0.0
        perfil_id = data.get('id')

        if perfil_id:
            # Update
            cursor.execute("""
                UPDATE PerfilesExamen SET nombre=?, categoria=?, precioEstandar=?
                WHERE id=?
            """, (data['nombre'], data['categoria'], precio, perfil_id))
            # Clear details to re-insert
            cursor.execute("DELETE FROM DetallePerfilAnalito WHERE perfilExamenId=?", perfil_id)
        else:
            # Insert
            cursor.execute("""
                INSERT INTO PerfilesExamen (nombre, categoria, precioEstandar)
                OUTPUT INSERTED.ID
                VALUES (?, ?, ?)
            """, (data['nombre'], data['categoria'], precio))
            perfil_id = cursor.fetchone()[0]

        # Insert Details
        for aid in analito_ids:
            cursor.execute("""
                INSERT INTO DetallePerfilAnalito (perfilExamenId, analitoId, orden)
                VALUES (?, ?, 0)
            """, (perfil_id, aid))

        conn.commit()

    # --- PHASE 2: PACIENTES ---
    def get_all_pacientes(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Pacientes ORDER BY nombreCompleto")
        return cursor.fetchall()

    def search_pacientes(self, term):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        term = f"%{term}%"
        cursor.execute("SELECT * FROM Pacientes WHERE nombreCompleto LIKE ? OR dni LIKE ?", (term, term))
        return cursor.fetchall()

    def upsert_paciente(self, data):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        nombre = data.get('nombreCompleto')
        edad = int(data.get('edad'))
        unidad_edad = data.get('unidadEdad')
        genero = data.get('genero')
        dni = self.sanitize_input(data.get('dni'))
        telefono = self.sanitize_input(data.get('telefono'))

        if data.get('id'):
             cursor.execute("""
                UPDATE Pacientes SET nombreCompleto=?, edad=?, unidadEdad=?, genero=?, dni=?, telefono=?
                WHERE id=?
            """, (nombre, edad, unidad_edad, genero, dni, telefono, data['id']))
        else:
            cursor.execute("""
                INSERT INTO Pacientes (nombreCompleto, edad, unidadEdad, genero, dni, telefono)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, edad, unidad_edad, genero, dni, telefono))
        conn.commit()

    # --- PHASE 2: MEDICOS & ORDENES ---
    def get_all_medicos(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Medicos ORDER BY nombre")
        return cursor.fetchall()

    def ensure_default_profile(self):
        """Ensures a 'Individual / General' profile exists for single analytes."""
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()

        # Check if ID 1 exists or look for a specific name
        cursor.execute("SELECT id FROM PerfilesExamen WHERE nombre = 'Examenes Individuales'")
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            # Create it
            cursor.execute("""
                INSERT INTO PerfilesExamen (nombre, categoria, precioEstandar)
                OUTPUT INSERTED.ID
                VALUES ('Examenes Individuales', 'General', 0)
            """)
            conn.commit()
            return cursor.fetchone()[0]

    def create_orden_trabajo(self, paciente_id, medico_id, items):
        """
        Creates an order with mixed Profiles and Individual Analytes.
        items: list of dicts {'type': 'perfil'|'analito', 'id': int, 'precio': float}
        """
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        default_profile_id = self.ensure_default_profile()

        # Calculate total
        total = sum(item.get('precio', 0) for item in items)

        # 1. Create Header
        cursor.execute("""
            INSERT INTO OrdenesTrabajo (pacienteId, medicoId, estado, totalPagar, fechaCreacion)
            OUTPUT INSERTED.ID
            VALUES (?, ?, 'Pendiente', ?, GETDATE())
        """, (paciente_id, medico_id, total))
        orden_id = cursor.fetchone()[0]

        # 2. Process Items
        for item in items:
            if item['type'] == 'perfil':
                # Insert into OrdenPerfiles
                cursor.execute("""
                    INSERT INTO OrdenPerfiles (ordenTrabajoId, perfilExamenId, precioCobrado)
                    VALUES (?, ?, ?)
                """, (orden_id, item['id'], item.get('precio', 0)))

                # Expand Analytes
                perfil_analitos = self.get_perfil_analitos(item['id']) # returns tuples/rows
                # Need to extract ID from row. Tuple index 0 is ID based on SELECT * FROM Analitos
                for row in perfil_analitos:
                    analito_id = row[0]
                    cursor.execute("""
                        INSERT INTO OrdenResultados (ordenTrabajoId, perfilExamenId, analitoId, estado)
                        VALUES (?, ?, ?, 'Pendiente')
                    """, (orden_id, item['id'], analito_id))

            elif item['type'] == 'analito':
                # Individual Analyte. Link to Default Profile.
                # Assuming we don't insert into OrdenPerfiles for individual items unless we want to track billing there?
                # User schema has `OrdenPerfiles`. If we want to bill, maybe we should add a row there too?
                # For simplicity, we just add the result row linked to default profile.
                cursor.execute("""
                    INSERT INTO OrdenResultados (ordenTrabajoId, perfilExamenId, analitoId, estado)
                    VALUES (?, ?, ?, 'Pendiente')
                """, (orden_id, default_profile_id, item['id']))

        conn.commit()
        return orden_id

    # --- PHASE 2: RESULTADOS ---
    def get_ordenes_pendientes(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        # Join with Pacientes to get name
        query = """
            SELECT o.id, p.nombreCompleto, o.fechaCreacion, o.estado
            FROM OrdenesTrabajo o
            JOIN Pacientes p ON o.pacienteId = p.id
            WHERE o.estado IN ('Pendiente', 'Ingresado')
            ORDER BY o.fechaCreacion DESC
        """
        cursor.execute(query)
        return cursor.fetchall()

    def get_resultados_orden(self, orden_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        # Return fields needed for UI: id, analitoName, valorResultado, estado, ranges info needed?
        # Actually we need patient info to calculate ranges.
        # But this method just gets the rows. The View will calculate ranges row by row?
        # Better: Join Analitos to get name.
        query = """
            SELECT r.id, r.analitoId, a.nombre, r.valorResultado, r.estado, a.unidad, a.tipoDato
            FROM OrdenResultados r
            JOIN Analitos a ON r.analitoId = a.id
            WHERE r.ordenTrabajoId = ?
        """
        cursor.execute(query, (orden_id,))
        return cursor.fetchall()

    def get_orden_header(self, orden_id):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM OrdenesTrabajo WHERE id = ?", (orden_id,))
        return cursor.fetchone() # Tuple

    def get_paciente(self, paciente_id):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Pacientes WHERE id = ?", (paciente_id,))
        return cursor.fetchone()

    def update_resultado(self, resultado_id, valor, estado='Ingresado'):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE OrdenResultados SET valorResultado = ?, estado = ?, fechaRegistro = GETDATE()
            WHERE id = ?
        """, (valor, estado, resultado_id))
        conn.commit()

    def get_rango_referencia_string(self, analito_id, p_genero, p_edad, p_unidad):
        """
        Calculates the specific reference range string for a patient.
        """
        conn = self.get_connection()
        if not conn: return ""
        cursor = conn.cursor()

        # 1. Normalize Patient Age to Days
        p_days = self._to_days(p_edad, p_unidad)

        # 2. Get all ranges for analytes
        cursor.execute("SELECT * FROM RangosReferencia WHERE analitoId = ?", (analito_id,))
        rows = cursor.fetchall()

        matched_range = None

        for row in rows:
            # row structure based on SELECT *:
            # id, analitoId, genero, edadMin, edadMax, valorMin, valorMax, refVisual, unidadEdad, ...
            # Let's rely on column names or strict index.
            # Index: 2=genero, 3=min, 4=max, 5=valMin, 6=valMax, 8=unidadEdad

            r_genero = row[2]
            r_min = row[3]
            r_max = row[4]
            r_unidad = row[8]

            # Gender Check
            if r_genero != 'Ambos' and r_genero != p_genero:
                continue

            # Age Check
            r_min_days = self._to_days(r_min, r_unidad)
            r_max_days = self._to_days(r_max, r_unidad)

            if r_min_days <= p_days <= r_max_days:
                matched_range = row
                break # Found match (assuming first match wins or non-overlapping)

        if matched_range:
            # Format: "min - max" or visual
            val_min = matched_range[5]
            val_max = matched_range[6]
            visual = matched_range[7]

            if visual:
                return visual
            elif val_min is not None and val_max is not None:
                return f"{val_min} - {val_max}"
            else:
                return ""

        return ""

    def _to_days(self, value, unit):
        if not value: return 0
        unit = unit.lower()
        if 'año' in unit:
            return value * 365
        elif 'mes' in unit:
            return value * 30
        else: # dias
            return value

# Global database instance
db = DatabaseManager()
