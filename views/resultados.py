import flet as ft
from database import db
from models.paciente import Paciente

class ResultadosView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True

        # Left Panel: List of Orders
        self.lv_ordenes = ft.ListView(expand=True, spacing=5, padding=10)

        # Right Panel: Results Detail
        self.current_orden_id = None
        self.lbl_orden_info = ft.Text("Seleccione una Orden", size=18, weight=ft.FontWeight.BOLD)
        self.table_resultados = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Analito")),
                ft.DataColumn(ft.Text("Rango Ref.")),
                ft.DataColumn(ft.Text("Resultado")),
                ft.DataColumn(ft.Text("Unidad")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Guardar")),
            ],
            rows=[]
        )

        # Split View
        self.controls = [
            ft.Text("Ingreso de Resultados", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                # Left Panel
                ft.Container(
                    width=300,
                    content=ft.Column([
                        ft.Text("Órdenes Pendientes", weight=ft.FontWeight.BOLD),
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
                        ft.Column([self.table_resultados], scroll=ft.ScrollMode.AUTO, expand=True)
                    ])
                )
            ], expand=True)
        ]

        self.load_ordenes(initial=True)

    def load_ordenes(self, initial=False):
        self.lv_ordenes.controls.clear()
        try:
            ordenes = db.get_ordenes_pendientes()
            if not ordenes:
                self.lv_ordenes.controls.append(ft.Text("No hay órdenes pendientes."))
            else:
                for o in ordenes:
                    # o: id, nombreCompleto, fechaCreacion, estado
                    oid = o[0]
                    nombre = o[1]
                    fecha = o[2].strftime("%d/%m %H:%M") if o[2] else ""
                    self.lv_ordenes.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.RECEIPT_LONG),
                            title=ft.Text(f"#{oid} - {nombre}"),
                            subtitle=ft.Text(f"{fecha} | {o[3]}"),
                            on_click=lambda e, x=oid: self.load_detalle_orden(x)
                        )
                    )

            if not initial:
                self.update()
        except Exception as e:
            print(f"Error loading orders: {e}")

    def load_detalle_orden(self, orden_id):
        self.current_orden_id = orden_id

        # Get Header Info
        header_tuple = db.get_orden_header(orden_id)
        # header: id, pacienteId, ...
        paciente_tuple = db.get_paciente(header_tuple[1])
        paciente = Paciente.from_tuple(paciente_tuple)

        self.lbl_orden_info.value = f"Orden #{orden_id} - {paciente.nombreCompleto} ({paciente.edad} {paciente.unidadEdad})"

        # Get Results Rows
        results = db.get_resultados_orden(orden_id)
        # results columns: id, analitoId, nombre, valorResultado, estado, unidad, tipoDato

        self.table_resultados.rows.clear()

        for r in results:
            rid = r[0]
            aid = r[1]
            a_nombre = r[2]
            val = r[3] or ""
            estado = r[4]
            unidad = r[5] or ""
            tipo_dato = r[6]

            # Calculate Reference Range String
            rango_str = db.get_rango_referencia_string(aid, paciente.genero, paciente.edad, paciente.unidadEdad)

            # Input Control
            txt_resultado = ft.TextField(value=val, width=150, on_submit=lambda e, rid=rid: self.save_result_row(rid, e.control.value))

            self.table_resultados.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(a_nombre)),
                    ft.DataCell(ft.Text(rango_str, color=ft.Colors.BLUE)),
                    ft.DataCell(txt_resultado),
                    ft.DataCell(ft.Text(unidad)),
                    ft.DataCell(ft.Text(estado)),
                    ft.DataCell(ft.IconButton(ft.Icons.SAVE, icon_color=ft.Colors.GREEN,
                                              on_click=lambda e, r=rid, t=txt_resultado: self.save_result_row(r, t.value))),
                ])
            )

        self.update()

    def save_result_row(self, result_id, value):
        try:
            db.update_resultado(result_id, value)
            self.page.snack_bar = ft.SnackBar(ft.Text("Resultado guardado"), bgcolor=ft.Colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()

            # Optional: Refresh status text in row without reloading whole table?
            # For simplicity, we can reload or just leave it.
            # Updating 'estado' cell visually would require keeping ref to cell.
            # Let's reload to be safe and show 'Ingresado'.
            # But reload clears focus. User might be tab-ing through.
            # Ideally we don't reload whole table.
            # We'll just trust the snackbar for now.

        except Exception as e:
            print(f"Error saving result: {e}")
            self.page.snack_bar = ft.SnackBar(ft.Text("Error al guardar"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()
