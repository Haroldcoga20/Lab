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

        # Tab 1: Analitos
        self.lv_disponibles = ft.ListView(expand=True, height=200)
        self.lv_asignados = ft.ListView(expand=True, height=200)
        self.disponibles_items = []
        self.asignados_items = [] # List of Analito
        self.txt_search_analitos = ft.TextField(
            prefix_icon=ft.Icons.SEARCH,
            hint_text="Filtrar analitos...",
            on_change=self.filter_analitos_disponibles
        )

        # Tab 2: Sub-Perfiles
        self.lv_sub_disponibles = ft.ListView(expand=True, height=200)
        self.lv_sub_asignados = ft.ListView(expand=True, height=200)
        self.sub_asignados_items = [] # List of PerfilExamen
        self.txt_search_sub = ft.TextField(
             prefix_icon=ft.Icons.SEARCH,
             hint_text="Filtrar perfiles...",
             on_change=self.filter_subperfiles_disponibles
        )

        # Tabs Container
        self.tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(
                    text="Analitos",
                    content=ft.Container(
                        content=self.build_analitos_selector(),
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Sub-Perfiles (Paquetes)",
                    content=ft.Container(
                        content=self.build_subperfiles_selector(),
                        padding=10
                    )
                )
            ],
            expand=True,
            height=400
        )

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

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar Perfil", on_click=self.save_perfil),
            ft.ElevatedButton("Limpiar", on_click=self.clear_form)
        ])

        self.controls = [
            ft.Text("Gestión de Perfiles de Examen", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([form_row, ft.Divider(), self.tabs, actions_row]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Text("Lista de Perfiles"),
            ft.ListView(controls=[self.table], expand=True, height=300)
        ]

        self.load_data(initial=True)

    def build_analitos_selector(self):
        return ft.Row([
            ft.Column([
                ft.Text("Analitos Disponibles"),
                self.txt_search_analitos,
                ft.Container(self.lv_disponibles, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
            ], expand=True),
            ft.Column([
                ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=self.add_analito_to_profile),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Column([
                ft.Text("Analitos Asignados (Reordenar)"),
                ft.Container(height=40),
                ft.Container(self.lv_asignados, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
            ], expand=True)
        ], expand=True)

    def build_subperfiles_selector(self):
        return ft.Row([
            ft.Column([
                ft.Text("Perfiles Disponibles"),
                self.txt_search_sub,
                ft.Container(self.lv_sub_disponibles, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
            ], expand=True),
            ft.Column([
                ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=self.add_subperfil_to_profile),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Column([
                ft.Text("Sub-Perfiles Asignados"),
                ft.Container(height=40),
                ft.Container(self.lv_sub_asignados, border=ft.border.all(1, "grey"), border_radius=5, expand=True)
            ], expand=True)
        ], expand=True)

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
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.Icons.EDIT, on_click=lambda e, item=p: self.edit_perfil(item)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, pid=p.id, name=p.nombre: self.confirm_delete(pid, name))
                        ])),
                    ])
                )

            # Load All Analitos
            a_rows = db.get_all_analitos()
            self.all_analitos = [Analito.from_tuple(r) for r in a_rows]

            self.refresh_selector(initial=initial)
            self.refresh_sub_selector(initial=initial)

            if not initial:
                self.update()

        except Exception as e:
            print(f"Error loading perfiles: {e}")

    # --- Analitos Logic ---
    def filter_analitos_disponibles(self, e):
        self.refresh_selector()

    def refresh_selector(self, initial=False):
        self.lv_disponibles.controls.clear()
        self.lv_asignados.controls.clear()

        def create_avail_tile(analito):
            return ft.Checkbox(
                label=analito.nombre,
                value=False,
                data=analito.id
            )

        assigned_ids = [a.id for a in self.asignados_items]
        search_term = self.txt_search_analitos.value.lower() if self.txt_search_analitos.value else ""

        for analito in self.all_analitos:
            if analito.id not in assigned_ids:
                if not search_term or search_term in analito.nombre.lower():
                    self.lv_disponibles.controls.append(create_avail_tile(analito))

        for i, analito in enumerate(self.asignados_items):
            is_first = (i == 0)
            is_last = (i == len(self.asignados_items) - 1)
            row = ft.Row([
                ft.Text(analito.nombre, expand=True),
                ft.IconButton(ft.Icons.ARROW_UPWARD, icon_size=20, disabled=is_first,
                              on_click=lambda e, idx=i: self.move_item_inline(idx, -1)),
                ft.IconButton(ft.Icons.ARROW_DOWNWARD, icon_size=20, disabled=is_last,
                              on_click=lambda e, idx=i: self.move_item_inline(idx, 1)),
                ft.IconButton(ft.Icons.CLOSE, icon_color=ft.Colors.RED, icon_size=20,
                              on_click=lambda e, idx=i: self.remove_item_inline(idx))
            ], alignment=ft.MainAxisAlignment.END, spacing=0)
            self.lv_asignados.controls.append(ft.Container(content=row, padding=5, bgcolor=ft.Colors.GREY_100, border_radius=5))

        if not initial:
            self.update()

    def add_analito_to_profile(self, e):
        for c in self.lv_disponibles.controls:
            if c.value:
                analito = next((a for a in self.all_analitos if a.id == c.data), None)
                if analito:
                    self.asignados_items.append(analito)
        self.refresh_selector()

    def remove_item_inline(self, index):
        if 0 <= index < len(self.asignados_items):
            self.asignados_items.pop(index)
            self.refresh_selector()

    def move_item_inline(self, index, direction):
        new_index = index + direction
        if 0 <= new_index < len(self.asignados_items):
            self.asignados_items[index], self.asignados_items[new_index] = self.asignados_items[new_index], self.asignados_items[index]
            self.refresh_selector()

    # --- Sub-Perfiles Logic ---
    def filter_subperfiles_disponibles(self, e):
        self.refresh_sub_selector()

    def refresh_sub_selector(self, initial=False):
        self.lv_sub_disponibles.controls.clear()
        self.lv_sub_asignados.controls.clear()

        def create_avail_tile(perfil):
            return ft.Checkbox(
                label=perfil.nombre,
                value=False,
                data=perfil.id
            )

        assigned_ids = [p.id for p in self.sub_asignados_items]
        search_term = self.txt_search_sub.value.lower() if self.txt_search_sub.value else ""

        current_id = self.selected_perfil_id

        for p in self.perfiles:
            # Prevent adding itself, prevent adding already assigned
            if p.id != current_id and p.id not in assigned_ids:
                if not search_term or search_term in p.nombre.lower():
                    self.lv_sub_disponibles.controls.append(create_avail_tile(p))

        for i, p in enumerate(self.sub_asignados_items):
            is_first = (i == 0)
            is_last = (i == len(self.sub_asignados_items) - 1)
            row = ft.Row([
                ft.Text(p.nombre, expand=True),
                ft.IconButton(ft.Icons.ARROW_UPWARD, icon_size=20, disabled=is_first,
                              on_click=lambda e, idx=i: self.move_sub_item_inline(idx, -1)),
                ft.IconButton(ft.Icons.ARROW_DOWNWARD, icon_size=20, disabled=is_last,
                              on_click=lambda e, idx=i: self.move_sub_item_inline(idx, 1)),
                ft.IconButton(ft.Icons.CLOSE, icon_color=ft.Colors.RED, icon_size=20,
                              on_click=lambda e, idx=i: self.remove_sub_item_inline(idx))
            ], alignment=ft.MainAxisAlignment.END, spacing=0)
            self.lv_sub_asignados.controls.append(ft.Container(content=row, padding=5, bgcolor=ft.Colors.GREY_100, border_radius=5))

        if not initial:
            self.update()

    def add_subperfil_to_profile(self, e):
        for c in self.lv_sub_disponibles.controls:
            if c.value:
                p = next((x for x in self.perfiles if x.id == c.data), None)
                if p:
                    self.sub_asignados_items.append(p)
        self.refresh_sub_selector()

    def remove_sub_item_inline(self, index):
         if 0 <= index < len(self.sub_asignados_items):
            self.sub_asignados_items.pop(index)
            self.refresh_sub_selector()

    def move_sub_item_inline(self, index, direction):
        new_index = index + direction
        if 0 <= new_index < len(self.sub_asignados_items):
            self.sub_asignados_items[index], self.sub_asignados_items[new_index] = self.sub_asignados_items[new_index], self.sub_asignados_items[index]
            self.refresh_sub_selector()

    # --- Common Logic ---
    def edit_perfil(self, perfil: PerfilExamen):
        self.selected_perfil_id = perfil.id
        self.txt_nombre.value = perfil.nombre
        self.dd_categoria.value = perfil.categoria
        self.txt_precio.value = str(perfil.precioEstandar)

        # Load Analitos
        rows = db.get_perfil_analitos(perfil.id)
        self.asignados_items = [Analito.from_tuple(r) for r in rows]

        # Load Sub-Perfiles
        sub_rows = db.get_perfil_hijos(perfil.id)
        self.sub_asignados_items = [PerfilExamen.from_tuple(r) for r in sub_rows]

        self.refresh_selector()
        self.refresh_sub_selector()
        self.update()

    def confirm_delete(self, perfil_id, name):
        def close_dlg(e):
            self.page_ref.close(dlg)

        def delete_confirmed(e):
            self.page_ref.close(dlg)
            self.delete_perfil(perfil_id)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar el perfil '{name}'? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Eliminar", on_click=delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page_ref.open(dlg)

    def delete_perfil(self, perfil_id):
        try:
            db.delete_perfil(perfil_id)
            self.load_data()
            self.page_ref.open(ft.SnackBar(ft.Text("Perfil eliminado"), bgcolor=ft.Colors.GREEN))
        except Exception as e:
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error al eliminar: {e}"), bgcolor=ft.Colors.RED))

    def clear_form(self, e=None):
        self.selected_perfil_id = None
        self.txt_nombre.value = ""
        self.dd_categoria.value = None
        self.txt_precio.value = ""
        self.asignados_items = []
        self.sub_asignados_items = []
        self.refresh_selector()
        self.refresh_sub_selector()
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
            sub_perfil_ids = [p.id for p in self.sub_asignados_items]

            db.upsert_perfil(data, analito_ids, sub_perfil_ids)

            self.clear_form()
            self.load_data()

            self.page_ref.open(ft.SnackBar(ft.Text("Perfil guardado correctamente"), bgcolor=ft.Colors.GREEN))

        except Exception as ex:
            print(f"Error saving perfil: {ex}")
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))
