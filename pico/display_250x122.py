"""
Generic E-ink Display Receiver - 250x122
For Waveshare 2.13" B displays (B&W or tri-color)
Auto-detects B&W vs tri-color!
"""

import network, socket, time, gc
from machine import Pin, SPI

gc.enable(); gc.collect()

SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"
USE_STATIC_IP = True
STATIC_IP = "192.168.1.106"
SUBNET_MASK = "255.255.255.0"
GATEWAY = "192.168.1.1"
DNS_SERVER = "8.8.8.8"
SERVER_PORT = 8080

DISPLAY_WIDTH = 250
DISPLAY_HEIGHT = 122
EXPECTED_BYTES_BW = (DISPLAY_WIDTH * DISPLAY_HEIGHT) // 8
EXPECTED_BYTES_BWR = EXPECTED_BYTES_BW * 2

spi = SPI(1, baudrate=4000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
rst, dc, cs, busy = Pin(12, Pin.OUT), Pin(8, Pin.OUT), Pin(9, Pin.OUT), Pin(13, Pin.IN)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF); wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        timeout = 10
        while not wlan.isconnected() and timeout > 0: time.sleep(1); timeout -= 1
    if wlan.isconnected():
        if USE_STATIC_IP: wlan.ifconfig((STATIC_IP, SUBNET_MASK, GATEWAY, DNS_SERVER))
        print(f"✓ {wlan.ifconfig()[0]}:{SERVER_PORT}"); return True
    return False

def cmd(c): dc.value(0); cs.value(0); spi.write(bytearray([c])); cs.value(1)
def data(d): dc.value(1); cs.value(0); spi.write(bytearray([d]) if isinstance(d, int) else d); cs.value(1)
def wait(): timeout = 10; start = time.time(); [time.sleep_ms(100) for _ in range(100) if busy.value() == 1 and time.time() - start < timeout]

def epd_init():
    print("Init 2.13\" B...")
    rst.value(1); time.sleep_ms(200); rst.value(0); time.sleep_ms(2); rst.value(1); time.sleep_ms(200); wait()
    cmd(0x01); data(0x03); data(0x00); data(0x2B); data(0x2B); data(0x03)
    cmd(0x06); data(0x17); data(0x17); data(0x17)
    cmd(0x04); wait()
    cmd(0x00); data(0x8F)
    cmd(0x50); data(0x77)
    cmd(0x61); data(0x00); data(0xFA); data(0x00); data(0x7A)
    print("✓ Init OK")

def epd_display(img_data):
    is_bw = len(img_data) == EXPECTED_BYTES_BW; is_bwr = len(img_data) == EXPECTED_BYTES_BWR
    if not (is_bw or is_bwr): print(f"✗ Invalid: {len(img_data)}"); return
    print(f"Display ({'B&W' if is_bw else 'BWR'})...")
    white = bytearray([0xFF] * 500)
    cmd(0x10); [data(white) for i in range(0, EXPECTED_BYTES_BW, 500)]
    cmd(0x13); bw_data = img_data[:EXPECTED_BYTES_BW] if is_bwr else img_data; [data(bw_data[i:i+500]) for i in range(0, len(bw_data), 500)]
    cmd(0x14)
    if is_bwr: red_data = img_data[EXPECTED_BYTES_BW:]; [data(red_data[i:i+500]) for i in range(0, len(red_data), 500)]
    else: [data(white) for i in range(0, EXPECTED_BYTES_BW, 500)]
    cmd(0x12); wait(); print("✓ Done")

def epd_sleep(): cmd(0x02); wait(); cmd(0x07); data(0xA5)

def handle_request(conn):
    try:
        req = b""; cl = 0; hd = False; body = b""
        while not hd:
            chunk = conn.recv(512)
            if not chunk: break
            req += chunk
            if b'\r\n\r\n' in req:
                hd = True; he = req.find(b'\r\n\r\n'); headers = req[:he]; body = req[he + 4:]
                for line in headers.split(b'\r\n'):
                    if line.startswith(b'Content-Length:'): cl = int(line.split(b':')[1].strip()); break
                if b'POST /update' not in headers: conn.send(b"HTTP/1.1 200 OK\r\n\r\nOK"); return
        while len(body) < cl: chunk = conn.recv(min(1024, cl - len(body))); [body := body + chunk for _ in [0] if chunk]
        conn.send(b"HTTP/1.1 200 OK\r\n\r\nOK"); del req, headers; gc.collect()
        epd_display(body); time.sleep(1); epd_sleep(); del body; gc.collect()
    except Exception as e: print(f"✗ {e}")
    finally: [conn.close() for _ in [0]]; gc.collect()

def start_server():
    addr = socket.getaddrinfo('0.0.0.0', SERVER_PORT)[0][-1]; s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr); s.listen(1); print("✓ Server running")
    while True: [handle_request(conn) for conn, addr in [s.accept()]] if True else None

if __name__ == "__main__": print(f"\n{DISPLAY_WIDTH}x{DISPLAY_HEIGHT} Display\n"); [start_server() for _ in [0] if connect_wifi() and epd_init() is None]
