import flet as ft
import db
import sync
import printer
from ui_theme import COLOR_PRIMARY, COLOR_ACCENT, COLOR_DARK_TEXT, COLOR_CARD_WHITE

def build_settings_tab(page: ft.Page, current_user, on_data_changed):
    is_admin = current_user["role"] == "admin"
    status_text = ft.Text("", size=12, color=COLOR_PRIMARY, weight=ft.FontWeight.BOLD)

    new_pin_field = ft.TextField(label="Новый PIN-код (4 цифры)", max_length=4, keyboard_type=ft.KeyboardType.NUMBER)
    def save_my_pin(e):
        val = (new_pin_field.value or "").strip()
        if len(val) == 4 and val.isdigit():
            db.update_user_pin(current_user["id"], val)
            current_user["pin"] = val
            new_pin_field.value = ""
            page.show_dialog(ft.SnackBar(ft.Text("PIN-код доступа успешно обновлен"), bgcolor="#059669"))
        else:
            page.show_dialog(ft.SnackBar(ft.Text("Введите ровно 4 цифры"), bgcolor="#E11D48"))

    pin_card = ft.Container(
        bgcolor=COLOR_CARD_WHITE, padding=14, border_radius=10,
        content=ft.Column(
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Text(f"Оператор: {current_user['name']} ({'Администратор' if is_admin else 'Кассир'})", weight=ft.FontWeight.BOLD),
                new_pin_field,
                ft.Button("Сохранить новый PIN", bgcolor=COLOR_PRIMARY, color="white", height=42, on_click=save_my_pin),
            ],
        ),
    )

    admin_controls = []
    if is_admin:
        mode_radio = ft.RadioGroup(
            value=db.get_setting("work_mode", "autonomous"),
            content=ft.Column(spacing=4, controls=[
                ft.Radio(value="autonomous", label="Автономный режим"),
                ft.Radio(value="network", label="Сетевой режим (Центральный сервер)"),
            ]),
        )
        shop_field = ft.TextField(label="Наименование торгового объекта", value=db.get_setting("shop_name", "Магазин «Кристалл»"))
        ip_field = ft.TextField(label="IP сервера «КРИСТАЛЛ-ПОС 4.0»", value=db.get_setting("server_ip", "192.168.1.100"))

        printer_type_dd = ft.Dropdown(
            label="Подключение чекового принтера",
            value=db.get_setting("printer_type", "bluetooth"),
            options=[
                ft.dropdown.Option(key="bluetooth", text="Bluetooth (Мобильный принтер)"),
                ft.dropdown.Option(key="wifi", text="Wi-Fi / LAN (Сетевой принтер)"),
            ],
        )
        printer_addr_field = ft.TextField(
            label="MAC-адрес Bluetooth или IP принтера",
            hint_text="Например: 00:11:22:33:44:55 или 192.168.1.200",
            value=db.get_setting("printer_addr", ""),
        )

        def save_sys_settings(e):
            db.set_setting("work_mode", mode_radio.value)
            db.set_setting("shop_name", (shop_field.value or "").strip())
            db.set_setting("server_ip", (ip_field.value or "").strip())
            db.set_setting("printer_type", printer_type_dd.value)
            db.set_setting("printer_addr", (printer_addr_field.value or "").strip())
            status_text.value = "Параметры оборудования и сети сохранены."
            status_text.color = "#059669"
            page.update()

        def test_printer_click(e):
            db.set_setting("printer_type", printer_type_dd.value)
            db.set_setting("printer_addr", (printer_addr_field.value or "").strip())
            ok, msg = printer.send_to_printer("ТЕСТОВАЯ ПЕЧАТЬ\nПроверка связи с чековым принтером\nПечать выполнена успешно.")
            status_text.value = msg
            status_text.color = "#059669" if ok else "#E11D48"
            page.update()

        def sync_all_from_pc(e):
            ip = (ip_field.value or "").strip()
            db.set_setting("server_ip", ip)
            try:
                p_cnt = sync.pull_catalog(ip)
                u_cnt = sync.pull_users(ip)
                on_data_changed()
                refresh_users_list()
                status_text.value = f"Синхронизация завершена: номенклатура ({p_cnt}), персонал ({u_cnt})."
                status_text.color = "#059669"
            except Exception as ex:
                status_text.value = f"Ошибка соединения с сервером: {ex}"
                status_text.color = "#E11D48"
            page.update()
        def push_all_to_pc(e):
            ip = (ip_field.value or "").strip()
            try:
                c_cnt = sync.push_receipts(ip)
                status_text.value = f"Передано учетных чеков на сервер: {c_cnt}."
                status_text.color = "#059669"
            except Exception as ex:
                status_text.value = f"Ошибка передачи данных: {ex}"
                status_text.color = "#E11D48"
            page.update()

        def remove_net_users(e):
            db.clear_network_users()
            db.set_setting("work_mode", "autonomous")
            mode_radio.value = "autonomous"
            refresh_users_list()
            status_text.value = "Сетевые профили отключены. Активирован автономный режим."
            status_text.color = COLOR_PRIMARY
            page.update()

        users_col = ft.Column(spacing=4)
        new_u_name = ft.TextField(label="ФИО / Имя сотрудника")
        new_u_pin = ft.TextField(label="PIN-код (4 цифры)", max_length=4, keyboard_type=ft.KeyboardType.NUMBER)
        new_u_role = ft.Dropdown(label="Роль доступа", value="cashier", options=[
            ft.dropdown.Option(key="cashier", text="Кассир"),
            ft.dropdown.Option(key="admin", text="Администратор"),
        ])

        def add_user_click(e):
            uname = (new_u_name.value or "").strip()
            upin = (new_u_pin.value or "").strip()
            if uname and len(upin) == 4 and upin.isdigit():
                db.add_local_user(uname, new_u_role.value, upin)
                new_u_name.value = ""
                new_u_pin.value = ""
                refresh_users_list()
                page.show_dialog(ft.SnackBar(ft.Text(f"Сотрудник «{uname}» добавлен"), bgcolor="#059669"))
            else:
                page.show_dialog(ft.SnackBar(ft.Text("Введите имя и 4 цифры PIN-кода"), bgcolor="#E11D48"))

        def refresh_users_list():
            users_col.controls.clear()
            for uid, uname, urole, upin, usrc in db.get_users():
                tag = "Сервер" if usrc == "network" else "Локальный"
                role_ru = "Администратор" if urole == "admin" else "Кассир"
                row_items = [ft.Text(f"• {uname} ({role_ru} • {tag})", size=12, expand=True)]
                if uid != current_user["id"]:
                    row_items.append(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color="#E11D48", on_click=lambda ev, i=uid: (db.delete_user(i), refresh_users_list())))
                users_col.controls.append(ft.Row(controls=row_items))
            page.update()

        refresh_users_list()

        admin_controls.append(
            ft.Container(
                bgcolor=COLOR_CARD_WHITE, padding=14, border_radius=10,
                content=ft.Column(
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Text("Оборудование и связь с сервером", weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                        mode_radio,
                        shop_field,
                        ip_field,
                        ft.Divider(),
                        ft.Text("Чековый принтер (ESC/POS)", weight=ft.FontWeight.BOLD, size=13),
                        printer_type_dd,
                        printer_addr_field,
                        ft.Button("Сохранить настройки", bgcolor=COLOR_PRIMARY, color="white", height=42, on_click=save_sys_settings),
                        ft.Button("Проверить печать на принтер", icon=ft.Icons.PRINT, bgcolor="#334155", color="white", height=42, on_click=test_printer_click),
                        ft.Divider(),
                        ft.Button("Загрузить справочники с сервера", icon=ft.Icons.SYNC, bgcolor=COLOR_ACCENT, color="white", height=42, on_click=sync_all_from_pc),
                        ft.Button("Выгрузить чеки на сервер", icon=ft.Icons.CLOUD_UPLOAD, bgcolor="#059669", color="white", height=42, on_click=push_all_to_pc),
                        ft.Button("Отключить сетевой профиль", bgcolor="#F1F5F9", color=COLOR_DARK_TEXT, height=40, on_click=remove_net_users),
                        status_text,
                    ],
                ),
            )
        )
        admin_controls.append(
            ft.Container(
                bgcolor=COLOR_CARD_WHITE, padding=14, border_radius=10,
                content=ft.Column(
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Text("Персонал и права доступа", weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY),
                        users_col,
                        new_u_name,
                        new_u_pin,
                        new_u_role,
                        ft.Button("+ Добавить сотрудника", bgcolor=COLOR_PRIMARY, color="white", height=42, on_click=add_user_click),
                    ],
                ),
            )
        )

    about_card = ft.Container(
        bgcolor=COLOR_CARD_WHITE, padding=14, border_radius=10,
        content=ft.Column(spacing=5, controls=[
            ft.Row(controls=[
                ft.Icon(ft.Icons.DIAMOND, color=COLOR_PRIMARY),
                ft.Text("КРИСТАЛЛ-ПОС: Мобильная касса", weight=ft.FontWeight.W_900, size=15, color=COLOR_PRIMARY),
            ]),
            ft.Text("Версия ПО: 2.0.1 (Сборка 2026.11)", size=12, color=COLOR_DARK_TEXT, weight=ft.FontWeight.W_600),
            ft.Text("Разработчик и издатель: ЗАО «НПО Кристалл-Софт»", size=12, color="#475569"),
            ft.Text("Статус лицензии: Корпоративная (Активирована)", size=12, color="#059669"),
            ft.Text("Мобильное рабочее место кассира с поддержкой Bluetooth/Wi-Fi печати чеков и обмена с «КРИСТАЛЛ-ПОС 4.0».", size=11, color="#64748B"),
        ]),
    )

    return ft.Container(
        expand=True, padding=14, visible=False,
        content=ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Text("Настройки системы", size=18, weight=ft.FontWeight.BOLD),
                pin_card,
                *admin_controls,
                about_card,
            ],
        ),
    )
