import socket
from datetime import datetime
import db

def send_to_printer(text_body):
    shop_name = db.get_setting("shop_name", "Магазин «Кристалл»")
    conn_type = db.get_setting("printer_type", "bluetooth")
    target_addr = db.get_setting("printer_addr", "").strip()
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    receipt_text = (
        f"{shop_name}\n"
        f"--------------------------------\n"
        f"{text_body}\n"
        f"--------------------------------\n"
        f"Дата/время: {now_str}\n"
        f"КРИСТАЛЛ-ПОС: Мобильная касса\n\n\n"
    )

    with open("print_spool.txt", "a", encoding="utf-8") as f:
        f.write(receipt_text + "================================\n")

    if not target_addr:
        return True, "Сформировано (принтер не задан, сохранено в ленту)"

    payload = b"\x1b\x40" + receipt_text.encode("cp866", errors="replace") + b"\x1d\x56\x41\x03"

    if conn_type == "bluetooth":
        try:
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(4.0)
            sock.connect((target_addr, 1))
            sock.sendall(payload)
            sock.close()
            return True, f"Напечатано по Bluetooth ({target_addr})"
        except AttributeError:
            return False, "Bluetooth доступен на Android или ПК с BT-модулем"
        except Exception as ex:
            return False, f"Ошибка Bluetooth ({ex})"

    try:
        with socket.create_connection((target_addr, 9100), timeout=3.0) as sock:
            sock.sendall(payload)
        return True, f"Напечатано по Wi-Fi ({target_addr})"
    except Exception as ex:
        return False, f"Ошибка сети ({ex})"
