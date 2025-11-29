import flet as ft
from database import db

class StatCard(ft.Container):
    def __init__(self, titulo, valor, icono, bg, color):
        super().__init__()
        self.expand = 1
        self.padding = 20
        self.bgcolor = "white"
        self.border_radius = 12
        self.shadow = ft.BoxShadow(blur_radius=10, color="#0D000000")
        self.content = ft.Row([
            ft.Container(content=ft.Icon(icono, color=color, size=30), bgcolor=bg, border_radius=50, padding=15),
            ft.Column([
                ft.Text(titulo, size=14, color="#757575", weight="w500"),
                ft.Text(str(valor), size=28, weight="bold", color="#263238")
            ], spacing=2)
        ])

class DashboardView(ft.Column):
    def __init__(self):
        super().__init__()
        # Carga datos al iniciar
        stats = db.obtener_estadisticas()
        self.controls = [
            ft.Text("Dashboard", size=32, weight="bold", color="#37474F"),
            ft.Row([
                StatCard("Pacientes", stats[0], "people", "#E0F7FA", "#00ACC1"),
                StatCard("Órdenes Hoy", stats[1], "assignment", "#FFF3E0", "#FF9800"),
                StatCard("Médicos", stats[2], "medical_services", "#E0F2F1", "#00897B"),
            ], spacing=20)
        ]