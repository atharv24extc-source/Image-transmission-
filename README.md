# Real-Time Image Transmission over Sockets with CRC-8 Error Detection

A software-only Python project that transmits image data between two devices over a Wi-Fi socket connection, injecting simulated channel noise and highlighting corrupted data blocks via CRC-8 verification.

## 📁 Repository Structure
- **`sender.py`**: Runs on Device A. Encodes an image, appends CRC-8 bytes, simulates channel bit flips, and transmits packets via TCP.
- **`receiver.py`**: Runs on Device B. Listens on a network port, verifies incoming CRC checksums, flags corrupted blocks, and renders the output image along with an error map.
- **`main.py`**: Single-script standalone simulation.

## 🚀 How to Run on Two Devices (Wi-Fi)

1. **Install dependencies on both devices:**
   ```bash
   pip install -r requirements.txt
   
