import flet as ft
from database import db
from views.reporte import generar_pdf_orden

class OrdenesView(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

        # Filter Toolbar Controls
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

        # List of Orders
        self.lv_ordenes = ft.ListView(expand=True, spacing=5, padding=10)

        self.controls = [
            ft.Text("Gestión de Órdenes e Informes", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Row([self.txt_search, self.dd_filter_medico, self.dd_filter_estado, self.btn_clear_filters]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            self.lv_ordenes
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
            # Get filters
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
                    fecha = o[2].strftime("%d/%m/%Y %H:%M") if o[2] else ""
                    estado_orden = o[3]
                    nombre_medico = o[4] or "Particular"

                    status_color = ft.Colors.GREEN if estado_orden == 'Completado' else ft.Colors.ORANGE

                    self.lv_ordenes.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.RECEIPT_LONG),
                                ft.Column([
                                    ft.Text(f"Orden #{oid} - {nombre}", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Médico: {nombre_medico}", size=12, italic=True),
                                    ft.Text(f"{fecha} | Estado: {estado_orden}", size=12, color=status_color, weight=ft.FontWeight.BOLD)
                                ], expand=True),
                                ft.Row([
                                    ft.IconButton(
                                        icon=ft.Icons.PRINT,
                                        tooltip="Configurar Impresión",
                                        icon_color=ft.Colors.BLUE,
                                        on_click=lambda e, x=oid: self.open_config_dialog(x)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Eliminar Orden",
                                        icon_color=ft.Colors.RED,
                                        on_click=lambda e, x=oid: self.confirm_delete(x)
                                    )
                                ])
                            ]),
                            padding=10,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=5
                        )
                    )

            if not initial:
                self.update()
        except Exception as e:
            print(f"Error loading orders: {e}")

    def confirm_delete(self, orden_id):
        def close_dlg(e):
            self.page_ref.close(dlg)

        def delete_confirmed(e):
            self.page_ref.close(dlg)
            self.delete_orden_click(orden_id)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar la Orden #{orden_id}? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Eliminar", on_click=delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page_ref.open(dlg)

    def delete_orden_click(self, orden_id):
        try:
            db.delete_orden(orden_id)
            self.page_ref.open(ft.SnackBar(ft.Text("Orden eliminada"), bgcolor=ft.Colors.GREEN))
            self.load_ordenes()
        except Exception as e:
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error al eliminar orden: {e}"), bgcolor=ft.Colors.RED))

    def open_config_dialog(self, orden_id):
        grouped_data = db.get_resultados_grouped(orden_id)
        if not grouped_data:
            self.page_ref.open(ft.SnackBar(ft.Text("Esta orden no tiene resultados."), bgcolor=ft.Colors.RED))
            return

        dialog = ConfigImpresionDialog(orden_id, grouped_data, self.page_ref)
        self.page_ref.open(dialog.dialog)

class ConfigImpresionDialog:
    def __init__(self, orden_id, grouped_data, page):
        self.orden_id = orden_id
        self.page = page

        self.config_items = []
        for g in grouped_data:
            self.config_items.append({
                'data': g,
                'include': True,
                'page_break': False
            })

        self.chk_firma = ft.Checkbox(label="Incluir Firma Digital", value=True)

        self.list_view = ft.ListView(expand=True)
        self.render_list()

        self.dialog = ft.AlertDialog(
            title=ft.Text(f"Configurar Impresión - Orden #{orden_id}"),
            content=ft.Container(
                content=ft.Column([
                    self.chk_firma,
                    ft.Divider(),
                    self.list_view
                ]),
                width=600,
                height=400
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.close),
                ft.ElevatedButton("GENERAR PDF", on_click=self.generate_pdf, icon=ft.Icons.PICTURE_AS_PDF)
            ]
        )

    def render_list(self):
        self.list_view.controls.clear()

        for i, item in enumerate(self.config_items):
            title = item['data']['title']
            gtype = item['data']['type']

            chk = ft.Checkbox(value=item['include'], on_change=lambda e, idx=i: self.toggle_include(idx, e.control.value))
            sw_break = ft.Switch(value=item['page_break'], on_change=lambda e, idx=i: self.toggle_break(idx, e.control.value))

            btn_up = ft.IconButton(ft.Icons.ARROW_UPWARD, disabled=(i==0), on_click=lambda e, idx=i: self.move_item(idx, -1))
            btn_down = ft.IconButton(ft.Icons.ARROW_DOWNWARD, disabled=(i==len(self.config_items)-1), on_click=lambda e, idx=i: self.move_item(idx, 1))

            row = ft.Row([
                ft.Row([chk, ft.Text(f"{title} ({gtype})", weight=ft.FontWeight.BOLD)], expand=True),
                ft.VerticalDivider(),
                ft.Text("Salto Pág:"),
                sw_break,
                ft.VerticalDivider(),
                btn_up,
                btn_down
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            container = ft.Container(
                content=row,
                padding=5,
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
                bgcolor=ft.Colors.WHITE if item['include'] else ft.Colors.GREY_100
            )
            self.list_view.controls.append(container)

        if self.dialog.open:
            self.dialog.update()

    def toggle_include(self, index, value):
        self.config_items[index]['include'] = value
        self.render_list()

    def toggle_break(self, index, value):
        self.config_items[index]['page_break'] = value

    def move_item(self, index, direction):
        new_index = index + direction
        if 0 <= new_index < len(self.config_items):
            self.config_items[index], self.config_items[new_index] = self.config_items[new_index], self.config_items[index]
            self.render_list()

    def close(self, e):
        self.page.close(self.dialog)

    def generate_pdf(self, e):
        clean_config = []
        for item in self.config_items:
            clean_config.append({
                'title': item['data']['title'],
                'type': item['data']['type'],
                'items': item['data']['items'],
                'include': item['include'],
                'page_break': item['page_break']
            })

        success, msg = generar_pdf_orden(self.orden_id, clean_config, include_signature=self.chk_firma.value)

        color = ft.Colors.GREEN if success else ft.Colors.RED
        self.page.open(ft.SnackBar(ft.Text(msg), bgcolor=color))
        if success:
            self.page.close(self.dialog)
