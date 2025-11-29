import flet as ft
from database import db
from models.paciente import Paciente

class PacientesView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

        self.pacientes = []
        self.selected_paciente_id = None

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

        # Pediatric Fields
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

        # Layout
        form_row1 = ft.Row([self.txt_nombre, self.txt_dni])
        form_row2 = ft.Row([self.txt_edad, self.dd_unidad_edad, self.dd_genero, self.txt_telefono])

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar", icon=ft.Icons.SAVE, on_click=self.save_paciente),
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
            ft.Text("Directorio de Pacientes"),
            ft.ListView(controls=[self.table], expand=True, height=400)
        ]

        self.load_data(initial=True)

    def load_data(self, initial=False):
        self.table.rows.clear()
        try:
            rows = db.get_all_pacientes()
            self.pacientes = [Paciente.from_tuple(r) for r in rows]

            for p in self.pacientes:
                self.table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(p.id))),
                        ft.DataCell(ft.Text(p.nombreCompleto)),
                        ft.DataCell(ft.Text(p.dni or "")),
                        ft.DataCell(ft.Text(f"{p.edad} {p.unidadEdad}")),
                        ft.DataCell(ft.Text(p.genero)),
                        ft.DataCell(ft.IconButton(ft.Icons.EDIT, on_click=lambda e, item=p: self.edit_paciente(item))),
                    ])
                )

            if not initial:
                self.update()
        except Exception as e:
            print(f"Error loading pacientes: {e}")

    def edit_paciente(self, p: Paciente):
        self.selected_paciente_id = p.id
        self.txt_nombre.value = p.nombreCompleto
        self.txt_dni.value = p.dni or ""
        self.txt_edad.value = str(p.edad)
        self.dd_unidad_edad.value = p.unidadEdad
        self.dd_genero.value = p.genero
        self.txt_telefono.value = p.telefono or ""

        # Reset borders
        self.txt_nombre.border_color = None
        self.txt_edad.border_color = None
        self.dd_unidad_edad.border_color = None
        self.dd_genero.border_color = None

        self.update()

    def clear_form(self, e=None):
        self.selected_paciente_id = None
        self.txt_nombre.value = ""
        self.txt_dni.value = ""
        self.txt_edad.value = ""
        self.dd_unidad_edad.value = "Años"
        self.dd_genero.value = None
        self.txt_telefono.value = ""

        # Reset borders
        self.txt_nombre.border_color = None
        self.txt_edad.border_color = None
        self.dd_unidad_edad.border_color = None
        self.dd_genero.border_color = None

        self.update()

    def save_paciente(self, e):
        # Visual Validation
        errors = False

        if not self.txt_nombre.value:
            self.txt_nombre.border_color = ft.Colors.RED
            errors = True
        else:
            self.txt_nombre.border_color = None

        if not self.txt_edad.value:
            self.txt_edad.border_color = ft.Colors.RED
            errors = True
        else:
            self.txt_edad.border_color = None

        if not self.dd_unidad_edad.value:
            self.dd_unidad_edad.border_color = ft.Colors.RED
            errors = True
        else:
            self.dd_unidad_edad.border_color = None

        if not self.dd_genero.value:
            self.dd_genero.border_color = ft.Colors.RED
            errors = True
        else:
            self.dd_genero.border_color = None

        if errors:
            self.page.open(ft.SnackBar(ft.Text("Por favor complete los campos obligatorios"), bgcolor=ft.Colors.RED))
            self.update()
            return

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

            self.page.open(ft.SnackBar(ft.Text("Paciente guardado"), bgcolor=ft.Colors.GREEN))

        except Exception as ex:
            print(f"Error: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"Error al guardar: {ex}"), bgcolor=ft.Colors.RED))
