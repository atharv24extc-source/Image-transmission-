import numpy as np
import matplotlib.pyplot as plt

# --- 1. CRC-8 ENCODER & DECODER ---
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

# --- 2. TRANSMISSION PIPELINE ---
def generate_sample_image(size=(64, 64)):
    x = np.linspace(-2, 2, size[0])
    y = np.linspace(-2, 2, size[1])
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X**2 + Y**2)
    return ((Z - Z.min()) / (Z.max() - Z.min()) * 255).astype(np.uint8)

def transmit_image(img_array, bit_error_rate=0.015, bytes_per_packet=8):
    height, width = img_array.shape
    raw_bytes = img_array.flatten()
    
    # Packetize and add CRC
    packets = []
    for i in range(0, len(raw_bytes), bytes_per_packet):
        chunk = raw_bytes[i : i + bytes_per_packet]
        crc = compute_crc8(chunk)
        packets.append(np.append(chunk, crc))
        
    packet_data = np.array(packets, dtype=np.uint8)
    
    # Inject Channel Noise (Bit Flips)
    bitstream = np.unpackbits(packet_data)
    noise_mask = np.random.rand(*bitstream.shape) < bit_error_rate
    corrupted_bitstream = bitstream ^ noise_mask.astype(np.uint8)
    
    # Receiver: Verify CRC
    rx_packet_data = np.packbits(corrupted_bitstream).reshape(packet_data.shape)
    reconstructed_bytes, error_mask_bytes = [], []
    corrupted_count = 0
    
    for packet in rx_packet_data:
        payload = packet[:-1]
        is_corrupted = (packet[-1] != compute_crc8(payload))
        if is_corrupted:
            corrupted_count += 1
            
        reconstructed_bytes.extend(payload)
        error_mask_bytes.extend([1 if is_corrupted else 0] * len(payload))
        
    rx_image = np.array(reconstructed_bytes, dtype=np.uint8).reshape((height, width))
    error_map = np.array(error_mask_bytes, dtype=np.uint8).reshape((height, width))
    
    return rx_image, error_map, corrupted_count, len(packets)

# --- 3. RUN AND PLOT ---
tx_image = generate_sample_image(size=(64, 64))
rx_image, error_map, err_pkts, total_pkts = transmit_image(tx_image)

plt.figure(figsize=(10, 4))
plt.subplot(1, 3, 1)
plt.title("Original Image")
plt.imshow(tx_image, cmap='gray')

plt.subplot(1, 3, 2)
plt.title("Received Image (Corrupted)")
plt.imshow(rx_image, cmap='gray')

plt.subplot(1, 3, 3)
plt.title(f"CRC Error Map\n({err_pkts}/{total_pkts} Packets Flagged)")
overlay = np.zeros((*tx_image.shape, 3), dtype=np.uint8)
overlay[error_map == 0] = [30, 180, 30]   # Green = Clean
overlay[error_map == 1] = [230, 30, 30]   # Red = Error Detected
plt.imshow(overlay)

plt.tight_layout()
plt.show()

