# ui/tabs/param_tab.py
from tkinter import ttk
import tkinter as tk
from utils.options_utils import save_yaml

def create_param_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Paramètres")

        inner = ttk.Frame(frame)
        inner.pack(expand=True)
    
        self.start_var = tk.StringVar(value=self.general_config["start_date"])
        self.end_var = tk.StringVar(value=self.general_config["end_date"])
        self.capital_var = tk.StringVar(value=str(self.general_config["capital"]))
        self.fee_rate_var = tk.StringVar(value=str(self.general_config["fee_rate"]*100))
        self.slippage_var = tk.StringVar(value=str(self.general_config["slippage"]*100))
    
        def on_change_start(*_):  # *_ ignore les args inutiles
            self.general_config["start_date"] = self.start_var.get()
            save_yaml(self.general_config, "config/general.yaml")

        def on_change_end(*_):
            self.general_config["end_date"] = self.end_var.get()
            save_yaml(self.general_config, "config/general.yaml")

        def on_change_capital(*_):
            self.general_config["capital"] = float(self.capital_var.get())
            save_yaml(self.general_config, "config/general.yaml")
            
        def on_change_fee_rate(*_):
            self.general_config["fee_rate"] = float(self.fee_rate_var.get())/100
            save_yaml(self.general_config, "config/general.yamconfig/general.yaml")    
        
        def on_change_slippage(*_):
            self.general_config["slippage"] = float(self.slippage_var.get())/100
            save_yaml(self.general_config, "config/general.yaml") 
        
        self.start_var.trace_add("write", on_change_start)
        self.end_var.trace_add("write", on_change_end)
        self.capital_var.trace_add("write", on_change_capital) 
        self.fee_rate_var.trace_add("write", on_change_fee_rate)
        self.slippage_var.trace_add("write", on_change_slippage) 
    
        ttk.Label(inner, text="Date de début:").grid(row=0, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.start_var, width=20).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(inner, text="Date de fin:").grid(row=1, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.end_var, width=20).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(inner, text="Capital initial:").grid(row=2, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.capital_var, width=20).grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(inner, text="Frais de transactions (%):").grid(row=3, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.fee_rate_var, width=20).grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(inner, text="Glissement (%):").grid(row=4, column=0, sticky='e', padx=10, pady=5)
        ttk.Entry(inner, textvariable=self.slippage_var, width=20).grid(row=4, column=1, padx=10, pady=5)

        return frame