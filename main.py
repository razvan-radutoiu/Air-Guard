import tkinter as tk
from serial_capture_app import SerialCaptureApp

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialCaptureApp(root)
    root.mainloop()
