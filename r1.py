from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from database import db
import os, platform, subprocess

def generar_pdf_orden(orden_id, incluir_firma=True):
    # --- 1. OBTENER DATOS ---
    resultados_raw = db.obtener_resultados_orden(orden_id)
    if not resultados_raw: return False, "No hay resultados cargados para esta orden"

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nombreCompleto, p.edad, p.unidadEdad, p.genero, 
               m.nombre as Medico, o.fechaCreacion
        FROM OrdenesTrabajo o
        JOIN Pacientes p ON o.pacienteId = p.id
        LEFT JOIN Medicos m ON o.medicoId = m.id
        WHERE o.id = ?
    """, (orden_id,))
    header_data = cursor.fetchone()
    conn.close()

    if not header_data: return False, "Datos de orden no encontrados"
    paciente, edad, unidad, genero, medico, fecha = header_data

    perfiles_map = {}
    orden_perfiles = []
    
    for r in resultados_raw:
        nom = r['Perfil']
        if nom not in perfiles_map:
            perfiles_map[nom] = []
            orden_perfiles.append(nom)
        
        val = str(r['valorResultado']).strip()
        if val or r['nombre'].upper() == "OBSERVACIONES":
            perfiles_map[nom].append(r)

    # --- 2. CONFIGURACIÓN PDF ---
    filename = f"Resultado_Orden_{orden_id}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4
    
    margen_x = 50 
    margen_y_bottom = 2.5 * cm
    ancho_util = w - (margen_x * 2)
    
    color_barra = colors.HexColor("#005b96")
    
    # --- FUNCIONES DE DIBUJO ---
    
    def dibujar_marca_agua():
        """Microscopio centrado en marca de agua (MÁS VISIBLE)"""
        ruta_agua = os.path.join(os.getcwd(), "assets", "microscopio_agua.png")
        if os.path.exists(ruta_agua):
            try:
                c.saveState()
                # CAMBIO: Opacidad aumentada a 0.25 (25%) para que se note más
                c.setFillAlpha(0.35) 
                
                # Tamaño GRANDE (500x500)
                ancho_agua = 500 
                alto_agua = 500
                x_pos = (w - ancho_agua) / 2
                y_pos = (h - alto_agua) / 2
                
                c.drawImage(ruta_agua, x_pos, y_pos, width=ancho_agua, height=alto_agua, mask='auto', preserveAspectRatio=True)
                c.restoreState()
            except: pass

    def dibujar_membrete(y_actual):
        ruta_membrete = os.path.join(os.getcwd(), "assets", "membrete_full.png")
        
        if os.path.exists(ruta_membrete):
            try:
                # MEMBRETE FIJO A 160pts (CONFIRMADO)
                ancho_imagen = w - 20 
                altura_imagen = 160   
                
                # Pegado arriba
                c.drawImage(ruta_membrete, 10, y_actual - altura_imagen + 20, width=ancho_imagen, height=altura_imagen, mask='auto', preserveAspectRatio=True)
                
                return y_actual - altura_imagen - 10
            except Exception as e:
                print(f"Error cargando membrete: {e}")
                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(w/2, y_actual - 30, "LABORATORIO DIVINO NIÑO")
                return y_actual - 50
        else:
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(w/2, y_actual - 30, "LABORATORIO DIVINO NIÑO")
            return y_actual - 50

    def dibujar_datos_paciente(y_actual):
        c.setStrokeColor(colors.grey)
        c.line(margen_x, y_actual, w - margen_x, y_actual)
        y_actual -= 15
        
        c.setFillColor(colors.black)
        
        c.setFont("Courier-Bold", 10)
        c.drawString(margen_x, y_actual, "PACIENTE:")
        c.setFont("Courier", 10)
        c.drawString(margen_x + 70, y_actual, str(paciente).upper())
        
        col2_x = w - margen_x - 200
        c.setFont("Courier-Bold", 10)
        c.drawString(col2_x, y_actual, "FECHA:")
        c.setFont("Courier", 10)
        c.drawString(col2_x + 50, y_actual, str(fecha)[:10])
        
        y_actual -= 15
        
        c.setFont("Courier-Bold", 10)
        c.drawString(margen_x, y_actual, "MÉDICO:")
        c.setFont("Courier", 10)
        c.drawString(margen_x + 70, y_actual, str(medico or "Particular").upper())
        
        c.setFont("Courier-Bold", 10)
        c.drawString(col2_x, y_actual, "EDAD:")
        c.setFont("Courier", 10)
        c.drawString(col2_x + 50, y_actual, f"{edad} {unidad} ({genero})")
        
        y_actual -= 10
        c.line(margen_x, y_actual, w - margen_x, y_actual)
        return y_actual - 10

    def dibujar_barra_titulos(y_actual):
        c.setFillColor(color_barra)
        c.rect(margen_x, y_actual - 12, ancho_util, 14, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Courier-Bold", 9)
        
        c.drawString(margen_x + 5, y_actual - 9, "ANÁLISIS")
        c.drawString(margen_x + (ancho_util * 0.4), y_actual - 9, "RESULTADO")
        c.drawString(margen_x + (ancho_util * 0.65), y_actual - 9, "V. REFERENCIALES")
        c.drawString(margen_x + (ancho_util * 0.88), y_actual - 9, "UNIDADES")
        
        return y_actual - 35 

    def dibujar_firma_pie():
        """Dibuja la firma al final de CADA página"""
        if not incluir_firma: return
        
        # Posición Fija en el Pie de Página
        y_firma = 2.5 * cm 
        x_firma_centro = w - margen_x - 100
        
        ruta_firma = os.path.join(os.getcwd(), "assets", "firma.png")
        
        if os.path.exists(ruta_firma):
            try:
                c.drawImage(ruta_firma, x_firma_centro - 110, y_firma - 30, width=220, height=90, mask='auto', preserveAspectRatio=True)
            except: pass
        
        c.setStrokeColor(colors.black)
        c.setDash(4, 3) 
        c.line(x_firma_centro - 90, y_firma, x_firma_centro + 90, y_firma)
        c.setDash([]) 

        c.setFillColor(colors.black)
        c.setFont("Courier", 9)
        c.drawCentredString(x_firma_centro, y_firma - 12, "LIC. COBEÑAS PALACIOS LUIS A.")
        c.drawCentredString(x_firma_centro, y_firma - 22, "TECNÓLOGO MÉDICO")
        c.drawCentredString(x_firma_centro, y_firma - 32, "C.T.M.P 10911")

    # --- INICIO DE PÁGINA ---
    y_inicio_hoja = h - 30 
    
    # FONDO PRIMERA PÁGINA
    dibujar_marca_agua()
    
    # CABECERA PRIMERA PÁGINA
    y = y_inicio_hoja
    y = dibujar_membrete(y)
    y = dibujar_datos_paciente(y)
    y = dibujar_barra_titulos(y)

    # --- CUERPO ---
    for nombre_perfil in orden_perfiles:
        items = perfiles_map[nombre_perfil]
        if not items: continue

        espacio = 40 + (len(items) * 15)
        limite_inferior = margen_y_bottom + 100 
        
        if y - espacio < limite_inferior:
            # FIRMA EN LA PÁGINA ACTUAL ANTES DE SALTAR
            dibujar_firma_pie()
            c.showPage()
            
            # NUEVA HOJA
            dibujar_marca_agua() # Marca de agua en nueva hoja
            y = y_inicio_hoja
            y = dibujar_membrete(y)
            y = dibujar_datos_paciente(y)
            y = dibujar_barra_titulos(y)

        c.setFillColor(colors.black)
        c.setFont("Courier-Bold", 11)
        c.drawString(margen_x, y, f"Examen :   {nombre_perfil}")
        y -= 15
        
        metodo_global = items[0]['metodo']
        if metodo_global and metodo_global != "Automatizado":
             c.setFont("Courier", 10)
             c.drawString(margen_x, y, f"Método :   {metodo_global}")
             y -= 15

        y -= 5 

        # ANALITOS
        subgrupos = {}
        orden_sub = []
        for item in items:
            sub = item['categoria'] or "General"
            if sub not in subgrupos:
                subgrupos[sub] = []
                orden_sub.append(sub)
            subgrupos[sub].append(item)

        for sub in orden_sub:
            lista = subgrupos[sub]
            
            es_obs = "OBSERVACIONES" in sub.upper()
            if sub != "General" and not es_obs:
                y -= 5
                c.setFont("Courier-Bold", 10)
                c.drawString(margen_x, y, f"{sub}:")
                y -= 12

            for item in lista:
                nombre = item['nombre']
                val = str(item['valorResultado'])
                ref = str(item['referenciaVisual'] or "")
                uni = str(item['unidad'] or "")

                if nombre.upper() == "OBSERVACIONES":
                    y -= 10
                    c.setFont("Courier-Bold", 10)
                    c.drawString(margen_x, y, "OBSERVACIONES:")
                    c.setFont("Courier", 10)
                    if val: c.drawString(margen_x + 110, y, val)
                    y -= 15
                    continue

                c.setFont("Courier", 10)
                c.drawString(margen_x, y, nombre)
                
                if "POSITIVO" in val.upper() or "REACTIVO" in val.upper():
                    c.setFont("Courier-Bold", 10)
                
                c.drawString(margen_x + (ancho_util * 0.4), y, val) 
                c.setFont("Courier", 10)
                c.drawString(margen_x + (ancho_util * 0.65), y, ref)
                c.drawString(margen_x + (ancho_util * 0.88), y, uni)
                
                y -= 12
            y -= 5 
        y -= 15

    # --- FIRMA FINAL ---
    # Siempre dibujamos la firma en la última página (y en las anteriores por el loop)
    dibujar_firma_pie()

    # --- GUARDAR ---
    try:
        c.save()
        try:
            if platform.system() == 'Windows': os.startfile(filename)
            else: subprocess.call(('xdg-open', filename))
        except: pass
        return True, "PDF Generado Correctamente"
    except PermissionError:
        return False, "ERROR: El archivo PDF está abierto. Ciérrelo e intente de nuevo."
    except Exception as e:
        return False, f"Error al guardar PDF: {str(e)}"