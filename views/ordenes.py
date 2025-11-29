import flet as ft
from database import db
from views.reporte import generar_pdf_orden

class OrdenesView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

        # List of Orders
        self.lv_ordenes = ft.ListView(expand=True, spacing=5, padding=10)

        self.controls = [
            ft.Text("Gestión de Órdenes e Informes", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            self.lv_ordenes
        ]

        self.load_ordenes(initial=True)

    def load_ordenes(self, initial=False):
        self.lv_ordenes.controls.clear()
        try:
            # We need all orders, maybe filter by date? For now get all from a new db method or reuse pending?
            # User wants "Gestión de Órdenes". Probably complete history?
            # Let's use get_all_ordenes from db (I added it in step 2).
            ordenes = db.get_all_ordenes()

            if not ordenes:
                self.lv_ordenes.controls.append(ft.Text("No hay órdenes registradas."))
            else:
                for o in ordenes:
                    oid = o[0]
                    nombre = o[1]
                    fecha = o[2].strftime("%d/%m/%Y %H:%M") if o[2] else ""
                    estado = o[3]

                    self.lv_ordenes.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.RECEIPT_LONG),
                                ft.Column([
                                    ft.Text(f"Orden #{oid} - {nombre}", weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{fecha} | Estado: {estado}", size=12, color=ft.Colors.GREY)
                                ], expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.PRINT,
                                    tooltip="Configurar Impresión",
                                    icon_color=ft.Colors.BLUE,
                                    on_click=lambda e, x=oid: self.open_config_dialog(x)
                                )
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

    def open_config_dialog(self, orden_id):
        # 1. Fetch Data
        grouped_data = db.get_resultados_grouped(orden_id)
        if not grouped_data:
            self.page.open(ft.SnackBar(ft.Text("Esta orden no tiene resultados."), bgcolor=ft.Colors.RED))
            return

        # 2. Create Dialog
        dialog = ConfigImpresionDialog(orden_id, grouped_data, self.page)
        self.page.open(dialog.dialog)

class ConfigImpresionDialog:
    def __init__(self, orden_id, grouped_data, page):
        self.orden_id = orden_id
        self.page = page
        # grouped_data structure: [{'type':.., 'title':.., 'items':..}]
        # We wrap them to manage state: {'data': group, 'include': bool, 'page_break': bool, 'control_row': Row}

        self.config_items = []
        for g in grouped_data:
            self.config_items.append({
                'data': g,
                'include': True,
                'page_break': False
            })

        self.list_view = ft.ListView(expand=True)
        self.render_list()

        self.dialog = ft.AlertDialog(
            title=ft.Text(f"Configurar Impresión - Orden #{orden_id}"),
            content=ft.Container(
                content=self.list_view,
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

            # Checkbox Include
            chk = ft.Checkbox(value=item['include'], on_change=lambda e, idx=i: self.toggle_include(idx, e.control.value))

            # Switch Page Break
            sw_break = ft.Switch(value=item['page_break'], on_change=lambda e, idx=i: self.toggle_break(idx, e.control.value))

            # Reorder Buttons
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

        if self.dialog.open: # Only update if already open, else handled by page.open logic
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
        # Prepare clean config list for report engine
        clean_config = []
        for item in self.config_items:
            clean_config.append({
                'title': item['data']['title'],
                'type': item['data']['type'],
                'items': item['data']['items'],
                'include': item['include'],
                'page_break': item['page_break']
            })

        success, msg = generar_pdf_orden(self.orden_id, clean_config)

        color = ft.Colors.GREEN if success else ft.Colors.RED
        self.page.open(ft.SnackBar(ft.Text(msg), bgcolor=color))
        if success:
            self.page.close(self.dialog)
