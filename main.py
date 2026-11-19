import flet as ft
import asyncio
import db
import printer
from ui_theme import (
    COLOR_PRIMARY, COLOR_ACCENT, COLOR_DARK_TEXT,
    COLOR_BG_LIGHT, COLOR_CARD_WHITE, build_splash, build_app_bar
)
from auth import build_login_screen
from catalog_editor import build_catalog_tab
from settings_view import build_settings_tab
from reports_view import build_reports_tab

async def main(page: ft.Page):
    db.init_db()
    page.title = "КРИСТАЛЛ-ПОС: Мобильная касса"
    page.bgcolor = COLOR_BG_LIGHT
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 410
    page.window.height = 820

    splash_view, progress_bar, status_lbl = build_splash()
    page.add(splash_view)
    page.update()

    steps = [
        (0.25, "Инициализация ядра КРИСТАЛЛ-ПОС..."),
        (0.55, "Проверка подключения оборудования..."),
        (0.85, "Загрузка номенклатуры и тарифов..."),
        (1.0, "Подготовка рабочего места оператора..."),
    ]
    for val, text in steps:
        await asyncio.sleep(0.65)
        progress_bar.value = val
        status_lbl.value = text
        page.update()
    await asyncio.sleep(0.45)

    def show_login():
        page.clean()
        page.add(build_login_screen(page, on_login_success=start_pos_session))
        page.update()

    def start_pos_session(current_user):
        page.clean()
        is_admin = current_user["role"] == "admin"
        cart = {}

        search_field = ft.TextField(
            hint_text="Штрих-код или название...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor=COLOR_CARD_WHITE,
            expand=True,
        )
        catalog_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=175)
        cart_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
        total_text = ft.Text("0.00 ₽", size=24, weight=ft.FontWeight.W_900, color=COLOR_PRIMARY)

        def refresh_catalog(e=None):
            catalog_list.controls.clear()
            q = (search_field.value or "").strip().lower()
            for b, name, price, stock in db.get_products():
                if q in name.lower() or q in b:
                    catalog_list.controls.append(
                        ft.Container(
                            bgcolor=COLOR_CARD_WHITE, padding=10, border_radius=8,
                            on_click=lambda ev, bc=b, nm=name, pr=price: add_to_cart(bc, nm, pr),
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(spacing=2, expand=True, controls=[
                                        ft.Text(name, weight=ft.FontWeight.W_600, size=14),
                                        ft.Text(f"ШК: {b} • Ост: {stock:g}", size=11, color="#64748B"),
                                    ]),
                                    ft.Text(f"{price:.2f} ₽", weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                                ],
                            ),
                        )
                    )
            page.update()

        search_field.on_change = refresh_catalog

        def open_scanner_dialog(e):
            scan_input = ft.TextField(label="Штрих-код товара", autofocus=True)
            def on_scan_submit(ev):
                code = (scan_input.value or "").strip()
                found = False
                for b, name, price, stock in db.get_products():
                    if b == code:
                        add_to_cart(b, name, price)
                        found = True
                        break
                page.pop_dialog()
                if found:
                    page.show_dialog(ft.SnackBar(ft.Text(f"Позиция {code} добавлена в чек"), bgcolor="#059669"))
                else:
                    page.show_dialog(ft.SnackBar(ft.Text(f"Штрих-код {code} не найден в справочнике"), bgcolor="#E11D48"))

            scan_input.on_submit = on_scan_submit
            dlg = ft.AlertDialog(
                title=ft.Row(controls=[ft.Icon(ft.Icons.QR_CODE_SCANNER, color=COLOR_PRIMARY), ft.Text("Сканер штрих-кода")]),
                content=ft.Column(tight=True, spacing=10, controls=[
                    ft.Container(
                        height=100, bgcolor="#0F172A", border_radius=10, alignment=ft.Alignment.CENTER,
                        content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                            ft.Icon(ft.Icons.CAMERA_ALT, color=COLOR_ACCENT, size=34),
                            ft.Text("Наведите камеру на штрих-код", color="white", size=12),
                        ]),
                    ),
                    scan_input,
                    ft.Button("ПОДТВЕРДИТЬ ВВОД", bgcolor=COLOR_ACCENT, color="white", width=260, on_click=on_scan_submit),
                ]),
            )
            page.show_dialog(dlg)
        def add_to_cart(b, name, price):
            if b in cart:
                cart[b]["qty"] += 1
            else:
                cart[b] = {"name": name, "price": price, "qty": 1}
            refresh_cart()

        def change_qty(b, delta):
            if b in cart:
                cart[b]["qty"] += delta
                if cart[b]["qty"] <= 0:
                    del cart[b]
            refresh_cart()

        def refresh_cart():
            cart_list.controls.clear()
            total = 0.0
            for b, item in cart.items():
                line_sum = item["price"] * item["qty"]
                total += line_sum
                cart_list.controls.append(
                    ft.Container(
                        bgcolor=COLOR_CARD_WHITE, padding=10, border_radius=8,
                        border=ft.Border.only(left=ft.BorderSide(4, COLOR_ACCENT)),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(spacing=2, expand=True, controls=[
                                    ft.Text(item["name"], weight=ft.FontWeight.BOLD, size=13),
                                    ft.Text(f"{item['price']:.2f} ₽ × {item['qty']} = {line_sum:.2f} ₽", size=12),
                                ]),
                                ft.Row(spacing=4, controls=[
                                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color="#E11D48", on_click=lambda ev, bc=b: change_qty(bc, -1)),
                                    ft.Text(str(item["qty"]), weight=ft.FontWeight.BOLD),
                                    ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_color="#059669", on_click=lambda ev, bc=b: change_qty(bc, 1)),
                                ]),
                            ],
                        ),
                    )
                )
            total_text.value = f"{total:.2f} ₽"
            page.update()

        def open_checkout(e):
            if db.get_setting("shift_open", "0") != "1":
                page.show_dialog(ft.SnackBar(ft.Text("Смена закрыта! Откройте смену во вкладке «Отчёты»."), bgcolor="#E11D48"))
                return
            if not cart:
                page.show_dialog(ft.SnackBar(ft.Text("Чек пуст! Выберите товары из каталога."), bgcolor="#E11D48"))
                return
            total = sum(i["price"] * i["qty"] for i in cart.values())
            cash_field = ft.TextField(label="Внесено покупателем (₽)", value=f"{total:.2f}", keyboard_type=ft.KeyboardType.NUMBER)
            change_txt = ft.Text("Сдача: 0.00 ₽", size=16, weight=ft.FontWeight.BOLD, color="#059669")

            def update_change(ev=None):
                try:
                    paid = float((cash_field.value or "0").replace(",", "."))
                    change_txt.value = f"Сдача: {max(0.0, paid - total):.2f} ₽"
                except ValueError:
                    change_txt.value = "Сдача: 0.00 ₽"
                page.update()

            def set_exact(ev):
                cash_field.value = f"{total:.2f}"
                update_change()

            cash_field.on_change = update_change

            def complete_payment(pay_label):
                lines = [f"{item['name']} x{item['qty']} = {item['price']*item['qty']:.2f}" for item in cart.values()]
                receipt_body = (
                    f"КАССОВЫЙ ЧЕК (ПРИХОД)\n"
                    f"Оператор: {current_user['name']}\n" +
                    "\n".join(lines) +
                    f"\nИТОГО: {total:.2f} ₽\nОплата: {pay_label}"
                )
                ok, print_msg = printer.send_to_printer(receipt_body)
                db.save_receipt(total, pay_label, cart)
                cart.clear()
                page.pop_dialog()
                refresh_cart()
                refresh_catalog()
                page.show_dialog(ft.SnackBar(ft.Text(f"Чек оформлен ({pay_label}). {print_msg}"), bgcolor="#059669" if ok else "#D97706"))

            dlg = ft.AlertDialog(
                title=ft.Text(f"К оплате: {total:.2f} ₽", weight=ft.FontWeight.BOLD),
                content=ft.Column(
                    tight=True, spacing=10,
                    controls=[
                        ft.Text("1. Наличный расчет:", weight=ft.FontWeight.BOLD, size=13),
                        cash_field,
                        ft.Button("Без сдачи", width=260, on_click=set_exact),
                        change_txt,
                        ft.Button("ОПЛАТИТЬ НАЛИЧНЫМИ", icon=ft.Icons.PAYMENTS, bgcolor=COLOR_PRIMARY, color="white", width=260, on_click=lambda ev: complete_payment("Наличные")),
                        ft.Divider(),
                        ft.Text("2. Безналичный расчет (внешний терминал):", weight=ft.FontWeight.BOLD, size=13),
                        ft.Button("ОПЛАЧЕНО КАРТОЙ", icon=ft.Icons.CREDIT_CARD, bgcolor=COLOR_ACCENT, color="white", width=260, on_click=lambda ev: complete_payment("Карта (Терминал)")),
                    ],
                ),
            )
            page.show_dialog(dlg)

        tab_pos = ft.Container(expand=True, padding=12, content=ft.Column(spacing=8, controls=[
            ft.Row(controls=[
                search_field,
                ft.Container(bgcolor=COLOR_PRIMARY, padding=12, border_radius=10, on_click=open_scanner_dialog, content=ft.Icon(ft.Icons.QR_CODE_SCANNER, color="white")),
            ]),
            catalog_list, ft.Divider(height=4), cart_list,
            ft.Container(bgcolor=COLOR_CARD_WHITE, padding=12, border_radius=12, content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(spacing=0, controls=[ft.Text("ИТОГО:", size=11), total_text]),
                    ft.Button("ПРОБИТЬ ЧЕК", bgcolor=COLOR_ACCENT, color="white", height=46, on_click=open_checkout),
                ],
            )),
        ]))

        receipts_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        def load_receipts():
            receipts_col.controls.clear()
            for r_id, dt_str, tot, p_type, synced in db.get_receipts():
                status = "Передан на сервер" if synced else "Сохранен локально"
                receipts_col.controls.append(ft.Container(bgcolor=COLOR_CARD_WHITE, padding=12, border_radius=10, content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=2, controls=[ft.Text(f"Чек №{r_id} • {p_type}", weight=ft.FontWeight.BOLD), ft.Text(f"{dt_str} ({status})", size=11)]),
                        ft.Text(f"{tot:.2f} ₽", weight=ft.FontWeight.W_900),
                    ],
                )))
            page.update()

        tab_receipts = ft.Container(expand=True, padding=14, visible=False, content=ft.Column(controls=[
            ft.Text("Журнал кассовых чеков", size=18, weight=ft.FontWeight.BOLD), receipts_col
        ]))

        tab_reports, refresh_reports = build_reports_tab(page, current_user)
        tab_catalog, reload_editor = build_catalog_tab(page, on_catalog_updated=refresh_catalog)
        tab_settings = build_settings_tab(page, current_user, on_data_changed=lambda: (refresh_catalog(), reload_editor()))

        tabs = [tab_pos, tab_receipts, tab_reports]
        nav_destinations = [
            ft.NavigationBarDestination(icon=ft.Icons.POINT_OF_SALE, label="Касса"),
            ft.NavigationBarDestination(icon=ft.Icons.RECEIPT_LONG, label="Чеки"),
            ft.NavigationBarDestination(icon=ft.Icons.ASSESSMENT, label="Отчёты"),
        ]
        if is_admin:
            tabs.append(tab_catalog)
            nav_destinations.append(ft.NavigationBarDestination(icon=ft.Icons.INVENTORY_2, label="Товары"))
        tabs.append(tab_settings)
        nav_destinations.append(ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Настройки"))

        def on_nav(e):
            idx = e.control.selected_index
            for i, t in enumerate(tabs):
                t.visible = (i == idx)
            if idx == 1:
                load_receipts()
            elif idx == 2:
                refresh_reports()
            elif is_admin and idx == 3:
                reload_editor()
            page.update()

        nav_bar = ft.NavigationBar(selected_index=0, on_change=on_nav, destinations=nav_destinations)
        page.add(build_app_bar(current_user["name"], on_logout=show_login), *tabs, nav_bar)
        refresh_catalog()

    show_login()

ft.run(main)
