from paths import get_resource_path
from utils import center_window

import customtkinter as ctk

class HelpWindow(ctk.CTkToplevel):
    def __init__(self, master, auto_center=False):
        super().__init__(master)
        self.master = master
        self.lang = "en"  # default language
        self.title("Help")
        self.geometry("500x800")
        self.configure(bg="#1e1e1e")
        self.resizable(False, False)

        # Language toggle buttons (EN / VI)
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.pack(anchor="ne", pady=(10, 0), padx=10)

        self.lang_en_btn = ctk.CTkButton(lang_frame, text="EN", width=60, command=lambda: self.set_language("en"))
        self.lang_vi_btn = ctk.CTkButton(lang_frame, text="VI", width=60, command=lambda: self.set_language("vi"))

        self.lang_en_btn.pack(side="left", padx=5)
        self.lang_vi_btn.pack(side="left", padx=5)

        # Scrollable textbox for content
        self.textbox = ctk.CTkTextbox(self, wrap="word", font=("Segoe UI", 14), text_color="white")
        self.textbox.pack(padx=20, pady=10, fill="both", expand=True)

        self.load_help_text()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Only center if auto_center is True (off by default)
        if auto_center:
            self.after(100, center_window())

    def set_language(self, lang):
        if self.lang != lang:
            self.lang = lang
            self.load_help_text()

    def load_help_text(self):
        filename = f"help_content_{self.lang}.md"

        try:
            with open(get_resource_path(filename), "r", encoding="utf-8") as f:
                help_text = f.read()
        except Exception:
            help_text = "Help content could not be loaded."

        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", help_text)
        self.textbox.configure(state="disabled")