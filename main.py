import flet as ft
from database import db
from views.configuracion import ConfiguracionView
from views.pacientes import PacientesView
from views.crear_orden import CrearOrdenView
from views.resultados import ResultadosView
from views.ordenes import OrdenesView

def main(page: ft.Page):
    page.title = "LIS - Lab Divino Niño"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Try to connect to DB
    # In sandbox, this will fail but app should continue.
    db_connected = db.connect()

    if not db_connected:
        page.open(ft.SnackBar(
            content=ft.Text("No se pudo conectar a la base de datos SQL Server local."),
            bgcolor=ft.Colors.RED,
        ))
    else:
        page.open(ft.SnackBar(
            content=ft.Text("Conectado a Base de Datos Exitosamente"),
            bgcolor=ft.Colors.GREEN,
        ))

    # Navigation Rail logic
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME, selected_icon=ft.Icons.HOME_FILLED, label="Inicio"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE, selected_icon=ft.Icons.PEOPLE, label="Pacientes"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ADD_CIRCLE_OUTLINE, selected_icon=ft.Icons.ADD_CIRCLE, label="Crear Orden"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SCIENCE, selected_icon=ft.Icons.SCIENCE, label="Resultados"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PRINT, selected_icon=ft.Icons.PRINT, label="Informes"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS, selected_icon=ft.Icons.SETTINGS_ODD, label="Configuración"
            ),
        ],
        on_change=lambda e: navigate(e.control.selected_index),
    )

    # Content Area
    content_area = ft.Column(expand=True)

    def navigate(index):
        # Cleanup: Remove FAB if exists from previous view
        page.floating_action_button = None
        page.update()

        content_area.controls.clear()
        if index == 0:
            content_area.controls.append(ft.Text("Bienvenido al Sistema de Laboratorio", size=20))
        elif index == 1:
            content_area.controls.append(PacientesView())
        elif index == 2:
            content_area.controls.append(CrearOrdenView())
        elif index == 3:
            content_area.controls.append(ResultadosView())
        elif index == 4:
            content_area.controls.append(OrdenesView())
        elif index == 5:
            content_area.controls.append(ConfiguracionView(page))
        page.update()

    # Initial Route
    navigate(0)

    page.add(
        ft.Row(
            [
                rail,
                ft.VerticalDivider(width=1),
                content_area,
            ],
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
