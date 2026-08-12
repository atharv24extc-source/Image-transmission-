# Digital Communication Micro-Project: Image Transmission with CRC Error Detection

A software-only simulation of a digital image transmission pipeline over a noisy channel using **Python**, featuring **CRC-8 error detection**.

## 🛠️ Features
- **Bitstream Conversion:** Flattens image pixels into raw binary packets.
- **Channel Coding:** Appends CRC-8 checksum bytes to each packet.
- **Noise Simulation:** Simulates a Binary Symmetric Channel (BSC) with custom Bit Error Rate (BER).
- **Error Detection & Visual Output:** Highlights corrupted pixel packets in an interactive Matplotlib error map.

## 🚀 How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
