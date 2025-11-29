import flet as ft
from database import db
import threading

class PacientesView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self._debounce_timer = None
        
        # Variable para saber qué paciente se está editando (None = Nuevo)
        self.editando_id = None 

        # --- BUSCADOR ---
        self.search = ft.TextField(
            hint_text="Buscar por nombre, DNI o historia...", 
            prefix_icon="search",
            on_change=self.filtrar_optimizado,
            border_radius=20,
            bgcolor="white",
            expand=True
        )
        
        # --- TABLA ---
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nombre Completo", weight="bold")),
                ft.DataColumn(ft.Text("Edad", weight="bold")),
                ft.DataColumn(ft.Text("DNI", weight="bold")),
                ft.DataColumn(ft.Text("Teléfono", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            width=float('inf'),
            rows=[],
            heading_row_color="#F5F5F5",
            data_row_max_height=60
        )
        
        # --- FORMULARIO ---
        self.dlg_nombre = ft.TextField(label="Nombre Completo *", prefix_icon="person")
        self.dlg_edad = ft.TextField(label="Edad *", width=100, input_filter=ft.InputFilter(regex_string=r"[0-9]"))
        self.dlg_unidad = ft.Dropdown(
            label="Unidad", 
            options=[ft.dropdown.Option("Años"), ft.dropdown.Option("Meses"), ft.dropdown.Option("Días")], 
            value="Años", width=100
        )
        self.dlg_genero = ft.Dropdown(
            label="Género *", 
            options=[ft.dropdown.Option("Masculino"), ft.dropdown.Option("Femenino")], 
            value="Masculino", prefix_icon="male"
        )
        self.dlg_dni = ft.TextField(label="DNI / Cédula", prefix_icon="badge")
        self.dlg_tel = ft.TextField(label="Teléfono", prefix_icon="phone", input_filter=ft.InputFilter(regex_string=r"[0-9]"))
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Datos del Paciente", weight="bold"),
            content=ft.Column([
                self.dlg_nombre, 
                ft.Row([self.dlg_edad, self.dlg_unidad], spacing=10), 
                self.dlg_genero, 
                self.dlg_dni, 
                self.dlg_tel
            ], tight=True, width=400),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cerrar_modal),
                ft.ElevatedButton("Guardar", on_click=self.guardar, bgcolor="#00ACC1", color="white")
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # --- UI ---
        self.controls = [
            ft.Row([
                ft.Icon("people", size=28, color="#37474F"),
                ft.Text("Gestión de Pacientes", size=24, weight="bold", color="#37474F"), 
                ft.Container(expand=True), 
                ft.ElevatedButton("Nuevo Paciente", icon="add", on_click=self.abrir_nuevo, bgcolor="#00ACC1", color="white")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10),
            ft.Row([self.search]),
            ft.Container(content=self.table, expand=True, bgcolor="white", border_radius=10, padding=10, shadow=ft.BoxShadow(blur_radius=5, color="#0D000000"))
        ]
        self.cargar()

    def cargar(self, termino=""):
        try:
            data = db.buscar_pacientes(termino)
            if self.table.rows is None: self.table.rows = []
            else: self.table.rows.clear()
                
            for p in data:
                self.table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(p['nombreCompleto'], weight="bold")),
                    ft.DataCell(ft.Text(f"{p['edad']} {p['unidadEdad']}")),
                    ft.DataCell(ft.Text(p['dni'] or "-")),
                    ft.DataCell(ft.Text(p['telefono'] or "-")),
                    ft.DataCell(ft.Row([
                        # AQUÍ ESTÁ LA MAGIA: Conectamos el botón Editar
                        ft.IconButton("edit", icon_color="blue", data=p, on_click=self.editar_paciente_click, tooltip="Editar"),
                        ft.IconButton("delete", icon_color="red", data=p['id'], on_click=self.eliminar, tooltip="Eliminar")
                    ]))
                ]))
            if self.page: self.update()
        except Exception as e:
            print(f"Error cargando tabla: {e}")

    def filtrar_optimizado(self, e):
        if self._debounce_timer: self._debounce_timer.cancel()
        self._debounce_timer = threading.Timer(0.5, self.cargar, args=[e.control.value])
        self._debounce_timer.start()
    
    def abrir_nuevo(self, e):
        self.editando_id = None # Modo Nuevo
        self.dlg_nombre.value = ""
        self.dlg_edad.value = ""
        self.dlg_dni.value = ""
        self.dlg_tel.value = ""
        self.dlg_unidad.value = "Años"
        self.dlg_genero.value = "Masculino"
        
        self.dlg_nombre.error_text = None
        self.dlg_edad.error_text = None
        e.page.open(self.dialog)

    def editar_paciente_click(self, e):
        # 1. Obtener datos del paciente desde el botón
        p = e.control.data 
        self.editando_id = p['id'] # Modo Edición
        
        # 2. Llenar formulario
        self.dlg_nombre.value = p['nombreCompleto']
        self.dlg_edad.value = str(p['edad'])
        self.dlg_unidad.value = p['unidadEdad']
        self.dlg_genero.value = p['genero']
        self.dlg_dni.value = p['dni'] or ""
        self.dlg_tel.value = p['telefono'] or ""
        
        # 3. Abrir modal
        self.dlg_nombre.error_text = None
        self.dlg_edad.error_text = None
        e.page.open(self.dialog)

    def cerrar_modal(self, e): e.page.close(self.dialog)

    def guardar(self, e):
        if not self.dlg_nombre.value or not self.dlg_edad.value:
            self.dlg_nombre.error_text = "Requerido" if not self.dlg_nombre.value else None
            self.dlg_edad.error_text = "Requerido" if not self.dlg_edad.value else None
            self.dlg_nombre.update()
            self.dlg_edad.update()
            return

        datos = {
            'nombre': self.dlg_nombre.value, 
            'edad': self.dlg_edad.value, 
            'unidad': self.dlg_unidad.value,
            'genero': self.dlg_genero.value, 
            'dni': self.dlg_dni.value, 
            'telefono': self.dlg_tel.value
        }

        try:
            if self.editando_id:
                # ACTUALIZAR
                db.editar_paciente(self.editando_id, datos)
                msg = "Paciente actualizado"
            else:
                # CREAR NUEVO
                db.agregar_paciente(datos)
                msg = "Paciente guardado"
            
            e.page.close(self.dialog)
            self.mostrar_snack(e, msg, "green")
            self.cargar()
            
        except Exception as ex:
            self.mostrar_snack(e, f"Error: {ex}", "red")

    def eliminar(self, e):
        try:
            db.eliminar_paciente(e.control.data)
            self.mostrar_snack(e, "Paciente eliminado", "orange")
            self.cargar()
        except Exception as ex:
            print(f"Error eliminando: {ex}")

    def mostrar_snack(self, e, texto, color):
        e.page.snack_bar = ft.SnackBar(ft.Text(texto), bgcolor=color)
        e.page.snack_bar.open = True
        e.page.update()