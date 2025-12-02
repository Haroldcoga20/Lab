from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from database import db
import os, platform, subprocess

def generar_pdf_orden(orden_id, config_list, include_signature=True):

    # --- 1. OBTENER DATOS HEADER ---
    header_data = db.get_report_header(orden_id)
    if not header_data: return False, "Datos de orden no encontrados"

    paciente, edad, unidad, genero, medico, fecha = header_data

    nombre_medico = str(medico).upper() if medico else ""
    ES_DR_CESPEDES = "CESPEDES" in nombre_medico and "HUGO" in nombre_medico

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
        if not ES_DR_CESPEDES:
            ruta_agua = os.path.join(os.getcwd(), "assets", "microscopio_agua.png")
            if os.path.exists(ruta_agua):
                try:
                    c.saveState()
                    c.setFillAlpha(0.25)
                    ancho_agua = 500
                    alto_agua = 500
                    x_pos = (w - ancho_agua) / 2
                    y_pos = (h - alto_agua) / 2
                    c.drawImage(ruta_agua, x_pos, y_pos, width=ancho_agua, height=alto_agua, mask='auto', preserveAspectRatio=True)
                    c.restoreState()
                except: pass

    def dibujar_membrete(y_actual):
        if ES_DR_CESPEDES:
            ruta_membrete = os.path.join(os.getcwd(), "assets", "membrete_cespedes.png")
        else:
            ruta_membrete = os.path.join(os.getcwd(), "assets", "membrete_full.png")

        if os.path.exists(ruta_membrete):
            try:
                ancho_imagen = w - 20
                altura_imagen = 160
                c.drawImage(ruta_membrete, 10, y_actual - altura_imagen + 20, width=ancho_imagen, height=altura_imagen, mask='auto', preserveAspectRatio=True)
                return y_actual - altura_imagen - 10
            except Exception as e:
                print(f"Error cargando membrete: {e}")
                return y_actual - 50
        else:
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(w/2, y_actual - 30, "LABORATORIO CLÍNICO")
            return y_actual - 50

    def dibujar_firma():
        y_firma = margen_y_bottom + 40
        x_firma_centro = w - margen_x - 100

        if include_signature:
            ruta_firma = os.path.join(os.getcwd(), "assets", "firma.png")
            if os.path.exists(ruta_firma):
                try:
                    c.drawImage(ruta_firma, x_firma_centro - 110, y_firma - 30, width=220, height=90, mask='auto', preserveAspectRatio=True)
                except: pass

        c.setStrokeColor(colors.black)
        c.setDash(4, 3)
        c.line(x_firma_centro - 90, y_firma, x_firma_centro + 90, y_firma)
        c.setDash([])

        c.setFont("Courier", 9)
        c.drawCentredString(x_firma_centro, y_firma - 12, "LIC. COBEÑAS PALACIOS LUIS A.")
        c.drawCentredString(x_firma_centro, y_firma - 22, "TECNÓLOGO MÉDICO")
        c.drawCentredString(x_firma_centro, y_firma - 32, "C.T.M.P 10911")

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

    def init_page():
        dibujar_marca_agua()
        y = h - 20
        y = dibujar_membrete(y)
        y = dibujar_datos_paciente(y)
        y = dibujar_barra_titulos(y)
        return y

    # --- INICIO DE PÁGINA 1 ---
    y = init_page()

    # --- CUERPO ---
    for group_config in config_list:
        if not group_config['include']:
            continue

        items = group_config['items']
        if not items: continue

        # Page Break Logic
        if group_config['page_break']:
             dibujar_firma()
             c.showPage()
             y = init_page()

        espacio_needed = 40 + (len(items) * 15)
        limite_inferior = margen_y_bottom + 100

        if y - espacio_needed < limite_inferior:
            dibujar_firma()
            c.showPage()
            y = init_page()

        c.setFillColor(colors.black)
        c.setFont("Courier-Bold", 11)

        c.drawString(margen_x, y, f"Examen :   {group_config['title']}")
        y -= 15

        metodo_global = items[0].get('metodo')
        if metodo_global and metodo_global != "Automatizado":
             c.setFont("Courier", 10)
             c.drawString(margen_x, y, f"Método :   {metodo_global}")
             y -= 15

        y -= 5

        current_cat = None
        current_sub = None

        for item in items:
            cat = item.get('categoria') or "General"
            subtitulo = item.get('subtituloReporte')

            # Category Header (For Profiles)
            if group_config['type'] == 'Perfil':
                 if cat != "General" and cat != current_cat and "OBSERVACIONES" not in cat.upper():
                    y -= 5
                    c.setFont("Courier-Bold", 10)
                    c.drawString(margen_x, y, f"{cat}:")
                    y -= 12
                    current_cat = cat

            # Subtitle Header (Phase 6.5)
            if subtitulo and subtitulo != current_sub:
                y -= 5
                c.setFont("Courier-Bold", 10)
                c.drawString(margen_x + 10, y, subtitulo)
                y -= 12
                current_sub = subtitulo

            nombre = item['nombre']
            raw_val = item['valor'] or ""
            val_str = str(raw_val).strip()

            if not val_str and val_str != "0":
                continue

            # Numeric Formatting
            try:
                float_val = float(val_str)
                val_str = "{:.2f}".format(float_val)
            except ValueError:
                pass

            # Reference Logic (Phase 9 Priority)
            # 1. Visual Specifica (DB logic does this in ranges query? No, ranges table has 'referenciaVisualEspecifica')
            # 2. Visual General (Restored field)
            # 3. Interpretation (Text from Range)
            # 4. Numeric Range

            # The current `db.get_smart_reference` implements logic: Gender match -> Age Match -> Return String.
            # But the string logic inside `get_smart_reference` was:
            # if r_visual: return r_visual (Specific)
            # elif numeric: return min-max

            # We need to inject the "General Visual" fallback.
            # `item['referenciaVisual']` comes from `Analitos` table.
            # `db.get_smart_reference` returns the "Calculated/Matched" range.
            # If `db.get_smart_reference` returns empty string (no match or no ranges), we fallback to `item['referenciaVisual']`.
            # I updated `db.get_smart_reference` in `database.py` to handle this fallback internally.
            # So calling `get_smart_reference` is sufficient if the DB method is correct.

            # Let's verify DB method in my thought process:
            # `get_smart_reference` calls `get_patient_range_values` -> if match, builds string.
            # If no match/empty, it queries `Analitos` table for `referenciaVisual`.
            # Yes, I implemented that in step 1.

            # So here we just call it. But wait, `generar_pdf_orden` calls `db.get_smart_reference`?
            # No, the loop uses `item['analitoId']` etc to call it.

            smart_ref = db.get_smart_reference(item['analitoId'], genero, edad, unidad)
            uni = str(item['unidad'] or "")

            if nombre.upper() == "OBSERVACIONES":
                y -= 10
                c.setFont("Courier-Bold", 10)
                c.drawString(margen_x, y, "OBSERVACIONES:")
                c.setFont("Courier", 10)
                if val_str: c.drawString(margen_x + 110, y, val_str)
                y -= 15
                continue

            c.setFont("Courier", 10)
            c.drawString(margen_x, y, nombre)

            if "POSITIVO" in val_str.upper() or "REACTIVO" in val_str.upper():
                c.setFont("Courier-Bold", 10)

            c.drawString(margen_x + (ancho_util * 0.4) + 10, y, val_str)

            c.setFont("Courier", 10)
            c.drawString(margen_x + (ancho_util * 0.65), y, smart_ref)
            c.drawString(margen_x + (ancho_util * 0.88), y, uni)

            y -= 12
        y -= 5
        y -= 15

    # --- FIRMA FINAL ---
    dibujar_firma()

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
