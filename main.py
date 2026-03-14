import sys
import threading
import yaml
import customtkinter as ctk
from tkinter import ttk

import bot_core
from database import search_maps, get_stats

CONFIG_FILE = "config.yml"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class EnterpriseApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("LatinBattle Map Manager Enterprise")
        self.geometry("1400x820")

        self.bot_running = False
        self.bot_thread = None

        self.create_layout()
        self.create_dashboard()
        self.create_maps()
        self.create_config()
        self.create_logs()

        self.show_page("dashboard")
        self.refresh_all()

    # ---------------------------
    # LAYOUT
    # ---------------------------

    def create_layout(self):

        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.main = ctk.CTkFrame(self)
        self.main.pack(side="right", fill="both", expand=True)

        title = ctk.CTkLabel(
            self.sidebar,
            text="LatinBattle\nManager",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        title.pack(pady=20)

        self.status_indicator = ctk.CTkLabel(
            self.sidebar,
            text="● BOT OFFLINE",
            text_color="red"
        )
        self.status_indicator.pack(pady=10)

        ctk.CTkButton(
            self.sidebar,
            text="Iniciar Bot",
            command=self.start_bot
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(
            self.sidebar,
            text="Detener Bot",
            command=self.stop_bot
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(
            self.sidebar,
            text="Dashboard",
            command=lambda: self.show_page("dashboard")
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(
            self.sidebar,
            text="Mapas",
            command=lambda: self.show_page("maps")
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(
            self.sidebar,
            text="Configuración",
            command=lambda: self.show_page("config")
        ).pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(
            self.sidebar,
            text="Logs",
            command=lambda: self.show_page("logs")
        ).pack(fill="x", padx=15, pady=5)

        self.pages = {}

    # ---------------------------
    # DASHBOARD
    # ---------------------------

    def create_dashboard(self):

        frame = ctk.CTkFrame(self.main)
        self.pages["dashboard"] = frame

        header = ctk.CTkLabel(
            frame,
            text="Dashboard",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=20)

        cards = ctk.CTkFrame(frame)
        cards.pack(fill="x", padx=20)

        self.card_total_maps = ctk.CTkLabel(
            cards,
            text="Total mapas\n0",
            width=250,
            height=120,
            fg_color="#2b2d31",
            corner_radius=10
        )
        self.card_total_maps.pack(side="left", padx=10)

        self.card_storage = ctk.CTkLabel(
            cards,
            text="Espacio usado\n0 MB",
            width=250,
            height=120,
            fg_color="#2b2d31",
            corner_radius=10
        )
        self.card_storage.pack(side="left", padx=10)

        self.card_bot = ctk.CTkLabel(
            cards,
            text="Estado Bot\nOFFLINE",
            width=250,
            height=120,
            fg_color="#2b2d31",
            corner_radius=10
        )
        self.card_bot.pack(side="left", padx=10)

        self.activity_box = ctk.CTkTextbox(frame, height=400)
        self.activity_box.pack(fill="both", expand=True, padx=20, pady=20)

    # ---------------------------
    # MAPS
    # ---------------------------

    def create_maps(self):

        frame = ctk.CTkFrame(self.main)
        self.pages["maps"] = frame

        top = ctk.CTkFrame(frame)
        top.pack(fill="x", padx=20, pady=20)

        self.search_entry = ctk.CTkEntry(top, placeholder_text="Buscar mapa...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10)

        ctk.CTkButton(
            top,
            text="Buscar",
            command=self.refresh_maps
        ).pack(side="left", padx=10)

        table_frame = ctk.CTkFrame(frame)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("ID", "Usuario", "Mapa", "Archivo", "Tamaño", "Fecha")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        for c in columns:
            self.tree.heading(c, text=c)

        self.tree.pack(fill="both", expand=True)

    # ---------------------------
    # CONFIG
    # ---------------------------

    def create_config(self):

        frame = ctk.CTkFrame(self.main)
        self.pages["config"] = frame

        header = ctk.CTkLabel(
            frame,
            text="Configuración",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        header.pack(anchor="w", padx=20, pady=20)

        cfg = self.load_config()

        self.token = ctk.CTkEntry(frame)
        self.token.insert(0, cfg["discord"]["token"])
        self.token.pack(pady=10, padx=20, fill="x")

        self.channel = ctk.CTkEntry(frame)
        self.channel.insert(0, cfg["discord"]["channel_name"])
        self.channel.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(
            frame,
            text="Guardar configuración",
            command=self.save_config
        ).pack(pady=10)

    # ---------------------------
    # LOGS
    # ---------------------------

    def create_logs(self):

        frame = ctk.CTkFrame(self.main)
        self.pages["logs"] = frame

        self.log_box = ctk.CTkTextbox(frame)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=20)

        sys.stdout = self
        sys.stderr = self

    def write(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def flush(self):
        pass

    # ---------------------------
    # BOT CONTROL
    # ---------------------------

    def start_bot(self):

        if self.bot_running:
            return

        def run():
            self.bot_running = True
            self.update_status()
            bot_core.start_bot()

        self.bot_thread = threading.Thread(target=run, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):

        if not self.bot_running:
            return

        bot_core.stop_bot()
        self.bot_running = False
        self.update_status()

    def update_status(self):

        if self.bot_running:
            self.status_indicator.configure(
                text="● BOT ONLINE",
                text_color="green"
            )
            self.card_bot.configure(text="Estado Bot\nONLINE")
        else:
            self.status_indicator.configure(
                text="● BOT OFFLINE",
                text_color="red"
            )
            self.card_bot.configure(text="Estado Bot\nOFFLINE")

    # ---------------------------
    # DATA
    # ---------------------------

    def refresh_maps(self):

        term = self.search_entry.get()
        rows = search_maps(term)

        for r in self.tree.get_children():
            self.tree.delete(r)

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["discord_user"],
                    row["map_name"],
                    row["map_file"],
                    f'{row["file_size"]/1024/1024:.2f} MB',
                    row["created_at"]
                )
            )

    def refresh_stats(self):

        stats = get_stats()

        self.card_total_maps.configure(
            text=f'Total mapas\n{stats["total_maps"]}'
        )

        size_mb = stats["total_size"] / 1024 / 1024

        self.card_storage.configure(
            text=f'Espacio usado\n{size_mb:.2f} MB'
        )

    def refresh_all(self):
        self.refresh_maps()
        self.refresh_stats()

    # ---------------------------
    # CONFIG
    # ---------------------------

    def load_config(self):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def save_config(self):

        cfg = self.load_config()

        cfg["discord"]["token"] = self.token.get()
        cfg["discord"]["channel_name"] = self.channel.get()

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f)

        print("Configuración guardada")

    # ---------------------------
    # NAVIGATION
    # ---------------------------

    def show_page(self, name):

        for p in self.pages.values():
            p.pack_forget()

        self.pages[name].pack(fill="both", expand=True)


if __name__ == "__main__":
    app = EnterpriseApp()
    app.mainloop()