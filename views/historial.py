import flet as ft
from database import db
from models.paciente import Paciente

class HistorialDialog:
    def __init__(self, paciente_id, page):
        self.paciente_id = paciente_id
        self.page_ref = page

        # Left Panel: Dates
        self.lv_dates = ft.ListView(expand=True, spacing=5, padding=10)

        # Right Panel: Results Detail (Read Only)
        self.lbl_orden_info = ft.Text("Seleccione una fecha", size=16, weight=ft.FontWeight.BOLD)
        self.result_container = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)

        self.dialog = ft.AlertDialog(
            title=ft.Text("Historial Clínico"),
            content=ft.Container(
                width=800,
                height=500,
                content=ft.Row([
                    # Left
                    ft.Container(
                        width=250,
                        content=ft.Column([
                            ft.Text("Atenciones Previas", weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            self.lv_dates
                        ]),
                        border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300))
                    ),
                    # Right
                    ft.Container(
                        expand=True,
                        padding=15,
                        content=ft.Column([
                            self.lbl_orden_info,
                            ft.Divider(),
                            self.result_container
                        ])
                    )
                ])
            ),
            actions=[ft.TextButton("Cerrar", on_click=self.close_dialog)]
        )

        self.load_history()

    def load_history(self):
        self.lv_dates.controls.clear()
        try:
            history = db.get_historial_fechas(self.paciente_id)

            if not history:
                self.lv_dates.controls.append(ft.Text("Sin historial."))
            else:
                for h in history:
                    oid = h[0]
                    fecha = h[1].strftime("%d/%m/%Y") if h[1] else "S/F"

                    self.lv_dates.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.BLUE),
                            title=ft.Text(fecha),
                            subtitle=ft.Text(f"Orden #{oid}"),
                            on_click=lambda e, x=oid: self.load_detail(x)
                        )
                    )

            if self.dialog.open:
                self.dialog.update()
        except Exception as e:
            print(f"Error loading history: {e}")

    def load_detail(self, orden_id):
        self.result_container.controls.clear()
        self.lbl_orden_info.value = f"Detalle Orden #{orden_id}"

        try:
            grouped_data = db.get_resultados_grouped(orden_id)

            for group in grouped_data:
                group_title = group['title']
                items = group['items']

                card_rows = []
                card_rows.append(ft.Row([
                    ft.Text("Analito", weight=ft.FontWeight.BOLD, expand=2),
                    ft.Text("Resultado", weight=ft.FontWeight.BOLD, expand=2),
                    ft.Text("Unid.", weight=ft.FontWeight.BOLD, width=60),
                ]))
                card_rows.append(ft.Divider())

                current_sub = None

                for item in items:
                    val = str(item['valor'] or "").strip()

                    # Ghost Logic for History too? Usually history shows everything recorded?
                    # User requirement: "REPORTE PDF (views/reporte.py) Y HISTORIAL (views/historial.py): Lógica Fantasma".
                    # So yes, hide empty unless "0".
                    if not val and val != "0": continue

                    # Subtitle Grouping
                    subtitulo = item.get('subtituloReporte')
                    if subtitulo and subtitulo != current_sub:
                        card_rows.append(ft.Text(subtitulo, weight=ft.FontWeight.BOLD))
                        current_sub = subtitulo

                    row_control = ft.Row([
                        ft.Text(item['nombre'], expand=2),
                        ft.Text(val, weight=ft.FontWeight.BOLD, expand=2),
                        ft.Text(item['unidad'] or "", width=60, size=12),
                    ], alignment=ft.MainAxisAlignment.CENTER)

                    card_rows.append(row_control)

                # Only add card if it has content (rows > 2 because header+divider)
                if len(card_rows) > 2:
                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(group_title, weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLUE_900),
                                ft.Divider(),
                                ft.Column(card_rows, spacing=5)
                            ]),
                            padding=10
                        ),
                        margin=ft.margin.only(bottom=5)
                    )
                    self.result_container.controls.append(card)

            if self.dialog.open:
                self.dialog.update()

        except Exception as e:
            print(f"Error loading detail: {e}")

    def close_dialog(self, e):
        self.page_ref.close(self.dialog)
