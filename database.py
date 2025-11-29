import pyodbc

class DatabaseManager:
    def __init__(self):
        self.server = r'LAPTOP-3COEKCGP\SQLEXPRESS'
        self.database = 'LabDivinoNinoDB'
        self.conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'Trusted_Connection=yes;'
        )

    def get_connection(self):
        try:
            return pyodbc.connect(self.conn_str, timeout=5)
        except Exception as e:
            print(f"❌ Error BD: {e}")
            return None

    # --- CONSULTAS GENERALES ---
    def obtener_estadisticas(self):
        conn = self.get_connection()
        if not conn: return (0, 0, 0, 0.00, 0)
        try:
            cursor = conn.cursor()
            pacientes = cursor.execute("SELECT COUNT(*) FROM Pacientes").fetchone()[0]
            medicos = cursor.execute("SELECT COUNT(*) FROM Medicos").fetchone()[0]
            ordenes_hoy = cursor.execute("SELECT COUNT(*) FROM OrdenesTrabajo WHERE CAST(fechaCreacion AS DATE) = CAST(GETDATE() AS DATE)").fetchone()[0]
            ingresos = cursor.execute("SELECT ISNULL(SUM(montoPagado), 0) FROM OrdenesTrabajo WHERE CAST(fechaCreacion AS DATE) = CAST(GETDATE() AS DATE)").fetchone()[0]
            pendientes = cursor.execute("SELECT COUNT(*) FROM OrdenesTrabajo WHERE estado = 'Pendiente'").fetchone()[0]
            return (pacientes, ordenes_hoy, medicos, ingresos, pendientes)
        except: return (0, 0, 0, 0.00, 0)
        finally: conn.close()

    # --- PACIENTES ---
    def buscar_pacientes(self, termino=""):
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            query = "SELECT TOP 50 id, nombreCompleto, edad, unidadEdad, genero, dni, telefono FROM Pacientes"
            if termino:
                query += " WHERE nombreCompleto LIKE ? OR dni LIKE ?"
                cursor.execute(query, (f'%{termino}%', f'%{termino}%'))
            else:
                cursor.execute(query + " ORDER BY fechaCreacion DESC")
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except: return []
        finally: conn.close()

    def agregar_paciente(self, d):
        conn = self.get_connection()
        if not conn: return
        try:
            conn.cursor().execute("INSERT INTO Pacientes (nombreCompleto, edad, unidadEdad, genero, dni, telefono) VALUES (?,?,?,?,?,?)",
                           (d['nombre'], d['edad'], d['unidad'], d['genero'], d['dni'], d['telefono'])).commit()
        finally: conn.close()

    # NUEVO: Función para editar paciente
    def editar_paciente(self, id_p, d):
        conn = self.get_connection()
        if not conn: return
        try:
            conn.cursor().execute("""
                UPDATE Pacientes 
                SET nombreCompleto=?, edad=?, unidadEdad=?, genero=?, dni=?, telefono=?
                WHERE id=?
            """, (d['nombre'], d['edad'], d['unidad'], d['genero'], d['dni'], d['telefono'], id_p)).commit()
        finally: conn.close()
    
    def eliminar_paciente(self, id_p):
        conn = self.get_connection()
        if not conn: return
        try: conn.cursor().execute("DELETE FROM Pacientes WHERE id = ?", (id_p,)).commit()
        finally: conn.close()

    # --- MÉDICOS ---
    def buscar_medicos(self, termino=""):
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            query = "SELECT id, nombre, especialidad, telefono, tieneConvenio FROM Medicos"
            if termino:
                query += " WHERE nombre LIKE ? OR especialidad LIKE ?"
                cursor.execute(query, (f'%{termino}%', f'%{termino}%'))
            else:
                cursor.execute(query + " ORDER BY nombre ASC")
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        except: return []
        finally: conn.close()

    def agregar_medico(self, d):
        conn = self.get_connection()
        if not conn: return
        try:
            convenio_bit = 1 if d['convenio'] else 0
            conn.cursor().execute("INSERT INTO Medicos (nombre, especialidad, telefono, tieneConvenio) VALUES (?,?,?,?)",
                           (d['nombre'], d['especialidad'], d['telefono'], convenio_bit)).commit()
        finally: conn.close()

    def eliminar_medico(self, id_m):
        conn = self.get_connection()
        if not conn: return
        try: conn.cursor().execute("DELETE FROM Medicos WHERE id = ?", (id_m,)).commit()
        finally: conn.close()

    def obtener_medicos(self):
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM Medicos ORDER BY nombre ASC")
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally: conn.close()

    # --- CONFIGURACIÓN (ANALITOS) ---
    def obtener_analitos(self):
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Analitos ORDER BY categoria, nombre ASC")
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally: conn.close()

    def agregar_analito(self, d):
        conn = self.get_connection()
        if not conn: return
        try:
            conn.cursor().execute("""
                INSERT INTO Analitos (nombre, unidad, categoria, subtituloReporte, tipoDato, metodo, valorRefMin, valorRefMax, referenciaVisual)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                (d['nombre'], d.get('unidad'), d['categoria'], d['subtitulo'], d['tipoDato'], d['metodo'], d.get('min'), d.get('max'), d['refVisual'])).commit()
        finally: conn.close()

    def editar_analito(self, id_analito, d):
        conn = self.get_connection()
        if not conn: return
        try:
            conn.cursor().execute("""
                UPDATE Analitos 
                SET nombre=?, unidad=?, categoria=?, subtituloReporte=?, tipoDato=?, metodo=?, valorRefMin=?, valorRefMax=?, referenciaVisual=?
                WHERE id=?
            """, (d['nombre'], d.get('unidad'), d['categoria'], d['subtitulo'], d['tipoDato'], d['metodo'], d.get('min'), d.get('max'), d['refVisual'], id_analito)).commit()
        finally: conn.close()

    # --- GESTIÓN DE PERFILES (CON ORDEN) ---
    def obtener_perfiles(self):
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, precioEstandar, categoria FROM PerfilesExamen ORDER BY nombre ASC")
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally: conn.close()

    def obtener_analitos_perfil(self, perfil_id):
        conn = self.get_connection()
        if not conn: return []
        try:
            return [r[0] for r in conn.cursor().execute("SELECT analitoId FROM DetallePerfilAnalito WHERE perfilExamenId = ? ORDER BY orden ASC", (perfil_id,)).fetchall()]
        finally: conn.close()

    def agregar_perfil(self, nombre, categoria, precio, analitos_ids):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            count = cursor.execute("SELECT COUNT(*) FROM PerfilesExamen WHERE nombre = ?", (nombre,)).fetchone()[0]
            if count > 0: return False

            cursor.execute("INSERT INTO PerfilesExamen (nombre, categoria, precioEstandar) OUTPUT INSERTED.id VALUES (?, ?, ?)", 
                           (nombre, categoria, precio))
            perfil_id = cursor.fetchone()[0]
            
            for i, aid in enumerate(analitos_ids):
                cursor.execute("INSERT INTO DetallePerfilAnalito (perfilExamenId, analitoId, orden) VALUES (?, ?, ?)", 
                               (perfil_id, aid, i+1))
            
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally: conn.close()

    def editar_perfil(self, perfil_id, nombre, categoria, precio, analitos_ids):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE PerfilesExamen SET nombre=?, categoria=?, precioEstandar=? WHERE id=?", 
                           (nombre, categoria, precio, perfil_id))
            cursor.execute("DELETE FROM DetallePerfilAnalito WHERE perfilExamenId=?", (perfil_id,))
            for i, aid in enumerate(analitos_ids):
                cursor.execute("INSERT INTO DetallePerfilAnalito (perfilExamenId, analitoId, orden) VALUES (?, ?, ?)", 
                               (perfil_id, aid, i+1))
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally: conn.close()

    def eliminar_perfil(self, perfil_id):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM DetallePerfilAnalito WHERE perfilExamenId = ?", (perfil_id,))
            cursor.execute("DELETE FROM PerfilesExamen WHERE id = ?", (perfil_id,))
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally: conn.close()

    # --- LÓGICA DE ÓRDENES ---
    def buscar_ordenes(self, termino=""):
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT o.id, p.nombreCompleto as Paciente, m.nombre as Medico, 
                       o.fechaCreacion, o.estado, o.totalPagar
                FROM OrdenesTrabajo o
                JOIN Pacientes p ON o.pacienteId = p.id
                LEFT JOIN Medicos m ON o.medicoId = m.id
            """
            if termino:
                query += " WHERE p.nombreCompleto LIKE ? OR CAST(o.id AS NVARCHAR) LIKE ?"
                cursor.execute(query + " ORDER BY o.fechaCreacion DESC", (f'%{termino}%', f'%{termino}%'))
            else:
                cursor.execute(query + " ORDER BY o.fechaCreacion DESC OFFSET 0 ROWS FETCH NEXT 50 ROWS ONLY")
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally: conn.close()

    def _obtener_ids_analitos_recursivo(self, cursor, perfil_id):
        analitos_ids = []
        cursor.execute("SELECT analitoId FROM DetallePerfilAnalito WHERE perfilExamenId = ? ORDER BY orden ASC", (perfil_id,))
        for row in cursor.fetchall(): analitos_ids.append(row[0])
        
        cursor.execute("SELECT perfilHijoId FROM DetallePerfilComposicion WHERE perfilPadreId = ? ORDER BY orden ASC", (perfil_id,))
        for hijo in cursor.fetchall(): analitos_ids.extend(self._obtener_ids_analitos_recursivo(cursor, hijo[0]))
        return list(dict.fromkeys(analitos_ids))

    def crear_orden(self, paciente_id, medico_id, perfiles_ids):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            total = 0.0
            detalles_precios = [] 
            
            for pid in perfiles_ids:
                precio = 0.0
                if medico_id:
                    cursor.execute("SELECT precioEspecial FROM TarifasConvenio WHERE medicoId = ? AND perfilExamenId = ?", (medico_id, pid))
                    row = cursor.fetchone()
                    precio = float(row[0]) if row else float(conn.cursor().execute("SELECT precioEstandar FROM PerfilesExamen WHERE id = ?", (pid,)).fetchone()[0])
                else:
                    precio = float(conn.cursor().execute("SELECT precioEstandar FROM PerfilesExamen WHERE id = ?", (pid,)).fetchone()[0])
                
                total += precio
                detalles_precios.append((pid, precio))

            cursor.execute("INSERT INTO OrdenesTrabajo (pacienteId, medicoId, estado, totalPagar, montoPagado) OUTPUT INSERTED.id VALUES (?, ?, 'Pendiente', ?, 0)", (paciente_id, medico_id, total))
            orden_id = cursor.fetchone()[0]

            for pid, precio in detalles_precios:
                cursor.execute("INSERT INTO OrdenPerfiles (ordenTrabajoId, perfilExamenId, precioCobrado) VALUES (?, ?, ?)", (orden_id, pid, precio))
                analitos_ids = self._obtener_ids_analitos_recursivo(cursor, pid)
                
                if not analitos_ids:
                    print(f"⚠️ ADVERTENCIA: El perfil {pid} no tiene analitos configurados.")
                
                for aid in analitos_ids:
                    if cursor.execute("SELECT COUNT(*) FROM OrdenResultados WHERE ordenTrabajoId = ? AND analitoId = ?", (orden_id, aid)).fetchone()[0] == 0:
                        cursor.execute("INSERT INTO OrdenResultados (ordenTrabajoId, perfilExamenId, analitoId, valorResultado) VALUES (?, ?, ?, '')", (orden_id, pid, aid)) 
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error creando orden: {e}")
            conn.rollback()
            return False
        finally: conn.close()

    def eliminar_orden(self, orden_id):
        conn = self.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM OrdenResultados WHERE ordenTrabajoId = ?", (orden_id,))
            cursor.execute("DELETE FROM OrdenPerfiles WHERE ordenTrabajoId = ?", (orden_id,))
            cursor.execute("DELETE FROM OrdenesTrabajo WHERE id = ?", (orden_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error eliminando orden: {e}")
            conn.rollback()
            return False
        finally: conn.close()

    def obtener_resultados_orden(self, orden_id):
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    r.analitoId, 
                    a.nombre, 
                    a.tipoDato, 
                    a.unidad, 
                    r.valorResultado, 
                    a.id as AnalitoID,
                    a.referenciaVisual,
                    a.metodo,
                    ISNULL(a.subtituloReporte, a.categoria) as categoria, 
                    p.nombre as Perfil
                FROM OrdenResultados r 
                JOIN Analitos a ON r.analitoId = a.id
                JOIN PerfilesExamen p ON r.perfilExamenId = p.id
                LEFT JOIN DetallePerfilAnalito dpa ON r.perfilExamenId = dpa.perfilExamenId AND r.analitoId = dpa.analitoId
                WHERE r.ordenTrabajoId = ? 
                ORDER BY p.nombre, ISNULL(dpa.orden, 9999), a.nombre
            """, (orden_id,))
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
        finally: conn.close()

    def obtener_opciones_analito(self, analito_id):
        conn = self.get_connection()
        if not conn: return []
        try: return [r[0] for r in conn.cursor().execute("SELECT valorOpcion FROM OpcionesAnalito WHERE analitoId = ?", (analito_id,)).fetchall()]
        finally: conn.close()

    def guardar_resultados(self, orden_id, resultados_dict):
        conn = self.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            for aid, valor in resultados_dict.items():
                cursor.execute("UPDATE OrdenResultados SET valorResultado = ? WHERE ordenTrabajoId = ? AND analitoId = ?", (valor, orden_id, aid))
            cursor.execute("UPDATE OrdenesTrabajo SET estado = 'Completado', fechaCompletado = GETDATE() WHERE id = ?", (orden_id,))
            conn.commit()
        finally: conn.close()

db = DatabaseManager()