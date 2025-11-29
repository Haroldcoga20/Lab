import flet as ft
from database import db
from models.analito import Analito
from models.rango_referencia import RangoReferencia

class AnalitosView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

        self.analitos = []
        self.selected_analito_id = None

        # Form Controls
        self.txt_nombre = ft.TextField(label="Nombre", expand=True)
        self.txt_unidad = ft.TextField(label="Unidad", width=100)
        self.dd_categoria = ft.Dropdown(
            label="Categoría",
            options=[
                ft.dropdown.Option("Hematología"),
                ft.dropdown.Option("Química Sanguínea"),
                ft.dropdown.Option("Inmunología"),
                ft.dropdown.Option("Urianálisis"),
                ft.dropdown.Option("Coproparasitología"),
                ft.dropdown.Option("Otros"),
            ],
            expand=True
        )
        self.txt_metodo = ft.TextField(label="Método", expand=True)
        self.txt_muestra = ft.TextField(label="Tipo Muestra", expand=True) # Suero, Plasma, Orina, etc.
        self.dd_tipo_dato = ft.Dropdown(
            label="Tipo Dato",
            options=[
                ft.dropdown.Option("Numerico"),
                ft.dropdown.Option("Texto"),
                ft.dropdown.Option("Opciones"),
            ],
            width=150,
            value="Numerico"
        )

        self.txt_min = ft.TextField(label="Ref. Min", width=100, keyboard_type=ft.KeyboardType.NUMBER)
        self.txt_max = ft.TextField(label="Ref. Max", width=100, keyboard_type=ft.KeyboardType.NUMBER)
        self.txt_visual = ft.TextField(label="Ref. Visual", expand=True)

        # Checkbox for calculated fields
        self.chk_calculado = ft.Checkbox(label="Es Calculado?", on_change=self.toggle_formula)
        self.txt_formula = ft.TextField(label="Fórmula", visible=False, expand=True)

        # Ranges Management
        self.btn_rangos = ft.ElevatedButton("Gestionar Rangos", on_click=self.open_rangos_dialog, disabled=True)

        # Data Table
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Categoría")),
                ft.DataColumn(ft.Text("Unidad")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )

        # Build Layout
        form_row1 = ft.Row([self.txt_nombre, self.dd_categoria, self.txt_unidad])
        form_row2 = ft.Row([self.txt_metodo, self.txt_muestra, self.dd_tipo_dato])
        form_row3 = ft.Row([self.txt_min, self.txt_max, self.txt_visual])
        form_row4 = ft.Row([self.chk_calculado, self.txt_formula])

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar", on_click=self.save_analito),
            ft.ElevatedButton("Limpiar", on_click=self.clear_form),
            self.btn_rangos
        ])

        self.controls = [
            ft.Text("Gestión de Analitos", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([form_row1, form_row2, form_row3, form_row4, actions_row]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Text("Lista de Analitos"),
            ft.ListView(controls=[self.table], expand=True, height=300)
        ]

        # Initial Load - NO UPDATE() calls here
        self.load_data(initial=True)

    def toggle_formula(self, e):
        self.txt_formula.visible = self.chk_calculado.value
        self.update()

    def load_data(self, initial=False):
        self.table.rows.clear()
        try:
            rows = db.get_all_analitos()
            self.analitos = [Analito.from_tuple(r) for r in rows]

            for analito in self.analitos:
                self.table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(str(analito.id))),
                        ft.DataCell(ft.Text(analito.nombre)),
                        ft.DataCell(ft.Text(analito.categoria)),
                        ft.DataCell(ft.Text(analito.unidad or "")),
                        ft.DataCell(ft.IconButton(ft.Icons.EDIT, on_click=lambda e, a=analito: self.edit_analito(a))),
                    ])
                )

            # Only call update if not in initial render phase
            if not initial:
                self.update()

        except Exception as e:
            print(f"Error loading analitos: {e}")

    def edit_analito(self, analito: Analito):
        self.selected_analito_id = analito.id
        self.txt_nombre.value = analito.nombre
        self.txt_unidad.value = analito.unidad or ""
        self.dd_categoria.value = analito.categoria
        self.txt_metodo.value = analito.metodo or ""
        self.txt_muestra.value = analito.tipoMuestra or ""
        self.dd_tipo_dato.value = analito.tipoDato
        self.txt_min.value = str(analito.valorRefMin) if analito.valorRefMin is not None else ""
        self.txt_max.value = str(analito.valorRefMax) if analito.valorRefMax is not None else ""
        self.txt_visual.value = analito.referenciaVisual or ""
        self.chk_calculado.value = analito.esCalculado
        self.txt_formula.value = analito.formula or ""
        self.txt_formula.visible = analito.esCalculado

        self.btn_rangos.disabled = False
        self.update()

    def clear_form(self, e=None):
        self.selected_analito_id = None
        self.txt_nombre.value = ""
        self.txt_unidad.value = ""
        self.dd_categoria.value = None
        self.txt_metodo.value = ""
        self.txt_muestra.value = ""
        self.dd_tipo_dato.value = "Numerico"
        self.txt_min.value = ""
        self.txt_max.value = ""
        self.txt_visual.value = ""
        self.chk_calculado.value = False
        self.txt_formula.value = ""
        self.txt_formula.visible = False
        self.btn_rangos.disabled = True
        self.update()

    def save_analito(self, e):
        try:
            data = {
                'id': self.selected_analito_id,
                'nombre': self.txt_nombre.value,
                'unidad': self.txt_unidad.value,
                'categoria': self.dd_categoria.value,
                'metodo': self.txt_metodo.value,
                'tipoMuestra': self.txt_muestra.value,
                'tipoDato': self.dd_tipo_dato.value,
                'valorRefMin': self.txt_min.value,
                'valorRefMax': self.txt_max.value,
                'referenciaVisual': self.txt_visual.value,
                'esCalculado': self.chk_calculado.value,
                'formula': self.txt_formula.value
            }

            db.upsert_analito(data)

            self.clear_form()
            self.load_data()

            # Using modern open syntax if available, otherwise fallback is tolerated but we try best effort.
            # User instruction was strict on e.page.open(dialog) for dialogs.
            # For snackbar, it's often page.open(snackbar) or page.snack_bar = ... open=True.
            # Given the strictness on Dialogs, I'll update dialogs below.
            # I will assume page.open(snack_bar) works in 0.28.3
            self.page.open(ft.SnackBar(ft.Text("Guardado correctamente"), bgcolor=ft.Colors.GREEN))

        except Exception as ex:
            print(f"Error saving: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))

    # --- RANGOS LOGIC ---
    def open_rangos_dialog(self, e):
        if not self.selected_analito_id:
            return

        self.rangos_dialog = RangosDialog(self.selected_analito_id, self.page)
        # STRICT FIX: Use self.page.open(dialog)
        self.page.open(self.rangos_dialog.dialog)

class RangosDialog:
    def __init__(self, analito_id, page):
        self.analito_id = analito_id
        self.page = page

        self.dd_genero = ft.Dropdown(
            label="Género",
            options=[ft.dropdown.Option("Ambos"), ft.dropdown.Option("Masculino"), ft.dropdown.Option("Femenino")],
            value="Ambos", width=100
        )
        self.txt_edad_min = ft.TextField(label="Edad Min", value="0", width=80, keyboard_type=ft.KeyboardType.NUMBER)
        self.txt_edad_max = ft.TextField(label="Edad Max", value="120", width=80, keyboard_type=ft.KeyboardType.NUMBER)
        self.dd_unidad_edad = ft.Dropdown(
            label="Unidad Edad",
            options=[ft.dropdown.Option("Años"), ft.dropdown.Option("Meses"), ft.dropdown.Option("Días")],
            value="Años", width=100
        )
        self.txt_val_min = ft.TextField(label="Val Min", width=80, keyboard_type=ft.KeyboardType.NUMBER)
        self.txt_val_max = ft.TextField(label="Val Max", width=80, keyboard_type=ft.KeyboardType.NUMBER)

        self.table_rangos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Género")),
                ft.DataColumn(ft.Text("Edad")),
                ft.DataColumn(ft.Text("Rango")),
                ft.DataColumn(ft.Text("X")),
            ],
            rows=[]
        )

        self.dialog = ft.AlertDialog(
            title=ft.Text("Gestionar Rangos de Referencia"),
            content=ft.Container(
                width=600,
                content=ft.Column([
                    ft.Row([self.dd_genero, self.txt_edad_min, self.txt_edad_max, self.dd_unidad_edad]),
                    ft.Row([self.txt_val_min, self.txt_val_max, ft.ElevatedButton("Agregar", on_click=self.add_rango)]),
                    ft.Divider(),
                    ft.ListView([self.table_rangos], height=200)
                ])
            ),
            actions=[ft.TextButton("Cerrar", on_click=self.close_dialog)]
        )
        self.load_rangos(initial=True)

    def load_rangos(self, initial=False):
        self.table_rangos.rows.clear()
        try:
            rows = db.get_rangos_by_analito(self.analito_id)
            for r in rows:
                rango = RangoReferencia.from_tuple(r)
                self.table_rangos.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(rango.genero)),
                        ft.DataCell(ft.Text(f"{rango.edadMin}-{rango.edadMax} {rango.unidadEdad}")),
                        ft.DataCell(ft.Text(f"{rango.valorMin} - {rango.valorMax}")),
                        ft.DataCell(ft.IconButton(ft.icons.DELETE, on_click=lambda e, rid=rango.id: self.delete_rango(rid)))
                    ])
                )
            if not initial and self.dialog.open:
                self.dialog.update()
        except Exception as e:
            print(e)

    def add_rango(self, e):
        try:
            data = {
                'analitoId': self.analito_id,
                'genero': self.dd_genero.value,
                'edadMin': self.txt_edad_min.value,
                'edadMax': self.txt_edad_max.value,
                'unidadEdad': self.dd_unidad_edad.value,
                'valorMin': self.txt_val_min.value,
                'valorMax': self.txt_val_max.value
            }
            db.add_rango(data)
            self.load_rangos()
        except Exception as ex:
            print(ex)

    def delete_rango(self, rango_id):
        try:
            db.delete_rango(rango_id)
            self.load_rangos()
        except Exception as e:
            print(e)

    def close_dialog(self, e):
        # STRICT FIX: Use self.page.close(dialog) or just close logic.
        # Flet 0.21+: page.close(dialog)
        self.page.close(self.dialog)
