"""
Generic E-ink Display Receiver - 400x300 Grayscale
For Waveshare 4.2" displays (4-level grayscale)

Auto-detects B&W vs Grayscale based on data size!
- B&W mode: 15,000 bytes (1 bit per pixel)
- Grayscale mode: 30,000 bytes (2 bits per pixel, 4 levels)

Note: This is for grayscale displays, NOT tri-color (BWR).
For tri-color 4.2" B displays, use display_400x300.py instead.
"""

import network
import socket
import time
from machine import Pin, SPI
import gc

gc.enable()
gc.collect()

# ===== NETWORK CONFIGURATION =====
SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

USE_STATIC_IP = True
STATIC_IP = "192.168.1.106"
SUBNET_MASK = "255.255.255.0"
GATEWAY = "192.168.1.1"
DNS_SERVER = "8.8.8.8"

SERVER_PORT = 8080
# ==================================

# Display Configuration
DISPLAY_WIDTH = 400
DISPLAY_HEIGHT = 300
EXPECTED_BYTES_BW = (DISPLAY_WIDTH * DISPLAY_HEIGHT) // 8      # 15,000 bytes (1 bpp)
EXPECTED_BYTES_GRAY = (DISPLAY_WIDTH * DISPLAY_HEIGHT) // 4    # 30,000 bytes (2 bpp)

# Pin Configuration
EPD_RST_PIN = 12
EPD_DC_PIN = 8
EPD_CS_PIN = 9
EPD_BUSY_PIN = 13

spi = SPI(1, baudrate=4000000, polarity=0, phase=0,
          sck=Pin(10), mosi=Pin(11), miso=Pin(12))

rst = Pin(EPD_RST_PIN, Pin.OUT)
dc = Pin(EPD_DC_PIN, Pin.OUT)
cs = Pin(EPD_CS_PIN, Pin.OUT)
busy = Pin(EPD_BUSY_PIN, Pin.IN)


def show_memory():
    free = gc.mem_free()
    allocated = gc.mem_alloc()
    total = free + allocated
    print(f"  Memory: {free:,} bytes free / {total:,} total ({(free/total)*100:.1f}% free)")


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print(f"Connecting to WiFi: {SSID}")
        wlan.connect(SSID, PASSWORD)

        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
        print()

    if wlan.isconnected():
        if USE_STATIC_IP:
            wlan.ifconfig((STATIC_IP, SUBNET_MASK, GATEWAY, DNS_SERVER))
            time.sleep(1)

        ip, subnet, gateway, dns = wlan.ifconfig()
        print("=" * 60)
        print(f"  IP: {ip}:{SERVER_PORT} | Display: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT} Gray")
        print("=" * 60)
        return ip
    return None


def epd_send_command(command):
    dc.value(0)
    cs.value(0)
    spi.write(bytearray([command]))
    cs.value(1)


def epd_send_data(data):
    dc.value(1)
    cs.value(0)
    spi.write(bytearray([data]))
    cs.value(1)


def epd_send_data_bytes(data):
    dc.value(1)
    cs.value(0)
    spi.write(data)
    cs.value(1)


def epd_wait_busy():
    timeout = 10
    start = time.time()
    while busy.value() == 1:
        if time.time() - start > timeout:
            return False
        time.sleep_ms(100)
    return True


def epd_reset():
    rst.value(1)
    time.sleep_ms(200)
    rst.value(0)
    time.sleep_ms(2)
    rst.value(1)
    time.sleep_ms(200)


def epd_init():
    """
    Initialize 4.2" grayscale display

    Note: Init commands may need adjustment based on Waveshare datasheet.
    These are placeholder values that may need hardware testing.
    """
    print("Initializing 4.2\" grayscale display...")
    epd_reset()
    epd_wait_busy()

    epd_send_command(0x01)  # Panel setting
    epd_send_data(0x03)
    epd_send_data(0x00)
    epd_send_data(0x2B)
    epd_send_data(0x2B)

    epd_send_command(0x06)  # Booster
    epd_send_data(0x17)
    epd_send_data(0x17)
    epd_send_data(0x17)

    epd_send_command(0x04)  # Power on
    epd_wait_busy()

    epd_send_command(0x00)  # Panel setting
    epd_send_data(0x8F)

    epd_send_command(0x50)  # VCOM
    epd_send_data(0x77)

    epd_send_command(0x61)  # Resolution: 400x300
    epd_send_data(0x01)  # 400 = 0x190
    epd_send_data(0x90)
    epd_send_data(0x01)  # 300 = 0x12C
    epd_send_data(0x2C)

    print("✓ Display initialized")


