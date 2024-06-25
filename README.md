# Air-Guard - ESP32 based Wi-Fi Intrusion Detection System
Air-Guard is a powerful and user-friendly tool designed to monitor and analyze wireless communication data in real-time. It uses an ESP32 microcontroller to capture WiFi packets and provides a graphical interface for data visualization and analysis.

## Features

- Real-time WiFi packet capture using ESP32
- Graphical user interface for easy interaction
- Live packet statistics and visualization
- Detection of deauthentication attacks and Evil_Twin attacks
- Machine learning-based detection of Kr00k vulnerability and web spoofing attacks
- Logging and data export via .pcap files or .log files

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/razvan-radutoiu/Air-Guard.git
    ```
2. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Connect your ESP32 device to your computer.
2. Upload the sniffer script from the ardunio folder to the ESP32 board (tested with Arduino IDE only, but should work with other tools like esptool.py or ESP-IDF)
3. Run the main script:
    ```bash
    python3 main.py
    ```
