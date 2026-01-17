"""
Generic E-ink Display Receiver - 400x300
For Waveshare 4.2" B displays (B&W or tri-color)

Auto-detects B&W vs tri-color based on data size!
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
STATIC_IP = "192.168.1.102"
SUBNET_MASK = "255.255.255.0"
GATEWAY = "192.168.1.1"
DNS_SERVER = "8.8.8.8"

SERVER_PORT = 8080
# ==================================

# Display Configuration
DISPLAY_WIDTH = 400
DISPLAY_HEIGHT = 300
EXPECTED_BYTES_BW = (DISPLAY_WIDTH * DISPLAY_HEIGHT) // 8    # 15,000 bytes
EXPECTED_BYTES_BWR = EXPECTED_BYTES_BW * 2                    # 30,000 bytes

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
        print(f"  IP: {ip}:{SERVER_PORT} | Display: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
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
    print("Initializing 4.2\" B display...")
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
    
    epd_send_command(0x61)  # Resolution
    epd_send_data(0x01)  # 400
    epd_send_data(0x90)
    epd_send_data(0x01)  # 300
    epd_send_data(0x2C)
    
    print("✓ Display initialized")


def epd_display_image(image_data):
    print(f"Displaying ({len(image_data)} bytes)...")
    
    is_bw = (len(image_data) == EXPECTED_BYTES_BW)
    is_bwr = (len(image_data) == EXPECTED_BYTES_BWR)
    
    if not (is_bw or is_bwr):
        print(f"✗ Invalid size: {len(image_data)} bytes")
        print(f"   Expected: {EXPECTED_BYTES_BW} (B&W) or {EXPECTED_BYTES_BWR} (BWR)")
        return
    
    mode = "B&W" if is_bw else "Tri-color"
    print(f"  Mode: {mode}")
    
    # Clear
    white = bytearray([0xFF] * 1000)
    epd_send_command(0x10)
    for i in range(0, EXPECTED_BYTES_BW, 1000):
        epd_send_data_bytes(white)
    
    # Write B&W
    epd_send_command(0x13)
    bw_data = image_data[:EXPECTED_BYTES_BW] if is_bwr else image_data
    for i in range(0, len(bw_data), 1000):
        epd_send_data_bytes(bw_data[i:i+1000])
    
    # Write red
    epd_send_command(0x14)
    if is_bwr:
        red_data = image_data[EXPECTED_BYTES_BW:]
        for i in range(0, len(red_data), 1000):
            epd_send_data_bytes(red_data[i:i+1000])
    else:
        for i in range(0, EXPECTED_BYTES_BW, 1000):
            epd_send_data_bytes(white)
    
    # Refresh
    epd_send_command(0x12)
    time.sleep_ms(100)
    epd_wait_busy()
    print("✓ Displayed!")


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
                        f"Generic E-ink ({DISPLAY_WIDTH}x{DISPLAY_HEIGHT})\n"
                        f"B&W: {EXPECTED_BYTES_BW}B or BWR: {EXPECTED_BYTES_BWR}B\n"
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
    print(f"\nGeneric Display ({DISPLAY_WIDTH}x{DISPLAY_HEIGHT})")
    print("Auto-detects B&W or Tri-color!\n")
    
    if connect_wifi():
        epd_init()
        start_server()


if __name__ == "__main__":
    main()