def epd_display_bw(data):
    """Display B&W image (1 bit per pixel)"""
    print(f"Displaying B&W ({len(data)} bytes)...")

    # Send B&W data
    epd_send_command(0x10)
    for i in range(0, len(data), 1000):
        epd_send_data_bytes(data[i:i+1000])

    # Refresh
    epd_send_command(0x12)
    time.sleep_ms(100)
    epd_wait_busy()
    print("✓ B&W displayed!")


def epd_display_gray(data):
    """
    Display 4-level grayscale image (2 bits per pixel)

    Grayscale levels:
    - 0b00 = White
    - 0b01 = Light gray
    - 0b10 = Dark gray
    - 0b11 = Black

    Note: Grayscale init/LUT may need adjustment based on Waveshare datasheet.
    This is a placeholder implementation that may need hardware testing.
    """
    print(f"Displaying grayscale ({len(data)} bytes)...")

    # TODO: Grayscale displays may require different LUT settings
    # The exact commands depend on the specific Waveshare model
    # This implementation sends data but may need init adjustments

    # Send grayscale data (2 bits per pixel packed into bytes)
    epd_send_command(0x10)
    for i in range(0, len(data), 1000):
        epd_send_data_bytes(data[i:i+1000])

    # Refresh
    epd_send_command(0x12)
    time.sleep_ms(100)
    epd_wait_busy()
    print("✓ Grayscale displayed!")


def epd_display_image(image_data):
    """Auto-detect and display B&W or grayscale image"""
    is_bw = len(image_data) == EXPECTED_BYTES_BW
    is_gray = len(image_data) == EXPECTED_BYTES_GRAY

    if is_bw:
        epd_display_bw(image_data)
    elif is_gray:
        epd_display_gray(image_data)
    else:
        print(f"✗ Invalid size: {len(image_data)} bytes")
        print(f"  Expected B&W: {EXPECTED_BYTES_BW} or Gray: {EXPECTED_BYTES_GRAY}")


def epd_sleep():
    epd_send_command(0x02)
    epd_wait_busy()
    epd_send_command(0x07)
    epd_send_data(0xA5)


def handle_request(conn, addr):
    try:
        request = b""
        content_length = 0
        headers_done = False
        body = b""

        while not headers_done:
            chunk = conn.recv(512)
            if not chunk:
                break
            request += chunk
            if b'\r\n\r\n' in request:
                headers_done = True
                header_end = request.find(b'\r\n\r\n')
                headers = request[:header_end]
                body = request[header_end + 4:]

                for line in headers.split(b'\r\n'):
                    if line.startswith(b'Content-Length:'):
                        content_length = int(line.split(b':')[1].strip())
                        break

                if b'POST /update' not in headers:
                    response = (
                        "HTTP/1.1 200 OK\r\n\r\n"
                        f"Generic E-ink ({DISPLAY_WIDTH}x{DISPLAY_HEIGHT} Grayscale)\n"
                        f"B&W: {EXPECTED_BYTES_BW}B or Gray: {EXPECTED_BYTES_GRAY}B\n"
                        "POST to /update"
                    )
                    conn.send(response.encode())
                    return

        if not headers_done or content_length == 0:
            return

        while len(body) < content_length:
            chunk = conn.recv(min(1024, content_length - len(body)))
            if not chunk:
                break
            body += chunk

        conn.send(b"HTTP/1.1 200 OK\r\n\r\nOK")

        del request, headers
        gc.collect()

        epd_display_image(body)
        time.sleep(2)
        epd_sleep()

        del body
        gc.collect()

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        try:
            conn.close()
        except:
            pass
        gc.collect()


def start_server():
    addr = socket.getaddrinfo('0.0.0.0', SERVER_PORT)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)

    print("✓ Server running")
    show_memory()

    while True:
        try:
            conn, addr = s.accept()
            handle_request(conn, addr)
        except Exception as e:
            print(f"✗ {e}")
            gc.collect()


def main():
    print(f"\nGeneric Display ({DISPLAY_WIDTH}x{DISPLAY_HEIGHT} Grayscale)")
    print("Auto-detects B&W or Grayscale!\n")

    if connect_wifi():
        epd_init()
        start_server()


if __name__ == "__main__":
    main()
