import flet as ft
from datetime import datetime

COLOR_PRIMARY = "#0D47A1"      # Сапфировый синий
COLOR_ACCENT = "#00ACC1"       # Кристально-бирюзовый
COLOR_DARK_TEXT = "#1E293B"    # Графитовый текст
COLOR_BG_LIGHT = "#F1F5F9"     # Светлый фон
COLOR_CARD_WHITE = "#FFFFFF"   # Белые карточки

def build_splash():
    progress = ft.ProgressBar(width=250, value=0.1, color="#4DD0E1", bgcolor="#1565C0", border_radius=6)
    status_label = ft.Text("Запуск системы...", size=13, color="#E0F7FA", weight=ft.FontWeight.W_500)

    container = ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=["#0A2472", "#0D47A1", "#006064"],
        ),
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            controls=[
                ft.Container(
                    width=110, height=110, bgcolor="#1AFFFFFF", border_radius=30,
                    alignment=ft.Alignment.CENTER,
                    border=ft.Border.all(2, "#4DD0E1"),
                    shadow=ft.BoxShadow(blur_radius=28, color="#6000ACC1"),
                    content=ft.Icon(ft.Icons.DIAMOND, size=62, color="#4DD0E1"),
                ),
                ft.Container(height=6),
                ft.Text("КРИСТАЛЛ-ПОС", size=32, weight=ft.FontWeight.W_900, color="white"),
                ft.Container(
                    bgcolor=COLOR_ACCENT,
                    padding=ft.Padding.symmetric(horizontal=20, vertical=6),
                    border_radius=20,
                    content=ft.Text("МОБИЛЬНАЯ КАССА", size=13, weight=ft.FontWeight.BOLD, color="white"),
                ),
                ft.Container(height=28),
                progress,
                status_label,
                ft.Container(height=36),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                    border_radius=8,
                    bgcolor="#15FFFFFF",
                    content=ft.Text("© 2026 ЗАО «НПО Кристалл-Софт»", size=11, color="#B2EBF2"),
                ),
            ],
        ),
    )
    return container, progress, status_label

def build_app_bar(user_name="", on_logout=None):
    now_str = datetime.now().strftime("%d.%m %H:%M")
    return ft.Container(
        bgcolor=COLOR_PRIMARY,
        padding=ft.Padding.only(left=14, right=10, top=30, bottom=12),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(
                            bgcolor=COLOR_ACCENT, padding=6, border_radius=8,
                            content=ft.Icon(ft.Icons.DIAMOND, color="white", size=18),
                        ),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Text("КРИСТАЛЛ-ПОС", size=15, weight=ft.FontWeight.W_900, color="white"),
                                ft.Text(f"{user_name} • {now_str}", size=11, color="#BBDEFB"),
                            ],
                        ),
                    ],
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color="white",
                    tooltip="Сменить оператора",
                    on_click=lambda e: on_logout() if on_logout else None,
                ),
            ],
        ),
    )
