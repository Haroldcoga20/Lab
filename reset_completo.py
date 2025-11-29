import pyodbc
from database import db
from inicializar_datos import cargar_datos_reales

def reiniciar_sistema():
    print("⚠️  ATENCIÓN: Se borrarán todos los datos de configuración y órdenes.")
    print("    (Pacientes y Médicos se conservarán por seguridad)")
    
    conn = db.get_connection()
    if not conn: return

    try:
        cursor = conn.cursor()
        
        # 1. BORRAR DATOS EN ORDEN (Para no romper relaciones)
        print("🧹 Borrando datos antiguos...")
        tablas = [
            "OrdenResultados",
            "OrdenPerfiles",
            "OrdenesTrabajo",
            "TarifasConvenio",
            "DetallePerfilComposicion",
            "DetallePerfilAnalito",
            "PerfilesExamen",
            "OpcionesAnalito",
            "RangosReferencia",
            "Analitos"
        ]

        for t in tablas:
            cursor.execute(f"DELETE FROM {t}")
            # Reiniciar contadores de ID para que empiecen en 1 otra vez
            try:
                cursor.execute(f"DBCC CHECKIDENT ('{t}', RESEED, 0)")
            except: pass
        
        conn.commit()
        print("✨ Base de datos limpia.")
        
    except Exception as e:
        print(f"❌ Error limpiando: {e}")
        conn.rollback()
        return
    finally:
        conn.close()

    # 2. CARGAR DATOS NUEVOS
    print("\n🔄 Recargando catálogos correctos...")
    cargar_datos_reales()
    print("\n✅ ¡SISTEMA LISTO! Ya puedes crear órdenes.")

if __name__ == "__main__":
    reiniciar_sistema()