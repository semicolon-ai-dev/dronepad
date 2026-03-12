"""DronePad — Entry point."""
import tkinter as tk
from app.ui.dashboard import DashboardApp


def main():
    root = tk.Tk()
    root.title("DronePad")
    root.geometry("1280x800")
    root.minsize(1024, 680)
    root.configure(bg="#0f0f11")

    try:
        root.iconphoto(True, tk.PhotoImage(file="assets/icon.png"))
    except Exception:
        pass

    app = DashboardApp(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
