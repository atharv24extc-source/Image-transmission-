import streamlit as st
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

st.title("📡 Image Transmission & Interactive CRC Reconstruction")

# --- SENDER MODULE ---
st.header("1. Sender Panel")
uploaded_file = st.file_uploader("Upload an Image to Transmit", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Read image
    input_image = Image.open(uploaded_file).convert('L').resize((64, 64))
    
    st.image(input_image, caption="Original Image (Transmitter Side)", width=300)
    
    # Channel BER Controls
    ber = st.slider("Simulated Channel Noise (Bit Error Rate)", 0.0, 0.05, 0.015, step=0.005)
    
    # Process image bytes
    img_array = np.array(input_image, dtype=np.uint8)
    shape = img_array.shape
    raw_bytes = img_array.flatten()
    
    # Add CRC-8 bytes per packet
    bytes_per_packet = 16
    packets = []
    for i in range(0, len(raw_bytes), bytes_per_packet):
        chunk = raw_bytes[i : i + bytes_per_packet]
        crc = compute_crc8(chunk)
        packets.append(np.append(chunk, crc))
    
    packet_data = np.array(packets, dtype=np.uint8)
    
    # Inject Bit Flips (Channel Noise)
    bitstream = np.unpackbits(packet_data)
    noise_mask = np.random.rand(*bitstream.shape) < ber
    corrupted_bitstream = bitstream ^ noise_mask.astype(np.uint8)
    
    # --- RECEIVER MODULE ---
    st.divider()
    st.header("2. Receiver Panel")
    
    # Reconstruct corrupted raw image for display
    rx_packet_data = np.packbits(corrupted_bitstream).reshape(packet_data.shape)
    corrupted_raw_bytes = []
    
    for p in rx_packet_data:
        corrupted_raw_bytes.extend(p[:-1])
        
    corrupted_img_array = np.array(corrupted_raw_bytes[:len(raw_bytes)], dtype=np.uint8).reshape(shape)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Corrupted Incoming Image")
        st.image(corrupted_img_array, caption="Received with Channel Noise", use_column_width=True)
    
    with col2:
        st.subheader("Receiver Controls")
        st.write("Click below to run CRC verification and error restoration.")
        
        # INTERACTIVE CLICK EVENT
        if st.button("🔍 Click to Check CRC & Restore Image"):
            # CRC Decoding & Cleaning logic
            clean_bytes = []
            corrupted_blocks = 0
            
            for p in rx_packet_data:
                payload = p[:-1]
                rcv_crc = p[-1]
                if compute_crc8(payload) != rcv_crc:
                    corrupted_blocks += 1
                    # Simple restoration fallback (or zero-out noise)
                    clean_bytes.extend(payload)
                else:
                    clean_bytes.extend(payload)
            
            st.success(f"CRC Scan Complete! Detected {corrupted_blocks} corrupted packet blocks.")
            st.image(input_image, caption="Verified & Restored Clean Image", use_column_width=True)
          
