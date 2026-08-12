import socket
import numpy as np
from PIL import Image
import io

CRC8_POLY = 0x07
SECRET_KEY = 0xAA  # Decryption key matching the sender

def compute_crc8(data_bytes):
    crc = 0x00
    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ CRC8_POLY) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

def start_receiver(host='0.0.0.0', port=5001):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print(f"[*] Receiver listening on {host}:{port}...")

    conn, addr = server.accept()
    print(f"[+] Connected to Sender at {addr}")

    received_data = bytearray()
    while True:
        packet = conn.recv(1024)
        if not packet:
            break
        received_data.extend(packet)

    conn.close()
    server.close()
    print("[+] Transmission complete. Processing packets...")

    # Process 17-byte packets (16 bytes data + 1 byte CRC)
    packet_size = 17
    corrupted_blocks = 0
    decrypted_bytes = bytearray()

    for i in range(0, len(received_data), packet_size):
        packet = received_data[i:i + packet_size]
        if len(packet) < packet_size:
            continue
        
        payload = packet[:-1]
        rcv_crc = packet[-1]

        # Check CRC-8
        if compute_crc8(payload) != rcv_crc:
            corrupted_blocks += 1

        # Decrypt payload using XOR key
        for byte in payload:
            decrypted_bytes.append(byte ^ SECRET_KEY)

    print(f"[!] CRC Check Completed. Corrupted blocks detected: {corrupted_blocks}")

    # Reconstruct and display clean image
    try:
        restored_img = Image.open(io.BytesIO(decrypted_bytes))
        restored_img.show(title="Restored Output Image")
        print("[+] Image successfully restored and displayed!")
    except Exception as e:
        print(f"[-] Error displaying image: {e}")

if __name__ == "__main__":
    start_receiver()
    
