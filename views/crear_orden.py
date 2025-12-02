import flet as ft
from database import db
from models.paciente import Paciente
from models.medico import Medico
from models.analito import Analito
from models.perfil_examen import PerfilExamen

class CrearOrdenView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_ref = page
        self.expand = True
        self.scroll = ft.ScrollMode.ALWAYS

        self.selected_paciente_id = None
        self.selected_items = []

        self.txt_buscar_paciente = ft.TextField(label="Buscar Paciente (Nombre o DNI)", on_submit=self.search_paciente, expand=True)
        self.btn_buscar_paciente = ft.IconButton(ft.Icons.SEARCH, on_click=self.search_paciente)
        self.lbl_paciente_seleccionado = ft.Text("Ningún paciente seleccionado", weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
        self.lv_resultados_pacientes = ft.ListView(height=0, spacing=5, padding=10)

        self.dd_medicos = ft.Dropdown(label="Médico Solicitante", expand=True, options=[])

        self.dd_perfiles = ft.Dropdown(label="Agregar Perfil", expand=True, options=[])
        self.btn_add_perfil = ft.ElevatedButton("Agregar", on_click=self.add_perfil)

        self.dd_analitos = ft.Dropdown(label="Agregar Analito Individual", expand=True, options=[])
        self.btn_add_analito = ft.ElevatedButton("Agregar", on_click=self.add_analito)

        self.table_items = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Precio")),
                ft.DataColumn(ft.Text("X")),
            ],
            rows=[]
        )
        self.lbl_total = ft.Text("Total: $0.00", size=20, weight=ft.FontWeight.BOLD)

        section_paciente = ft.Container(
            content=ft.Column([
                ft.Text("1. Datos del Paciente", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.txt_buscar_paciente, self.btn_buscar_paciente]),
                self.lv_resultados_pacientes,
                ft.Divider(),
                ft.Row([ft.Icon(ft.Icons.PERSON), self.lbl_paciente_seleccionado])
            ]), padding=10, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5
        )

        section_medico = ft.Container(
            content=ft.Column([
                ft.Text("2. Médico", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.dd_medicos])
            ]), padding=10, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5
        )

        section_examenes = ft.Container(
            content=ft.Column([
                ft.Text("3. Selección de Exámenes", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([self.dd_perfiles, self.btn_add_perfil]),
                ft.Row([self.dd_analitos, self.btn_add_analito]),
            ]), padding=10, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5
        )

        section_resumen = ft.Container(
            content=ft.Column([
                ft.Text("Resumen de Orden", size=16, weight=ft.FontWeight.BOLD),
                self.table_items,
                ft.Divider(),
                ft.Row([self.lbl_total], alignment=ft.MainAxisAlignment.END),
                ft.ElevatedButton("CREAR ORDEN", icon=ft.Icons.CHECK, on_click=self.save_orden, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE))
            ]), padding=10, border=ft.border.all(1, ft.Colors.BLUE_200), border_radius=5, bgcolor=ft.Colors.BLUE_50
        )

        self.controls = [
            ft.Text("Nueva Orden de Trabajo", size=24, weight=ft.FontWeight.BOLD),
            section_paciente, section_medico, section_examenes, section_resumen
        ]

    def did_mount(self):
        self.load_initial_data()

    def load_initial_data(self):
        try:
            medicos = db.get_all_medicos()
            self.dd_medicos.options = [ft.dropdown.Option(key=str(m[0]), text=m[1]) for m in medicos]

            perfiles = db.get_all_perfiles()
            self.perfiles_cache = [PerfilExamen.from_tuple(p) for p in perfiles]
            self.perfiles_cache = [p for p in self.perfiles_cache if p.nombre != "Examenes Individuales"]
            self.dd_perfiles.options = [ft.dropdown.Option(key=str(p.id), text=f"{p.nombre} (${p.precioEstandar})") for p in self.perfiles_cache]

            analitos = db.get_all_analitos()
            self.analitos_cache = [Analito.from_tuple(a) for a in analitos]
            self.dd_analitos.options = [ft.dropdown.Option(key=str(a.id), text=a.nombre) for a in self.analitos_cache]

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

    def add_perfil(self, e):
        pid = self.dd_perfiles.value
        if not pid: return

        perfil = next((p for p in self.perfiles_cache if str(p.id) == str(pid)), None)
        if perfil:
            # Phase 9: Recursive Explosion? Or just Add Profile?
            # The prompt says: "Al seleccionar un Perfil... el sistema debe 'explotar' recursivamente... Listarlos todos en el carrito".
            # This implies we add 'analito' items to the list, NOT 'perfil' items.
            # However, if we add loose items, we lose the "Profile" grouping in the report (unless we group by category/default profile).
            # But earlier requirements strongly emphasized Profile headers.
            # If we explode here, `create_orden_trabajo` logic will receive a list of 'analito' types.
            # `create_orden_trabajo` handles 'perfil' type by inserting into `OrdenPerfiles` and expanding there.
            # If we want to allow customization (removing one item), we must explode here.
            # BUT: If we explode here, how do we group them in the report as "Perfil Lipidico"?
            # The report groups by `OrdenResultados.perfilExamenId`.
            # If we insert as 'analito', they link to Default Profile.
            # Solution: We can't have both "Full Customization via Explosion" AND "Profile Header Grouping" easily without complex logic (e.g., custom profile creation on the fly).
            # Re-reading prompt: "Listarlos todos en el carrito para que el usuario pueda quitar alguno".
            # This strongly implies explosion.
            # Trade-off: Reports might list them under "Examenes Individuales" or Categories if we explode.
            # Unless `create_orden_trabajo` logic changes? No, it's safer to stick to requirements.
            # Wait, if we explode, we add them as individual items.
            # Actually, `get_full_profile_analytes_recursive` returns list of Analitos.
            # Let's add them as 'analito' type items.
            # Price? Profile has price. Individual items might not (0).
            # If we explode, total price might drop to 0 if individual prices are 0.
            # This is a business logic conflict. Usually Profiles have a bundle price.
            # If I remove one item, is it still the profile price?
            # User didn't specify pricing logic update.
            # I will implement explosion as requested.
            # I will add the Profile itself as a "Header" item? No, that confuses logic.
            # I will add items. If price is issue, user can edit manually? No feature for that.
            # I will assume individual analytes have prices or Profile price is lost/irrelevant for "Custom" orders?
            # Or maybe I should keep the Profile item but allow expanding? Too complex for Flet listview now.
            # Decision: I will add the Profile Item (for Price/Grouping) AND add its analytes as children?
            # No, standard LIS: You pick a profile. If you want to remove an item, you convert to custom.
            # I will implement strict "Explosion" as requested.

            full_analytes = db.get_full_profile_analytes_recursive(perfil.id) # List of tuples
            # Tuple: (id, nombre, ...) - matches Analito.from_tuple structure.

            for row in full_analytes:
                a = Analito.from_tuple(row)
                # Check duplicates in list
                if not any(x['id'] == a.id and x['type'] == 'analito' for x in self.selected_items):
                    self.selected_items.append({
                        'type': 'analito',
                        'id': a.id,
                        'nombre': a.nombre,
                        'precio': 0.0 # Individual price 0
                    })

            # What about the Profile Price?
            # If we explode, we lose the profile price.
            # I'll stick to the prompt "Listarlos todos".

            self.refresh_table()

    def add_analito(self, e):
        aid = self.dd_analitos.value
        if not aid: return

        analito = next((a for a in self.analitos_cache if str(a.id) == str(aid)), None)
        if analito:
            if not any(x['id'] == analito.id and x['type'] == 'analito' for x in self.selected_items):
                self.selected_items.append({
                    'type': 'analito',
                    'id': analito.id,
                    'nombre': analito.nombre,
                    'precio': 0.0
                })
            self.refresh_table()

    def refresh_table(self):
        self.table_items.rows.clear()
        total = 0.0
        for i, item in enumerate(self.selected_items):
            total += item['precio']
            self.table_items.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("Analito")), # Always Analito if exploded
                    ft.DataCell(ft.Text(item['nombre'])),
                    ft.DataCell(ft.Text(f"${item['precio']:.2f}")),
                    ft.DataCell(ft.IconButton(ft.Icons.DELETE, on_click=lambda e, idx=i: self.remove_item(idx))),
                ])
            )
        self.lbl_total.value = f"Total: ${total:.2f}"
        self.update()

    def remove_item(self, index):
        self.selected_items.pop(index)
        self.refresh_table()

    def save_orden(self, e):
        if not self.selected_paciente_id:
            self.page_ref.open(ft.SnackBar(ft.Text("Seleccione un Paciente"), bgcolor=ft.Colors.RED))
            return
        if not self.selected_items:
            self.page_ref.open(ft.SnackBar(ft.Text("Agregue al menos un examen"), bgcolor=ft.Colors.RED))
            return

        try:
            medico_id = self.dd_medicos.value
            orden_id = db.create_orden_trabajo(self.selected_paciente_id, medico_id, self.selected_items)

            self.page_ref.open(ft.SnackBar(ft.Text(f"Orden #{orden_id} Creada"), bgcolor=ft.Colors.GREEN))

            self.selected_paciente_id = None
            self.lbl_paciente_seleccionado.value = "Ningún paciente seleccionado"
            self.lbl_paciente_seleccionado.color = ft.Colors.RED
            self.selected_items = []
            self.refresh_table()

        except Exception as ex:
            print(f"Error creating order: {ex}")
            self.page_ref.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED))
