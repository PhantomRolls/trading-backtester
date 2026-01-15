import tkinter as tk
from tkinter import ttk

class ValueLabel(ttk.Frame):
    def __init__(self, parent, label, suffix="", secondary_suffix="", color=None, secondary=False):
        super().__init__(parent)

        self.suffix = suffix
        self.secondary_suffix = secondary_suffix
        self.color = color
        self.secondary = secondary

        # Label texte
        ttk.Label(self, text=f"{label}: ", font=("Segoe UI", 10)).pack(side="left")

        # Valeur principale
        self.value_var = tk.StringVar(value="N/A")
        self.value_label = tk.Label(
            self,
            textvariable=self.value_var,
            font=("Segoe UI", 10 if not secondary else 9, "bold")
        )
        self.value_label.pack(side="left", padx=5)

        # Valeur secondaire : exemple "(+5%)"
        self.sec_var = tk.StringVar(value="")
        self.secondary_label = tk.Label(
            self,
            textvariable=self.sec_var,
            font=("Segoe UI", 9),
            fg="#008000"   # mis en vert par défaut
        )
        self.secondary_label.pack(side="left", padx=5)

    # ---- Coloration intelligente ----
    def apply_color_logic(self, stat_name, value):
        if value is None:
            self.value_label.config(fg="black")
            return

        if "Return" in stat_name:
            self.value_label.config(fg="#008000" if value > 0 else "#B00000")

        elif "Volatility" in stat_name:
            self.value_label.config(fg="#004CFF")

        elif "Sharpe" in stat_name:
            if value > 1:
                self.value_label.config(fg="#008000")
            elif value > 0:
                self.value_label.config(fg="#000000")
            else:
                self.value_label.config(fg="#B00000")

        elif "Drawdown" in stat_name:
            self.value_label.config(fg="#B00000")
        elif "P/L" in stat_name or "PnL" in stat_name:
            # Spécifique au IV Crush : colorer selon profit/perte
            self.value_label.config(fg="#008000" if value > 0 else "#B00000")

        else:
            self.value_label.config(fg=self.color or "black")

    # ---- Mise à jour ----
    def set(self, stat_name, value, secondary_value=None):
        """Met à jour la valeur principale + secondaire."""
        # ---------- Valeur principale ----------
        if value is None:
            self.value_var.set("N/A")
            self.apply_color_logic(stat_name, None)
        else:
            if isinstance(value, float):
                self.value_var.set(f"{value:.2f}{self.suffix}")
            else:
                self.value_var.set(str(value))
            self.apply_color_logic(stat_name, value)

        # ---------- Valeur secondaire ----------
        if secondary_value is None:
            self.sec_var.set("")
        else:
            if isinstance(secondary_value, float):
                self.sec_var.set(f"({secondary_value:.2f}{self.secondary_suffix})")
            else:
                self.sec_var.set(f"({secondary_value}{self.secondary_suffix})")
