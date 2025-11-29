import flet as ft
from database import db
from views.configuracion import ConfiguracionView

def main(page: ft.Page):
    page.title = "LIS - Lab Divino Niño"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Try to connect to DB
    # In sandbox, this will fail but app should continue.
    db_connected = db.connect()

    if not db_connected:
        page.snack_bar = ft.SnackBar(
            content=ft.Text("No se pudo conectar a la base de datos SQL Server local."),
            bgcolor=ft.colors.ERROR,
        )
        page.snack_bar.open = True
        page.update()
    else:
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Conectado a Base de Datos Exitosamente"),
            bgcolor=ft.colors.GREEN,
        )
        page.snack_bar.open = True
        page.update()

    # Navigation Rail logic
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.HOME, selected_icon=ft.icons.HOME_FILLED, label="Inicio"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS, selected_icon=ft.icons.SETTINGS_ODD, label="Configuración"
            ),
        ],
        on_change=lambda e: navigate(e.control.selected_index),
    )

    # Content Area
    content_area = ft.Column(expand=True)

    def navigate(index):
        content_area.controls.clear()
        if index == 0:
            content_area.controls.append(ft.Text("Bienvenido al Sistema de Laboratorio", size=20))
        elif index == 1:
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
