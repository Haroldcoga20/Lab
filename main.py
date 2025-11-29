import flet as ft
from dashboard import DashboardView

def main(page: ft.Page):
    page.title = "LIS - Divino Niño"
    page.theme_mode = "light"
    page.bgcolor = "#ECEFF1"
    page.window_min_width = 1000
    page.window_min_height = 700
    
    # 1. Dashboard inicial
    dashboard = DashboardView()
    
    # 2. Vistas vacías (Lazy Loading)
    vistas = {
        0: dashboard,
        1: None, # Pacientes
        2: None, # Órdenes
        3: None, # Médicos (AHORA SÍ FUNCIONARÁ)
        4: None  # Configuración
    }
    
    body = ft.Container(content=dashboard, expand=True, padding=20)

    def cambiar_ruta(e):
        idx = e.control.selected_index
        
        # --- LOGICA DE CARGA PEREZOSA ---
        if idx == 1 and vistas[1] is None:
            body.content = ft.ProgressRing()
            page.update()
            from pacientes import PacientesView
            vistas[1] = PacientesView()
            
        elif idx == 2 and vistas[2] is None:
            body.content = ft.ProgressRing()
            page.update()
            from ordenes import OrdenesView
            vistas[2] = OrdenesView()

        elif idx == 3 and vistas[3] is None:
            body.content = ft.ProgressRing()
            page.update()
            # IMPORTAMOS EL NUEVO MÓDULO
            from medicos import MedicosView
            vistas[3] = MedicosView()
            
        elif idx == 4 and vistas[4] is None:
            body.content = ft.ProgressRing()
            page.update()
            from configuracion import ConfiguracionView
            vistas[4] = ConfiguracionView()
            
        # --- MOSTRAR VISTA ---
        if vistas.get(idx):
            body.content = vistas[idx]
        else:
            body.content = ft.Container(
                content=ft.Text("Módulo en construcción...", size=20, color="grey"),
                alignment=ft.alignment.center
            )
            
        body.update()

    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type="all",
        extended=True,
        leading=ft.Icon("science", color="cyan", size=40),
        bgcolor="white",
        destinations=[
            ft.NavigationRailDestination(icon="dashboard", label="Inicio"),
            ft.NavigationRailDestination(icon="people", label="Pacientes"),
            ft.NavigationRailDestination(icon="assignment", label="Órdenes"),
            ft.NavigationRailDestination(icon="medical_services", label="Médicos"),
            ft.NavigationRailDestination(icon="settings", label="Config"),
        ],
        on_change=cambiar_ruta
    )

    page.add(ft.Row([sidebar, ft.VerticalDivider(width=1), body], expand=True))

ft.app(target=main)