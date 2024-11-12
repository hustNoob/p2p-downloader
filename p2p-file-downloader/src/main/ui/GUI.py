import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import asyncio
import threading
import time
from typing import Optional, Dict
from .ProgressBar import ProgressBar
from ..download.DownloadManager import DownloadManager


class DownloadItem(ttk.Frame):
    def __init__(self, master, file_id: str, file_name: str, **kwargs):
        super().__init__(master, **kwargs)

        self.file_id = file_id
        self.file_name = file_name

        # 文件名标签
        self.name_label = ttk.Label(self, text=file_name)
        self.name_label.grid(row=0, column=0, sticky='w', padx=5)

        # 进度条
        self.progress_bar = ProgressBar(self)
        self.progress_bar.grid(row=1, column=0, sticky='ew', padx=5)

        # 速度显示
        self.speed_label = ttk.Label(self, text="0 KB/s")
        self.speed_label.grid(row=0, column=1, padx=5)

        # 状态显示
        self.status_label = ttk.Label(self, text="Waiting...")
        self.status_label.grid(row=1, column=1, padx=5)

        # 控制按钮
        self.control_frame = ttk.Frame(self)
        self.control_frame.grid(row=0, column=2, rowspan=2, padx=5)

        self.pause_button = ttk.Button(self.control_frame, text="Pause",
                                       command=self.toggle_pause)
        self.pause_button.pack(side='left', padx=2)

        self.cancel_button = ttk.Button(self.control_frame, text="Cancel",
                                        command=self.cancel)
        self.cancel_button.pack(side='left', padx=2)

        self.is_paused = False
        self.last_update_time = time.time()
        self.last_downloaded_bytes = 0

    def update_progress(self, progress: float, downloaded_bytes: int):
        self.progress_bar.set_progress(progress)

        # 计算下载速度
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        if time_diff >= 1.0:  # 每秒更新一次速度
            bytes_diff = downloaded_bytes - self.last_downloaded_bytes
            speed = bytes_diff / time_diff

            # 转换速度单位
            if speed >= 1024 * 1024:
                speed_text = f"{speed / (1024 * 1024):.1f} MB/s"
            else:
                speed_text = f"{speed / 1024:.1f} KB/s"

            self.speed_label.config(text=speed_text)
            self.last_update_time = current_time
            self.last_downloaded_bytes = downloaded_bytes

    def update_status(self, status: str):
        self.status_label.config(text=status)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_button.config(text="Resume" if self.is_paused else "Pause")
        # 实现暂停/继续逻辑

    def cancel(self):
        # 实现取消下载逻辑
        pass


class GUI:
    def __init__(self, download_manager: DownloadManager):
        self.download_manager = download_manager
        self.root = tk.Tk()
        self.root.title("P2P File Downloader")
        self.root.geometry("800x600")
        self.setup_ui()
        self.downloads = {}
        self.loop = asyncio.new_event_loop()
        self.thread = None

    def setup_ui(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New Download", command=self.new_download)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="Preferences", command=self.show_preferences)

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.downloads_frame = ttk.LabelFrame(self.main_frame, text="Downloads", padding="5")
        self.downloads_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.downloads_frame.columnconfigure(0, weight=1)

    def new_download(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Download")
        dialog.geometry("400x200")
        dialog.transient(self.root)

        ttk.Label(dialog, text="URL:").grid(row=0, column=0, padx=5, pady=5)
        url_entry = ttk.Entry(dialog, width=40)
        url_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Save to:").grid(row=1, column=0, padx=5, pady=5)
        save_path_var = tk.StringVar()
        save_path_entry = ttk.Entry(dialog, textvariable=save_path_var, width=40)
        save_path_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(dialog, text="Browse",
                  command=lambda: save_path_var.set(filedialog.asksaveasfilename())
                  ).grid(row=1, column=2, padx=5, pady=5)

        def start():
            url = url_entry.get()
            save_path = save_path_var.get()
            if url and save_path:
                self.start_download(url, save_path)
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Please enter URL and save path")

        ttk.Button(dialog, text="Start Download", command=start).grid(
            row=2, column=0, columnspan=3, pady=20)

    def start_download(self, file_id: str, save_path: str):
        download_frame = ttk.Frame(self.downloads_frame)
        download_frame.grid(sticky=(tk.W, tk.E), padx=5, pady=5)
        download_frame.columnconfigure(1, weight=1)

        ttk.Label(download_frame, text=file_id).grid(row=0, column=0, padx=5)
        progress_bar = ProgressBar(download_frame)
        progress_bar.grid(row=0, column=1, padx=5)

        cancel_button = ttk.Button(download_frame, text="Cancel",
                                 command=lambda: self.cancel_download(file_id))
        cancel_button.grid(row=0, column=2, padx=5)

        self.downloads[file_id] = {
            'frame': download_frame,
            'progress_bar': progress_bar,
            'cancel_button': cancel_button
        }

        async def download():
            await self.download_manager.start_download(
                file_id, {}, save_path,
                lambda p: progress_bar.set_progress(p)
            )

        self.loop.create_task(download())

    def cancel_download(self, file_id: str):
        if file_id in self.downloads:
            self.downloads[file_id]['frame'].destroy()
            del self.downloads[file_id]

    def show_preferences(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Preferences")
        dialog.geometry("400x300")
        dialog.transient(self.root)

        # 从配置中读取当前值
        current_speed = self.download_manager.get_max_speed() / 1024  # 转换为KB/s
        current_concurrent = self.download_manager.get_concurrent_downloads()

        ttk.Label(dialog, text="Max Download Speed (KB/s):").grid(row=0, column=0, padx=5, pady=5)
        speed_var = tk.StringVar(value=str(int(current_speed)))
        speed_entry = ttk.Entry(dialog, textvariable=speed_var)
        speed_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Concurrent Downloads:").grid(row=1, column=0, padx=5, pady=5)
        concurrent_var = tk.StringVar(value=str(current_concurrent))
        concurrent_entry = ttk.Entry(dialog, textvariable=concurrent_var)
        concurrent_entry.grid(row=1, column=1, padx=5, pady=5)

        def save():
            try:
                speed = int(speed_var.get()) * 1024  # 转换为字节/秒
                concurrent = int(concurrent_var.get())

                # 更新下载管理器的设置
                self.download_manager.set_max_speed(speed)
                self.download_manager.set_concurrent_downloads(concurrent)

                # 保存到配置文件
                self.download_manager.save_settings()

                dialog.destroy()
                messagebox.showinfo("Success", "Settings saved successfully!")
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")

        ttk.Button(dialog, text="Save", command=save).grid(
            row=2, column=0, columnspan=2, pady=20)

    def run(self):
        def run_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        self.root.mainloop()

    def stop(self):
        if self.loop.is_running():
            self.loop.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join()
