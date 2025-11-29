import flet as ft
from database import db
from models.perfil_examen import PerfilExamen
from models.analito import Analito

class PerfilesView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

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

        # Layout Building
        form_row = ft.Row([self.txt_nombre, self.dd_categoria, self.txt_precio])

        # Buttons for Assigned List
        self.btn_up = ft.IconButton(ft.Icons.ARROW_UPWARD, on_click=lambda e: self.move_item(-1))
        self.btn_down = ft.IconButton(ft.Icons.ARROW_DOWNWARD, on_click=lambda e: self.move_item(1))

        # Selector UI
        selector = ft.Row([
            ft.Column([
                ft.Text("Analitos Disponibles"),
                ft.Container(self.lv_disponibles, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
            ], expand=True),
            ft.Column([
                ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=self.add_analito_to_profile),
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.remove_analito_from_profile)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Column([
                ft.Text("Analitos Asignados"),
                ft.Row([
                    ft.Container(self.lv_asignados, border=ft.border.all(1, "grey"), border_radius=5, expand=True),
                    ft.Column([self.btn_up, self.btn_down], alignment=ft.MainAxisAlignment.CENTER)
                ], expand=True)
            ], expand=True)
        ], height=250)

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar Perfil", on_click=self.save_perfil),
            ft.ElevatedButton("Limpiar", on_click=self.clear_form)
        ])

        self.controls = [
            ft.Text("Gestión de Perfiles de Examen", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([form_row, ft.Divider(), selector, actions_row]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Text("Lista de Perfiles"),
            ft.ListView(controls=[self.table], expand=True, height=300)
        ]

        self.load_data(initial=True)

    def load_data(self, initial=False):
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
                        ft.DataCell(ft.IconButton(ft.Icons.EDIT, on_click=lambda e, item=p: self.edit_perfil(item))),
                    ])
                )

            # Load All Analitos for the selector
            a_rows = db.get_all_analitos()
            self.all_analitos = [Analito.from_tuple(r) for r in a_rows]

            self.refresh_selector(initial=initial)

            if not initial:
                self.update()

        except Exception as e:
            print(f"Error loading perfiles: {e}")

    def refresh_selector(self, initial=False):
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
                pass
            else:
                self.lv_disponibles.controls.append(create_tile(analito, False))

        for analito in self.asignados_items:
             self.lv_asignados.controls.append(create_tile(analito, True))

        if not initial:
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

    def move_item(self, direction):
        # Find selected item in assigned list (checked)
        # Assuming single selection move for simplicity, or move all checked?
        # Standard UX: Move focused/selected item. Checkboxes are for adding/removing.
        # Let's interpret Checkboxes in assigned list as "Selected for Move" too.

        # Identify indices to move
        indices_to_move = []
        for i, c in enumerate(self.lv_asignados.controls):
            if c.value:
                indices_to_move.append(i)

        if not indices_to_move: return

        # Sort indices based on direction to avoid overwriting during swap
        if direction == -1: # Up
            indices_to_move.sort()
        else: # Down
            indices_to_move.sort(reverse=True)

        for i in indices_to_move:
            new_i = i + direction
            if 0 <= new_i < len(self.asignados_items):
                # Swap in data list
                self.asignados_items[i], self.asignados_items[new_i] = self.asignados_items[new_i], self.asignados_items[i]

        self.refresh_selector()

    def edit_perfil(self, perfil: PerfilExamen):
        self.selected_perfil_id = perfil.id
        self.txt_nombre.value = perfil.nombre
        self.dd_categoria.value = perfil.categoria
        self.txt_precio.value = str(perfil.precioEstandar)

        # Load details sorted by order (default db query might be random if not ordered)
        # We need a method that gets them ordered.
        # database.py -> get_perfil_analitos: currently selects *. Order by?
        # We should update database to order by `orden`.

        rows = db.get_perfil_analitos(perfil.id)
        # Sort rows based on `orden` column if it exists in tuple?
        # `get_perfil_analitos` returns columns from `Analitos`. It joins `Detalle`.
        # I need to update `get_perfil_analitos` to return sorted items.
        # Or I can sort here if I had the order index.
        # Let's update DB method in next step.

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
            analito_ids = [a.id for a in self.asignados_items] # Ordered list

            db.upsert_perfil(data, analito_ids) # Pass ordered list

            self.clear_form()
            self.load_data()

            self.page.open(ft.SnackBar(ft.Text("Perfil guardado correctamente"), bgcolor=ft.Colors.GREEN))

        except Exception as ex:
            print(f"Error saving perfil: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))
