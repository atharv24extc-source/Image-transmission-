import socket
import numpy as np
from PIL import Image
import io

CRC8_POLY = 0x07
SECRET_KEY = 0xAA  # Encryption key

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

def send_image(image_path, receiver_ip, port=5001, ber=0.015):
    # Load and prepare image
    img = Image.open(image_path).convert('RGB').resize((256, 256))
    
    # Save image to PNG bytes format
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    raw_bytes = buffer.getvalue()

    # XOR Encrypt byte stream
    encrypted_bytes = bytearray([b ^ SECRET_KEY for b in raw_bytes])

    # Packetize (16 bytes data + 1 byte CRC)
    packet_data = bytearray()
    bytes_per_packet = 16

    for i in range(0, len(encrypted_bytes), bytes_per_packet):
        chunk = encrypted_bytes[i:i + bytes_per_packet]
        if len(chunk) < bytes_per_packet:
            chunk = chunk.ljust(bytes_per_packet, b'\x00')
        crc = compute_crc8(chunk)
        packet_data.extend(chunk)
        packet_data.append(crc)

    # Inject Bit-Flip Channel Noise
    bitstream = np.unpackbits(np.frombuffer(packet_data, dtype=np.uint8))
    noise_mask = np.random.rand(*bitstream.shape) < ber
    corrupted_bitstream = bitstream ^ noise_mask.astype(np.uint8)
    noisy_packet_data = np.packbits(corrupted_bitstream).tobytes()

    # Transmit over Socket Connection
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[*] Connecting to Receiver at {receiver_ip}:{port}...")
    client.connect((receiver_ip, port))
    
    client.sendall(noisy_packet_data)
    print("[+] Transmission finished successfully!")
    client.close()

if __name__ == "__main__":
    # Replace '192.168.1.X' with Receiver device's Wi-Fi IP address
    RECEIVER_IP = "127.0.0.1" 
    send_image("test.jpg", RECEIVER_IP)
    
