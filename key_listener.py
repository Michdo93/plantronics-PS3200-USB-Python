import time
import platform
import threading
import hid

VENDOR_ID = 0x047F  # Plantronics / Poly

def listen_to_path(path, dev_name, usage_page):
    """Liest ein einzelnes HID-Interface im eigenen Thread aus."""
    try:
        device = hid.device()
        device.open_path(path)
        device.set_nonblocking(True)
        print(f"[+] Interface geöffnet: UsagePage={hex(usage_page)}")

        last_data = None
        while True:
            data = device.read(64)
            if data:
                # Nur ausgeben, wenn sich die Daten ändern (Taste gedrückt / losgelassen)
                if data != last_data:
                    # Ignoriere reine Null-Pakete beim Loslassen, falls gewünscht
                    hex_str = " ".join([f"{b:02X}" for b in data])
                    print(f"\n[EVENT auf UsagePage {hex(usage_page)}] Bytes: {hex_str}")
                    last_data = data
            time.sleep(0.02)
    except Exception as e:
        # Manche Windows-Interfaces sind vom System blockiert, das ist normal
        pass

def main():
    print(f"Betriebssystem: {platform.system()}")
    print("Suche nach allen Schnittstellen des Calisto 3200...\n")

    all_devices = hid.enumerate()
    calisto_interfaces = [d for d in all_devices if d['vendor_id'] == VENDOR_ID]

    if not calisto_interfaces:
        print("[!] Kein Plantronics/Poly Calisto 3200 gefunden!")
        return

    print(f"[✓] {len(calisto_interfaces)} HID-Interfaces für Calisto gefunden.")
    print("Starte Listener auf allen Schnittstellen...\n")
    print("--- JETZT TASTEN AM CALISTO DRÜCKEN (Anruf, Mute, Lauter, Leiser) ---")
    print("Drücke Strg+C zum Beenden.\n")

    # Für jedes gefundene Interface einen Listener-Thread starten
    threads = []
    for dev_info in calisto_interfaces:
        path = dev_info['path']
        usage_page = dev_info.get('usage_page', 0)
        prod = dev_info.get('product_string', 'Calisto')
        
        t = threading.Thread(target=listen_to_path, args=(path, prod, usage_page), daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nListener beendet.")

if __name__ == "__main__":
    main()
