import flet as ft
from database import db
from models.analito import Analito
from models.rango_referencia import RangoReferencia

class AnalitosView(ft.Column):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
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
        self.txt_muestra = ft.TextField(label="Tipo Muestra", expand=True)
        self.dd_tipo_dato = ft.Dropdown(
            label="Tipo Dato",
            options=[
                ft.dropdown.Option("Numerico"),
                ft.dropdown.Option("Texto"),
                ft.dropdown.Option("Opciones"),
            ],
            width=150,
            value="Numerico",
            on_change=self.toggle_panels
        )

        # Phase 6.5 New Fields
        self.txt_subtitulo = ft.TextField(label="Subtítulo Reporte (Opcional)", expand=True)
        self.txt_valor_defecto = ft.TextField(label="Valor por Defecto", expand=True)

        self.chk_calculado = ft.Checkbox(label="Es Calculado?", on_change=self.toggle_formula)
        self.txt_formula = ft.TextField(label="Fórmula", visible=False, expand=True)

        self.btn_rangos = ft.ElevatedButton("Gestionar Rangos", on_click=self.open_rangos_dialog, disabled=True)

        # Opciones Panel (For 'Opciones' type)
        self.txt_opcion_val = ft.TextField(label="Valor Opción", expand=True)
        self.chk_opcion_default = ft.Checkbox(label="Predeterminado")
        self.lv_opciones = ft.ListView(height=150)

        self.panel_opciones = ft.Container(
            visible=False,
            content=ft.Column([
                ft.Text("Opciones del Analito", weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.txt_opcion_val,
                    self.chk_opcion_default,
                    ft.IconButton(ft.Icons.ADD, on_click=self.add_opcion)
                ]),
                self.lv_opciones
            ], spacing=10),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5
        )

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

        form_row1 = ft.Row([self.txt_nombre, self.dd_categoria, self.txt_unidad])
        form_row2 = ft.Row([self.txt_metodo, self.txt_muestra, self.dd_tipo_dato])
        form_row3 = ft.Row([self.txt_subtitulo, self.txt_valor_defecto])
        form_row4 = ft.Row([self.chk_calculado, self.txt_formula])

        actions_row = ft.Row([
            ft.ElevatedButton("Guardar", on_click=self.save_analito),
            ft.ElevatedButton("Limpiar", on_click=self.clear_form),
            self.btn_rangos
        ])

        self.controls = [
            ft.Text("Gestión de Analitos", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([form_row1, form_row2, form_row3, form_row4, self.panel_opciones, actions_row]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Text("Lista de Analitos"),
            ft.ListView(controls=[self.table], expand=True, height=300)
        ]

        self.load_data(initial=True)

    def toggle_formula(self, e):
        self.txt_formula.visible = self.chk_calculado.value
        self.update()

    def toggle_panels(self, e):
        is_opciones = (self.dd_tipo_dato.value == "Opciones")
        self.panel_opciones.visible = is_opciones
        self.txt_valor_defecto.visible = not is_opciones # Only for Numeric/Text
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
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.Icons.EDIT, on_click=lambda e, a=analito: self.edit_analito(a)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, aid=analito.id, name=analito.nombre: self.confirm_delete(aid, name))
                        ])),
                    ])
                )

            if not initial:
                self.update()
        except Exception as e:
            print(f"Error loading analitos: {e}")

    def load_opciones_list(self):
        self.lv_opciones.controls.clear()
        if not self.selected_analito_id: return

        opts = db.get_opciones_analito(self.selected_analito_id)
        for o in opts:
            # o: id, aid, val, isDef
            oid, val, isDef = o[0], o[2], bool(o[3])
            icon = ft.Icons.CHECK if isDef else None
            self.lv_opciones.controls.append(
                ft.ListTile(
                    title=ft.Text(val, weight=ft.FontWeight.BOLD if isDef else ft.FontWeight.NORMAL),
                    trailing=ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, x=oid: self.delete_opcion(x)),
                    leading=ft.Icon(icon, color=ft.Colors.GREEN) if icon else None
                )
            )
        self.update()

    def add_opcion(self, e):
        if not self.selected_analito_id:
            self.page_ref.open(ft.SnackBar(ft.Text("Primero guarde el analito"), bgcolor=ft.Colors.RED))
            return
        if not self.txt_opcion_val.value: return

        db.add_opcion_analito(self.selected_analito_id, self.txt_opcion_val.value, self.chk_opcion_default.value)
        self.txt_opcion_val.value = ""
        self.chk_opcion_default.value = False
        self.load_opciones_list()

    def delete_opcion(self, oid):
        db.delete_opcion_analito(oid)
        self.load_opciones_list()

    def edit_analito(self, analito: Analito):
        self.selected_analito_id = analito.id
        self.txt_nombre.value = analito.nombre
        self.txt_unidad.value = analito.unidad or ""
        self.dd_categoria.value = analito.categoria
        self.txt_metodo.value = analito.metodo or ""
        self.txt_muestra.value = analito.tipoMuestra or ""
        self.dd_tipo_dato.value = analito.tipoDato

        self.txt_subtitulo.value = getattr(analito, 'subtituloReporte', "")
        self.txt_valor_defecto.value = getattr(analito, 'valorPorDefecto', "")

        self.chk_calculado.value = analito.esCalculado
        self.txt_formula.value = analito.formula or ""
        self.txt_formula.visible = analito.esCalculado

        self.toggle_panels(None)
        if self.dd_tipo_dato.value == "Opciones":
            self.load_opciones_list()

        self.btn_rangos.disabled = False
        self.update()

    def confirm_delete(self, analito_id, name):
        def close_dlg(e):
            self.page_ref.close(dlg)

        def delete_confirmed(e):
            self.page_ref.close(dlg)
            self.delete_analito(analito_id)

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Está seguro de eliminar el analito '{name}'? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Eliminar", on_click=delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page_ref.open(dlg)

    def delete_analito(self, analito_id):
        try:
            db.delete_analito(analito_id)
            self.load_data()
            self.page_ref.open(ft.SnackBar(ft.Text("Analito eliminado"), bgcolor=ft.Colors.GREEN))
        except Exception as e:
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error al eliminar: {e}"), bgcolor=ft.Colors.RED))

    def clear_form(self, e=None):
        self.selected_analito_id = None
        self.txt_nombre.value = ""
        self.txt_unidad.value = ""
        self.dd_categoria.value = None
        self.txt_metodo.value = ""
        self.txt_muestra.value = ""
        self.dd_tipo_dato.value = "Numerico"
        self.txt_subtitulo.value = ""
        self.txt_valor_defecto.value = ""
        self.chk_calculado.value = False
        self.txt_formula.value = ""
        self.txt_formula.visible = False
        self.btn_rangos.disabled = True
        self.toggle_panels(None)
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
                'valorRefMin': None,
                'valorRefMax': None,
                'referenciaVisual': None,
                'esCalculado': self.chk_calculado.value,
                'formula': self.txt_formula.value,
                'subtituloReporte': self.txt_subtitulo.value,
                'valorPorDefecto': self.txt_valor_defecto.value
            }

            db.upsert_analito(data)

            self.clear_form()
            self.load_data()

            self.page_ref.open(ft.SnackBar(ft.Text("Guardado correctamente"), bgcolor=ft.Colors.GREEN))

        except Exception as ex:
            print(f"Error saving: {ex}")
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))

    def open_rangos_dialog(self, e):
        if not self.selected_analito_id:
            return

        self.rangos_dialog = RangosDialog(self.selected_analito_id, self.page_ref)
        self.page_ref.open(self.rangos_dialog.dialog)

class RangosDialog:
    def __init__(self, analito_id, page):
        self.analito_id = analito_id
        self.page_ref = page

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
                        ft.DataCell(ft.IconButton(ft.Icons.DELETE, on_click=lambda e, rid=rango.id: self.delete_rango(rid)))
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
        self.page_ref.close(self.dialog)
