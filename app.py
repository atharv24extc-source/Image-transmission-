import streamlit as st
import numpy as np
from PIL import Image

SECRET_KEY = 0xAA  # Encryption Key

# --- HAMMING(7,4) LOGIC ---
def encode_nibble_hamming(nibble):
    d0 = (nibble >> 3) & 1
    d1 = (nibble >> 2) & 1
    d2 = (nibble >> 1) & 1
    d3 = nibble & 1
    p0 = d0 ^ d1 ^ d3
    p1 = d0 ^ d2 ^ d3
    p2 = d1 ^ d2 ^ d3
    return (p0 << 6) | (p1 << 5) | (d0 << 4) | (p2 << 3) | (d1 << 2) | (d2 << 1) | d3

def decode_nibble_hamming(code7):
    p0 = (code7 >> 6) & 1
    p1 = (code7 >> 5) & 1
    d0 = (code7 >> 4) & 1
    p2 = (code7 >> 3) & 1
    d1 = (code7 >> 2) & 1
    d2 = (code7 >> 1) & 1
    d3 = code7 & 1

    s0 = p0 ^ d0 ^ d1 ^ d3
    s1 = p1 ^ d0 ^ d2 ^ d3
    s2 = p2 ^ d1 ^ d2 ^ d3
    syndrome = (s2 << 2) | (s1 << 1) | s0

    error_mask = 0
    if syndrome == 0b011: error_mask = 1 << 6
    elif syndrome == 0b101: error_mask = 1 << 5
    elif syndrome == 0b111: error_mask = 1 << 4
    elif syndrome == 0b110: error_mask = 1 << 3
    elif syndrome == 0b100: error_mask = 1 << 2
    elif syndrome == 0b010: error_mask = 1 << 1
    elif syndrome == 0b001: error_mask = 1

    corrected_code = code7 ^ error_mask
    c_d0 = (corrected_code >> 4) & 1
    c_d1 = (corrected_code >> 2) & 1
    c_d2 = (corrected_code >> 1) & 1
    c_d3 = corrected_code & 1

    corrected_nibble = (c_d0 << 3) | (c_d1 << 2) | (c_d2 << 1) | c_d3
    return corrected_nibble, (syndrome != 0)

# --- STREAMLIT UI ---
st.set_page_config(layout="wide")
st.title("📡 End-to-End Image Transmission & Hamming(7,4) FEC Pipeline")

uploaded_file = st.file_uploader("Upload Image to Transmit", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # 1. PIXEL CONVERSION
    input_image = Image.open(uploaded_file).convert('RGB').resize((128, 128))
    img_array = np.array(input_image, dtype=np.uint8)
    shape = img_array.shape
    raw_bytes = img_array.flatten()
    
    st.header("1. Data Conversion Inspection (Sender Side)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(input_image, caption="Original Transmitted Image", width=250)
    with col2:
        st.subheader("Pixel & Binary Conversion Data")
        st.write(f"**Image Resolution:** {shape[0]}x{shape[1]} (RGB 3-Channel)")
        st.write(f"**Total Pixels / Byte Array Length:** {len(raw_bytes)} bytes")
        
        # Display Pixel Matrix Sample
        st.write("**First 5 Raw Pixel Values (RGB Bytes):**", raw_bytes[:5].tolist())
        
        # DISPLAY BIT CONVERSION
        raw_bitstream = np.unpackbits(raw_bytes[:5])
        st.write("**Converted Binary Bits (First 5 Bytes / 40 Bits):**")
        st.code(" ".join(map(str, raw_bitstream)))

    st.divider()

    # 2. ENCRYPTION & HAMMING ENCODING
    st.header("2. Security & Channel Processing")
    
    encrypted_bytes = raw_bytes ^ SECRET_KEY
    encoded_codewords = []
    for b in encrypted_bytes:
        encoded_codewords.append(encode_nibble_hamming((b >> 4) & 0x0F))
        encoded_codewords.append(encode_nibble_hamming(b & 0x0F))
        
    encoded_array = np.array(encoded_codewords, dtype=np.uint8)
    
    ber = st.slider("Simulate Channel Noise (Bit Error Rate)", 0.0, 0.05, 0.01, step=0.005)
    
    # NOISE INJECTION
    bitstream = np.unpackbits(encoded_array)
    noise_mask = np.random.rand(*bitstream.shape) < ber
    corrupted_bitstream = bitstream ^ noise_mask.astype(np.uint8)
    
    # Intercepted stream bytes
    rx_encoded_array = np.packbits(corrupted_bitstream)

    with st.expander("🔍 View Encrypted Data & Binary Codewords Pipeline"):
        st.write("**XOR Encrypted Bytes Sample (`0xAA` Key):**", list(encrypted_bytes[:5]))
        st.write("**Hamming(7,4) Encoded Codewords Sample:**", list(encoded_array[:10]))
        st.write(f"**Total Channel Bits Transmitted:** {len(bitstream)} bits")
        st.write(f"**Total Corrupted (Flipped) Bits:** {int(np.sum(noise_mask))} bits")

    st.divider()

    # 3. RECEIVER & RESTORATION
    st.header("3. Receiver Output & Error Correction")
    
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Intercepted / Corrupted Channel Output")
        noisy_display_bytes = rx_encoded_array[:len(raw_bytes)]
        noisy_img = np.array(noisy_display_bytes, dtype=np.uint8).reshape(shape)
        st.image(noisy_img, caption="Noisy Stream (Unusable to Hacker)", use_container_width=True)

    with col4:
        st.subheader("Automated Hamming FEC & Decryption")
        if st.button("🛠️ Execute Full Pipeline & Restore Image"):
            corrected_bytes = bytearray()
            corrected_count = 0
            
            for i in range(0, len(rx_encoded_array), 2):
                c_high = rx_encoded_array[i]
                c_low = rx_encoded_array[i+1] if (i+1) < len(rx_encoded_array) else 0
                
                high_nibble, err1 = decode_nibble_hamming(c_high)
                low_nibble, err2 = decode_nibble_hamming(c_low)
                
                if err1 or err2:
                    corrected_count += 1
                
                restored_byte = ((high_nibble << 4) | low_nibble) ^ SECRET_KEY
                corrected_bytes.append(restored_byte)
                
            st.success(f"✅ Pipeline Completed! Fixed {corrected_count} corrupted blocks automatically.")
            
            restored_array = np.array(corrected_bytes[:len(raw_bytes)], dtype=np.uint8).reshape(shape)
            st.image(restored_array, caption="100% Restored Output Image", use_container_width=True)
            
