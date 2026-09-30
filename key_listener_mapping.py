import time
import platform
import threading
import hid

VENDOR_ID = 0x047F  # Plantronics / Poly

# Status-Variablen
is_in_call = False
is_muted_in_call = False
last_event_time = 0
DEBOUNCE_TIME = 0.3  # Entprellzeit in Sekunden gegen doppelte HID-Frames

def parse_calisto_event(usage_page, data):
    """
    Wertet die exakten Hex-Bytes des Calisto 3200 präzise und entprellt aus.
    """
    global is_in_call, is_muted_in_call, last_event_time
    
    now = time.time()
    hex_str = " ".join([f"{b:02X}" for b in data])

    # 1. Lautstärke (Usage Page 0x0C - Consumer Control)
    if usage_page == 0x0C:
        if hex_str == "FF 01":
            return "Lauter gedrückt"
        elif hex_str == "FF 02":
            return "Leiser gedrückt"

    # 2. Telephonie & Mute (Usage Page 0x0B - Telephony)
    elif usage_page == 0x0B:
        # Entprellung für Telephonie-Events (verhindert Doppel-Trigger)
        if now - last_event_time < DEBOUNCE_TIME:
            return None

        # --- IM ANRUF ---
        if is_in_call:
            # Mute-Taste im Anruf
            if hex_str in ["F0 03", "F0 02"]:
                last_event_time = now
                is_muted_in_call = not is_muted_in_call
                state_str = "Mute EIN" if is_muted_in_call else "Mute AUS"
                return f"{state_str} (im Anruf)"
            
            # Anruf beenden (Auflegen-Taste)
            elif hex_str == "F0 00":
                last_event_time = now
                is_in_call = False
                is_muted_in_call = False
                return "Anruf beendet"

        # --- KEIN ANRUF (IDLE) ---
        else:
            # Anruf starten (Anruf-Taste)
            if hex_str == "F0 01":
                last_event_time = now
                is_in_call = True
                is_muted_in_call = False
                return "Anruf gestartet"
            
            # System-Mute (Mute-Taste ohne Anruf)
            elif hex_str == "F0 02":
                last_event_time = now
                return "Mute gedrückt (System-Mute)"

    return None

def listen_to_path(path, usage_page):
    """Liest die HID-Schnittstelle aus."""
    try:
        device = hid.device()
        device.open_path(path)
        device.set_nonblocking(True)

        last_data = None
        while True:
            data = device.read(64)
            if data:
                if data != last_data:
                    action = parse_calisto_event(usage_page, data)
                    if action:
                        print(f"[CALISTO] {action}")
                    last_data = data
            else:
                # Puffer zurücksetzen, sobald keine Daten mehr anliegen
                last_data = None

            time.sleep(0.02)
    except Exception:
        pass

def main():
    print(f"Betriebssystem: {platform.system()}")
    print("Starte Calisto 3200 Final Mapping Listener (mit Debounce)...\n")

    all_devices = hid.enumerate()
    calisto_interfaces = [d for d in all_devices if d['vendor_id'] == VENDOR_ID]

    if not calisto_interfaces:
        print("[!] Kein Plantronics/Poly Calisto 3200 gefunden!")
        return

    for dev_info in calisto_interfaces:
        path = dev_info['path']
        usage_page = dev_info.get('usage_page', 0)
        
        t = threading.Thread(target=listen_to_path, args=(path, usage_page), daemon=True)
        t.start()

    print("--- READY: LAUSCHE AUF TASTEN ---")
    print("Drücke Strg+C zum Beenden.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMapping-Listener beendet.")

if __name__ == "__main__":
    main()
