import flet as ft
from database import db
from models.paciente import Paciente
from models.medico import Medico
from models.analito import Analito
from models.perfil_examen import PerfilExamen

class CrearOrdenView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

        self.selected_paciente_id = None
        self.selected_medico_id = None
        self.selected_items = [] # list of dicts: {'type': 'perfil'|'analito', 'id': int, 'nombre': str, 'precio': float}

        # --- Controls ---

        # 1. Patient Selector
        self.txt_buscar_paciente = ft.TextField(
            label="Buscar Paciente (Nombre o DNI)",
            on_submit=self.search_paciente,
            expand=True
        )
        self.btn_buscar_paciente = ft.IconButton(ft.Icons.SEARCH, on_click=self.search_paciente)
        self.lbl_paciente_seleccionado = ft.Text("Ningún paciente seleccionado", weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
        self.lv_resultados_pacientes = ft.ListView(height=0, spacing=5, padding=10) # Hidden initially

        # 2. Doctor Selector
        self.dd_medicos = ft.Dropdown(
            label="Médico Solicitante",
            expand=True,
            options=[],
            on_change=self.on_medico_change
        )

        # 3. Exam Selector (Combined Logic)
        self.dd_perfiles = ft.Dropdown(label="Agregar Perfil", expand=True, options=[])
        self.btn_add_perfil = ft.ElevatedButton("Agregar", on_click=self.add_perfil)

        self.dd_analitos = ft.Dropdown(label="Agregar Analito Individual", expand=True, options=[])
        self.btn_add_analito = ft.ElevatedButton("Agregar", on_click=self.add_analito)

        # 4. Order Summary
        self.table_items = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Precio")),
                ft.DataColumn(ft.Text("X")),
            ],
            rows=[]
        )

        # TOTAL PAYABLE - EDITABLE
        self.txt_total = ft.TextField(
            label="Total a Pagar",
            value="0.00",
            text_align=ft.TextAlign.RIGHT,
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # --- Layout ---

        section_paciente = ft.Container(
            content=ft.Column([
                ft.Text("1. Datos del Paciente", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.txt_buscar_paciente, self.btn_buscar_paciente]),
                self.lv_resultados_pacientes,
                ft.Divider(),
                ft.Row([ft.Icon(ft.Icons.PERSON), self.lbl_paciente_seleccionado])
            ]),
            padding=10, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5
        )

        section_medico = ft.Container(
            content=ft.Column([
                ft.Text("2. Médico", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.dd_medicos])
            ]),
            padding=10, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5
        )

        section_examenes = ft.Container(
            content=ft.Column([
                ft.Text("3. Selección de Exámenes", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.dd_perfiles, self.btn_add_perfil]),
                ft.Row([self.dd_analitos, self.btn_add_analito]),
            ]),
            padding=10, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5
        )

        section_resumen = ft.Container(
            content=ft.Column([
                ft.Text("Resumen de Orden", size=16, weight=ft.FontWeight.BOLD),
                self.table_items,
                ft.Divider(),
                ft.Row([ft.Text("Total: $", size=20, weight=ft.FontWeight.BOLD), self.txt_total], alignment=ft.MainAxisAlignment.END),
                ft.ElevatedButton("CREAR ORDEN", icon=ft.Icons.CHECK, on_click=self.save_orden, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE))
            ]),
            padding=10, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=5, bgcolor=ft.Colors.BLUE_50
        )

        self.controls = [
            ft.Text("Nueva Orden de Trabajo", size=24, weight=ft.FontWeight.BOLD),
            section_paciente,
            section_medico,
            section_examenes,
            section_resumen
        ]

        self.load_initial_data(initial=True)

    def load_initial_data(self, initial=False):
        try:
            # Load Medicos
            medicos_rows = db.get_all_medicos()
            self.medicos_cache = [Medico.from_tuple(m) for m in medicos_rows]
            self.dd_medicos.options = [ft.dropdown.Option(key=str(m.id), text=m.nombre) for m in self.medicos_cache]

            # Load Perfiles
            perfiles = db.get_all_perfiles()
            self.perfiles_cache = [PerfilExamen.from_tuple(p) for p in perfiles]
            # Exclude default profile from dropdown
            self.perfiles_cache = [p for p in self.perfiles_cache if p.nombre != "Examenes Individuales"]

            self.dd_perfiles.options = [ft.dropdown.Option(key=str(p.id), text=f"{p.nombre}") for p in self.perfiles_cache]

            # Load Analitos
            analitos = db.get_all_analitos()
            self.analitos_cache = [Analito.from_tuple(a) for a in analitos]
            self.dd_analitos.options = [ft.dropdown.Option(key=str(a.id), text=a.nombre) for a in self.analitos_cache]

            if not initial:
                self.update()
        except Exception as e:
            print(e)

    def search_paciente(self, e):
        term = self.txt_buscar_paciente.value
        if not term: return

        results = db.search_pacientes(term)
        self.lv_resultados_pacientes.controls.clear()

        if not results:
            self.lv_resultados_pacientes.controls.append(ft.Text("No se encontraron pacientes."))
            self.lv_resultados_pacientes.height = 30
        else:
            for r in results:
                p = Paciente.from_tuple(r)
                self.lv_resultados_pacientes.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON),
                        title=ft.Text(p.nombreCompleto),
                        subtitle=ft.Text(f"DNI: {p.dni} | {p.edad} {p.unidadEdad}"),
                        on_click=lambda e, item=p: self.select_paciente(item)
                    )
                )
            self.lv_resultados_pacientes.height = min(len(results) * 60, 200)

        self.update()

    def select_paciente(self, p: Paciente):
        self.selected_paciente_id = p.id
        self.lbl_paciente_seleccionado.value = f"{p.nombreCompleto} ({p.edad} {p.unidadEdad})"
        self.lbl_paciente_seleccionado.color = ft.Colors.BLACK
        self.lv_resultados_pacientes.controls.clear()
        self.lv_resultados_pacientes.height = 0
        self.txt_buscar_paciente.value = ""
        self.update()

    def on_medico_change(self, e):
        self.recalculate_prices()
        self.update()

    def add_perfil(self, e):
        pid = self.dd_perfiles.value
        if not pid: return

        perfil = next((p for p in self.perfiles_cache if str(p.id) == str(pid)), None)
        if perfil:
            self.selected_items.append({
                'type': 'perfil',
                'id': perfil.id,
                'nombre': perfil.nombre,
                'precio_base': perfil.precioEstandar,
                'precio': perfil.precioEstandar # Will be recalculated
            })
            self.recalculate_prices()
            self.refresh_table()

    def add_analito(self, e):
        aid = self.dd_analitos.value
        if not aid: return

        analito = next((a for a in self.analitos_cache if str(a.id) == str(aid)), None)
        if analito:
            self.selected_items.append({
                'type': 'analito',
                'id': analito.id,
                'nombre': analito.nombre,
                'precio_base': 0.0,
                'precio': 0.0
            })
            self.recalculate_prices()
            self.refresh_table()

    def recalculate_prices(self):
        medico_id = self.dd_medicos.value

        has_convenio = False
        if medico_id:
            medico = next((m for m in self.medicos_cache if str(m.id) == str(medico_id)), None)
            if medico and medico.tieneConvenio:
                has_convenio = True

        total = 0.0

        for item in self.selected_items:
            price = item['precio_base']

            if item['type'] == 'perfil' and has_convenio:
                # Check tariff
                special_price = db.get_tarifa_especial(int(medico_id), item['id'])
                if special_price is not None:
                    price = special_price

            item['precio'] = price
            total += price

        self.txt_total.value = f"{total:.2f}"

    def refresh_table(self):
        self.table_items.rows.clear()
        for i, item in enumerate(self.selected_items):
            self.table_items.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("Perfil" if item['type'] == 'perfil' else "Analito")),
                    ft.DataCell(ft.Text(item['nombre'])),
                    ft.DataCell(ft.Text(f"${item['precio']:.2f}")),
                    ft.DataCell(ft.IconButton(ft.Icons.DELETE, on_click=lambda e, idx=i: self.remove_item(idx))),
                ])
            )
        self.update()

    def remove_item(self, index):
        self.selected_items.pop(index)
        self.recalculate_prices()
        self.refresh_table()

    def save_orden(self, e):
        if not self.selected_paciente_id:
            self.page.open(ft.SnackBar(ft.Text("Seleccione un Paciente"), bgcolor=ft.Colors.RED))
            self.update()
            return

        if not self.selected_items:
            self.page.open(ft.SnackBar(ft.Text("Agregue al menos un examen"), bgcolor=ft.Colors.RED))
            self.update()
            return

        try:
            medico_id = self.dd_medicos.value

            try:
                final_price = float(self.txt_total.value)
            except ValueError:
                final_price = 0.0

            orden_id = db.create_orden_trabajo(self.selected_paciente_id, medico_id, self.selected_items, final_price)

            self.page.open(ft.SnackBar(ft.Text(f"Orden #{orden_id} Creada Exitosamente"), bgcolor=ft.Colors.GREEN))

            # Reset
            self.selected_paciente_id = None
            self.lbl_paciente_seleccionado.value = "Ningún paciente seleccionado"
            self.lbl_paciente_seleccionado.color = ft.Colors.RED
            self.selected_items = []
            self.txt_total.value = "0.00"
            self.refresh_table()

        except Exception as ex:
            print(f"Error creating order: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))
            self.update()
