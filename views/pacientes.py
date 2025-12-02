import flet as ft
from database import db
from models.paciente import Paciente

class PacientesView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

        self.pacientes = []
        self.selected_paciente_id = None

        # Pagination State
        self.limit = 50
        self.offset = 0
        self.current_page = 1

        # Form Controls
        self.txt_nombre = ft.TextField(label="Nombre Completo", expand=True)
        self.txt_dni = ft.TextField(label="DNI", width=150)
        self.dd_genero = ft.Dropdown(
            label="Género",
            options=[
                ft.dropdown.Option("Masculino"),
                ft.dropdown.Option("Femenino"),
            ],
            width=150
        )
        self.txt_telefono = ft.TextField(label="Teléfono", width=150)
        self.txt_edad = ft.TextField(label="Edad", width=100, keyboard_type=ft.KeyboardType.NUMBER)
        self.dd_unidad_edad = ft.Dropdown(
            label="Unidad",
            options=[
                ft.dropdown.Option("Años"),
                ft.dropdown.Option("Meses"),
                ft.dropdown.Option("Días"),
            ],
            value="Años",
            width=100
        )

        # Search Control
        self.txt_search = ft.TextField(
            prefix_icon=ft.Icons.SEARCH,
            hint_text="Buscar por nombre o DNI (Enter)",
            expand=True,
            on_submit=self.perform_search
        )

        # Data Table
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("DNI")),
                ft.DataColumn(ft.Text("Edad")),
                ft.DataColumn(ft.Text("Género")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        # Pagination Controls
        self.btn_prev = ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=self.prev_page, disabled=True)
        self.btn_next = ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=self.next_page)
        self.lbl_page = ft.Text("Página 1")

        # Layout
        form_row1 = ft.Row([self.txt_nombre, self.txt_dni])
        form_row2 = ft.Row([self.txt_edad, self.dd_unidad_edad, self.dd_genero, self.txt_telefono])

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=self.check_duplicates_and_save),
            ft.ElevatedButton("Limpiar", icon=ft.Icons.CLEAR, on_click=self.clear_form)
        ])

        self.controls = [
            ft.Text("Gestión de Pacientes", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([form_row1, form_row2, actions_row]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Row([self.txt_search]),
            ft.ListView(controls=[self.table], expand=True, height=400),
            ft.Row([self.btn_prev, self.lbl_page, self.btn_next], alignment=ft.MainAxisAlignment.CENTER)
        ]

    def did_mount(self):
        self.load_data()

    def perform_search(self, e):
        self.offset = 0
        self.current_page = 1
        self.load_data()

    def load_data(self):
        self.table.rows.clear()
        search_query = self.txt_search.value
        try:
            rows = db.get_pacientes_paginated(self.limit, self.offset, search_query)
            self.pacientes = [Paciente.from_tuple(r) for r in rows]

            for p in self.pacientes:
                self.table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(p.id))),
                        ft.DataCell(ft.Text(p.nombreCompleto)),
                        ft.DataCell(ft.Text(p.dni or "")),
                        ft.DataCell(ft.Text(f"{p.edad} {p.unidadEdad}")),
                        ft.DataCell(ft.Text(p.genero)),
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.Icons.HISTORY, icon_color=ft.Colors.BLUE, tooltip="Ver Historial", on_click=lambda e, pid=p.id: self.open_historial(pid)),
                            ft.IconButton(ft.Icons.EDIT, on_click=lambda e, item=p: self.edit_paciente(item)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, pid=p.id, name=p.nombreCompleto: self.confirm_delete(pid, name))
                        ])),
                    ])
                )

            # Update pagination buttons
            total_records = db.count_pacientes(search_query)
            self.btn_prev.disabled = (self.offset == 0)
            self.btn_next.disabled = (self.offset + self.limit >= total_records)
            self.lbl_page.value = f"Página {self.current_page}"

            self.update()
        except Exception as e:
            print(f"Error loading pacientes: {e}")

    def prev_page(self, e):
        if self.offset >= self.limit:
            self.offset -= self.limit
            self.current_page -= 1
            self.load_data()

    def next_page(self, e):
        self.offset += self.limit
        self.current_page += 1
        self.load_data()

    def edit_paciente(self, p: Paciente):
        self.selected_paciente_id = p.id
        self.txt_nombre.value = p.nombreCompleto
        self.txt_dni.value = p.dni or ""
        self.txt_edad.value = str(p.edad)
        self.dd_unidad_edad.value = p.unidadEdad
        self.dd_genero.value = p.genero
        self.txt_telefono.value = p.telefono or ""

        self.txt_nombre.border_color = None
        self.txt_edad.border_color = None
        self.dd_unidad_edad.border_color = None
        self.dd_genero.border_color = None

        self.update()

    def confirm_delete(self, paciente_id, name):
        def close_dlg(e): self.page_ref.close(dlg)
        def delete_confirmed(e):
            self.page_ref.close(dlg)
            self.delete_paciente_click(paciente_id)
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Eliminar '{name}'?"),
            actions=[ft.TextButton("Cancelar", on_click=close_dlg), ft.TextButton("Eliminar", on_click=delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.RED))]
        )
        self.page_ref.open(dlg)

    def delete_paciente_click(self, paciente_id):
        try:
            db.delete_paciente(paciente_id)
            self.page_ref.open(ft.SnackBar(ft.Text("Paciente eliminado"), bgcolor=ft.Colors.GREEN))
            self.load_data()
        except Exception as e:
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error: {e}"), bgcolor=ft.Colors.RED))

    def clear_form(self, e=None):
        self.selected_paciente_id = None
        self.txt_nombre.value = ""
        self.txt_dni.value = ""
        self.txt_edad.value = ""
        self.dd_unidad_edad.value = "Años"
        self.dd_genero.value = None
        self.txt_telefono.value = ""
        self.update()

    def check_duplicates_and_save(self, e):
        # 1. Basic Validation
        errors = False
        if not self.txt_nombre.value:
            self.txt_nombre.border_color = ft.Colors.RED
            errors = True
        else: self.txt_nombre.border_color = None

        if not self.txt_edad.value:
            self.txt_edad.border_color = ft.Colors.RED
            errors = True
        else: self.txt_edad.border_color = None

        if not self.dd_unidad_edad.value:
            self.dd_unidad_edad.border_color = ft.Colors.RED
            errors = True
        else: self.dd_unidad_edad.border_color = None

        if not self.dd_genero.value:
            self.dd_genero.border_color = ft.Colors.RED
            errors = True
        else: self.dd_genero.border_color = None

        if errors:
            self.page_ref.open(ft.SnackBar(ft.Text("Por favor complete los campos obligatorios"), bgcolor=ft.Colors.RED))
            self.update()
            return

        # 2. Check Duplicates
        if self.selected_paciente_id:
            self.save_paciente()
            return

        dupes = db.check_paciente_duplicates(self.txt_dni.value, self.txt_nombre.value)
        if dupes:
            self.show_duplicate_warning(dupes)
        else:
            self.save_paciente()

    def show_duplicate_warning(self, dupes):
        list_dupes = ft.ListView(height=150)
        for d in dupes:
            # d tuple structure: id, nombre, edad, unidad, genero...
            pid, pname, pedad, punidad, pgen = d[0], d[1], d[2], d[3], d[4]
            list_dupes.controls.append(
                ft.ListTile(
                    title=ft.Text(pname, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"ID: {pid} | {pedad} {punidad} | {pgen}"),
                    leading=ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE)
                )
            )

        def close_warn(e): self.page_ref.close(dlg)
        def force_save(e):
            self.page_ref.close(dlg)
            self.save_paciente()

        dlg = ft.AlertDialog(
            title=ft.Text("Posibles Duplicados Encontrados"),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    ft.Text("Se encontraron pacientes similares:", color=ft.Colors.RED),
                    ft.Divider(),
                    list_dupes,
                    ft.Divider(),
                    ft.Text("¿Desea registrarlo de todas formas?")
                ])
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=close_warn),
                ft.ElevatedButton("Es una persona nueva (Crear)", on_click=force_save, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
            ]
        )
        self.page_ref.open(dlg)

    def save_paciente(self):
        try:
            data = {
                'id': self.selected_paciente_id,
                'nombreCompleto': self.txt_nombre.value,
                'edad': self.txt_edad.value,
                'unidadEdad': self.dd_unidad_edad.value,
                'genero': self.dd_genero.value,
                'dni': self.txt_dni.value,
                'telefono': self.txt_telefono.value
            }
            db.upsert_paciente(data)
            self.clear_form()
            self.load_data()
            self.page_ref.open(ft.SnackBar(ft.Text("Paciente guardado"), bgcolor=ft.Colors.GREEN))
        except Exception as ex:
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))

    def open_historial(self, paciente_id):
        from views.historial import HistorialDialog
        dialog = HistorialDialog(paciente_id, self.page_ref)
        self.page_ref.open(dialog.dialog)
