import tkinter as tk
from tkinter import ttk
from typing import Optional

class ProgressBar(ttk.Frame):
    def __init__(self, master: Optional[tk.Widget] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.columnconfigure(0, weight=1)

        self.label = ttk.Label(self, text="0%")
        self.label.grid(row=0, column=1, padx=5)

    def set_progress(self, value: float):
        percentage = min(max(value * 100, 0), 100)
        self.progress_var.set(percentage)
        self.label.config(text=f"{percentage:.1f}%")

    def get_progress(self) -> float:
        return self.progress_var.get() / 100

    def reset(self):
        self.set_progress(0)
