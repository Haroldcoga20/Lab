import flet as ft
from views.analitos import AnalitosView
from views.perfiles import PerfilesView

def ConfiguracionView(page: ft.Page):
    t = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Analitos",
                content=AnalitosView()
            ),
            ft.Tab(
                text="Perfiles",
                content=PerfilesView()
            ),
        ],
        expand=True,
    )

    return ft.Column(
        [
            ft.Text("Módulo de Configuración", size=30, weight=ft.FontWeight.BOLD),
            t
        ],
        expand=True
    )
