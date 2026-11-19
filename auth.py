import flet as ft
import db
from ui_theme import COLOR_PRIMARY, COLOR_ACCENT, COLOR_DARK_TEXT, COLOR_BG_LIGHT, COLOR_CARD_WHITE

def build_login_screen(page: ft.Page, on_login_success):
    users = db.get_users()
    if not users:
        db.add_local_user("Администратор", "admin", "0000")
        users = db.get_users()

    u_id, u_name, u_role, u_pin, u_src = next(iter(users))
    selected_user = {
        "id": u_id,
        "name": u_name,
        "role": u_role,
        "pin": str(u_pin),
    }
    state = {"pin": ""}

    pin_dots = ft.Text("○  ○  ○  ○", size=30, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)
    error_text = ft.Text("", size=13, color="#E11D48", weight=ft.FontWeight.BOLD)
    mode_badge = ft.Container(
        bgcolor="#E0F2FE",
        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
        border_radius=20,
        content=ft.Text(
            "Сетевой режим (Сервер)" if db.get_setting("work_mode") == "network" else "Автономный режим ККТ",
            size=11, color=COLOR_PRIMARY, weight=ft.FontWeight.W_600
        ),
    )

    def update_dots():
        filled = len(state["pin"])
        dots = ["●" if i < filled else "○" for i in range(4)]
        pin_dots.value = "  ".join(dots)
        page.update()

    def on_user_change(e):
        target_id = int(e.control.value)
        for rid, rname, rrole, rpin, rsrc in db.get_users():
            if rid == target_id:
                selected_user.update({
                    "id": rid,
                    "name": rname,
                    "role": rrole,
                    "pin": str(rpin),
                })
                break
        state["pin"] = ""
        error_text.value = ""
        update_dots()

    dropdown_options = [
        ft.dropdown.Option(key=str(rid), text=rname)
        for rid, rname, rrole, rpin, rsrc in users
    ]

    user_dropdown = ft.Dropdown(
        label="Оператор смены",
        value=str(selected_user["id"]),
        bgcolor=COLOR_CARD_WHITE,
        border_radius=12,
        width=290,
        options=dropdown_options,
    )
    user_dropdown.on_change = on_user_change

    def press_digit(digit):
        if len(state["pin"]) < 4:
            state["pin"] += digit
            error_text.value = ""
            update_dots()
            if len(state["pin"]) == 4:
                if state["pin"] == selected_user["pin"]:
                    on_login_success(selected_user)
                else:
                    error_text.value = "Неверный PIN-код доступа"
                    state["pin"] = ""
                    update_dots()

    def press_backspace(e):
        state["pin"] = state["pin"][:-1]
        error_text.value = ""
        update_dots()

    def num_btn(digit):
        return ft.Container(
            width=76, height=62, bgcolor=COLOR_CARD_WHITE, border_radius=16,
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(blur_radius=6, color="#12000000"),
            on_click=lambda e, d=digit: press_digit(d),
            content=ft.Text(digit, size=24, weight=ft.FontWeight.BOLD, color=COLOR_DARK_TEXT),
        )

    keypad = ft.Column(
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=14, controls=[num_btn("1"), num_btn("2"), num_btn("3")]),
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=14, controls=[num_btn("4"), num_btn("5"), num_btn("6")]),
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=14, controls=[num_btn("7"), num_btn("8"), num_btn("9")]),
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=14, controls=[
                ft.Container(width=76, height=62),
                num_btn("0"),
                ft.Container(
                    width=76, height=62, bgcolor="#FEE2E2", border_radius=16,
                    alignment=ft.Alignment.CENTER,
                    on_click=press_backspace,
                    content=ft.Icon(ft.Icons.BACKSPACE_OUTLINED, color="#E11D48", size=24),
                ),
            ]),
        ],
    )

    return ft.Container(
        expand=True,
        bgcolor=COLOR_BG_LIGHT,
        padding=20,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            controls=[
                ft.Container(
                    bgcolor=COLOR_PRIMARY, padding=16, border_radius=20,
                    shadow=ft.BoxShadow(blur_radius=14, color="#300D47A1"),
                    content=ft.Icon(ft.Icons.DIAMOND, color=COLOR_ACCENT, size=38),
                ),
                ft.Text("КРИСТАЛЛ-ПОС", size=22, weight=ft.FontWeight.W_900, color=COLOR_DARK_TEXT),
                mode_badge,
                user_dropdown,
                ft.Container(
                    bgcolor=COLOR_CARD_WHITE, padding=ft.Padding.symmetric(horizontal=28, vertical=10),
                    border_radius=14,
                    shadow=ft.BoxShadow(blur_radius=6, color="#10000000"),
                    content=pin_dots
                ),
                error_text,
                keypad,
            ],
        ),
    )
