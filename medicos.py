import flet as ft
from database import db
import threading

class MedicosView(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        # --- BUSCADOR ---
        self.search = ft.TextField(
            hint_text="Buscar médico por nombre o especialidad...",
            prefix_icon="search",
            border_radius=20,
            bgcolor="white",
            on_change=self.filtrar_optimizado,
            expand=True
        )
        
        # --- TABLA ---
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nombre", weight="bold")),
                ft.DataColumn(ft.Text("Especialidad", weight="bold")),
                ft.DataColumn(ft.Text("Teléfono", weight="bold")),
                ft.DataColumn(ft.Text("Convenio", weight="bold")),
                ft.DataColumn(ft.Text("Acciones", weight="bold")),
            ],
            width=float('inf'),
            rows=[],
            heading_row_color="#F5F5F5",
            data_row_max_height=60
        )
        
        # --- MODAL FORMULARIO ---
        self.dlg_nombre = ft.TextField(label="Nombre del Médico *", prefix_icon="person")
        self.dlg_esp = ft.TextField(label="Especialidad", prefix_icon="medical_services", value="General")
        self.dlg_tel = ft.TextField(label="Teléfono", prefix_icon="phone", input_filter=ft.InputFilter(regex_string=r"[0-9]"))
        
        # Switch para activar convenio (Si está activo, se pueden configurar precios especiales)
        self.dlg_convenio = ft.Switch(label="Tiene Convenio", value=False, active_color="#00ACC1")
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nuevo Médico", weight="bold"),
            content=ft.Column([
                self.dlg_nombre,
                self.dlg_esp,
                self.dlg_tel,
                ft.Container(height=10),
                ft.Container(content=self.dlg_convenio, bgcolor="#E0F7FA", padding=10, border_radius=10)
            ], tight=True, width=400),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cerrar_modal),
                ft.ElevatedButton("Guardar", on_click=self.guardar, bgcolor="#00ACC1", color="white")
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # --- ESTRUCTURA UI ---
        self.controls = [
            ft.Row([
                ft.Icon("medical_services", size=28, color="#37474F"),
                ft.Text("Directorio Médico", size=24, weight="bold", color="#37474F"), 
                ft.Container(expand=True), 
                ft.ElevatedButton(
                    "Nuevo Médico", 
                    icon="add", 
                    on_click=self.abrir_modal, 
                    bgcolor="#00ACC1", 
                    color="white"
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10),
            ft.Row([self.search]),
            ft.Container(
                content=self.table, 
                expand=True, 
                bgcolor="white", 
                border_radius=10, 
                padding=10,
                shadow=ft.BoxShadow(blur_radius=5, color="#0D000000")
            )
        ]
        
        self._debounce_timer = None
        self.cargar()

    def cargar(self, termino=""):
        try:
            data = db.buscar_medicos(termino)
            
            if self.table.rows is None: self.table.rows = []
            else: self.table.rows.clear()
                
            for m in data:
                # Icono visual para convenio
                icono_convenio = ft.Icon("check_circle", color="green") if m['tieneConvenio'] else ft.Icon("cancel", color="grey")
                
                self.table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(m['nombre'], weight="bold")),
                    ft.DataCell(ft.Text(m['especialidad'])),
                    ft.DataCell(ft.Text(m['telefono'] or "-")),
                    ft.DataCell(icono_convenio),
                    ft.DataCell(ft.IconButton("delete", icon_color="red", data=m['id'], on_click=self.eliminar, tooltip="Eliminar"))
                ]))
            
            if self.page: self.update()
            
        except Exception as e:
            print(f"Error cargando médicos: {e}")

    def filtrar_optimizado(self, e):
        if self._debounce_timer: self._debounce_timer.cancel()
        self._debounce_timer = threading.Timer(0.5, self.cargar, args=[e.control.value])
        self._debounce_timer.start()
    
    def abrir_modal(self, e):
        self.dlg_nombre.value = ""
        self.dlg_esp.value = "General"
        self.dlg_tel.value = ""
        self.dlg_convenio.value = False
        e.page.open(self.dialog)

    def cerrar_modal(self, e): e.page.close(self.dialog)

    def guardar(self, e):
        if not self.dlg_nombre.value:
            self.dlg_nombre.error_text = "Requerido"
            self.dlg_nombre.update()
            return

        try:
            db.agregar_medico({
                'nombre': self.dlg_nombre.value, 
                'especialidad': self.dlg_esp.value, 
                'telefono': self.dlg_tel.value,
                'convenio': self.dlg_convenio.value
            })
            
            e.page.snack_bar = ft.SnackBar(ft.Text("Médico registrado"), bgcolor="green")
            e.page.snack_bar.open = True
            e.page.close(self.dialog)
            self.cargar()
            e.page.update()
            
        except Exception as ex:
            e.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red")
            e.page.snack_bar.open = True
            e.page.update()

    def eliminar(self, e):
        try:
            db.eliminar_medico(e.control.data)
            self.cargar()
            e.page.snack_bar = ft.SnackBar(ft.Text("Médico eliminado"), bgcolor="orange")
            e.page.snack_bar.open = True
            e.page.update()
        except Exception as ex:
            print(f"Error eliminando: {ex}")