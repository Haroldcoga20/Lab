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
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

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
            query = """
                UPDATE Analitos SET
                nombre=?, unidad=?, categoria=?, metodo=?, tipoMuestra=?, tipoDato=?,
                valorRefMin=?, valorRefMax=?, referenciaVisual=?, esCalculado=?, formula=?
                WHERE id=?
            """
            cursor.execute(query, (nombre, unidad, categoria, metodo, tipoMuestra, tipoDato,
                                   val_min, val_max, visual, esCalculado, formula, data['id']))
        else:
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
            SELECT a.*
            FROM Analitos a
            JOIN DetallePerfilAnalito dpa ON a.id = dpa.analitoId
            WHERE dpa.perfilExamenId = ?
            ORDER BY dpa.orden ASC
        """, perfil_id)
        return cursor.fetchall()

    def upsert_perfil(self, data, analito_ids):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        precio = float(data['precioEstandar']) if data.get('precioEstandar') else 0.0
        perfil_id = data.get('id')

        if perfil_id:
            cursor.execute("""
                UPDATE PerfilesExamen SET nombre=?, categoria=?, precioEstandar=?
                WHERE id=?
            """, (data['nombre'], data['categoria'], precio, perfil_id))
            cursor.execute("DELETE FROM DetallePerfilAnalito WHERE perfilExamenId=?", perfil_id)
        else:
            cursor.execute("""
                INSERT INTO PerfilesExamen (nombre, categoria, precioEstandar)
                OUTPUT INSERTED.ID
                VALUES (?, ?, ?)
            """, (data['nombre'], data['categoria'], precio))
            perfil_id = cursor.fetchone()[0]

        for idx, aid in enumerate(analito_ids):
            cursor.execute("""
                INSERT INTO DetallePerfilAnalito (perfilExamenId, analitoId, orden)
                VALUES (?, ?, ?)
            """, (perfil_id, aid, idx))

        conn.commit()

    # --- PHASE 2: PACIENTES ---
    def get_all_pacientes(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Pacientes ORDER BY id DESC")
        return cursor.fetchall()

    def search_pacientes(self, term):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        term = f"%{term}%"
        cursor.execute("SELECT * FROM Pacientes WHERE nombreCompleto LIKE ? OR dni LIKE ? ORDER BY id DESC", (term, term))
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
                INSERT INTO Pacientes (nombreCompleto, edad, unidadEdad, genero, dni, telefono, fechaCreacion)
                VALUES (?, ?, ?, ?, ?, ?, GETDATE())
            """, (nombre, edad, unidad_edad, genero, dni, telefono))
        conn.commit()

    def delete_paciente(self, paciente_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Pacientes WHERE id = ?", (paciente_id,))
        conn.commit()

    # --- PHASE 2: MEDICOS & ORDENES ---
    def get_all_medicos(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Medicos ORDER BY nombre")
        return cursor.fetchall()

    def ensure_default_profile(self):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM PerfilesExamen WHERE nombre = 'Examenes Individuales'")
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            cursor.execute("""
                INSERT INTO PerfilesExamen (nombre, categoria, precioEstandar)
                OUTPUT INSERTED.ID
                VALUES ('Examenes Individuales', 'General', 0)
            """)
            conn.commit()
            return cursor.fetchone()[0]

    def create_orden_trabajo(self, paciente_id, medico_id, items):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        default_profile_id = self.ensure_default_profile()
        total = sum(item.get('precio', 0) for item in items)

        cursor.execute("""
            INSERT INTO OrdenesTrabajo (pacienteId, medicoId, estado, totalPagar, fechaCreacion)
            OUTPUT INSERTED.ID
            VALUES (?, ?, 'Pendiente', ?, GETDATE())
        """, (paciente_id, medico_id, total))
        orden_id = cursor.fetchone()[0]

        for item in items:
            if item['type'] == 'perfil':
                cursor.execute("""
                    INSERT INTO OrdenPerfiles (ordenTrabajoId, perfilExamenId, precioCobrado)
                    VALUES (?, ?, ?)
                """, (orden_id, item['id'], item.get('precio', 0)))

                perfil_analitos = self.get_perfil_analitos(item['id'])
                for row in perfil_analitos:
                    analito_id = row[0]
                    cursor.execute("""
                        INSERT INTO OrdenResultados (ordenTrabajoId, perfilExamenId, analitoId, estado)
                        VALUES (?, ?, ?, 'Pendiente')
                    """, (orden_id, item['id'], analito_id))

            elif item['type'] == 'analito':
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
        query = """
            SELECT o.id, p.nombreCompleto, o.fechaCreacion, o.estado
            FROM OrdenesTrabajo o
            JOIN Pacientes p ON o.pacienteId = p.id
            WHERE o.estado IN ('Pendiente', 'Ingresado')
            ORDER BY o.fechaCreacion DESC
        """
        cursor.execute(query)
        return cursor.fetchall()

    # --- PHASE 3: REPORTES & CONSULTAS ---
    def get_all_ordenes(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        # Updated to LEFT JOIN Medicos and select name
        query = """
            SELECT o.id, p.nombreCompleto, o.fechaCreacion, o.estado, m.nombre as nombreMedico
            FROM OrdenesTrabajo o
            JOIN Pacientes p ON o.pacienteId = p.id
            LEFT JOIN Medicos m ON o.medicoId = m.id
            ORDER BY o.fechaCreacion DESC
        """
        cursor.execute(query)
        return cursor.fetchall()

    def delete_orden(self, orden_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM OrdenesTrabajo WHERE id = ?", (orden_id,))
        conn.commit()

    def get_resultados_grouped(self, orden_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()

        default_profile_id = self.ensure_default_profile()

        query = """
            SELECT
                r.id, r.analitoId, a.nombre, r.valorResultado, r.estado, a.unidad, a.tipoDato, a.categoria,
                p.id as perfilId, p.nombre as perfilNombre, a.metodo
            FROM OrdenResultados r
            JOIN Analitos a ON r.analitoId = a.id
            JOIN PerfilesExamen p ON r.perfilExamenId = p.id
            LEFT JOIN DetallePerfilAnalito dpa ON (dpa.perfilExamenId = r.perfilExamenId AND dpa.analitoId = r.analitoId)
            WHERE r.ordenTrabajoId = ?
            ORDER BY p.nombre, ISNULL(dpa.orden, 9999) ASC, a.categoria, a.nombre
        """
        cursor.execute(query, (orden_id,))
        rows = cursor.fetchall()

        groups = {}

        for row in rows:
            rid, aid, aname, val, est, unit, dtype, cat, pid, pname, metodo = row

            item_data = {
                'id': rid, 'analitoId': aid, 'nombre': aname, 'valor': val,
                'estado': est, 'unidad': unit, 'tipoDato': dtype, 'metodo': metodo,
                'categoria': cat, 'perfilNombre': pname
            }

            if pid == default_profile_id:
                key = ('Categoria', cat.upper())
            else:
                key = ('Perfil', pname.upper())

            if key not in groups:
                groups[key] = []
            groups[key].append(item_data)

        result_list = []
        for (gtype, gtitle), items in groups.items():
            result_list.append({'type': gtype, 'title': gtitle, 'items': items})

        result_list.sort(key=lambda x: (0 if x['type'] == 'Perfil' else 1, x['title']))
        return result_list

    def update_resultado_batch(self, updates):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        # 1. Update values
        orden_id = None
        for u in updates:
            # We need orden_id to check status later. Get it from one update.
            # Efficient way: Get it before update or assuming caller knows?
            # Caller didn't pass it. We can fetch it or just get it from the first ID.
            if not orden_id:
                cursor.execute("SELECT ordenTrabajoId FROM OrdenResultados WHERE id = ?", (u['id'],))
                res = cursor.fetchone()
                if res: orden_id = res[0]

            cursor.execute("""
                UPDATE OrdenResultados SET valorResultado = ?, estado = 'Ingresado', fechaRegistro = GETDATE()
                WHERE id = ?
            """, (u['valor'], u['id']))

        conn.commit()

        # 2. Check Order Completion Status
        if orden_id:
            self._check_and_update_orden_status(orden_id)

    def _check_and_update_orden_status(self, orden_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        # Count Total
        cursor.execute("SELECT COUNT(*) FROM OrdenResultados WHERE ordenTrabajoId = ?", (orden_id,))
        total = cursor.fetchone()[0]

        # Count Filled (Not Null and Not Empty)
        cursor.execute("SELECT COUNT(*) FROM OrdenResultados WHERE ordenTrabajoId = ? AND valorResultado IS NOT NULL AND valorResultado <> ''", (orden_id,))
        filled = cursor.fetchone()[0]

        if total > 0 and total == filled:
            # Complete
            cursor.execute("""
                UPDATE OrdenesTrabajo SET estado = 'Completado', fechaCompletado = GETDATE()
                WHERE id = ?
            """, (orden_id,))
        else:
            # Pendiente (or revert to Pendiente if cleared)
            cursor.execute("""
                UPDATE OrdenesTrabajo SET estado = 'Pendiente', fechaCompletado = NULL
                WHERE id = ?
            """, (orden_id,))

        conn.commit()

    def get_smart_reference(self, analito_id, p_genero, p_edad, p_unidad):
        conn = self.get_connection()
        if not conn: return ""
        cursor = conn.cursor()

        p_days = self._to_days(p_edad, p_unidad)

        cursor.execute("SELECT * FROM RangosReferencia WHERE analitoId = ?", (analito_id,))
        rows = cursor.fetchall()

        match_str = ""

        for row in rows:
            r_genero = row[2]
            r_min = row[3]
            r_max = row[4]
            r_val_min = row[5]
            r_val_max = row[6]
            r_visual = row[7]
            r_unidad = row[8]
            r_interp = row[9]

            if r_genero != 'Ambos' and r_genero != p_genero:
                continue

            r_min_days = self._to_days(r_min, r_unidad)
            r_max_days = self._to_days(r_max, r_unidad)

            if r_min_days <= p_days <= r_max_days:
                prefix = ""
                if r_genero == 'Masculino': prefix = "H: "
                elif r_genero == 'Femenino': prefix = "M: "

                if r_interp:
                    prefix += f"{r_interp}: "

                content = ""
                if r_visual:
                    content = r_visual
                elif r_val_min is not None and r_val_max is not None:
                    content = f"{r_val_min} - {r_val_max}"

                if content:
                    match_str = prefix + content
                    break

        return match_str

    def get_orden_header(self, orden_id):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM OrdenesTrabajo WHERE id = ?", (orden_id,))
        return cursor.fetchone()

    def get_report_header(self, orden_id):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.nombreCompleto, p.edad, p.unidadEdad, p.genero,
                   m.nombre as Medico, o.fechaCreacion
            FROM OrdenesTrabajo o
            JOIN Pacientes p ON o.pacienteId = p.id
            LEFT JOIN Medicos m ON o.medicoId = m.id
            WHERE o.id = ?
        """, (orden_id,))
        return cursor.fetchone()

    def get_paciente(self, paciente_id):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Pacientes WHERE id = ?", (paciente_id,))
        return cursor.fetchone()

    def _to_days(self, value, unit):
        if not value: return 0
        unit = unit.lower()
        if 'año' in unit:
            return value * 365
        elif 'mes' in unit:
            return value * 30
        else:
            return value

db = DatabaseManager()
