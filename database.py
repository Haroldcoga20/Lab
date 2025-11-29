import pyodbc
import threading

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

# Global database instance
db = DatabaseManager()
