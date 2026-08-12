import socket
import numpy as np
from PIL import Image

CRC8_POLY = 0x07

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

def send_image(receiver_ip, image_path, port=5000, bytes_per_packet=8, ber=0.01):
    # Load image and convert to grayscale matrix
    img = Image.open(image_path).convert('L').resize((64, 64))  # Resized to 64x64 for speed
    img_np = np.array(img, dtype=np.uint8)
    height, width = img_np.shape
    raw_bytes = img_np.flatten()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[SENDER] Connecting to Receiver at {receiver_ip}:{port}...")
    client_socket.connect((receiver_ip, port))

    # Send Image Header (Height, Width)
    header = np.array([height, width], dtype=np.int32).tobytes()
    client_socket.sendall(header)

    print("[SENDER] Encoding packets with CRC-8 and transmitting...")
    
    # Process and send packets
    for i in range(0, len(raw_bytes), bytes_per_packet):
        chunk = raw_bytes[i : i + bytes_per_packet]
        crc = compute_crc8(chunk)
        
        # Assemble Packet: [Payload Bytes ..., CRC Byte]
        packet = bytearray(chunk)
        packet.append(crc)
        
        # Inject Channel Noise (Optional Bit Flips based on BER)
        if ber > 0:
            bits = np.unpackbits(np.frombuffer(packet, dtype=np.uint8))
            noise = np.random.rand(*bits.shape) < ber
            corrupted_bits = bits ^ noise.astype(np.uint8)
            packet = bytearray(np.packbits(corrupted_bits).tobytes())

        client_socket.sendall(packet)

    client_socket.close()
    print("[SENDER] Transmission Complete!")

if __name__ == "__main__":
    # Replace with Device B's Local Wi-Fi IP address
    RECEIVER_IP = "192.168.1.5" 
    
    # Send a sample image (Make sure you have an image file named test.png)
    send_image(receiver_ip=RECEIVER_IP, image_path="test.png", ber=0.015)
  
