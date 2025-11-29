import flet as ft
from database import db
from reporte import generar_pdf_orden

class OrdenesView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        # --- TABLA PRINCIPAL ---
        self.search = ft.TextField(
            hint_text="Buscar orden por paciente o ID...", prefix_icon="search",
            on_change=self.filtrar, expand=True
        )
        
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", weight="bold")),
                ft.DataColumn(ft.Text("Fecha", weight="bold")),
                ft.DataColumn(ft.Text("Paciente", weight="bold")),
                ft.DataColumn(ft.Text("Médico", weight="bold")),
                ft.DataColumn(ft.Text("Estado", weight="bold")),
                ft.DataColumn(ft.Text("Total", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            width=float('inf'),
            heading_row_color="#F5F5F5",
            rows=[]
        )

        # --- MODAL NUEVA ORDEN ---
        self.dd_paciente = ft.Dropdown(label="Seleccionar Paciente", options=[]) 
        self.dd_medico = ft.Dropdown(label="Médico Referidor", options=[])
        self.lv_perfiles = ft.ListView(expand=True, spacing=5, padding=10)
        self.txt_total = ft.Text("Total: S/ 0.00", size=20, weight="bold", color="green")
        self.selected_perfiles_ids = set()

        self.dialog_nueva = ft.AlertDialog(
            title=ft.Text("Nueva Orden"),
            content=ft.Container(
                width=500,
                height=500,
                content=ft.Column([
                    self.dd_paciente, 
                    self.dd_medico, 
                    ft.Divider(),
                    ft.Text("Catálogo de Exámenes:", weight="bold"),
                    
                    ft.Container(
                        content=self.lv_perfiles, 
                        border=ft.border.all(1, "#EEEEEE"), 
                        border_radius=5, 
                        expand=True 
                    ),
                    
                    ft.Container(height=10), 
                    self.txt_total
                ])
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cerrar_modal_nueva),
                ft.ElevatedButton("Crear Orden", on_click=self.crear_orden, bgcolor="#00ACC1", color="white")
            ]
        )

        # --- MODAL RESULTADOS ---
        self.tabs_resultados = ft.Tabs(selected_index=0, animation_duration=300, tabs=[], expand=True)
        self.current_orden_id = None
        self.input_controls = {} 

        self.dialog_resultados = ft.AlertDialog(
            title=ft.Text("Ingresar Resultados"),
            content=ft.Container(width=900, height=600, content=self.tabs_resultados),
            actions=[
                ft.TextButton("Cerrar", on_click=self.cerrar_resultados),
                ft.ElevatedButton("Guardar Todo", on_click=self.guardar_resultados_bd, bgcolor="green", color="white")
            ]
        )

        # --- UI PRINCIPAL ---
        self.controls = [
            ft.Row([
                ft.Text("Gestión de Órdenes", size=30, weight="bold", color="#37474F"),
                ft.Container(expand=True),
                ft.ElevatedButton("Nueva Orden", icon="add_circle", bgcolor="#00ACC1", color="white", on_click=self.abrir_modal_nueva)
            ]),
            ft.Container(height=10),
            ft.Row([self.search]),
            ft.Container(content=self.table, expand=True, bgcolor="white", border_radius=10, padding=10)
        ]
        self.cargar_datos()

    def cargar_datos(self, query=""):
        try:
            self.table.rows.clear()
            ordenes = db.buscar_ordenes(query)
            for o in ordenes:
                estado_color = "orange" if o['estado'] == 'Pendiente' else "green"
                self.table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(o['id']))),
                    ft.DataCell(ft.Text(str(o['fechaCreacion'])[:10])),
                    ft.DataCell(ft.Text(o['Paciente'])),
                    ft.DataCell(ft.Text(o['Medico'] or "Particular")),
                    ft.DataCell(ft.Container(content=ft.Text(o['estado'], color="white", size=12), bgcolor=estado_color, padding=5, border_radius=10)),
                    ft.DataCell(ft.Text(f"S/ {o['totalPagar']:.2f}")),
                    ft.DataCell(ft.Row([
                        ft.IconButton("science", tooltip="Resultados", icon_color="blue", data=o['id'], on_click=self.abrir_resultados),
                        ft.IconButton("print", tooltip="Imprimir", icon_color="grey", data=o['id'], on_click=self.imprimir_reporte_click),
                        ft.IconButton("delete", tooltip="Eliminar Orden", icon_color="red", data=o['id'], on_click=self.eliminar_orden_click),
                    ]))
                ]))
            if self.page: self.update()
        except: pass

    def filtrar(self, e): self.cargar_datos(e.control.value)

    # --- LÓGICA NUEVA ORDEN ---
    def abrir_modal_nueva(self, e):
        pacientes = db.buscar_pacientes()
        medicos = db.obtener_medicos()
        perfiles = db.obtener_perfiles() 

        self.dd_paciente.options = [ft.dropdown.Option(key=p['id'], text=f"{p['nombreCompleto']} ({p['dni']})") for p in pacientes]
        self.dd_medico.options = [ft.dropdown.Option(key=m['id'], text=m['nombre']) for m in medicos]
        self.dd_paciente.value = None
        self.dd_medico.value = None
        
        self.lv_perfiles.controls.clear()
        self.selected_perfiles_ids.clear()
        
        grupos = {}
        for p in perfiles:
            cat = p['categoria']
            if cat not in grupos: grupos[cat] = []
            grupos[cat].append(p)
            
        for cat, lista_perfiles in sorted(grupos.items()):
            checkboxes = []
            for p in lista_perfiles:
                checkboxes.append(
                    ft.Checkbox(
                        label=f"{p['nombre']} - S/ {p['precioEstandar']:.2f}", 
                        value=False, 
                        data=p, 
                        on_change=self.actualizar_total
                    )
                )
            
            self.lv_perfiles.controls.append(
                ft.ExpansionTile(
                    title=ft.Text(cat, weight="bold", color="#37474F"),
                    leading=ft.Icon("folder", color="blue"),
                    controls=checkboxes,
                    controls_padding=20,
                    dense=True,
                    initially_expanded=False 
                )
            )
        
        self.txt_total.value = "Total: S/ 0.00"
        e.page.open(self.dialog_nueva)

    def cerrar_modal_nueva(self, e): e.page.close(self.dialog_nueva)

    def actualizar_total(self, e):
        total = 0.0
        self.selected_perfiles_ids.clear()
        
        for tile in self.lv_perfiles.controls:
            if isinstance(tile, ft.ExpansionTile):
                for chk in tile.controls:
                    if isinstance(chk, ft.Checkbox) and chk.value:
                        total += float(chk.data['precioEstandar'])
                        self.selected_perfiles_ids.add(chk.data['id'])
        
        self.txt_total.value = f"Total Aprox: S/ {total:.2f}"
        self.txt_total.update()

    def crear_orden(self, e):
        if not self.dd_paciente.value:
            self.mostrar_snack(e, "Seleccione un paciente", "red")
            return
        
        medico = self.dd_medico.value if self.dd_medico.value else None
        
        if not self.selected_perfiles_ids:
            self.mostrar_snack(e, "Seleccione al menos un examen", "red")
            return

        if db.crear_orden(self.dd_paciente.value, medico, list(self.selected_perfiles_ids)):
            e.page.close(self.dialog_nueva)
            self.cargar_datos()
            self.mostrar_snack(e, "Orden creada exitosamente", "green")
        else:
            self.mostrar_snack(e, "Error al crear orden", "red")

    def eliminar_orden_click(self, e):
        orden_id = e.control.data
        
        def confirmar_eliminacion(e_btn):
            self.page.close(dlg_confirm)
            if db.eliminar_orden(orden_id):
                self.cargar_datos()
                self.mostrar_snack(e, "Orden eliminada correctamente", "green")
            else:
                self.mostrar_snack(e, "Error al eliminar orden", "red")

        dlg_confirm = ft.AlertDialog(
            title=ft.Text("Eliminar Orden"),
            content=ft.Text("¿Está seguro de eliminar esta orden y sus resultados?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dlg_confirm)),
                ft.ElevatedButton("Eliminar", bgcolor="red", color="white", on_click=confirmar_eliminacion)
            ]
        )
        self.page.open(dlg_confirm)

    # --- LÓGICA RESULTADOS ---
    def abrir_resultados(self, e):
        self.current_orden_id = e.control.data
        self.tabs_resultados.tabs.clear()
        self.input_controls.clear()
        
        analitos_ordenados = db.obtener_resultados_orden(self.current_orden_id)
        
        if not analitos_ordenados:
            self.tabs_resultados.tabs.append(ft.Tab(text="Error", content=ft.Text("No hay analitos. Verifique la configuración del perfil.")))
        else:
            grupos_perfil = {}
            for a in analitos_ordenados:
                perfil = a['Perfil']
                if perfil not in grupos_perfil: grupos_perfil[perfil] = []
                grupos_perfil[perfil].append(a)
            
            for nombre_perfil, lista_analitos in grupos_perfil.items():
                
                columna_inputs = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=15)
                columna_inputs.controls.append(ft.Container(height=10)) 
                
                ultimo_subtitulo = ""
                
                for a in lista_analitos:
                    sub = a.get('categoria') or "General"
                    if sub != "General" and sub != ultimo_subtitulo:
                        columna_inputs.controls.append(ft.Text(sub, weight="bold", color="blue", size=12))
                        ultimo_subtitulo = sub

                    label_text = f"{a['nombre']}"
                    if a['unidad']: label_text += f" ({a['unidad']})"
                    val = a['valorResultado'] or ""
                    
                    if a['tipoDato'] == 'Opciones':
                        ops = db.obtener_opciones_analito(a['AnalitoID'])
                        ctl = ft.Dropdown(label=label_text, value=val, options=[ft.dropdown.Option(op) for op in ops], dense=True)
                    elif a['tipoDato'] == 'Texto':
                        ctl = ft.TextField(label=label_text, value=val, multiline=True, min_lines=2)
                    else:
                        ctl = ft.TextField(label=label_text, value=val, keyboard_type=ft.KeyboardType.NUMBER)
                    
                    self.input_controls[a['AnalitoID']] = ctl
                    columna_inputs.controls.append(ctl)
                
                self.tabs_resultados.tabs.append(
                    ft.Tab(
                        text=nombre_perfil, 
                        icon="assignment",
                        content=ft.Container(content=columna_inputs, padding=20)
                    )
                )

        e.page.open(self.dialog_resultados)

    def cerrar_resultados(self, e): e.page.close(self.dialog_resultados)

    def guardar_resultados_bd(self, e):
        resultados = {k: v.value for k, v in self.input_controls.items()}
        db.guardar_resultados(self.current_orden_id, resultados)
        e.page.close(self.dialog_resultados)
        self.cargar_datos()
        self.mostrar_snack(e, "Resultados guardados", "green")

    # --- IMPRESIÓN ---
    def imprimir_reporte_click(self, e):
        orden_id = e.control.data
        
        sw_firma = ft.Switch(label="Incluir Firma Digital", value=True, active_color="blue")
        
        def confirmar_impresion(e_btn):
            self.page.close(dlg)
            success, mensaje = generar_pdf_orden(orden_id, incluir_firma=sw_firma.value)
            self.mostrar_snack(e, mensaje, "green" if success else "red")

        dlg = ft.AlertDialog(
            title=ft.Text("Generar PDF"),
            content=ft.Column([
                ft.Text("¿Desea generar el reporte ahora?"),
                sw_firma
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dlg)),
                ft.ElevatedButton("Generar", on_click=confirmar_impresion)
            ]
        )
        self.page.open(dlg)

    def mostrar_snack(self, e, texto, color):
        e.page.snack_bar = ft.SnackBar(ft.Text(texto), bgcolor=color)
        e.page.snack_bar.open = True
        e.page.update()