import flet as ft
import db
import printer
from ui_theme import COLOR_PRIMARY, COLOR_ACCENT, COLOR_DARK_TEXT, COLOR_CARD_WHITE

def build_reports_tab(page: ft.Page, current_user):
    total_lbl = ft.Text("0.00 ₽", size=26, weight=ft.FontWeight.W_900, color=COLOR_PRIMARY)
    cash_lbl = ft.Text("0.00 ₽", size=15, weight=ft.FontWeight.BOLD, color="#059669")
    card_lbl = ft.Text("0.00 ₽", size=15, weight=ft.FontWeight.BOLD, color=COLOR_ACCENT)
    count_lbl = ft.Text("0 шт.", size=15, weight=ft.FontWeight.BOLD, color=COLOR_DARK_TEXT)
    shift_badge = ft.Text("", size=13, weight=ft.FontWeight.BOLD)
    report_preview = ft.Text("Нажмите кнопку отчета для формирования и печати.", size=12, color="#475569")

    def refresh_stats():
        is_open = db.get_setting("shift_open", "0") == "1"
        shift_badge.value = "Статус смены: ОТКРЫТА" if is_open else "Статус смены: ЗАКРЫТА"
        shift_badge.color = "#059669" if is_open else "#E11D48"

        rows = db.get_receipts()
        tot_sum = 0.0
        cash_sum = 0.0
        card_sum = 0.0
        for r_id, dt_str, tot, p_type, synced in rows:
            val = float(tot)
            tot_sum += val
            if "Наличные" in str(p_type):
                cash_sum += val
            else:
                card_sum += val

        total_lbl.value = f"{tot_sum:.2f} ₽"
        cash_lbl.value = f"{cash_sum:.2f} ₽"
        card_lbl.value = f"{card_sum:.2f} ₽"
        count_lbl.value = f"{len(rows)} шт."
        page.update()

    def open_shift_click(e):
        if db.get_setting("shift_open", "0") == "1":
            page.show_dialog(ft.SnackBar(ft.Text("Кассовая смена уже открыта"), bgcolor=COLOR_PRIMARY))
            return
        db.set_setting("shift_open", "1")
        body = f"ОТКРЫТИЕ КАССОВОЙ СМЕНЫ\nОператор: {current_user['name']}"
        ok, msg = printer.send_to_printer(body)
        report_preview.value = f"{body}\nСтатус печати: {msg}"
        refresh_stats()
        page.show_dialog(ft.SnackBar(ft.Text(f"Смена открыта. {msg}"), bgcolor="#059669" if ok else "#D97706"))

    def make_x_report(e):
        body = (
            f"X-ОТЧЁТ (БЕЗ ГАШЕНИЯ)\n"
            f"Оператор: {current_user['name']}\n"
            f"Чеков за смену: {count_lbl.value}\n"
            f"Наличные: {cash_lbl.value}\n"
            f"Безналичные (Карта): {card_lbl.value}\n"
            f"ИТОГО ВЫРУЧКА: {total_lbl.value}"
        )
        ok, msg = printer.send_to_printer(body)
        report_preview.value = f"{body}\nСтатус печати: {msg}"
        page.show_dialog(ft.SnackBar(ft.Text(f"X-отчёт: {msg}"), bgcolor=COLOR_PRIMARY))
        page.update()

    def make_z_report(e):
        if db.get_setting("shift_open", "0") != "1":
            page.show_dialog(ft.SnackBar(ft.Text("Смена уже закрыта"), bgcolor="#E11D48"))
            return
        body = (
            f"Z-ОТЧЁТ (ЗАКРЫТИЕ СМЕНЫ)\n"
            f"Оператор: {current_user['name']}\n"
            f"Чеков за смену: {count_lbl.value}\n"
            f"Наличные: {cash_lbl.value}\n"
            f"Безналичные (Карта): {card_lbl.value}\n"
            f"ИТОГО ЗА СМЕНУ: {total_lbl.value}\n"
            f"СМЕНА ЗАКРЫТА"
        )
        db.set_setting("shift_open", "0")
        ok, msg = printer.send_to_printer(body)
        report_preview.value = f"{body}\nСтатус печати: {msg}"
        refresh_stats()
        page.show_dialog(ft.SnackBar(ft.Text(f"Смена закрыта. {msg}"), bgcolor="#059669" if ok else "#D97706"))

    refresh_stats()

    container = ft.Container(
        expand=True, padding=14, visible=False,
        content=ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Text("Управление сменой и отчёты", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(
                    bgcolor=COLOR_CARD_WHITE, padding=14, border_radius=12,
                    content=ft.Column(spacing=6, controls=[
                        shift_badge,
                        ft.Divider(),
                        ft.Text("Выручка за текущую смену:", size=12, color="#64748B"),
                        total_lbl,
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Наличные:"), cash_lbl]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Безналичные (Терминал):"), card_lbl]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Оформлено чеков:"), count_lbl]),
                    ]),
                ),
                ft.Button("ОТКРЫТЬ КАССОВУЮ СМЕНУ", icon=ft.Icons.PLAY_CIRCLE_OUTLINE, bgcolor="#059669", color="white", height=46, on_click=open_shift_click),
                ft.Button("ПЕЧАТЬ X-ОТЧЁТА (БЕЗ ГАШЕНИЯ)", icon=ft.Icons.PRINT, bgcolor=COLOR_PRIMARY, color="white", height=46, on_click=make_x_report),
                ft.Button("ЗАКРЫТЬ СМЕНУ (Z-ОТЧЁТ)", icon=ft.Icons.LOCK_CLOCK, bgcolor="#E11D48", color="white", height=46, on_click=make_z_report),
                ft.Container(
                    bgcolor=COLOR_CARD_WHITE, padding=12, border_radius=10,
                    content=report_preview,
                ),
            ],
        ),
    )
    return container, refresh_stats
