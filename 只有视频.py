import sensor
import time
import network
import socket
import gc
SSID = "P"
KEY = "12345678"
HOST = "192.168.69.250"
PORT = 8080
try:
    print("Initializing camera...")
    sensor.reset()
    sensor.set_framesize(sensor.QVGA)
    sensor.set_pixformat(sensor.RGB565)
    sensor.skip_frames(time = 2000)
    print("Camera initialized.")
except Exception as e:
    print(f"Error initializing camera: {e}")
    raise e
wlan = None
try:
    print("Initializing WLAN...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("WLAN initialized.")
    if not wlan.isconnected():
        print('Trying to connect to "{:s}"...'.format(SSID))
        wlan.connect(SSID, KEY)
        connect_start_time = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), connect_start_time) > 20000:
                raise OSError("WiFi connection timed out")
            print("Waiting for WiFi connection...")
            time.sleep_ms(1000)
    ip_info = wlan.ifconfig()
    print("WiFi Connected ", ip_info)
    if ip_info[0] == '0.0.0.0':
        print("Invalid IP (0.0.0.0), retrying WiFi connection...")
        wlan.disconnect()
        time.sleep_ms(2000)
        wlan.connect(SSID, KEY)
        reconnect_start_time = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), reconnect_start_time) > 15000:
                raise OSError("WiFi re-connection timed out after invalid IP.")
            print("Retrying WiFi connection...")
            time.sleep_ms(1000)
        ip_info = wlan.ifconfig()
        print("Reconnected WiFi, IP info:", ip_info)
        if ip_info[0] == '0.0.0.0':
            raise OSError("Failed to get valid IP address after retry.")
except Exception as e:
    print(f"Error connecting to WiFi: {e}")
    raise e
server_socket = None
try:
    print(f"Creating server socket on port {PORT}...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print("Server socket created and listening.")
    server_socket.setblocking(True)
except Exception as e:
    print(f"Error setting up server socket: {e}")
    if server_socket:
        server_socket.close()
    raise e
def init_stream_server():
    global stream_socket
    try:
        if stream_socket:
            try:
                print("关闭旧的视频流服务器 socket...")
                stream_socket.close()
            except Exception as close_e:
                 print(f"警告：关闭旧视频流服务器 socket 时出错: {close_e}")
            stream_socket = None
            gc.collect()
            time.sleep_ms(200)
        print("创建新的视频流服务器 socket...")
        stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        stream_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        stream_socket.bind(('', STREAM_PORT))
        stream_socket.listen(1)
        stream_socket.setblocking(False)
        print(f"视频流服务器初始化成功，监听端口: {STREAM_PORT}")
        return True
    except Exception as e:
        print(f"错误：视频流服务器初始化失败: {e}")
        if stream_socket:
            try:
                stream_socket.close()
            except: pass
        stream_socket = None
        return False
def start_streaming(server_sock):
    client = None
    addr = None
    print("\nWaiting for connections...")
    try:
        client, addr = server_sock.accept()
        client.settimeout(5.0)
        print("Connected to " + addr[0] + ":" + str(addr[1]))
        try:
            request_data = client.recv(1024)
        except socket.timeout:
            print("Warning: Timeout reading client request.")
        except Exception as recv_e:
             print(f"Error reading client request: {recv_e}")
             if client: client.close()
             return
        try:
            client.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Server: OpenMV\r\n"
                b"Content-Type: multipart/x-mixed-replace; boundary=--openmv_frame_boundary\r\n"
                b"Cache-Control: no-cache\r\n"
                b"Pragma: no-cache\r\n"
                b"Connection: close\r\n"
                b"Access-Control-Allow-Origin: *\r\n"
                b"\r\n"
            )
            print("Sent HTTP header to client.")
            client.settimeout(None)
        except Exception as header_e:
             print(f"Error sending HTTP header: {header_e}")
             if client: client.close()
             return
        clock = time.clock()
        frame_count = 0
        print("Starting image streaming...")
        while True:
            try:
                clock.tick()
                frame = sensor.snapshot()
                cframe = frame.compress(quality=35)
                frame_size = cframe.size()
                boundary = b"\r\n----openmv_frame_boundary\r\n"
                header = b"Content-Type: image/jpeg\r\nContent-Length: " + str(frame_size).encode() + b"\r\n\r\n"
                client.sendall(boundary)
                client.sendall(header)
                client.sendall(cframe)
                frame_count += 1
            except OSError as e:
                if e.errno == 22:
                    print("Client likely disconnected (EINVAL).")
                else:
                    print(f"Streaming OSError: {e}")
                break
            except Exception as e:
                print(f"Error during streaming loop: {e}")
                time.sleep_ms(100)
                continue
    except socket.timeout:
         print("Client connection timed out during accept.")
         if addr: print(f"Timeout waiting for connection from {addr[0]}:{addr[1]}")
    except Exception as e:
        print(f"Error accepting connection or setting up client: {e}")
    finally:
        if client:
            try:
                if addr: print("Client connection closed for " + addr[0] + ":" + str(addr[1]))
                else: print("Client connection closed.")
            except Exception as close_e:
                print(f"Warning: Error closing client socket: {close_e}")
print("\nEntering main loop. Waiting for client connections...")
while True:
    try:
        start_streaming(server_socket)
        gc.collect()
        print(f"Free memory after client disconnect: {gc.mem_free()} bytes")
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Shutting down...")
        break
    except Exception as e:
        print(f"Unhandled error in main loop: {e}")
        print("Attempting to re-initialize stream server...")
        if server_socket:
            try: server_socket.close();
            except:
                pass;
                server_socket=None
        if not init_stream_server():
             print("FATAL: Failed to re-initialize server socket. Exiting.")
             break
        time.sleep_ms(2000)
print("\nCleaning up resources...")
if server_socket:
    try:
        server_socket.close()
        print("Server socket closed.")
    except:
        pass
if wlan and wlan.isconnected():
    try:
        print("WiFi disconnected.")
    except:
        pass
    wlan.active(False)
    print("WLAN deactivated.")
print("Program finished.")
