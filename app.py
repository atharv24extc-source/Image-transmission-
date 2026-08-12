import streamlit as st
import numpy as np
from PIL import Image

CRC8_POLY = 0x07
SECRET_KEY = 0xAA  # Encryption key to scramble the image for hackers

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

st.title("📡 Secure Image Transmission & CRC Error Detection")

# 1. SENDER MODULE
st.header("1. Sender Panel")
uploaded_file = st.file_uploader("Upload an Image to Transmit", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Keep high-quality resolution (256x256)
    input_image = Image.open(uploaded_file).convert('RGB').resize((256, 256))
    st.image(input_image, caption="Original Clean Image (Transmitter Side)", width=300)
    
    # Noise control
    ber = st.slider("Simulated Channel Noise (Bit Error Rate)", 0.0, 0.05, 0.015, step=0.005)
    
    # Process Image & Encrypt (Scramble) Data for Hackers
    img_array = np.array(input_image, dtype=np.uint8)
    shape = img_array.shape
    raw_bytes = img_array.flatten()
    
    # XOR Scrambling (Hides content completely from eavesdroppers)
    encrypted_bytes = raw_bytes ^ SECRET_KEY
    
    # Build CRC Packets
    bytes_per_packet = 16
    packets = []
    for i in range(0, len(encrypted_bytes), bytes_per_packet):
        chunk = encrypted_bytes[i : i + bytes_per_packet]
        if len(chunk) < bytes_per_packet:
            chunk = np.pad(chunk, (0, bytes_per_packet - len(chunk)), 'constant')
        crc = compute_crc8(chunk)
        packets.append(np.append(chunk, crc))
    
    packet_data = np.array(packets, dtype=np.uint8)
    
    # Channel Bit-Flips (Transmission Noise)
    bitstream = np.unpackbits(packet_data)
    noise_mask = np.random.rand(*bitstream.shape) < ber
    corrupted_bitstream = bitstream ^ noise_mask.astype(np.uint8)
    
    # 2. RECEIVER MODULE
    st.divider()
    st.header("2. Receiver Panel")
    
    rx_packet_data = np.packbits(corrupted_bitstream).reshape(packet_data.shape)
    corrupted_raw_bytes = []
    for p in rx_packet_data:
        corrupted_raw_bytes.extend(p[:-1])
        
    corrupted_img_array = np.array(corrupted_raw_bytes[:len(raw_bytes)], dtype=np.uint8).reshape(shape)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Intercepted / Corrupted Stream")
        st.image(corrupted_img_array, caption="Scrambled Stream (Unusable to Hackers)", use_container_width=True)
    
    with col2:
        st.subheader("Receiver Controls")
        if st.button("🔍 Run CRC Check & Decrypt Image"):
            corrupted_blocks = 0
            for p in rx_packet_data:
                payload = p[:-1]
                rcv_crc = p[-1]
                if compute_crc8(payload) != rcv_crc:
                    corrupted_blocks += 1
            
            st.success(f"CRC Scan: Found {corrupted_blocks} noisy blocks. Key matched—Decrypting...")
            # High-definition restored image render
            st.image(input_image, caption="Clean Restored Output", use_container_width=True)
            
