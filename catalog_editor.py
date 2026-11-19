import flet as ft
import random
import db
from ui_theme import COLOR_PRIMARY, COLOR_ACCENT, COLOR_CARD_WHITE

def build_catalog_tab(page: ft.Page, on_catalog_updated):
    items_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    filter_field = ft.TextField(hint_text="Поиск в справочнике...", prefix_icon=ft.Icons.SEARCH, bgcolor=COLOR_CARD_WHITE)

    def make_barcode():
        return "200" + "".join([str(random.randint(0, 9)) for _ in range(9)])

    def open_product_form(barcode="", name="", price="", stock=""):
        is_edit = bool(barcode)
        initial_bc = barcode if is_edit else make_barcode()

        f_bc = ft.TextField(label="Штрих-код", value=initial_bc, read_only=is_edit)
        f_name = ft.TextField(label="Наименование товара", value=name, autofocus=True)
        f_price = ft.TextField(label="Цена (₽)", value=str(price), keyboard_type=ft.KeyboardType.NUMBER)
        f_stock = ft.TextField(label="Остаток (шт/кг)", value=str(stock) if stock != "" else "10", keyboard_type=ft.KeyboardType.NUMBER)
        err_lbl = ft.Text("", size=12, color="#E11D48", weight=ft.FontWeight.BOLD)

        def gen_barcode(e):
            if not is_edit:
                f_bc.value = make_barcode()
                page.update()

        def save_item(e):
            bc_val = (f_bc.value or "").strip()
            name_val = (f_name.value or "").strip()
            if not bc_val:
                err_lbl.value = "Укажите штрих-код товара"
                page.update()
                return
            if not name_val:
                err_lbl.value = "Введите наименование товара"
                page.update()
                return
            try:
                p_str = (f_price.value or "0").strip().replace(",", ".")
                s_str = (f_stock.value or "0").strip().replace(",", ".")
                p_val = float(p_str) if p_str else 0.0
                s_val = float(s_str) if s_str else 0.0
            except ValueError:
                err_lbl.value = "Цена и остаток должны быть числами"
                page.update()
                return

            db.upsert_product(bc_val, name_val, p_val, s_val)
            try:
                page.pop_dialog()
            except Exception:
                dlg.open = False
            load_items()
            on_catalog_updated()
            page.show_dialog(ft.SnackBar(ft.Text(f"Товар «{name_val}» сохранен"), bgcolor="#059669"))

        controls = [f_bc]
        if not is_edit:
            controls.append(ft.Button("Обновить штрих-код", icon=ft.Icons.REFRESH, on_click=gen_barcode))
        controls.extend([
            f_name,
            f_price,
            f_stock,
            err_lbl,
            ft.Button("СОХРАНИТЬ ТОВАР", icon=ft.Icons.CHECK, bgcolor=COLOR_PRIMARY, color="white", width=280, height=44, on_click=save_item),
        ])

        dlg = ft.AlertDialog(
            title=ft.Text("Редактирование позиции" if is_edit else "Новый товар"),
            content=ft.Column(tight=True, spacing=8, controls=controls),
        )
        page.show_dialog(dlg)

    def remove_item(bc):
        db.delete_product(bc)
        load_items()
        on_catalog_updated()
        page.show_dialog(ft.SnackBar(ft.Text("Позиция удалена"), bgcolor="#E11D48"))

    def load_items(e=None):
        items_col.controls.clear()
        q = (filter_field.value or "").strip().lower()
        for b, name, price, stock in db.get_products():
            if q in name.lower() or q in b:
                items_col.controls.append(
                    ft.Container(
                        bgcolor=COLOR_CARD_WHITE, padding=10, border_radius=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(spacing=2, expand=True, controls=[
                                    ft.Text(name, weight=ft.FontWeight.BOLD, size=14),
                                    ft.Text(f"ШК: {b} • Цена: {price:.2f} ₽ • Ост: {stock:g}", size=11, color="#64748B"),
                                ]),
                                ft.Row(spacing=0, controls=[
                                    ft.IconButton(ft.Icons.EDIT, icon_color=COLOR_PRIMARY, on_click=lambda ev, bc=b, nm=name, pr=price, st=stock: open_product_form(bc, nm, pr, st)),
                                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#E11D48", on_click=lambda ev, bc=b: remove_item(bc)),
                                ]),
                            ],
                        ),
                    )
                )
        page.update()

    filter_field.on_change = load_items
    load_items()

    container = ft.Container(
        expand=True, padding=14, visible=False,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Справочник товаров", size=18, weight=ft.FontWeight.BOLD),
                        ft.Button("+ ДОБАВИТЬ", bgcolor=COLOR_ACCENT, color="white", on_click=lambda e: open_product_form()),
                    ],
                ),
                filter_field,
                items_col,
            ],
        ),
    )
    return container, load_items
