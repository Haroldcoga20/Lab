import flet as ft
from database import db
from models.medico import Medico

class MedicosView(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

        self.medicos = []
        self.selected_medico_id = None

        # Form
        self.txt_nombre = ft.TextField(label="Nombre", expand=True)
        self.txt_especialidad = ft.TextField(label="Especialidad", width=200)
        self.txt_telefono = ft.TextField(label="Teléfono", width=150)

        # Table
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Especialidad")),
                ft.DataColumn(ft.Text("Teléfono")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        # Layout
        form_row = ft.Row([self.txt_nombre, self.txt_especialidad, self.txt_telefono])

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=self.save_medico),
            ft.ElevatedButton("Limpiar", icon=ft.Icons.CLEAR, on_click=self.clear_form)
        ])

        self.controls = [
            ft.Text("Gestión de Médicos", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([form_row, actions_row]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Text("Directorio de Médicos"),
            ft.ListView(controls=[self.table], expand=True, height=400)
        ]

        self.load_data(initial=True)

    def load_data(self, initial=False):
        self.table.rows.clear()
        try:
            rows = db.get_all_medicos()
            # Assuming get_all_medicos returns tuples: id, nombre, especialidad, telefono, tieneConvenio
            # We can use Medico model if it exists or map manually.
            # Previous models/medico.py exists.
            self.medicos = [Medico.from_tuple(r) for r in rows]

            for m in self.medicos:
                self.table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(m.id))),
                        ft.DataCell(ft.Text(m.nombre)),
                        ft.DataCell(ft.Text(m.especialidad)),
                        ft.DataCell(ft.Text(m.telefono or "")),
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.Icons.EDIT, on_click=lambda e, item=m: self.edit_medico(item)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, mid=m.id, name=m.nombre: self.confirm_delete(mid, name))
                        ]))
                    ])
                )

            if not initial:
                self.update()
        except Exception as e:
            print(f"Error loading medicos: {e}")

    def edit_medico(self, m: Medico):
        self.selected_medico_id = m.id
        self.txt_nombre.value = m.nombre
        self.txt_especialidad.value = m.especialidad
        self.txt_telefono.value = m.telefono or ""
        self.update()

    def clear_form(self, e=None):
        self.selected_medico_id = None
        self.txt_nombre.value = ""
        self.txt_especialidad.value = ""
        self.txt_telefono.value = ""
        self.update()

    def save_medico(self, e):
        if not self.txt_nombre.value:
            self.page_ref.open(ft.SnackBar(ft.Text("Nombre es obligatorio"), bgcolor=ft.Colors.RED))
            return

        try:
            data = {
                'id': self.selected_medico_id,
                'nombre': self.txt_nombre.value,
                'especialidad': self.txt_especialidad.value,
                'telefono': self.txt_telefono.value
            }
            db.upsert_medico(data)
            self.clear_form()
            self.load_data()
            self.page_ref.open(ft.SnackBar(ft.Text("Médico guardado"), bgcolor=ft.Colors.GREEN))
        except Exception as ex:
            print(f"Error: {ex}")
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))

    def confirm_delete(self, medico_id, name):
        def close_dlg(e):
            self.page_ref.close(dlg)

        def delete_confirmed(e):
            self.page_ref.close(dlg)
            self.delete_medico(medico_id)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar al médico '{name}'? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Eliminar", on_click=delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page_ref.open(dlg)

    def delete_medico(self, medico_id):
        try:
            db.delete_medico(medico_id)
            self.load_data()
            self.page_ref.open(ft.SnackBar(ft.Text("Médico eliminado"), bgcolor=ft.Colors.GREEN))
        except Exception as e:
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error al eliminar: {e}"), bgcolor=ft.Colors.RED))
