"""
Waveshare E-ink Display Firmware - 648x480
5.83" Model (Black/White only)

Runs on Raspberry Pi Pico W. Receives image data via HTTP POST
and displays it on the connected e-ink screen.

Color Mode:
  - B&W only: 38,880 bytes (1 bit per pixel)

Pin Configuration:
  BUSY -> GP13, RST -> GP12, DC -> GP8, CS -> GP9
  CLK -> GP10, DIN -> GP11, VCC -> 3.3V, GND -> GND
"""

import network
import socket
import time
from machine import Pin, SPI
import gc

gc.enable()
gc.collect()

# ===== NETWORK CONFIGURATION =====
# ⚠️ IMPORTANT: Update these before uploading!
SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

USE_STATIC_IP = True
STATIC_IP = "192.168.1.100"  # Change to your IP
SUBNET_MASK = "255.255.255.0"
GATEWAY = "192.168.1.1"
DNS_SERVER = "8.8.8.8"

SERVER_PORT = 8080
# ==================================

# Display Configuration
DISPLAY_WIDTH = 648
DISPLAY_HEIGHT = 480
EXPECTED_BYTES = (DISPLAY_WIDTH * DISPLAY_HEIGHT) // 8  # 38,880 bytes (B&W)

# Pin Configuration
EPD_RST_PIN = 12
EPD_DC_PIN = 8
EPD_CS_PIN = 9
EPD_BUSY_PIN = 13

# SPI Configuration
spi = SPI(1, baudrate=4000000, polarity=0, phase=0, 
          sck=Pin(10), mosi=Pin(11), miso=Pin(12))

# Initialize pins
rst = Pin(EPD_RST_PIN, Pin.OUT)
dc = Pin(EPD_DC_PIN, Pin.OUT)
cs = Pin(EPD_CS_PIN, Pin.OUT)
busy = Pin(EPD_BUSY_PIN, Pin.IN)


def show_memory():
    """Show current memory usage"""
    free = gc.mem_free()
    allocated = gc.mem_alloc()
    total = free + allocated
    print(f"  Memory: {free:,} bytes free / {total:,} total ({(free/total)*100:.1f}% free)")


