import flet as ft
from database import db

class ConfiguracionView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        # --- TAB 1: ANALITOS ---
        self.lista_analitos_ui = ft.ListView(expand=True, spacing=10, padding=10)
        self.editando_analito_id = None

        # Formulario Analito
        self.n_nombre = ft.TextField(label="Nombre Analito (Ej. Hemoglobina)", prefix_icon="science")
        
        # 1. CATEGORÍA (Para organizar en pantalla)
        self.n_cat = ft.Dropdown(
            label="Categoría General (Organización)", 
            options=[ft.dropdown.Option(x) for x in ["Hematología", "Química", "Uroanálisis", "Inmunología", "Hormonas", "Microbiología", "Parasitología"]],
            value="Hematología"
        )

        # 2. SUBTÍTULO (Para el PDF) - ESTE ES EL QUE FALTABA
        self.n_subtitulo = ft.TextField(
            label="Subtítulo en Reporte (Opcional)", 
            hint_text="Ej: SERIE ROJA, EXAMEN MACROSCÓPICO...", 
            prefix_icon="title"
        )

        self.n_tipo = ft.Dropdown(
            label="Tipo de Resultado", 
            options=[ft.dropdown.Option("Numerico"), ft.dropdown.Option("Opciones"), ft.dropdown.Option("Texto")], 
            value="Numerico", on_change=self.cambiar_tipo_analito
        )
        self.n_unidad = ft.TextField(label="Unidad")
        self.n_metodo = ft.TextField(label="Método")
        self.n_min = ft.TextField(label="Min", width=80)
        self.n_max = ft.TextField(label="Max", width=80)
        self.n_ref = ft.TextField(label="Ref. Visual")
        self.n_es_calculado = ft.Checkbox(label="¿Es Calculado?", value=False)
        self.n_formula = ft.TextField(label="Fórmula (Ej: [HB] * 3)", visible=True)

        self.btn_rangos = ft.ElevatedButton("Gestionar Rangos", icon="list", on_click=self.abrir_dialog_rangos)

        self.dialog_analito = ft.AlertDialog(
            title=ft.Text("Analito"),
            content=ft.Column([
                self.n_nombre, 
                self.n_cat,      # Categoría General
                self.n_subtitulo,# Subtítulo PDF
                self.n_tipo, self.n_metodo,
                ft.Row([self.n_min, self.n_max, self.n_unidad]), self.n_ref,
                ft.Divider(),
                self.n_es_calculado, self.n_formula,
                ft.Divider(),
                self.btn_rangos
            ], tight=True, width=400),
            actions=[ft.TextButton("Guardar", on_click=self.guardar_analito)]
        )

        # --- DIALOG RANGOS ---
        self.r_genero = ft.Dropdown(label="Género", options=[ft.dropdown.Option("Ambos"), ft.dropdown.Option("M"), ft.dropdown.Option("F")], value="Ambos", width=100)
        self.r_unidad_edad = ft.Dropdown(label="Unidad", options=[ft.dropdown.Option("Años"), ft.dropdown.Option("Meses"), ft.dropdown.Option("Días")], value="Años", width=100)
        self.r_edad_min = ft.TextField(label="Edad Min", width=80, value="0")
        self.r_edad_max = ft.TextField(label="Edad Max", width=80, value="150")
        self.r_val_min = ft.TextField(label="Ref Min", width=80)
        self.r_val_max = ft.TextField(label="Ref Max", width=80)
        self.r_pan_min = ft.TextField(label="Pánico Min", width=80)
        self.r_pan_max = ft.TextField(label="Pánico Max", width=80)
        self.r_texto = ft.TextField(label="Interpretación (Opcional)", expand=True)
        self.editando_rango_id = None # Para saber si estamos editando

        self.btn_guardar_rango = ft.ElevatedButton("Guardar Rango", on_click=self.guardar_rango_click)
        self.btn_cancelar_edicion = ft.TextButton("Cancelar Edición", on_click=self.cancelar_edicion_rango, visible=False)

        self.tabla_rangos = ft.DataTable(columns=[
            ft.DataColumn(ft.Text("Sexo")),
            ft.DataColumn(ft.Text("Edad")),
            ft.DataColumn(ft.Text("Rango")),
            ft.DataColumn(ft.Text("Pánico")),
            ft.DataColumn(ft.Text("Acciones")),
        ], rows=[])

        self.dialog_rangos = ft.AlertDialog(
            title=ft.Text("Rangos de Referencia"),
            content=ft.Container(
                width=700,
                content=ft.Column([
                    ft.Row([self.r_genero, self.r_unidad_edad, self.r_edad_min, self.r_edad_max]),
                    ft.Row([self.r_val_min, self.r_val_max, self.r_pan_min, self.r_pan_max]),
                    ft.Row([self.r_texto, self.btn_guardar_rango, self.btn_cancelar_edicion]),
                    ft.Divider(),
                    ft.Container(content=self.tabla_rangos, height=200, scroll=ft.ScrollMode.AUTO)
                ], tight=True)
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
        
        # LISTA ORDENADA
        self.selected_analitos = [] 
        self.all_analitos_cache = [] 

        self.dialog_perfil = ft.AlertDialog(
            title=ft.Text("Perfil de Examen"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    self.p_nombre, ft.Row([self.p_cat, self.p_precio]), ft.Divider(),
                    self.search_analitos_perfil, ft.Text("Componentes (Orden de selección importa):", weight="bold", size=12),
                    ft.Container(content=self.col_analitos_check, border=ft.border.all(1, "grey"), border_radius=5, padding=10)
                ], tight=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(self.dialog_perfil)),
                ft.ElevatedButton("Guardar Perfil", on_click=self.guardar_perfil, bgcolor="#00ACC1", color="white")
            ]
        )

        # --- UI ---
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
                    # Mostramos el subtítulo para referencia
                    subtitulo_text = f"Subtítulo PDF: {a['subtituloReporte']}" if a.get('subtituloReporte') else "Subtítulo PDF: (Ninguno)"
                    
                    row = ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(a['nombre'], weight="bold", size=14),
                                ft.Text(subtitulo_text, size=11, italic=True, color="grey")
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
        self.n_nombre.value = ""
        self.n_cat.value = "Hematología"
        self.n_subtitulo.value = ""
        self.n_unidad.value = ""
        self.n_min.value = ""
        self.n_max.value = ""
        self.n_ref.value = ""
        self.n_es_calculado.value = False
        self.n_formula.value = ""
        self.btn_rangos.visible = False # No se pueden gestionar rangos hasta guardar
        e.page.open(self.dialog_analito)

    def editar_analito_click(self, e):
        data = e.control.data
        self.editando_analito_id = data['id']
        self.n_nombre.value = data['nombre']
        self.n_cat.value = data['categoria']
        # Recuperamos el subtítulo si existe
        self.n_subtitulo.value = data['subtituloReporte'] if data.get('subtituloReporte') else ""
        
        self.n_tipo.value = data['tipoDato']
        self.n_metodo.value = data['metodo']
        self.n_unidad.value = data['unidad'] or ""
        self.n_min.value = str(data['valorRefMin']) if data['valorRefMin'] else ""
        self.n_max.value = str(data['valorRefMax']) if data['valorRefMax'] else ""
        self.n_ref.value = data['referenciaVisual'] or ""

        # Campos nuevos
        self.n_es_calculado.value = bool(data.get('esCalculado'))
        self.n_formula.value = data.get('formula') or ""

        self.btn_rangos.visible = True
        self.cambiar_tipo_analito(None)
        e.page.open(self.dialog_analito)

    def guardar_analito(self, e):
        if not self.n_nombre.value: 
            self.n_nombre.error_text = "Requerido"
            self.n_nombre.update()
            return

        datos = {
            'nombre': self.n_nombre.value,
            'categoria': self.n_cat.value, # Categoría General (Dropdown)
            'subtitulo': self.n_subtitulo.value, # Subtítulo PDF (Texto Libre)
            'tipoDato': self.n_tipo.value,
            'metodo': self.n_metodo.value,
            'unidad': self.n_unidad.value if self.n_tipo.value == "Numerico" else None,
            'min': self.n_min.value if self.n_tipo.value == "Numerico" else None,
            'max': self.n_max.value if self.n_tipo.value == "Numerico" else None,
            'refVisual': self.n_ref.value,
            'esCalculado': 1 if self.n_es_calculado.value else 0,
            'formula': self.n_formula.value
        }
        
        if self.editando_analito_id:
            db.editar_analito(self.editando_analito_id, datos)
            self.mostrar_snack(e, "Analito actualizado")
        else:
            db.agregar_analito(datos)
            self.mostrar_snack(e, "Analito creado")
            
        e.page.close(self.dialog_analito)
        self.cargar_analitos()

    # --- LÓGICA DE RANGOS ---
    def abrir_dialog_rangos(self, e):
        self.cancelar_edicion_rango(None) # Resetea formulario
        self.cargar_rangos_tabla()
        e.page.open(self.dialog_rangos)

    def cargar_rangos_tabla(self):
        self.tabla_rangos.rows.clear()
        rangos = db.obtener_rangos(self.editando_analito_id)

        for r in rangos:
            self.tabla_rangos.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r['genero'])),
                ft.DataCell(ft.Text(f"{r['edadMin']}-{r['edadMax']} {r['unidadEdad']}")),
                ft.DataCell(ft.Text(f"{r['valorMin']} - {r['valorMax']}")),
                ft.DataCell(ft.Text(f"{r.get('panicoMin','')} - {r.get('panicoMax','')}")),
                ft.DataCell(ft.Row([
                    ft.IconButton("edit", icon_color="blue", data=r, on_click=self.cargar_rango_para_editar),
                    ft.IconButton("delete", icon_color="red", data=r['id'], on_click=self.eliminar_rango_click)
                ]))
            ]))
        if self.page: self.dialog_rangos.update()

    def cargar_rango_para_editar(self, e):
        r = e.control.data
        self.editando_rango_id = r['id']
        self.r_genero.value = r['genero']
        self.r_unidad_edad.value = r['unidadEdad']
        self.r_edad_min.value = str(r['edadMin'])
        self.r_edad_max.value = str(r['edadMax'])
        self.r_val_min.value = str(r['valorMin'])
        self.r_val_max.value = str(r['valorMax'])
        self.r_pan_min.value = str(r.get('panicoMin') or "")
        self.r_pan_max.value = str(r.get('panicoMax') or "")
        self.r_texto.value = r.get('textoInterpretacion') or ""

        self.btn_guardar_rango.text = "Actualizar Rango"
        self.btn_cancelar_edicion.visible = True
        self.dialog_rangos.update()

    def cancelar_edicion_rango(self, e):
        self.editando_rango_id = None
        self.r_genero.value = "Ambos"
        self.r_unidad_edad.value = "Años"
        self.r_edad_min.value = "0"
        self.r_edad_max.value = "150"
        self.r_val_min.value = ""
        self.r_val_max.value = ""
        self.r_pan_min.value = ""
        self.r_pan_max.value = ""
        self.r_texto.value = ""

        self.btn_guardar_rango.text = "Agregar Rango"
        self.btn_cancelar_edicion.visible = False
        if self.page: self.dialog_rangos.update()

    def guardar_rango_click(self, e):
        try:
            d = {
                'analitoId': self.editando_analito_id,
                'genero': self.r_genero.value,
                'unidadEdad': self.r_unidad_edad.value,
                'edadMin': float(self.r_edad_min.value),
                'edadMax': float(self.r_edad_max.value),
                'valorMin': float(self.r_val_min.value),
                'valorMax': float(self.r_val_max.value),
                'panicoMin': float(self.r_pan_min.value) if self.r_pan_min.value else None,
                'panicoMax': float(self.r_pan_max.value) if self.r_pan_max.value else None,
                'textoInterpretacion': self.r_texto.value
            }

            if self.editando_rango_id:
                if db.editar_rango(self.editando_rango_id, d):
                    self.mostrar_snack(e, "Rango actualizado")
                    self.cancelar_edicion_rango(None)
                    self.cargar_rangos_tabla()
                else:
                    self.mostrar_snack(e, "Error al actualizar", "red")
            else:
                if db.agregar_rango(d):
                    self.mostrar_snack(e, "Rango agregado")
                    self.cancelar_edicion_rango(None)
                    self.cargar_rangos_tabla()
                else:
                    self.mostrar_snack(e, "Error al agregar", "red")

        except ValueError:
            self.mostrar_snack(e, "Error: Revise que los campos numéricos sean válidos", "red")

    def eliminar_rango_click(self, e):
        rid = e.control.data
        db.eliminar_rango(rid)
        self.cargar_rangos_tabla()

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