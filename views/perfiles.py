import flet as ft
from database import db
from models.perfil_examen import PerfilExamen
from models.analito import Analito

class PerfilesView(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
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

        # Selector UI
        selector = ft.Row([
            ft.Column([
                ft.Text("Analitos Disponibles"),
                ft.Container(self.lv_disponibles, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
            ], expand=True),
            ft.Column([
                ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=self.add_analito_to_profile),
                # Remove Left Arrow button as we will use per-row remove button on right list
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Column([
                ft.Text("Analitos Asignados (Reordenar)"),
                ft.Container(self.lv_asignados, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
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

        # Helper to create checkbox tiles for available
        def create_avail_tile(analito):
            return ft.Checkbox(
                label=analito.nombre,
                value=False,
                data=analito.id
            )

        assigned_ids = [a.id for a in self.asignados_items]

        # Populate Available
        for analito in self.all_analitos:
            if analito.id not in assigned_ids:
                self.lv_disponibles.controls.append(create_avail_tile(analito))

        # Populate Assigned (Inline Actions)
        for i, analito in enumerate(self.asignados_items):
            is_first = (i == 0)
            is_last = (i == len(self.asignados_items) - 1)

            row = ft.Row([
                ft.Text(analito.nombre, expand=True),
                ft.IconButton(ft.Icons.ARROW_UPWARD,
                              icon_size=20,
                              disabled=is_first,
                              on_click=lambda e, idx=i: self.move_item_inline(idx, -1)),
                ft.IconButton(ft.Icons.ARROW_DOWNWARD,
                              icon_size=20,
                              disabled=is_last,
                              on_click=lambda e, idx=i: self.move_item_inline(idx, 1)),
                ft.IconButton(ft.Icons.CLOSE,
                              icon_color=ft.Colors.RED,
                              icon_size=20,
                              tooltip="Quitar",
                              on_click=lambda e, idx=i: self.remove_item_inline(idx))
            ], alignment=ft.MainAxisAlignment.END, spacing=0)

            self.lv_asignados.controls.append(ft.Container(content=row, padding=5, bgcolor=ft.Colors.GREY_100, border_radius=5))

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

    def remove_item_inline(self, index):
        if 0 <= index < len(self.asignados_items):
            self.asignados_items.pop(index)
            self.refresh_selector()

    def remove_analito_from_profile(self, e):
        # Legacy method kept if button still exists, but we removed the button from UI.
        pass

    def move_item_inline(self, index, direction):
        new_index = index + direction
        if 0 <= new_index < len(self.asignados_items):
            # Swap
            self.asignados_items[index], self.asignados_items[new_index] = self.asignados_items[new_index], self.asignados_items[index]
            self.refresh_selector()

    def edit_perfil(self, perfil: PerfilExamen):
        self.selected_perfil_id = perfil.id
        self.txt_nombre.value = perfil.nombre
        self.dd_categoria.value = perfil.categoria
        self.txt_precio.value = str(perfil.precioEstandar)

        # Load details sorted by order (DB method already updated to sort by orden ASC)
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
            analito_ids = [a.id for a in self.asignados_items] # Ordered list

            db.upsert_perfil(data, analito_ids) # Pass ordered list

            self.clear_form()
            self.load_data()

            self.page.open(ft.SnackBar(ft.Text("Perfil guardado correctamente"), bgcolor=ft.Colors.GREEN))

        except Exception as ex:
            print(f"Error saving perfil: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))
