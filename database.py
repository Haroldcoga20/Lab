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
        try:
            # Si no existe, conectamos
            if not hasattr(self, 'connection') or self.connection is None:
                self.connection = pyodbc.connect(self.connection_string)
            
            # Probamos si está viva
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
            except Exception:
                # Si falló, reconectamos a la fuerza
                self.connection = pyodbc.connect(self.connection_string)
            
            return self.connection
        except Exception as e:
            print(f"Error connecting to DB: {e}")
            return None

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

        # New Fields Phase 6.5
        subtitulo = self.sanitize_input(data.get('subtituloReporte'))
        valor_defecto = self.sanitize_input(data.get('valorPorDefecto'))

        # New Field Phase 8
        abreviatura = self.sanitize_input(data.get('abreviatura'))

        if data.get('id'):
            query = """
                UPDATE Analitos SET
                nombre=?, unidad=?, categoria=?, metodo=?, tipoMuestra=?, tipoDato=?,
                valorRefMin=?, valorRefMax=?, referenciaVisual=?, esCalculado=?, formula=?,
                subtituloReporte=?, valorPorDefecto=?, abreviatura=?
                WHERE id=?
            """
            cursor.execute(query, (nombre, unidad, categoria, metodo, tipoMuestra, tipoDato,
                                   val_min, val_max, visual, esCalculado, formula,
                                   subtitulo, valor_defecto, abreviatura, data['id']))
        else:
            query = """
                INSERT INTO Analitos (
                    nombre, unidad, categoria, metodo, tipoMuestra, tipoDato,
                    valorRefMin, valorRefMax, referenciaVisual, esCalculado, formula,
                    subtituloReporte, valorPorDefecto, abreviatura
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (nombre, unidad, categoria, metodo, tipoMuestra, tipoDato,
                                   val_min, val_max, visual, esCalculado, formula,
                                   subtitulo, valor_defecto, abreviatura))
        conn.commit()

    def delete_analito(self, analito_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Analitos WHERE id = ?", (analito_id,))
        conn.commit()

    # --- CRUD OPCIONES ANALITO ---
    def get_opciones_analito(self, analito_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT id, analitoId, valorOpcion, esPredeterminado FROM OpcionesAnalito WHERE analitoId = ? ORDER BY id", (analito_id,))
        return cursor.fetchall()

    def add_opcion_analito(self, analito_id, valor, es_predeterminado):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        if es_predeterminado:
            cursor.execute("UPDATE OpcionesAnalito SET esPredeterminado = 0 WHERE analitoId = ?", (analito_id,))

        cursor.execute("INSERT INTO OpcionesAnalito (analitoId, valorOpcion, esPredeterminado) VALUES (?, ?, ?)",
                       (analito_id, valor, 1 if es_predeterminado else 0))
        conn.commit()

    def delete_opcion_analito(self, opcion_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM OpcionesAnalito WHERE id = ?", (opcion_id,))
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
            INSERT INTO RangosReferencia (analitoId, genero, edadMin, edadMax, unidadEdad, valorMin, valorMax, panicoMin, panicoMax)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['analitoId'],
            data['genero'],
            int(data['edadMin']),
            int(data['edadMax']),
            data['unidadEdad'],
            float(data['valorMin']) if data.get('valorMin') else None,
            float(data['valorMax']) if data.get('valorMax') else None,
            float(data['panicoMin']) if data.get('panicoMin') else None,
            float(data['panicoMax']) if data.get('panicoMax') else None
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

    def get_perfil_hijos(self, perfil_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*
            FROM PerfilesExamen p
            JOIN DetallePerfilComposicion dpc ON p.id = dpc.perfilHijoId
            WHERE dpc.perfilPadreId = ?
            ORDER BY dpc.orden ASC
        """, perfil_id)
        return cursor.fetchall()

    def upsert_perfil(self, data, analito_ids, sub_perfil_ids=[]):
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
            # Limpiar relaciones anteriores
            cursor.execute("DELETE FROM DetallePerfilAnalito WHERE perfilExamenId=?", perfil_id)
            cursor.execute("DELETE FROM DetallePerfilComposicion WHERE perfilPadreId=?", perfil_id)
        else:
            cursor.execute("""
                INSERT INTO PerfilesExamen (nombre, categoria, precioEstandar)
                OUTPUT INSERTED.ID
                VALUES (?, ?, ?)
            """, (data['nombre'], data['categoria'], precio))
            perfil_id = cursor.fetchone()[0]

        # Insertar Analitos Directos
        for idx, aid in enumerate(analito_ids):
            cursor.execute("""
                INSERT INTO DetallePerfilAnalito (perfilExamenId, analitoId, orden)
                VALUES (?, ?, ?)
            """, (perfil_id, aid, idx))

        # Insertar Sub-Perfiles
        for idx, sub_pid in enumerate(sub_perfil_ids):
            cursor.execute("""
                INSERT INTO DetallePerfilComposicion (perfilPadreId, perfilHijoId, orden)
                VALUES (?, ?, ?)
            """, (perfil_id, sub_pid, idx))

        conn.commit()

    def delete_perfil(self, perfil_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PerfilesExamen WHERE id = ?", (perfil_id,))
        conn.commit()

    def get_analitos_by_perfil_recursivo(self, perfil_id):
        """
        Devuelve una lista de tuplas (analito_id, perfil_origen_id)
        Traversa recursivamente los sub-perfiles.
        """
        results = []
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()

        # 1. Analitos directos de este perfil
        cursor.execute("""
            SELECT analitoId
            FROM DetallePerfilAnalito
            WHERE perfilExamenId = ?
            ORDER BY orden ASC
        """, perfil_id)
        direct_analitos = cursor.fetchall()
        for row in direct_analitos:
            results.append((row[0], perfil_id))

        # 2. Analitos de sub-perfiles
        cursor.execute("""
            SELECT perfilHijoId
            FROM DetallePerfilComposicion
            WHERE perfilPadreId = ?
            ORDER BY orden ASC
        """, perfil_id)
        hijos = cursor.fetchall()

        for hijo in hijos:
            hijo_id = hijo[0]
            # Recursion: los analitos del hijo pertenecen al hijo (o sus propios hijos)
            sub_results = self.get_analitos_by_perfil_recursivo(hijo_id)
            results.extend(sub_results)

        return results

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

    # --- PHASE 7: DUPLICADOS & HISTORIAL ---
    def check_paciente_duplicates(self, dni, nombre):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()

        if dni:
            cursor.execute("SELECT * FROM Pacientes WHERE dni = ?", (dni,))
            by_dni = cursor.fetchall()
            if by_dni: return by_dni

        term = f"%{nombre}%"
        cursor.execute("SELECT * FROM Pacientes WHERE nombreCompleto LIKE ?", (term,))
        return cursor.fetchall()

    def get_historial_fechas(self, paciente_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, fechaCreacion, estado, totalPagar
            FROM OrdenesTrabajo
            WHERE pacienteId = ?
            ORDER BY fechaCreacion DESC
        """, (paciente_id,))
        return cursor.fetchall()

    # --- PHASE 6: MEDICOS ---
    def get_all_medicos(self):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Medicos ORDER BY nombre")
        return cursor.fetchall()

    def upsert_medico(self, data):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        nombre = data.get('nombre')
        especialidad = self.sanitize_input(data.get('especialidad'))
        telefono = self.sanitize_input(data.get('telefono'))
        tiene_convenio = 1 if data.get('tieneConvenio') else 0

        if data.get('id'):
            cursor.execute("""
                UPDATE Medicos SET nombre=?, especialidad=?, telefono=?, tieneConvenio=?
                WHERE id=?
            """, (nombre, especialidad, telefono, tiene_convenio, data['id']))
        else:
            cursor.execute("""
                INSERT INTO Medicos (nombre, especialidad, telefono, tieneConvenio)
                VALUES (?, ?, ?, ?)
            """, (nombre, especialidad, telefono, tiene_convenio))
        conn.commit()

    def delete_medico(self, medico_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Medicos WHERE id = ?", (medico_id,))
        conn.commit()

    # --- TARIFAS CONVENIO ---
    def get_tarifa_especial(self, medico_id, perfil_id):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()
        cursor.execute("""
            SELECT precioEspecial FROM TarifasConvenio
            WHERE medicoId = ? AND perfilExamenId = ?
        """, (medico_id, perfil_id))
        row = cursor.fetchone()
        return float(row[0]) if row else None

    def upsert_tarifa_convenio(self, medico_id, perfil_id, precio):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        # Check if exists
        cursor.execute("SELECT id FROM TarifasConvenio WHERE medicoId=? AND perfilExamenId=?", (medico_id, perfil_id))
        row = cursor.fetchone()

        if row:
            cursor.execute("UPDATE TarifasConvenio SET precioEspecial=? WHERE id=?", (precio, row[0]))
        else:
            cursor.execute("INSERT INTO TarifasConvenio (medicoId, perfilExamenId, precioEspecial) VALUES (?, ?, ?)",
                           (medico_id, perfil_id, precio))
        conn.commit()

    def get_tarifas_medico(self, medico_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        query = """
            SELECT t.id, p.nombre, t.precioEspecial
            FROM TarifasConvenio t
            JOIN PerfilesExamen p ON t.perfilExamenId = p.id
            WHERE t.medicoId = ?
            ORDER BY p.nombre
        """
        cursor.execute(query, (medico_id,))
        return cursor.fetchall()

    def delete_tarifa_convenio(self, tarifa_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM TarifasConvenio WHERE id = ?", (tarifa_id,))
        conn.commit()


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

    def create_orden_trabajo(self, paciente_id, medico_id, items, total_pagar=0.0):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        default_profile_id = self.ensure_default_profile()

        # Insertar Orden
        cursor.execute("""
            INSERT INTO OrdenesTrabajo (pacienteId, medicoId, estado, totalPagar, fechaCreacion)
            OUTPUT INSERTED.ID
            VALUES (?, ?, 'Pendiente', ?, GETDATE())
        """, (paciente_id, medico_id, total_pagar))
        orden_id = cursor.fetchone()[0]

        # Insertar Items (Perfiles facturados)
        for item in items:
            if item['type'] == 'perfil':
                # Solo guardamos el perfil Padre en OrdenPerfiles para facturación
                cursor.execute("""
                    INSERT INTO OrdenPerfiles (ordenTrabajoId, perfilExamenId, precioCobrado)
                    VALUES (?, ?, ?)
                """, (orden_id, item['id'], item.get('precio', 0)))

                # RECURSIVIDAD: Obtener todos los analitos (hijos, nietos...) con su padre inmediato
                analitos_data = self.get_analitos_by_perfil_recursivo(item['id'])

                for aid, pid in analitos_data:
                    cursor.execute("""
                        INSERT INTO OrdenResultados (ordenTrabajoId, perfilExamenId, analitoId, estado)
                        VALUES (?, ?, ?, 'Pendiente')
                    """, (orden_id, pid, aid))

            elif item['type'] == 'analito':
                cursor.execute("""
                    INSERT INTO OrdenResultados (ordenTrabajoId, perfilExamenId, analitoId, estado)
                    VALUES (?, ?, ?, 'Pendiente')
                """, (orden_id, default_profile_id, item['id']))

        conn.commit()
        return orden_id

    # --- PHASE 6: FILTROS ORDENES ---
    def get_ordenes_filtradas(self, search_term=None, medico_id=None, estado=None):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()

        query = """
            SELECT o.id, p.nombreCompleto, o.fechaCreacion, o.estado, m.nombre as nombreMedico, p.dni
            FROM OrdenesTrabajo o
            JOIN Pacientes p ON o.pacienteId = p.id
            LEFT JOIN Medicos m ON o.medicoId = m.id
            WHERE 1=1
        """
        params = []

        if search_term:
            query += " AND (p.nombreCompleto LIKE ? OR p.dni LIKE ?)"
            term = f"%{search_term}%"
            params.extend([term, term])

        if medico_id and str(medico_id).isdigit():
            query += " AND o.medicoId = ?"
            params.append(medico_id)

        if estado and estado != "Todos":
            query += " AND o.estado = ?"
            params.append(estado)

        query += " ORDER BY o.fechaCreacion DESC"

        cursor.execute(query, params)
        return cursor.fetchall()

    def get_ordenes_pendientes_filtradas(self, search_term=None, medico_id=None):
        return self.get_ordenes_filtradas(search_term, medico_id, estado=None)

    def delete_orden(self, orden_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM OrdenesTrabajo WHERE id = ?", (orden_id,))
        conn.commit()

    def validate_orden(self, orden_id, user):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        # Validar Resultados
        cursor.execute("""
            UPDATE OrdenResultados
            SET estado = 'Validado', validadoPor = ?
            WHERE ordenTrabajoId = ?
        """, (user, orden_id))

        # Update Orden header if needed (optional)
        # cursor.execute("UPDATE OrdenesTrabajo SET estado = 'Validado' WHERE id = ?", (orden_id,))

        conn.commit()

    def unlock_orden(self, orden_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE OrdenResultados
            SET estado = 'Ingresado', validadoPor = NULL
            WHERE ordenTrabajoId = ?
        """, (orden_id,))

        conn.commit()


    def get_resultados_grouped(self, orden_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()

        default_profile_id = self.ensure_default_profile()

        # Added a.abreviatura, a.formula, a.esCalculado, r.validadoPor
        query = """
            SELECT
                r.id, r.analitoId, a.nombre, r.valorResultado, r.estado, a.unidad, a.tipoDato, a.categoria,
                p.id as perfilId, p.nombre as perfilNombre, a.metodo,
                a.subtituloReporte, a.valorPorDefecto,
                a.abreviatura, a.formula, a.esCalculado, r.validadoPor
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
            rid, aid, aname, val, est, unit, dtype, cat, pid, pname, metodo, subtitulo, def_val, abbr, formula, es_calc, val_por = row

            opciones_list = []
            if dtype == 'Opciones':
                opts = self.get_opciones_analito(aid)
                for o in opts:
                    opciones_list.append({'text': o[2], 'default': bool(o[3])})

            item_data = {
                'id': rid, 'analitoId': aid, 'nombre': aname, 'valor': val,
                'estado': est, 'unidad': unit, 'tipoDato': dtype, 'metodo': metodo,
                'categoria': cat, 'perfilNombre': pname,
                'subtitulo': subtitulo, 'valorPorDefecto': def_val,
                'opciones': opciones_list,
                'abreviatura': abbr, 'formula': formula, 'esCalculado': bool(es_calc),
                'validadoPor': val_por
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

        orden_id = None
        for u in updates:
            if not orden_id:
                cursor.execute("SELECT ordenTrabajoId FROM OrdenResultados WHERE id = ?", (u['id'],))
                res = cursor.fetchone()
                if res: orden_id = res[0]

            cursor.execute("""
                UPDATE OrdenResultados SET valorResultado = ?, estado = 'Ingresado', fechaRegistro = GETDATE()
                WHERE id = ? AND estado != 'Validado'
            """, (u['valor'], u['id']))

        conn.commit()

        if orden_id:
            self._check_and_update_orden_status(orden_id)

    def _check_and_update_orden_status(self, orden_id):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM OrdenResultados WHERE ordenTrabajoId = ?", (orden_id,))
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM OrdenResultados WHERE ordenTrabajoId = ? AND valorResultado IS NOT NULL AND valorResultado <> ''", (orden_id,))
        filled = cursor.fetchone()[0]

        if total > 0 and total == filled:
            cursor.execute("""
                UPDATE OrdenesTrabajo SET estado = 'Completado', fechaCompletado = GETDATE()
                WHERE id = ?
            """, (orden_id,))
        else:
            cursor.execute("""
                UPDATE OrdenesTrabajo SET estado = 'Pendiente', fechaCompletado = NULL
                WHERE id = ?
            """, (orden_id,))

        conn.commit()

    # REEMPLAZA TU FUNCIÓN get_smart_reference ACTUAL CON ESTA:
    def get_smart_reference(self, analito_id, genero_paciente, edad_paciente, unidad_edad_paciente):
        conn = self.get_connection()
        if not conn: return ""
        try:
            cursor = conn.cursor()
            
            # 1. HACEMOS LA CONSULTA DIRECTA AQUÍ (Pidiendo explícitamente las 6 columnas)
            # Nota: Usamos ISNULL(col, 0) o manejo de NULLs si fuera necesario, pero aquí Python lo maneja.
            query = """
                SELECT valorMin, valorMax, panicoMin, panicoMax, referenciaVisualEspecifica, textoInterpretacion
                FROM RangosReferencia
                WHERE analitoId = ? 
                AND (genero = ? OR genero = 'Ambos' OR genero = 'Indistinto')
                AND unidadEdad = ?
                AND ? BETWEEN edadMin AND edadMax
            """
            # Ejecutamos buscando al paciente específico
            cursor.execute(query, (analito_id, genero_paciente, unidad_edad_paciente, edad_paciente))
            row = cursor.fetchone()
            
            # 2. SI ENCONTRAMOS RANGO ESPECÍFICO
            if row:
                # Ahora sí, row tiene 6 elementos porque los pedimos arriba en el SELECT
                r_min, r_max, r_pmin, r_pmax, r_visual_esp, r_interp = row
                
                # Lógica de Prioridades para mostrar el texto
                
                # A. Si tiene Texto Largo (Ej: Tabla de semanas), gana esto.
                if r_visual_esp and str(r_visual_esp).strip():
                    return str(r_visual_esp)
                
                # B. Si tiene Interpretación Corta (Ej: "Negativo" o "R.N."), lo mostramos.
                if r_interp and str(r_interp).strip():
                    # Si además tiene números, los ponemos juntos: "R.N.: 10 - 20"
                    if r_min is not None and r_max is not None:
                        return f"{r_interp}: {r_min} - {r_max}"
                    return str(r_interp)

                # C. Si solo son números, mostramos el rango numérico
                if r_min is not None and r_max is not None:
                    return f"{r_min} - {r_max}"
            
            # 3. SI NO HAY RANGO ESPECÍFICO (Buscamos el genérico del Analito)
            cursor.execute("SELECT referenciaVisual, valorRefMin, valorRefMax FROM Analitos WHERE id = ?", (analito_id,))
            row_gen = cursor.fetchone()
            if row_gen:
                ref_vis, v_min, v_max = row_gen
                if ref_vis: return str(ref_vis)
                if v_min is not None and v_max is not None: return f"{v_min} - {v_max}"
            
            return "" # Nada encontrado

        except Exception as e:
            print(f"Error getting smart reference: {e}")
            return ""
 
    def get_patient_range_values(self, analito_id, p_genero, p_edad, p_unidad):
        """
        Returns (min, max, panicoMin, panicoMax) for validation.
        """
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()

        p_days = self._to_days(p_edad, p_unidad)
        cursor.execute("SELECT * FROM RangosReferencia WHERE analitoId = ?", (analito_id,))
        rows = cursor.fetchall()

        for row in rows:
            # 2=genero, 3=min, 4=max
            r_genero = row[2]
            r_min = row[3]
            r_max = row[4]
            r_unidad = row[8]

            if r_genero != 'Ambos' and r_genero != p_genero: continue

            r_min_days = self._to_days(r_min, r_unidad)
            r_max_days = self._to_days(r_max, r_unidad)

            if r_min_days <= p_days <= r_max_days:
                # Found match
                # 5=valMin, 6=valMax, 10=panicoMin, 11=panicoMax
                return (row[5], row[6], row[10], row[11])

        return None

    def _build_smart_ref_string(self, analito_id, p_genero, p_edad, p_unidad):
        # Re-implementation of previous get_smart_reference but fully self-contained
        conn = self.get_connection()
        if not conn: return ""
        cursor = conn.cursor()

        p_days = self._to_days(p_edad, p_unidad)

        cursor.execute("SELECT * FROM RangosReferencia WHERE analitoId = ?", (analito_id,))
        rows = cursor.fetchall()

        for row in rows:
            r_genero = row[2]
            r_min = row[3]
            r_max = row[4]
            r_val_min = row[5]
            r_val_max = row[6]
            r_visual = row[7]
            r_unidad = row[8]
            r_interp = row[9]

            if r_genero != 'Ambos' and r_genero != p_genero: continue

            r_min_days = self._to_days(r_min, r_unidad)
            r_max_days = self._to_days(r_max, r_unidad)

            if r_min_days <= p_days <= r_max_days:
                prefix = ""
                if r_genero == 'Masculino': prefix = "H: "
                elif r_genero == 'Femenino': prefix = "M: "
                if r_interp: prefix += f"{r_interp}: "

                content = ""
                if r_visual: content = r_visual
                elif r_val_min is not None and r_val_max is not None: content = f"{r_val_min} - {r_val_max}"

                if content: return prefix + content
        return ""

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
