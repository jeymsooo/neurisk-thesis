import time
import socket

try:
    import serial
except ImportError:
    serial = None

def capture_emg_serial(port, baudrate, duration):
    if serial is None:
        raise ImportError("pyserial is not installed.")
    ser = serial.Serial(port, baudrate, timeout=0.01)  # Short timeout!
    data = []
    start_time = time.time()
    while time.time() - start_time < duration:
        line = ser.readline().decode('utf-8').strip()
        if line:
            try:
                value = float(line)
                data.append(value)
            except ValueError:
                continue
        time.sleep(0.001)  # Prevent 100% CPU usage
    ser.close()
    return data

def capture_emg_tcp(ip, port, duration):
    data = []
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    s.settimeout(0.01)  # Short timeout!
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            line = s.recv(32).decode('utf-8').strip()
            if line:
                try:
                    value = float(line)
                    data.append(value)
                except ValueError:
                    continue
        except socket.timeout:
            continue
        time.sleep(0.001)  # Prevent 100% CPU usage
    s.close()
    return data

# Optionally, you can add Bluetooth support here using bleak or pybluez