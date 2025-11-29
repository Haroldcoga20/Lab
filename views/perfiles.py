import flet as ft
from database import db
from models.perfil_examen import PerfilExamen
from models.analito import Analito

class PerfilesView(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.perfiles = []
        self.selected_perfil_id = None
        self.all_analitos = []

        # Form Controls
        self.txt_nombre = ft.TextField(label="Nombre Perfil", expand=True)
        self.dd_categoria = ft.Dropdown(
            label="Categoría",
            options=[
                ft.dropdown.Option("Hematología"),
                ft.dropdown.Option("Química Sanguínea"),
                ft.dropdown.Option("Inmunología"),
                ft.dropdown.Option("Paquetes"),
                ft.dropdown.Option("Otros"),
            ],
            expand=True
        )
        self.txt_precio = ft.TextField(label="Precio Estándar", width=150, keyboard_type=ft.KeyboardType.NUMBER)

        # Double List Selector for Analitos
        self.lv_disponibles = ft.ListView(expand=True, height=200)
        self.lv_asignados = ft.ListView(expand=True, height=200)

        self.disponibles_items = [] # list of Analito objects
        self.asignados_items = [] # list of Analito objects

        # Data Table
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Categoría")),
                ft.DataColumn(ft.Text("Precio")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

    def build(self):
        self.load_data()

        form_row = ft.Row([self.txt_nombre, self.dd_categoria, self.txt_precio])

        # Selector UI
        selector = ft.Row([
            ft.Column([
                ft.Text("Analitos Disponibles"),
                ft.Container(self.lv_disponibles, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
            ], expand=True),
            ft.Column([
                ft.IconButton(ft.icons.ARROW_FORWARD, on_click=self.add_analito_to_profile),
                ft.IconButton(ft.icons.ARROW_BACK, on_click=self.remove_analito_from_profile)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Column([
                ft.Text("Analitos Asignados"),
                ft.Container(self.lv_asignados, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
            ], expand=True)
        ], height=250)

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar Perfil", on_click=self.save_perfil),
            ft.ElevatedButton("Limpiar", on_click=self.clear_form)
        ])

        return ft.Column([
            ft.Text("Gestión de Perfiles de Examen", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([form_row, ft.Divider(), selector, actions_row]),
                padding=10,
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Text("Lista de Perfiles"),
            ft.ListView(controls=[self.table], expand=True, height=300)
        ], scroll=ft.ScrollMode.ALWAYS, expand=True)

    def load_data(self):
        self.table.rows.clear()
        try:
            # Load Perfiles
            rows = db.get_all_perfiles()
            self.perfiles = [PerfilExamen.from_tuple(r) for r in rows]

            for p in self.perfiles:
                self.table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(p.id))),
                        ft.DataCell(ft.Text(p.nombre)),
                        ft.DataCell(ft.Text(p.categoria)),
                        ft.DataCell(ft.Text(str(p.precioEstandar))),
                        ft.DataCell(ft.IconButton(ft.icons.EDIT, on_click=lambda e, item=p: self.edit_perfil(item))),
                    ])
                )

            # Load All Analitos for the selector
            a_rows = db.get_all_analitos()
            self.all_analitos = [Analito.from_tuple(r) for r in a_rows]

            self.refresh_selector()
            self.update()

        except Exception as e:
            print(f"Error loading perfiles: {e}")

    def refresh_selector(self):
        # Clear Lists
        self.lv_disponibles.controls.clear()
        self.lv_asignados.controls.clear()

        # Helper to create checkbox tiles
        def create_tile(analito, is_assigned):
            return ft.Checkbox(
                label=analito.nombre,
                value=False,
                data=analito.id  # Store ID in data
            )

        # Separate Assigned vs Available
        # If editing, filter out assigned. If new, all are available.
        assigned_ids = [a.id for a in self.asignados_items]

        for analito in self.all_analitos:
            if analito.id in assigned_ids:
                # It is assigned, don't show in available, show in assigned logic handled by self.asignados_items loop
                pass
            else:
                self.lv_disponibles.controls.append(create_tile(analito, False))

        for analito in self.asignados_items:
             self.lv_asignados.controls.append(create_tile(analito, True))

        self.update()

    def add_analito_to_profile(self, e):
        # Move checked items from available to assigned
        to_move = []
        for c in self.lv_disponibles.controls:
            if c.value:
                # Find the analito obj
                analito = next((a for a in self.all_analitos if a.id == c.data), None)
                if analito:
                    self.asignados_items.append(analito)
        self.refresh_selector()

    def remove_analito_from_profile(self, e):
        # Move checked items from assigned to available
        to_remove_ids = []
        for c in self.lv_asignados.controls:
            if c.value:
                to_remove_ids.append(c.data)

        self.asignados_items = [a for a in self.asignados_items if a.id not in to_remove_ids]
        self.refresh_selector()

    def edit_perfil(self, perfil: PerfilExamen):
        self.selected_perfil_id = perfil.id
        self.txt_nombre.value = perfil.nombre
        self.dd_categoria.value = perfil.categoria
        self.txt_precio.value = str(perfil.precioEstandar)

        # Load details
        rows = db.get_perfil_analitos(perfil.id)
        self.asignados_items = [Analito.from_tuple(r) for r in rows]

        self.refresh_selector()
        self.update()

    def clear_form(self, e=None):
        self.selected_perfil_id = None
        self.txt_nombre.value = ""
        self.dd_categoria.value = None
        self.txt_precio.value = ""
        self.asignados_items = []
        self.refresh_selector()
        self.update()

    def save_perfil(self, e):
        try:
            data = {
                'id': self.selected_perfil_id,
                'nombre': self.txt_nombre.value,
                'categoria': self.dd_categoria.value,
                'precioEstandar': self.txt_precio.value
            }
            analito_ids = [a.id for a in self.asignados_items]

            db.upsert_perfil(data, analito_ids)

            self.clear_form()
            self.load_data()

            self.page.snack_bar = ft.SnackBar(ft.Text("Perfil guardado correctamente"), bgcolor=ft.colors.GREEN)
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as ex:
            print(f"Error saving perfil: {ex}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.colors.ERROR)
            self.page.snack_bar.open = True
            self.page.update()
