import flet as ft
from database import db
from models.medico import Medico
from models.perfil_examen import PerfilExamen

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
        self.chk_convenio = ft.Checkbox(label="Tiene Convenio", on_change=self.toggle_tarifa_btn)

        self.btn_tarifas = ft.ElevatedButton(
            "Gestionar Tarifas",
            icon=ft.Icons.PRICE_CHANGE,
            disabled=True,
            on_click=self.open_tarifas_dialog
        )

        # Table
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Especialidad")),
                ft.DataColumn(ft.Text("Teléfono")),
                ft.DataColumn(ft.Text("Convenio")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        # Layout
        form_row = ft.Row([self.txt_nombre, self.txt_especialidad, self.txt_telefono])
        extra_row = ft.Row([self.chk_convenio, self.btn_tarifas])

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=self.save_medico),
            ft.ElevatedButton("Limpiar", icon=ft.Icons.CLEAR, on_click=self.clear_form)
        ])

        self.controls = [
            ft.Text("Gestión de Médicos", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([form_row, extra_row, actions_row]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Text("Directorio de Médicos"),
            ft.ListView(controls=[self.table], expand=True, height=400)
        ]

        self.load_data(initial=True)

    def toggle_tarifa_btn(self, e):
        self.btn_tarifas.disabled = not self.chk_convenio.value
        self.update()

    def load_data(self, initial=False):
        self.table.rows.clear()
        try:
            rows = db.get_all_medicos()
            self.medicos = [Medico.from_tuple(r) for r in rows]

            for m in self.medicos:
                self.table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(m.id))),
                        ft.DataCell(ft.Text(m.nombre)),
                        ft.DataCell(ft.Text(m.especialidad)),
                        ft.DataCell(ft.Text(m.telefono or "")),
                        ft.DataCell(ft.Icon(ft.Icons.CHECK if m.tieneConvenio else ft.Icons.CLOSE,
                                            color=ft.Colors.GREEN if m.tieneConvenio else ft.Colors.GREY)),
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
        self.chk_convenio.value = m.tieneConvenio
        self.btn_tarifas.disabled = not m.tieneConvenio
        self.update()

    def clear_form(self, e=None):
        self.selected_medico_id = None
        self.txt_nombre.value = ""
        self.txt_especialidad.value = ""
        self.txt_telefono.value = ""
        self.chk_convenio.value = False
        self.btn_tarifas.disabled = True
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
                'telefono': self.txt_telefono.value,
                'tieneConvenio': self.chk_convenio.value
            }
            db.upsert_medico(data)

            # If we were editing and just saved, we keep the ID selection so they can manage tarifs immediately if they want?
            # Or clear. Usually clear is standard.
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

    # --- TARIFAS DIALOG LOGIC ---
    def open_tarifas_dialog(self, e):
        if not self.selected_medico_id:
            self.page_ref.open(ft.SnackBar(ft.Text("Primero guarde o seleccione un médico"), bgcolor=ft.Colors.RED))
            return

        content = TarifasContent(self.selected_medico_id)

        dlg = ft.AlertDialog(
            title=ft.Text(f"Tarifas: Dr. {self.txt_nombre.value}"),
            content=content,
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.page_ref.close(dlg))
            ],
        )
        self.page_ref.open(dlg)

class TarifasContent(ft.Column):
    def __init__(self, medico_id):
        super().__init__()
        self.medico_id = medico_id
        self.width = 500
        self.height = 400

        # UI Elements
        self.dd_perfil = ft.Dropdown(
            label="Seleccionar Perfil",
            expand=True,
            options=[]
        )
        self.txt_precio_esp = ft.TextField(label="Precio Especial", width=100, keyboard_type=ft.KeyboardType.NUMBER)

        self.lv_tarifas = ft.ListView(expand=True, height=200, spacing=10)

        self.controls = [
            ft.Row([self.dd_perfil, self.txt_precio_esp, ft.IconButton(ft.Icons.ADD, on_click=self.add_tarifa)]),
            ft.Divider(),
            ft.Text("Tarifas Definidas", weight=ft.FontWeight.BOLD),
            ft.Container(self.lv_tarifas, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5, padding=5, expand=True)
        ]

    def did_mount(self):
        self.load_data()

    def load_data(self):
        try:
            # Load Dropdown
            perfiles = db.get_all_perfiles()
            self.dd_perfil.options = [ft.dropdown.Option(key=str(p[0]), text=p[1]) for p in perfiles]

            # Load List
            self.load_tarifas_list()
            self.update()
        except Exception as e:
            print(f"Error loading dialog data: {e}")

    def load_tarifas_list(self):
        self.lv_tarifas.controls.clear()
        rows = db.get_tarifas_medico(self.medico_id)

        if not rows:
            self.lv_tarifas.controls.append(ft.Text("No hay tarifas especiales configuradas."))
        else:
            for row in rows:
                tid, perfil_nombre, precio = row
                self.lv_tarifas.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(perfil_nombre, expand=True),
                            ft.Text(f"${precio:.2f}", weight=ft.FontWeight.BOLD),
                            ft.IconButton(
                                ft.Icons.DELETE,
                                icon_color=ft.Colors.RED,
                                icon_size=20,
                                on_click=lambda e, x=tid: self.delete_tarifa(x)
                            )
                        ]),
                        padding=5,
                        bgcolor=ft.Colors.GREY_100,
                        border_radius=5
                    )
                )

    def add_tarifa(self, e):
        pid = self.dd_perfil.value
        price = self.txt_precio_esp.value

        if not pid or not price: return

        try:
            db.upsert_tarifa_convenio(self.medico_id, int(pid), float(price))
            self.txt_precio_esp.value = ""
            self.dd_perfil.value = None
            self.load_tarifas_list()
            self.update()
        except Exception as ex:
            print(ex)

    def delete_tarifa(self, tarifa_id):
        try:
            db.delete_tarifa_convenio(tarifa_id)
            self.load_tarifas_list()
            self.update()
        except Exception as ex:
            print(ex)
