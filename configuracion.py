import flet as ft
from database import db

class ConfiguracionView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        # --- TAB 1: ANALITOS ---
        self.lista_analitos_ui = ft.ListView(expand=True, spacing=10, padding=10)
        self.editando_analito_id = None
        self.analito_actual_para_rangos = None # ID del analito que se está configurando rangos

        # --- FORMULARIO ANALITO (Nivel 1) ---
        self.n_nombre = ft.TextField(label="Nombre Analito", prefix_icon="science")
        
        self.n_cat = ft.Dropdown(
            label="Categoría General", 
            options=[ft.dropdown.Option(x) for x in ["Hematología", "Química", "Uroanálisis", "Inmunología", "Hormonas", "Microbiología", "Parasitología"]],
            value="Hematología"
        )
        self.n_subtitulo = ft.TextField(label="Subtítulo en Reporte", hint_text="Ej: SERIE ROJA", prefix_icon="title")
        
        self.n_tipo = ft.Dropdown(
            label="Tipo de Resultado", 
            options=[ft.dropdown.Option("Numerico"), ft.dropdown.Option("Opciones"), ft.dropdown.Option("Texto")], 
            value="Numerico", on_change=self.cambiar_tipo_analito
        )
        
        # Nuevos Campos de Cálculo
        self.n_calculado = ft.Switch(label="¿Es un valor calculado?", value=False, on_change=self.cambiar_es_calculado)
        self.n_formula = ft.TextField(label="Fórmula (Ej: [COL]-[HDL]-([TRIG]/5))", visible=False, prefix_icon="functions")
        
        # Campos estándar (Generales)
        self.n_unidad = ft.TextField(label="Unidad")
        self.n_metodo = ft.TextField(label="Método")
        self.n_min = ft.TextField(label="Min (Gral)", width=80)
        self.n_max = ft.TextField(label="Max (Gral)", width=80)
        self.n_ref = ft.TextField(label="Ref. Visual (Texto General)")

        # Botón para abrir el gestor avanzado de rangos
        self.btn_rangos = ft.ElevatedButton(
            "Gestionar Rangos de Referencia (Pediatría/Sexo)", 
            icon="settings_accessibility", 
            bgcolor="#FF9800", color="white",
            on_click=self.abrir_gestionar_rangos,
            visible=False # Solo visible al editar
        )

        self.dialog_analito = ft.AlertDialog(
            title=ft.Text("Configurar Analito"),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    self.n_nombre, 
                    ft.Row([self.n_cat, self.n_tipo]),
                    self.n_subtitulo,
                    self.n_calculado, self.n_formula,
                    ft.Divider(),
                    ft.Text("Valores por Defecto:", size=12, color="grey"),
                    self.n_metodo,
                    ft.Row([self.n_min, self.n_max, self.n_unidad]), 
                    self.n_ref,
                    ft.Divider(),
                    self.btn_rangos
                ], tight=True, scroll=ft.ScrollMode.AUTO, height=500)
            ),
            actions=[ft.TextButton("Guardar", on_click=self.guardar_analito)]
        )

        # --- FORMULARIO RANGOS (Nivel 2 - Modal sobre Modal) ---
        # Inputs para crear un rango
        self.r_genero = ft.Dropdown(label="Género", options=[ft.dropdown.Option("Ambos"), ft.dropdown.Option("Masculino"), ft.dropdown.Option("Femenino")], value="Ambos", width=120)
        self.r_unidad = ft.Dropdown(label="Unidad Edad", options=[ft.dropdown.Option("Años"), ft.dropdown.Option("Meses"), ft.dropdown.Option("Días")], value="Años", width=120)
        self.r_edad_min = ft.TextField(label="Edad Min", width=80, value="0")
        self.r_edad_max = ft.TextField(label="Edad Max", width=80, value="100")
        
        self.r_val_min = ft.TextField(label="Val Min", width=80)
        self.r_val_max = ft.TextField(label="Val Max", width=80)
        self.r_panico_min = ft.TextField(label="Pánico Min", width=80, border_color="red")
        self.r_panico_max = ft.TextField(label="Pánico Max", width=80, border_color="red")
        self.r_texto = ft.TextField(label="Texto Interpretación (Opcional)", hint_text="Ej: Alto Riesgo")

        self.tabla_rangos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Género")),
                ft.DataColumn(ft.Text("Edad")),
                ft.DataColumn(ft.Text("Rango")),
                ft.DataColumn(ft.Text("Pánico")),
                ft.DataColumn(ft.Text("Interp.")),
                ft.DataColumn(ft.Text("X")),
            ],
            rows=[]
        )

        self.dialog_rangos = ft.AlertDialog(
            title=ft.Text("Rangos de Referencia Avanzados"),
            content=ft.Container(
                width=700, height=600,
                content=ft.Column([
                    ft.Text("Agregar Nuevo Rango:", weight="bold"),
                    ft.Row([self.r_genero, self.r_unidad, self.r_edad_min, self.r_edad_max]),
                    ft.Row([self.r_val_min, self.r_val_max, self.r_panico_min, self.r_panico_max]),
                    ft.Row([self.r_texto, ft.ElevatedButton("Agregar", icon="add", on_click=self.agregar_rango, bgcolor="green", color="white")]),
                    ft.Divider(),
                    ft.Column([self.tabla_rangos], scroll=ft.ScrollMode.AUTO, expand=True)
                ])
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.page.close(self.dialog_rangos))]
        )


        # --- TAB 2: PERFILES ---
        self.lista_perfiles_ui = ft.ListView(expand=True, spacing=10, padding=10)
        self.editando_perfil_id = None
        self.p_nombre = ft.TextField(label="Nombre Perfil", prefix_icon="folder_special")
        self.p_cat = ft.Dropdown(label="Categoría General", options=[ft.dropdown.Option(x) for x in ["Hematología", "Química", "Uroanálisis", "Inmunología", "Perfiles", "Hormonas", "Parasitología"]], value="Perfiles")
        self.p_precio = ft.TextField(label="Precio (S/)", prefix_icon="attach_money", input_filter=ft.InputFilter(regex_string=r"[0-9.]"))
        self.search_analitos_perfil = ft.TextField(hint_text="Buscar analito...", prefix_icon="search", on_change=self.filtrar_analitos_perfil)
        self.col_analitos_check = ft.Column(scroll=ft.ScrollMode.AUTO, height=300)
        self.selected_analitos = [] 
        self.all_analitos_cache = [] 

        self.dialog_perfil = ft.AlertDialog(
            title=ft.Text("Perfil de Examen"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    self.p_nombre, ft.Row([self.p_cat, self.p_precio]), ft.Divider(),
                    self.search_analitos_perfil, ft.Text("Componentes:", weight="bold", size=12),
                    ft.Container(content=self.col_analitos_check, border=ft.border.all(1, "grey"), border_radius=5, padding=10)
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(self.dialog_perfil)),
                ft.ElevatedButton("Guardar Perfil", on_click=self.guardar_perfil, bgcolor="#00ACC1", color="white")
            ]
        )

        # --- UI PRINCIPAL ---
        self.controls = [
            ft.Text("Configuración", size=30, weight="bold", color="#37474F"),
            ft.Tabs(selected_index=0, animation_duration=300, tabs=[
                ft.Tab(text="Analitos", icon="science", content=ft.Column([
                    ft.Container(height=10),
                    ft.ElevatedButton("Nuevo Analito", icon="add", on_click=self.abrir_nuevo_analito, bgcolor="#00ACC1", color="white"),
                    ft.Container(height=10),
                    ft.Container(content=self.lista_analitos_ui, bgcolor="white", border_radius=10, padding=10, expand=True, shadow=ft.BoxShadow(blur_radius=5, color="#0D000000"))
                ], expand=True)),
                ft.Tab(text="Perfiles", icon="inventory_2", content=ft.Column([
                    ft.Container(height=10),
                    ft.ElevatedButton("Nuevo Perfil", icon="add", on_click=self.abrir_nuevo_perfil, bgcolor="#00ACC1", color="white"),
                    ft.Container(height=10),
                    ft.Container(content=self.lista_perfiles_ui, bgcolor="white", border_radius=10, padding=10, expand=True, shadow=ft.BoxShadow(blur_radius=5, color="#0D000000"))
                ], expand=True)),
            ], expand=True)
        ]
        self.cargar_analitos()
        self.cargar_perfiles()

    # --- LÓGICA DE ANALITOS ---
    def cambiar_tipo_analito(self, e):
        es_num = self.n_tipo.value == "Numerico"
        self.n_min.visible = self.n_max.visible = self.n_unidad.visible = es_num
        self.n_calculado.visible = es_num # Solo numericos pueden ser calculados
        if self.page: self.page.update()

    def cambiar_es_calculado(self, e):
        self.n_formula.visible = self.n_calculado.value
        if self.page: self.page.update()

    def cargar_analitos(self):
        try:
            self.lista_analitos_ui.controls.clear()
            data = db.obtener_analitos()
            grupos = {}
            for a in data:
                cat = a['categoria']
                if cat not in grupos: grupos[cat] = []
                grupos[cat].append(a)
            
            for cat, lista in sorted(grupos.items()):
                contenido_tile = []
                for a in lista:
                    subtitulo_text = f"Sub: {a['subtituloReporte']}" if a.get('subtituloReporte') else ""
                    es_calc_text = " (Calculado)" if a.get('esCalculado') else ""
                    
                    row = ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{a['nombre']}{es_calc_text}", weight="bold", size=14),
                                ft.Text(f"{subtitulo_text}", size=11, italic=True, color="grey")
                            ], expand=True),
                            ft.Container(content=ft.Text(a['tipoDato'], size=10, color="white"), bgcolor="blue" if a['tipoDato']=="Numerico" else "orange", padding=5, border_radius=5),
                            ft.IconButton("edit", icon_color="blue", data=a, on_click=self.editar_analito_click)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.only(left=10, right=10, bottom=5), border=ft.border.only(bottom=ft.border.BorderSide(1, "#EEEEEE"))
                    )
                    contenido_tile.append(row)

                self.lista_analitos_ui.controls.append(ft.ExpansionTile(
                    title=ft.Text(cat, weight="bold", color="#37474F"),
                    leading=ft.Icon("science", color="blue"),
                    controls=contenido_tile, controls_padding=10, bgcolor="#F9FAFB"
                ))
            if self.page: self.update()
        except: pass

    def abrir_nuevo_analito(self, e):
        self.editando_analito_id = None
        self.btn_rangos.visible = False # No se pueden agregar rangos hasta que exista el analito
        self.n_nombre.value = ""
        self.n_cat.value = "Hematología"
        self.n_subtitulo.value = ""
        self.n_unidad.value = ""
        self.n_min.value = ""
        self.n_max.value = ""
        self.n_ref.value = ""
        self.n_calculado.value = False
        self.n_formula.value = ""
        self.cambiar_tipo_analito(None)
        self.cambiar_es_calculado(None)
        e.page.open(self.dialog_analito)

    def editar_analito_click(self, e):
        data = e.control.data
        self.editando_analito_id = data['id']
        self.analito_actual_para_rangos = data['id']
        self.btn_rangos.visible = True # Habilitar gestion de rangos

        self.n_nombre.value = data['nombre']
        self.n_cat.value = data['categoria']
        self.n_subtitulo.value = data['subtituloReporte'] if data.get('subtituloReporte') else ""
        self.n_tipo.value = data['tipoDato']
        self.n_metodo.value = data['metodo']
        self.n_unidad.value = data['unidad'] or ""
        self.n_min.value = str(data['valorRefMin']) if data['valorRefMin'] is not None else ""
        self.n_max.value = str(data['valorRefMax']) if data['valorRefMax'] is not None else ""
        self.n_ref.value = data['referenciaVisual'] or ""
        
        # Cargar datos nuevos
        self.n_calculado.value = bool(data.get('esCalculado'))
        self.n_formula.value = data.get('formula') or ""
        
        self.cambiar_tipo_analito(None)
        self.cambiar_es_calculado(None)
        e.page.open(self.dialog_analito)

    def guardar_analito(self, e):
        if not self.n_nombre.value: 
            self.n_nombre.error_text = "Requerido"
            self.n_nombre.update()
            return

        datos = {
            'nombre': self.n_nombre.value,
            'categoria': self.n_cat.value,
            'subtitulo': self.n_subtitulo.value,
            'tipoDato': self.n_tipo.value,
            'metodo': self.n_metodo.value,
            'unidad': self.n_unidad.value if self.n_tipo.value == "Numerico" else None,
            'min': self.n_min.value if self.n_tipo.value == "Numerico" else None,
            'max': self.n_max.value if self.n_tipo.value == "Numerico" else None,
            'refVisual': self.n_ref.value,
            'formula': self.n_formula.value if self.n_calculado.value else None,
            'esCalculado': 1 if self.n_calculado.value else 0
        }
        
        if self.editando_analito_id:
            db.editar_analito(self.editando_analito_id, datos)
            self.mostrar_snack(e, "Analito actualizado")
        else:
            db.agregar_analito(datos)
            self.mostrar_snack(e, "Analito creado")
            
        e.page.close(self.dialog_analito)
        self.cargar_analitos()

    # --- LÓGICA DE RANGOS DE REFERENCIA (SUB-MODAL) ---
    def abrir_gestionar_rangos(self, e):
        self.cargar_tabla_rangos()
        e.page.open(self.dialog_rangos)

    def cargar_tabla_rangos(self):
        # SQL DIRECTO AQUÍ PARA NO MODIFICAR DATABASE.PY
        if not self.analito_actual_para_rangos: return
        try:
            self.tabla_rangos.rows.clear()
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, genero, unidadEdad, edadMin, edadMax, rangoMin, rangoMax, panicoMin, panicoMax, textoInterpretacion FROM RangosReferencia WHERE analitoId = ? ORDER BY unidadEdad, edadMin", (self.analito_actual_para_rangos,))
            filas = cursor.fetchall()
            
            for r in filas:
                rid, gen, uni, emin, emax, rmin, rmax, pmin, pmax, txt = r
                
                # Formateo visual
                rango_txt = f"{rmin} - {rmax}"
                panico_txt = ""
                if pmin or pmax: panico_txt = f"<{pmin} | >{pmax}"
                
                edad_txt = f"{emin}-{emax} {uni}"

                self.tabla_rangos.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(gen)),
                    ft.DataCell(ft.Text(edad_txt)),
                    ft.DataCell(ft.Text(rango_txt)),
                    ft.DataCell(ft.Text(panico_txt, color="red")),
                    ft.DataCell(ft.Text(txt or "")),
                    ft.DataCell(ft.IconButton("delete", icon_color="red", data=rid, on_click=self.eliminar_rango)),
                ]))
            conn.close()
            if self.tabla_rangos.page: self.tabla_rangos.update()
        except Exception as ex:
            print(f"Error cargando rangos: {ex}")

    def agregar_rango(self, e):
        if not self.r_val_min.value or not self.r_val_max.value: return
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO RangosReferencia (analitoId, genero, unidadEdad, edadMin, edadMax, rangoMin, rangoMax, panicoMin, panicoMax, textoInterpretacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.analito_actual_para_rangos,
                self.r_genero.value,
                self.r_unidad.value,
                int(self.r_edad_min.value),
                int(self.r_edad_max.value),
                float(self.r_val_min.value),
                float(self.r_val_max.value),
                float(self.r_panico_min.value) if self.r_panico_min.value else None,
                float(self.r_panico_max.value) if self.r_panico_max.value else None,
                self.r_texto.value
            ))
            conn.commit()
            conn.close()
            
            # Limpiar campos
            self.r_val_min.value = ""
            self.r_val_max.value = ""
            self.r_panico_min.value = ""
            self.r_panico_max.value = ""
            self.r_texto.value = ""
            self.r_val_min.update()
            
            self.cargar_tabla_rangos() # Recargar tabla
            
        except Exception as ex:
            self.mostrar_snack(e, f"Error SQL: {ex}", "red")

    def eliminar_rango(self, e):
        rid = e.control.data
        try:
            conn = db.get_connection()
            conn.cursor().execute("DELETE FROM RangosReferencia WHERE id = ?", (rid,)).commit()
            conn.close()
            self.cargar_tabla_rangos()
        except: pass

    # --- LÓGICA PERFILES ---
    def cargar_perfiles(self):
        try:
            self.lista_perfiles_ui.controls.clear()
            perfiles = db.obtener_perfiles()
            all_analitos = db.obtener_analitos()
            mapa = {a['id']: a['nombre'] for a in all_analitos}

            for p in perfiles:
                ids = db.obtener_analitos_perfil(p['id'])
                noms = [mapa.get(aid, "Desconocido") for aid in ids]
                
                contenido = [ft.Text("Contenido (En orden de reporte):", weight="bold", size=12)]
                for i, nom in enumerate(noms, 1): 
                    contenido.append(ft.Text(f" {i}. {nom}", size=12, color="#546E7A"))
                
                contenido.append(ft.Container(height=10))
                contenido.append(ft.Row([
                    ft.ElevatedButton("Modificar", icon="edit", data=p, on_click=self.editar_perfil_click, bgcolor="#00ACC1", color="white"),
                    ft.ElevatedButton("Eliminar", icon="delete", data=p['id'], on_click=self.eliminar_perfil_click, bgcolor="red", color="white")
                ]))

                self.lista_perfiles_ui.controls.append(ft.ExpansionTile(
                    title=ft.Text(p['nombre'], weight="bold", color="#37474F"),
                    subtitle=ft.Text(f"{p['categoria']} - S/ {p['precioEstandar']:.2f}", size=12, italic=True),
                    leading=ft.Icon("folder_open", color="#00ACC1"),
                    controls=[ft.Container(content=ft.Column(contenido), padding=ft.padding.only(left=50, bottom=20), bgcolor="#F1F8E9")]
                ))
            if self.page: self.update()
        except Exception as e:
            print(f"Error cargando perfiles: {e}")

    def renderizar_lista_analitos(self, filtro=""):
        self.col_analitos_check.controls.clear()
        grupos = {}
        for a in self.all_analitos_cache:
            if filtro.lower() in a['nombre'].lower() or filtro.lower() in a['categoria'].lower():
                cat = a['categoria']
                if cat not in grupos: grupos[cat] = []
                grupos[cat].append(a)
        
        for cat, lista in sorted(grupos.items()):
            checks = []
            for a in lista:
                is_checked = a['id'] in self.selected_analitos
                checks.append(ft.Checkbox(label=a['nombre'], value=is_checked, data=a['id'], on_change=self.toggle_analito))
            
            initially_expanded = True if filtro else False
            self.col_analitos_check.controls.append(ft.ExpansionTile(
                title=ft.Text(cat, weight="bold", color="blue"), controls=checks, 
                initially_expanded=initially_expanded, controls_padding=10, dense=True
            ))
        if self.col_analitos_check.page: self.col_analitos_check.update()

    def filtrar_analitos_perfil(self, e): self.renderizar_lista_analitos(e.control.value)

    def abrir_nuevo_perfil(self, e):
        self.editando_perfil_id = None
        self.p_nombre.value = ""
        self.p_precio.value = ""
        self.search_analitos_perfil.value = ""
        self.selected_analitos = []
        self.all_analitos_cache = db.obtener_analitos()
        self.renderizar_lista_analitos()
        e.page.open(self.dialog_perfil)

    def editar_perfil_click(self, e):
        data = e.control.data
        self.editando_perfil_id = data['id']
        self.p_nombre.value = data['nombre']
        self.p_cat.value = data['categoria']
        self.p_precio.value = str(data['precioEstandar'])
        
        ids_actuales = db.obtener_analitos_perfil(data['id'])
        self.selected_analitos = list(ids_actuales) # Lista para mantener orden
        
        self.all_analitos_cache = db.obtener_analitos()
        self.search_analitos_perfil.value = ""
        self.renderizar_lista_analitos()
        e.page.open(self.dialog_perfil)

    def eliminar_perfil_click(self, e):
        pid = e.control.data
        if db.eliminar_perfil(pid):
            self.mostrar_snack(e, "Perfil eliminado", "orange")
            self.cargar_perfiles()
        else:
            self.mostrar_snack(e, "Error al eliminar", "red")

    def toggle_analito(self, e):
        aid = e.control.data
        if e.control.value:
            if aid not in self.selected_analitos:
                self.selected_analitos.append(aid)
        else:
            if aid in self.selected_analitos:
                self.selected_analitos.remove(aid)

    def guardar_perfil(self, e):
        if not self.p_nombre.value or not self.p_precio.value: return
        if not self.selected_analitos: 
            self.mostrar_snack(e, "Selecciona analitos", "red")
            return

        analitos_list = self.selected_analitos 
        
        if self.editando_perfil_id:
            db.editar_perfil(self.editando_perfil_id, self.p_nombre.value, self.p_cat.value, float(self.p_precio.value), analitos_list)
            self.mostrar_snack(e, "Perfil actualizado")
        else:
            if db.agregar_perfil(self.p_nombre.value, self.p_cat.value, float(self.p_precio.value), analitos_list):
                self.mostrar_snack(e, "Perfil creado")
            else:
                self.mostrar_snack(e, "Error: Nombre duplicado", "red")
            
        e.page.close(self.dialog_perfil)
        self.cargar_perfiles()

    def mostrar_snack(self, e, texto, color="green"):
        e.page.snack_bar = ft.SnackBar(ft.Text(texto), bgcolor=color)
        e.page.snack_bar.open = True
        e.page.update()