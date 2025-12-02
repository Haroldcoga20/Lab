import flet as ft
from database import db
from models.paciente import Paciente
import re

class ResultadosView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_ref = page
        self.expand = True

        # Maps and Lists
        self.inputs_map = {} # abbr -> control (TextField/Dropdown)
        self.ordered_inputs = [] # List of controls for navigation
        self.input_data_map = {} # Metadata store

        # Filter Toolbar
        self.txt_search = ft.TextField(
            prefix_icon=ft.Icons.SEARCH,
            hint_text="Buscar por Paciente/DNI",
            expand=True,
            on_submit=self.apply_filters
        )
        self.dd_filter_medico = ft.Dropdown(
            label="Filtrar por Médico",
            width=200,
            options=[],
            on_change=self.apply_filters
        )
        self.dd_filter_estado = ft.Dropdown(
            label="Estado",
            width=150,
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Pendiente"),
                ft.dropdown.Option("Completado"),
            ],
            value="Todos",
            on_change=self.apply_filters
        )
        self.btn_clear_filters = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip="Limpiar Filtros",
            on_click=self.clear_filters
        )

        # Left Panel: List of Orders
        self.lv_ordenes = ft.ListView(expand=True, spacing=5, padding=10)

        # Right Panel: Results Detail (Grouped)
        self.current_orden_id = None
        self.lbl_orden_info = ft.Text("Seleccione una Orden", size=18, weight=ft.FontWeight.BOLD)
        self.result_container = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)

        self.input_controls = []

        # Split View
        self.controls = [
            ft.Text("Ingreso de Resultados", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Row([self.txt_search, self.dd_filter_medico, self.dd_filter_estado, self.btn_clear_filters]),
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5
            ),
            ft.Divider(),
            ft.Row([
                # Left Panel
                ft.Container(
                    width=350,
                    content=ft.Column([
                        ft.Text("Lista de Órdenes", weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        self.lv_ordenes
                    ]),
                    border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300))
                ),
                # Right Panel
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column([
                        self.lbl_orden_info,
                        ft.Divider(),
                        self.result_container
                    ])
                )
            ], expand=True)
        ]

    def did_mount(self):
        self.load_initial_data()
        self.load_ordenes()

    def load_initial_data(self):
        try:
            medicos = db.get_all_medicos()
            self.dd_filter_medico.options = [ft.dropdown.Option(key=str(m[0]), text=m[1]) for m in medicos]
            self.update()
        except Exception as e:
            print(f"Error loading filters: {e}")

    def apply_filters(self, e):
        self.load_ordenes()

    def clear_filters(self, e):
        self.txt_search.value = ""
        self.dd_filter_medico.value = None
        self.dd_filter_estado.value = "Todos"
        self.load_ordenes()

    def load_ordenes(self, initial=False):
        self.lv_ordenes.controls.clear()
        try:
            search = self.txt_search.value
            medico_id = self.dd_filter_medico.value
            estado = self.dd_filter_estado.value

            ordenes = db.get_ordenes_filtradas(search, medico_id, estado)

            if not ordenes:
                self.lv_ordenes.controls.append(ft.Text("No se encontraron órdenes."))
            else:
                for o in ordenes:
                    oid = o[0]
                    nombre = o[1]
                    fecha = o[2].strftime("%d/%m %H:%M") if o[2] else ""
                    estado_orden = o[3]

                    self.lv_ordenes.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.RECEIPT_LONG),
                            title=ft.Text(f"#{oid} - {nombre}"),
                            subtitle=ft.Text(f"{fecha} | {estado_orden}"),
                            on_click=lambda e, x=oid: self.load_detalle_orden(x)
                        )
                    )

            if not initial:
                self.update()
        except Exception as e:
            print(f"Error loading orders: {e}")

    def load_detalle_orden(self, orden_id):
        self.current_orden_id = orden_id
        self.input_controls = []
        self.inputs_map = {}
        self.ordered_inputs = []
        self.input_data_map = {}
        self.result_container.controls.clear()

        # Header
        header_tuple = db.get_orden_header(orden_id)
        if not header_tuple: return
        paciente_tuple = db.get_paciente(header_tuple[1])
        paciente = Paciente.from_tuple(paciente_tuple)

        self.lbl_orden_info.value = f"Orden #{orden_id} - {paciente.nombreCompleto} ({paciente.edad} {paciente.unidadEdad})"

        self.page_ref.floating_action_button = ft.FloatingActionButton(
            icon=ft.Icons.SAVE,
            on_click=self.save_all
        )
        self.page_ref.update()

        grouped_data = db.get_resultados_grouped(orden_id)

        for group in grouped_data:
            group_title = group['title']
            items = group['items']

            card_rows = []

            card_rows.append(ft.Row([
                ft.Text("Analito", weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Resultado", weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Ref", weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Unid.", weight=ft.FontWeight.BOLD, width=60),
            ]))
            card_rows.append(ft.Divider())

            for item in items:
                # --- INPUT LOGIC ---
                tipo = item['tipoDato']
                current_val = item['valor']
                aid = item['analitoId']
                es_calculado = bool(item.get('esCalculado'))

                range_vals = db.get_patient_range_values(aid, paciente.genero, paciente.edad, paciente.unidadEdad)

                # Determine value to display
                val_to_display = current_val
                if val_to_display is None:
                    if tipo == 'Opciones':
                        opts = item.get('opciones', [])
                        for o in opts:
                            if o['default']:
                                val_to_display = o['text']
                                break
                    else:
                        val_to_display = item.get('valorPorDefecto')

                val_to_display = val_to_display or ""

                warning_icon = ft.Container(content=ft.Icon(ft.Icons.WARNING, color=ft.Colors.RED, size=16), visible=False)

                input_control = None

                if tipo == 'Opciones':
                    opts = item.get('opciones', [])
                    dd_opts = [ft.dropdown.Option(o['text']) for o in opts]
                    input_control = ft.Dropdown(
                        options=dd_opts,
                        value=val_to_display,
                        expand=2,
                        height=40,
                        content_padding=5,
                        on_change=lambda e: self.on_result_change(e),
                        # Dropdowns generally not read-only for calculation unless specific logic, but assuming Calc is Numeric.
                    )
                else:
                    input_control = ft.TextField(
                        value=val_to_display,
                        expand=2,
                        height=40,
                        content_padding=5,
                        on_change=lambda e: self.on_result_change(e),
                        on_submit=lambda e: self.focus_next(e),
                        read_only=es_calculado, # READ-ONLY FOR CALCULATED
                        bgcolor=ft.Colors.GREY_100 if es_calculado else None # VISUAL CUE
                    )

                control_meta = {
                    'id': item['id'],
                    'analitoId': aid,
                    'tipo': tipo,
                    'ranges': range_vals,
                    'formula': item.get('formula'),
                    'esCalculado': es_calculado,
                    'abreviatura': item.get('abreviatura'),
                    'warning_icon': warning_icon
                }

                input_control.data = control_meta

                if item.get('abreviatura'):
                    self.inputs_map[item['abreviatura']] = input_control

                self.ordered_inputs.append(input_control)
                self.input_controls.append({'id': item['id'], 'control': input_control})

                smart_ref = db.get_smart_reference(aid, paciente.genero, paciente.edad, paciente.unidadEdad)

                row_control = ft.Row([
                    ft.Text(item['nombre'], expand=2),
                    ft.Stack([input_control, ft.Container(warning_icon, right=5, top=10)], expand=2),
                    ft.Text(smart_ref, color=ft.Colors.BLUE, size=12, expand=2),
                    ft.Text(item['unidad'] or "", width=60, size=12),
                ], alignment=ft.MainAxisAlignment.CENTER)

                card_rows.append(row_control)

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(group_title, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.BLUE_900),
                        ft.Divider(),
                        ft.Column(card_rows, spacing=10)
                    ]),
                    padding=15
                ),
                margin=ft.margin.only(bottom=10)
            )
            self.result_container.controls.append(card)

        self.run_validations_and_calcs()
        self.update()

    def run_validations_and_calcs(self):
        self.recalculate_formulas()
        for ctrl in self.ordered_inputs:
            self.validate_ranges(ctrl)

    def on_result_change(self, e):
        ctrl = e.control
        self.validate_ranges(ctrl)
        self.recalculate_formulas()
        self.update()

    def validate_ranges(self, control):
        meta = control.data
        val_str = control.value
        if not val_str or meta['tipo'] != 'Numerico':
            control.text_style = ft.TextStyle(color=ft.Colors.BLACK)
            meta['warning_icon'].visible = False
            return

        try:
            val = float(val_str)
            ranges = meta['ranges']
            if not ranges: return

            r_min, r_max, r_pmin, r_pmax = ranges

            color = ft.Colors.BLACK
            icon_visible = False

            if (r_pmin is not None and val < r_pmin) or (r_pmax is not None and val > r_pmax):
                color = ft.Colors.RED
                icon_visible = True
            elif (r_min is not None and val < r_min) or (r_max is not None and val > r_max):
                color = ft.Colors.ORANGE

            control.text_style = ft.TextStyle(color=color)
            meta['warning_icon'].visible = icon_visible

        except ValueError:
            pass

    def recalculate_formulas(self):
        for ctrl in self.ordered_inputs:
            meta = ctrl.data
            if meta.get('esCalculado') and meta.get('formula'):
                formula = meta['formula']
                tokens = re.findall(r'\[(.*?)\]', formula)

                can_calc = True
                calc_expr = formula

                for token in tokens:
                    src_ctrl = self.inputs_map.get(token)
                    if src_ctrl:
                        val_str = src_ctrl.value
                        try:
                            val = float(val_str)
                            calc_expr = calc_expr.replace(f"[{token}]", str(val))
                        except (ValueError, TypeError):
                            can_calc = False
                            break
                    else:
                        can_calc = False

                if can_calc:
                    try:
                        allowed_chars = "0123456789.+-*/() "
                        if not all(c in allowed_chars for c in calc_expr):
                            continue

                        res = eval(calc_expr)
                        ctrl.value = "{:.2f}".format(res)
                        ctrl.update()
                        self.validate_ranges(ctrl)
                    except:
                        pass

    def focus_next(self, e):
        ctrl = e.control
        try:
            idx = self.ordered_inputs.index(ctrl)
            if idx < len(self.ordered_inputs) - 1:
                next_ctrl = self.ordered_inputs[idx + 1]
                next_ctrl.focus()
        except ValueError:
            pass

    def save_all(self, e):
        updates = []
        for inp in self.input_controls:
            val = inp['control'].value
            if val is not None:
                updates.append({'id': inp['id'], 'valor': val})

        if not updates:
            self.page_ref.open(ft.SnackBar(ft.Text("No hay datos para guardar"), bgcolor=ft.Colors.GREY))
            return

        try:
            db.update_resultado_batch(updates)
            self.page_ref.open(ft.SnackBar(ft.Text("Resultados guardados y estado actualizado"), bgcolor=ft.Colors.GREEN))
            self.load_ordenes()
        except Exception as ex:
            print(ex)
            self.page_ref.open(ft.SnackBar(ft.Text("Error al guardar"), bgcolor=ft.Colors.RED))
