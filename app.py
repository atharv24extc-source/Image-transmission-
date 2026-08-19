
import streamlit as st
import numpy as np
from PIL import Image

SECRET_KEY = 0xAA  # Encryption key

# --- HAMMING(7,4) ENCODING & DECODING LOGIC ---
def encode_nibble_hamming(nibble):
    """Encodes 4 data bits into 7 bits using Hamming(7,4) matrix multiplication"""
    d0 = (nibble >> 3) & 1
    d1 = (nibble >> 2) & 1
    d2 = (nibble >> 1) & 1
    d3 = nibble & 1

    # Parity bits calculation
    p0 = d0 ^ d1 ^ d3
    p1 = d0 ^ d2 ^ d3
    p2 = d1 ^ d2 ^ d3

    # 7-bit codeword: [p0, p1, d0, p2, d1, d2, d3]
    return (p0 << 6) | (p1 << 5) | (d0 << 4) | (p2 << 3) | (d1 << 2) | (d2 << 1) | d3

def decode_nibble_hamming(code7):
    """Detects and automatically CORRECTS 1-bit errors using syndrome decoding"""
    p0 = (code7 >> 6) & 1
    p1 = (code7 >> 5) & 1
    d0 = (code7 >> 4) & 1
    p2 = (code7 >> 3) & 1
    d1 = (code7 >> 2) & 1
    d2 = (code7 >> 1) & 1
    d3 = code7 & 1

    # Calculate Syndrome bits
    s0 = p0 ^ d0 ^ d1 ^ d3
    s1 = p1 ^ d0 ^ d2 ^ d3
    s2 = p2 ^ d1 ^ d2 ^ d3
    
    syndrome = (s2 << 2) | (s1 << 1) | s0

    # Syndrome mapping to fix error bit index
    error_mask = 0
    if syndrome == 0b011: error_mask = 1 << 6 # p0
    elif syndrome == 0b101: error_mask = 1 << 5 # p1
    elif syndrome == 0b111: error_mask = 1 << 4 # d0
    elif syndrome == 0b110: error_mask = 1 << 3 # p2
    elif syndrome == 0b011: error_mask = 1 << 2 # d1
    elif syndrome == 0b101: error_mask = 1 << 1 # d2
    elif syndrome == 0b111: error_mask = 1 # d3

    # Automatically correct the bit flip
    corrected_code = code7 ^ error_mask

    # Extract corrected 4 data bits
    c_d0 = (corrected_code >> 4) & 1
    c_d1 = (corrected_code >> 2) & 1
    c_d2 = (corrected_code >> 1) & 1
    c_d3 = corrected_code & 1

    corrected_nibble = (c_d0 << 3) | (c_d1 << 2) | (c_d2 << 1) | c_d3
    was_error = (syndrome != 0)
    return corrected_nibble, was_error


st.title("📡 Image Transmission with Hamming(7,4) Error Correction")

# 1. SENDER MODULE
st.header("1. Sender Panel")
uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    input_image = Image.open(uploaded_file).convert('RGB').resize((256, 256))
    st.image(input_image, caption="Original Clean Image", width=300)
    
    ber = st.slider("Channel Noise (Bit Error Rate)", 0.0, 0.05, 0.01, step=0.005)
    
    img_array = np.array(input_image, dtype=np.uint8)
    shape = img_array.shape
    raw_bytes = img_array.flatten()
    
    # Encrypt
    encrypted_bytes = raw_bytes ^ SECRET_KEY
    
    # Hamming Encode (Split byte into two 4-bit nibbles)
    encoded_codewords = []
    for b in encrypted_bytes:
        high_nibble = (b >> 4) & 0x0F
        low_nibble = b & 0x0F
        
        encoded_codewords.append(encode_nibble_hamming(high_nibble))
        encoded_codewords.append(encode_nibble_hamming(low_nibble))
        
    encoded_array = np.array(encoded_codewords, dtype=np.uint8)
    
    # Inject Bit-Flip Noise over channel
    bitstream = np.unpackbits(encoded_array)
    noise_mask = np.random.rand(*bitstream.shape) < ber
    corrupted_bitstream = bitstream ^ noise_mask.astype(np.uint8)
    
    # 2. RECEIVER MODULE
    st.divider()
    st.header("2. Receiver Panel")
    
    rx_encoded_array = np.packbits(corrupted_bitstream)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Intercepted Stream")
        # Visualizing corrupted/encrypted byte matrix
        noisy_display_bytes = rx_encoded_array[:len(raw_bytes)]
        noisy_img = np.array(noisy_display_bytes, dtype=np.uint8).reshape(shape)
        st.image(noisy_img, caption="Noisy Channel Output", use_container_width=True)
        
    with col2:
        st.subheader("Correction Controls")
        if st.button("🛠️ Run Hamming Error Correction & Decrypt"):
            corrected_bytes = bytearray()
            corrected_count = 0
            
            for i in range(0, len(rx_encoded_array), 2):
                c_high = rx_encoded_array[i]
                c_low = rx_encoded_array[i+1] if (i+1) < len(rx_encoded_array) else 0
                
                high_nibble, err1 = decode_nibble_hamming(c_high)
                low_nibble, err2 = decode_nibble_hamming(c_low)
                
                if err1 or err2:
                    corrected_count += 1
                
                restored_byte = (high_nibble << 4) | low_nibble
                # Decrypt byte
                decrypted_byte = restored_byte ^ SECRET_KEY
                corrected_bytes.append(decrypted_byte)
                
            st.success(f"Hamming FEC active: Found and automatically FIXED errors in {corrected_count} nibbles!")
            
            restored_array = np.array(corrected_bytes[:len(raw_bytes)], dtype=np.uint8).reshape(shape)
            st.image(restored_array, caption="Automatically Restored & Corrected Output", use_container_width=True)