def connect_wifi():
    """Connect to WiFi"""
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
            print(f"Configuring static IP: {STATIC_IP}")
            wlan.ifconfig((STATIC_IP, SUBNET_MASK, GATEWAY, DNS_SERVER))
            time.sleep(1)
        
        ip, subnet, gateway, dns = wlan.ifconfig()
        print("=" * 60)
        print("Network Configuration:")
        print(f"  IP Address: {ip}")
        print(f"  Port: {SERVER_PORT}")
        print(f"  Display: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
        print("=" * 60)
        print(f"\n✓ Connected to WiFi")
        
        return ip
    else:
        print("✗ Failed to connect to WiFi")
        return None


def epd_send_command(command):
    """Send command to e-paper display"""
    dc.value(0)
    cs.value(0)
    spi.write(bytearray([command]))
    cs.value(1)


def epd_send_data(data):
    """Send data to e-paper display"""
    dc.value(1)
    cs.value(0)
    spi.write(bytearray([data]))
    cs.value(1)


def epd_send_data_bytes(data):
    """Send multiple bytes of data"""
    dc.value(1)
    cs.value(0)
    spi.write(data)
    cs.value(1)


def epd_wait_busy():
    """Wait until display is not busy"""
    print("  Waiting for display ready...", end="")
    timeout = 10
    start = time.time()
    while busy.value() == 1:
        if time.time() - start > timeout:
            print(" timeout")
            return False
        time.sleep_ms(100)
    print(" ✓")
    return True


def epd_reset():
    """Hardware reset of e-paper display"""
    rst.value(1)
    time.sleep_ms(200)
    rst.value(0)
    time.sleep_ms(2)
    rst.value(1)
    time.sleep_ms(200)


def epd_init():
    """Initialize 5.83\" e-paper display"""
    print("Initializing display...")
    epd_reset()
    epd_wait_busy()
    
    # Panel setting
    epd_send_command(0x01)
    epd_send_data(0x37)
    epd_send_data(0x00)
    
    # Power setting
    epd_send_command(0x00)
    epd_send_data(0xCF)
    epd_send_data(0x08)
    
    # PLL control
    epd_send_command(0x06)
    epd_send_data(0xC7)
    epd_send_data(0xCC)
    epd_send_data(0x28)
    
    # Power on
    epd_send_command(0x04)
    epd_wait_busy()
    
    # Panel setting
    epd_send_command(0x30)
    epd_send_data(0x3C)
    
    # Temperature sensor
    epd_send_command(0x41)
    epd_send_data(0x00)
    
    # VCOM and data interval setting
    epd_send_command(0x50)
    epd_send_data(0x77)
    
    # Resolution setting
    epd_send_command(0x61)
    epd_send_data(0x02)  # 648
    epd_send_data(0x88)
    epd_send_data(0x01)  # 480
    epd_send_data(0xE0)
    
    # VCM_DC setting
    epd_send_command(0x82)
    epd_send_data(0x0A)
    
    print("✓ Display initialized")


def epd_display_image(image_data):
    """Display image on screen"""
    print(f"Displaying image ({len(image_data)} bytes)...")
    
    if len(image_data) != EXPECTED_BYTES:
        print(f"✗ Invalid data size: {len(image_data)} bytes")
        print(f"   Expected: {EXPECTED_BYTES} bytes")
        return
    
    # Send image data
    print("  Writing image data...")
    epd_send_command(0x10)
    for i in range(0, len(image_data), 1000):
        chunk = image_data[i:i+1000]
        epd_send_data_bytes(chunk)
        if i % 10000 == 0:
            print(f"    {i*100//len(image_data)}%")
    print("    100%")
    
    # Refresh display
    print("  Refreshing...")
    epd_send_command(0x12)
    time.sleep_ms(100)
    epd_wait_busy()
    
    print("✓ Image displayed!")


def epd_sleep():
    """Put display in deep sleep mode"""
    print("  Entering deep sleep...")
    epd_send_command(0x02)
    epd_wait_busy()
    epd_send_command(0x07)
    epd_send_data(0xA5)
    print("  ✓ Display in deep sleep")


def handle_request(conn, addr):
    """Handle HTTP request"""
    print(f"\n{'='*60}")
    print(f"Connection from {addr}")
    show_memory()
    
    try:
        request = b""
        content_length = 0
        headers_done = False
        body = b""
        
        # Read headers
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
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n\r\n"
                        f"Generic E-ink Display ({DISPLAY_WIDTH}x{DISPLAY_HEIGHT})\n"
                        f"B&W mode: {EXPECTED_BYTES} bytes\n"
                        "POST to /update"
                    )
                    conn.send(response.encode())
                    return
        
        if not headers_done or content_length == 0:
            print("✗ Invalid request")
            return
        
        print(f"Receiving: {content_length} bytes...")
        
        # Read remaining body
        while len(body) < content_length:
            remaining = content_length - len(body)
            chunk = conn.recv(min(1024, remaining))
            if not chunk:
                break
            body += chunk
            
            if len(body) % 10000 == 0:
                print(f"  {len(body)*100//content_length}%")
        
        if len(body) < content_length:
            print(f"✗ Incomplete")
            return
        
        print(f"✓ Received")
        
        # Send response
        response = "HTTP/1.1 200 OK\r\n\r\nOK"
        conn.send(response.encode())
        
        # Clean up
        del request
        del headers
        gc.collect()
        
        # Display image
        epd_display_image(body)
        
        # Wait for display to stabilize
        print("  Waiting for display to stabilize...")
        time.sleep(2)
        
        # Put display to sleep
        epd_sleep()
        
        # Clean up
        del body
        gc.collect()
        
        print("✓ Complete!")
        show_memory()
        print(f"{'='*60}\n")
        
    except MemoryError as e:
        print(f"✗ OOM: {e}")
        show_memory()
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        try:
            conn.close()
        except:
            pass
        gc.collect()


def start_server():
    """Start HTTP server"""
    addr = socket.getaddrinfo('0.0.0.0', SERVER_PORT)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    
    print(f"\n{'='*60}")
    print("✓ Server running")
    print("  Waiting for content from plugins...")
    show_memory()
    print(f"{'='*60}\n")
    
    while True:
        try:
            conn, addr = s.accept()
            handle_request(conn, addr)
            gc.collect()
        except Exception as e:
            print(f"✗ {e}")
            gc.collect()


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print(f"Generic E-ink Display Receiver")
    print(f"{DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")
    print("Works with ANY plugin!")
    print("=" * 60 + "\n")
    
    show_memory()
    
    ip = connect_wifi()
    if not ip:
        print("\n✗ Cannot start without WiFi")
        return
    
    try:
        epd_init()
    except Exception as e:
        print(f"⚠️  Init failed: {e}")
        print("Server will run but screen won't update")
    
    show_memory()
    start_server()


if __name__ == "__main__":
    main()
