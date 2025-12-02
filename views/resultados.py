import flet as ft
from database import db
from models.paciente import Paciente

class ResultadosView(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
        self.expand = True

        # Filter Toolbar
        self.txt_search = ft.TextField(
            prefix_icon=ft.Icons.SEARCH,
            hint_text="Buscar por Paciente/DNI",
            expand=True,
            on_submit=self.apply_filters
        )
        self.dd_filter_medico = ft.Dropdown(
            label="Filtrar por Médico",
            width=200,
            options=[],
            on_change=self.apply_filters
        )
        self.dd_filter_estado = ft.Dropdown(
            label="Estado",
            width=150,
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Pendiente"),
                ft.dropdown.Option("Completado"),
            ],
            value="Todos",
            on_change=self.apply_filters
        )
        self.btn_clear_filters = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip="Limpiar Filtros",
            on_click=self.clear_filters
        )

        # Left Panel: List of Orders
        self.lv_ordenes = ft.ListView(expand=True, spacing=5, padding=10)

        # Right Panel: Results Detail (Grouped)
        self.current_orden_id = None
        self.lbl_orden_info = ft.Text("Seleccione una Orden", size=18, weight=ft.FontWeight.BOLD)
        self.result_container = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)

        self.input_controls = []

        # Split View
        self.controls = [
            ft.Text("Ingreso de Resultados", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Row([self.txt_search, self.dd_filter_medico, self.dd_filter_estado, self.btn_clear_filters]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Row([
                # Left Panel
                ft.Container(
                    width=350, # Wider for filters?
                    content=ft.Column([
                        ft.Text("Lista de Órdenes", weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        self.lv_ordenes
                    ]),
                    border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300))
                ),
                # Right Panel
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column([
                        self.lbl_orden_info,
                        ft.Divider(),
                        self.result_container
                    ])
                )
            ], expand=True)
        ]

        self.load_initial_data()
        self.load_ordenes(initial=True)

    def load_initial_data(self):
        try:
            medicos = db.get_all_medicos()
            self.dd_filter_medico.options = [ft.dropdown.Option(key=str(m[0]), text=m[1]) for m in medicos]
            self.update()
        except Exception as e:
            print(f"Error loading filters: {e}")

    def apply_filters(self, e):
        self.load_ordenes()

    def clear_filters(self, e):
        self.txt_search.value = ""
        self.dd_filter_medico.value = None
        self.dd_filter_estado.value = "Todos"
        self.load_ordenes()

    def load_ordenes(self, initial=False):
        self.lv_ordenes.controls.clear()
        try:
            search = self.txt_search.value
            medico_id = self.dd_filter_medico.value
            estado = self.dd_filter_estado.value

            ordenes = db.get_ordenes_filtradas(search, medico_id, estado)

            if not ordenes:
                self.lv_ordenes.controls.append(ft.Text("No se encontraron órdenes."))
            else:
                for o in ordenes:
                    oid = o[0]
                    nombre = o[1]
                    fecha = o[2].strftime("%d/%m %H:%M") if o[2] else ""
                    estado_orden = o[3]

                    self.lv_ordenes.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.RECEIPT_LONG),
                            title=ft.Text(f"#{oid} - {nombre}"),
                            subtitle=ft.Text(f"{fecha} | {estado_orden}"),
                            on_click=lambda e, x=oid: self.load_detalle_orden(x)
                        )
                    )

            if not initial:
                self.update()
        except Exception as e:
            print(f"Error loading orders: {e}")

    def load_detalle_orden(self, orden_id):
        self.current_orden_id = orden_id
        self.input_controls = []
        self.result_container.controls.clear()

        # Header
        header_tuple = db.get_orden_header(orden_id)
        if not header_tuple: return
        paciente_tuple = db.get_paciente(header_tuple[1])
        paciente = Paciente.from_tuple(paciente_tuple)

        self.lbl_orden_info.value = f"Orden #{orden_id} - {paciente.nombreCompleto} ({paciente.edad} {paciente.unidadEdad})"

        # Set FAB (Icon Only)
        self.page_ref.floating_action_button = ft.FloatingActionButton(
            icon=ft.Icons.SAVE,
            on_click=self.save_all
        )
        self.page_ref.update()

        # Get Grouped Results (Ordered by DB logic now)
        grouped_data = db.get_resultados_grouped(orden_id)

        for group in grouped_data:
            group_title = group['title']
            items = group['items']

            card_rows = []

            card_rows.append(ft.Row([
                ft.Text("Analito", weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Resultado", weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Ref", weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Unid.", weight=ft.FontWeight.BOLD, width=60),
            ]))
            card_rows.append(ft.Divider())

            for item in items:
                smart_ref = db.get_smart_reference(item['analitoId'], paciente.genero, paciente.edad, paciente.unidadEdad)

                # Determine Input Type and Pre-fill
                current_val = item['valor']
                tipo = item['tipoDato']
                input_control = None

                if tipo == 'Opciones':
                    options = item.get('opciones', [])
                    dropdown_opts = [ft.dropdown.Option(o['text']) for o in options]

                    # Logic: If current_val is set, use it. Else find default.
                    val_to_set = current_val
                    if not val_to_set:
                        # Find default
                        for o in options:
                            if o['default']:
                                val_to_set = o['text']
                                break

                    input_control = ft.Dropdown(
                        options=dropdown_opts,
                        value=val_to_set,
                        expand=2,
                        height=40,
                        content_padding=5
                    )
                else:
                    # Text/Numeric
                    val_to_set = current_val
                    if not val_to_set:
                        val_to_set = item.get('valorPorDefecto') or ""

                    input_control = ft.TextField(
                        value=val_to_set,
                        expand=2,
                        height=40,
                        content_padding=5
                    )

                self.input_controls.append({'id': item['id'], 'control': input_control})

                row_control = ft.Row([
                    ft.Text(item['nombre'], expand=2),
                    input_control,
                    ft.Text(smart_ref, color=ft.Colors.BLUE, size=12, expand=2),
                    ft.Text(item['unidad'] or "", width=60, size=12),
                ], alignment=ft.MainAxisAlignment.CENTER)

                card_rows.append(row_control)

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(group_title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLUE_900),
                        ft.Divider(),
                        ft.Column(card_rows, spacing=10)
                    ]),
                    padding=15
                ),
                margin=ft.margin.only(bottom=10)
            )
            self.result_container.controls.append(card)

        self.update()

    def save_all(self, e):
        updates = []
        for inp in self.input_controls:
            val = inp['control'].value
            # Save updates
            if val is not None:
                updates.append({'id': inp['id'], 'valor': val})

        if not updates:
            self.page_ref.open(ft.SnackBar(ft.Text("No hay datos para guardar"), bgcolor=ft.Colors.GREY))
            return

        try:
            db.update_resultado_batch(updates)
            self.page_ref.open(ft.SnackBar(ft.Text("Resultados guardados y estado actualizado"), bgcolor=ft.Colors.GREEN))
            # Refresh list to show updated status
            self.load_ordenes()
        except Exception as ex:
            print(ex)
            self.page_ref.open(ft.SnackBar(ft.Text("Error al guardar"), bgcolor=ft.Colors.RED))
