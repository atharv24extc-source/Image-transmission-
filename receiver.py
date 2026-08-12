import socket
import numpy as np
import matplotlib.pyplot as plt

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

def start_receiver(host='0.0.0.0', port=5000, bytes_per_packet=8):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    
    print(f"[RECEIVER] Listening for incoming image on port {port}...")
    conn, addr = server_socket.accept()
    print(f"[RECEIVER] Connected to sender: {addr}")

    # Read image dimensions (Height, Width)
    dimensions = conn.recv(8)
    height, width = np.frombuffer(dimensions, dtype=np.int32)
    print(f"[RECEIVER] Expecting Image Size: {height}x{width}")

    packet_size = bytes_per_packet + 1  # Payload + 1 CRC Byte
    total_expected_packets = (height * width + bytes_per_packet - 1) // bytes_per_packet
    
    reconstructed_bytes = []
    error_mask_bytes = []
    corrupted_packets = 0

    # Receive packets in a loop
    for _ in range(total_expected_packets):
        packet = b""
        while len(packet) < packet_size:
            chunk = conn.recv(packet_size - len(packet))
            if not chunk:
                break
            packet += chunk
        
        if not packet:
            break
            
        payload = list(packet[:-1])
        received_crc = packet[-1]
        
        # Verify CRC
        computed_crc = compute_crc8(payload)
        is_corrupted = (received_crc != computed_crc)
        
        if is_corrupted:
            corrupted_packets += 1

        reconstructed_bytes.extend(payload)
        error_mask_bytes.extend([1 if is_corrupted else 0] * len(payload))

    conn.close()
    server_socket.close()
    
    # Trim padding and reshape into 2D Image Matrix
    total_pixels = height * width
    rx_image = np.array(reconstructed_bytes[:total_pixels], dtype=np.uint8).reshape((height, width))
    error_map = np.array(error_mask_bytes[:total_pixels], dtype=np.uint8).reshape((height, width))

    print(f"[RECEIVER] Reception complete! Corrupted Packets: {corrupted_packets}/{total_expected_packets}")

    # Plot Received Image and CRC Error Overlay
    plt.figure(figsize=(10, 4))
    
    plt.subplot(1, 2, 1)
    plt.title("Received Image")
    plt.imshow(rx_image, cmap='gray')
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.title(f"CRC Error Map\n({corrupted_packets} Packets Flagged)")
    overlay = np.zeros((*rx_image.shape, 3), dtype=np.uint8)
    overlay[error_map == 0] = [30, 180, 30]  # Green = Clean
    overlay[error_map == 1] = [230, 30, 30]  # Red = CRC Error Detected
    plt.imshow(overlay)
    plt.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    start_receiver()
  
