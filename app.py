# coding: utf-8
"""
WSL Orchestrator (Multi-Language Version)

Windows Subsystem for Linux (WSL2) のディストリビューションを管理するための
シンプルなGUIツールです。
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import re
import os
import tempfile
import threading
import json
import configparser
import sys

def resource_path(relative_path):
    """ 開発環境とEXE実行環境の両方でリソースへの絶対パスを取得する """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WSLOrchestrator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_file = 'config.ini'
        self.load_config()
        self.load_language()
        self.title(self.get_string("app_title", fallback="WSL Orchestrator"))
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        style = ttk.Style(self)
        style.configure("TButton", padding=6, relief="flat", font=('Yu Gothic UI', 10))
        style.configure("TLabel", padding=5)
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=('Yu Gothic UI', 10, 'bold'))
        self.create_menus()
        self.create_widgets()
        self.populate_wsl_list()
        self.update_idletasks()
        min_width = self.winfo_reqwidth()
        min_height = self.winfo_reqheight()
        self.minsize(min_width, min_height)

    def get_string(self, key, fallback=None, **kwargs):
        if fallback is None:
            fallback = key
        return self.lang_data.get(key, fallback).format(**kwargs)

    def load_language(self):
        try:
            locale_path = resource_path(os.path.join("locale", f"{self.current_language}.json"))
            with open(locale_path, 'r', encoding='utf-8-sig') as f:
                self.lang_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.current_language = 'en'
            self.lang_data = {}
            messagebox.showwarning("Language Error", f"Could not load language file '{self.current_language}'.\nError: {e}\nFalling back to English.")
            try:
                fallback_path = resource_path(os.path.join("locale", "en.json"))
                with open(fallback_path, 'r', encoding='utf-8-sig') as f:
                    self.lang_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                 messagebox.showerror("Critical Error", "Default language file 'locale/en.json' is missing or corrupt.")

    def load_config(self):
        self.app_config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.app_config.read(self.config_file)
            self.current_language = self.app_config.get('Settings', 'language', fallback='ja')
        else:
            self.current_language = 'ja'

    def save_config(self):
        if 'Settings' not in self.app_config:
            self.app_config['Settings'] = {}
        self.app_config['Settings']['language'] = self.current_language
        with open(self.config_file, 'w') as configfile:
            self.app_config.write(configfile)

    def on_closing(self):
        self.save_config()
        self.destroy()

    def create_menus(self):
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.get_string("menu_file"), menu=self.file_menu)
        self.file_menu.add_command(label=self.get_string("menu_quit"), command=self.on_closing)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.get_string("menu_settings"), menu=self.settings_menu)
        self.lang_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label=self.get_string("menu_language"), menu=self.lang_menu)
        self.lang_menu.add_command(label="日本語", command=lambda: self.change_language('ja'))
        self.lang_menu.add_command(label="English", command=lambda: self.change_language('en'))
        self.lang_menu.add_command(label="Español", command=lambda: self.change_language('es'))
        self.lang_menu.add_command(label="Français", command=lambda: self.change_language('fr'))
        self.lang_menu.add_command(label="العربية", command=lambda: self.change_language('ar'))
        self.lang_menu.add_command(label="हिन्दी", command=lambda: self.change_language('hi'))
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.get_string("menu_help"), menu=self.help_menu)
        self.help_menu.add_command(label=self.get_string("menu_about"), command=self.show_about)

    def create_widgets(self):
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.destroy()
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True)
        cols = ("Name", "State", "Version")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        button_frame = ttk.Frame(main_frame, padding=(0, 10))
        button_frame.pack(fill="x")
        self.refresh_button = ttk.Button(button_frame, command=self.populate_wsl_list)
        self.refresh_button.pack(side="left", padx=5)

        # ★★★ ここからが変更点 ★★★
        self.terminal_button = ttk.Button(button_frame, command=self.open_terminal, state="disabled")
        self.terminal_button.pack(side="left", padx=5)
        # ★★★ ここまでが変更点 ★★★

        self.start_button = ttk.Button(button_frame, command=self.start_distro, state="disabled")
        self.start_button.pack(side="left", padx=5)
        self.rename_button = ttk.Button(button_frame, command=self.rename_distro, state="disabled")
        self.rename_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(button_frame, command=self.terminate_distro, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        self.shutdown_button = ttk.Button(button_frame, command=self.shutdown_all)
        self.shutdown_button.pack(side="left", padx=5)
        self.shortcut_frame = ttk.LabelFrame(main_frame, padding="10")
        self.shortcut_frame.pack(fill="x", pady=10)
        self.shortcut_label1 = ttk.Label(self.shortcut_frame)
        self.shortcut_label1.pack(anchor="w")
        self.shortcut_command_var = tk.StringVar()
        shortcut_entry = ttk.Entry(self.shortcut_frame, textvariable=self.shortcut_command_var, state="readonly", font=('Courier New', 10))
        shortcut_entry.pack(fill="x", pady=(0, 5))
        self.shortcut_label2 = ttk.Label(self.shortcut_frame, foreground="gray")
        self.shortcut_label2.pack(anchor="w")
        guidance_frame = ttk.Frame(main_frame)
        guidance_frame.pack(fill="x")
        self.usb_guide_button = ttk.Button(guidance_frame, command=self.show_usb_guide)
        self.usb_guide_button.pack(side="left", padx=5)
        self.update_ui_language()

    def update_ui_language(self):
        self.title(self.get_string("app_title"))
        self.menubar.entryconfig(1, label=self.get_string("menu_file"))
        self.file_menu.entryconfig(0, label=self.get_string("menu_quit"))
        self.menubar.entryconfig(2, label=self.get_string("menu_settings"))
        self.settings_menu.entryconfig(0, label=self.get_string("menu_language"))
        self.menubar.entryconfig(3, label=self.get_string("menu_help"))
        self.help_menu.entryconfig(0, label=self.get_string("menu_about"))
        self.tree.heading("Name", text=self.get_string("column_name"))
        self.tree.heading("State", text=self.get_string("column_state"))
        self.tree.heading("Version", text=self.get_string("column_version"))
        self.refresh_button.config(text=self.get_string("button_refresh"))
        self.terminal_button.config(text=self.get_string("button_terminal")) # ★★★ 追加 ★★★
        self.start_button.config(text=self.get_string("button_start"))
        self.rename_button.config(text=self.get_string("button_rename"))
        self.stop_button.config(text=self.get_string("button_stop"))
        self.shutdown_button.config(text=self.get_string("button_shutdown"))
        self.usb_guide_button.config(text=self.get_string("usb_guide_button"))
        self.shortcut_frame.config(text=self.get_string("shortcut_title"))
        self.shortcut_label1.config(text=self.get_string("shortcut_label"))
        self.shortcut_label2.config(text=self.get_string("shortcut_howto"))
    
    def change_language(self, lang_code):
        if self.current_language == lang_code: return
        self.current_language = lang_code
        self.load_language()
        self.update_ui_language()
    
    def show_about(self):
        messagebox.showinfo(self.get_string("about_title"), self.get_string("about_message"))

    def run_command(self, command):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-16-le', errors='ignore', check=True, startupinfo=startupinfo)
            return result.stdout
        except FileNotFoundError:
            return f"Error: {self.get_string('error_wsl_not_found')}"
        except subprocess.CalledProcessError as e:
            return f"Error: Command Error\n{e.stderr}"

    def populate_wsl_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        output = self.run_command(["wsl", "--list", "--verbose"])
        if output is None or output.startswith("Error:"): return
        lines = output.strip().split('\n')[1:]
        for line in lines:
            cleaned_line = line.strip().lstrip('\ufeff')
            if not cleaned_line: continue
            if cleaned_line.startswith('*'):
                processed_line = cleaned_line[1:].lstrip()
            else:
                processed_line = cleaned_line
            parts = re.split(r'\s{2,}', processed_line)
            if len(parts) == 3:
                name = re.sub(r'[^\w.-]', '', parts[0])
                state = parts[1].strip().replace('\x00', '')
                version = parts[2].strip().replace('\x00', '')
                self.tree.insert("", "end", values=(name, state, version))
        self.on_item_select(None)

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = self.tree.item(selected_items[0])
            distro_name, distro_state, _ = selected_item['values']
            
            # ★★★ ここからが変更点 ★★★
            self.terminal_button.config(state="normal") # 常に有効化
            
            if distro_state == "Stopped":
                self.start_button.config(state="normal")
                self.rename_button.config(state="normal")
                self.stop_button.config(state="disabled")
            else: # Running or other states
                self.start_button.config(state="disabled")
                self.rename_button.config(state="disabled")
                self.stop_button.config(state="normal")
            
            if ' ' in distro_name:
                command = f'wsl.exe -d "{distro_name}"'
            else:
                command = f'wsl.exe -d {distro_name}'
            self.shortcut_command_var.set(command)
        else:
            self.terminal_button.config(state="disabled") # ★★★ 追加 ★★★
            self.start_button.config(state="disabled")
            self.stop_button.config(state="disabled")
            self.rename_button.config(state="disabled")
            self.shortcut_command_var.set("")
        # ★★★ ここまでが変更点 ★★★

    # ★★★ ここからが変更点 ★★★
    def open_terminal(self):
        """選択されたWSLインスタンスのターミナルを開く"""
        selected_items = self.tree.selection()
        if not selected_items: return
        distro_name = self.tree.item(selected_items[0])['values'][0]
        try:
            command_to_run = ["wsl", "-d", distro_name, "--cd", "~"]
            subprocess.Popen(command_to_run, creationflags=subprocess.CREATE_NEW_CONSOLE)
            # 起動と違い、状態が変わらないためリストの自動更新は不要
        except FileNotFoundError:
            messagebox.showerror(self.get_string("error_title"), self.get_string("error_wsl_not_found"))
    # ★★★ ここまでが変更点 ★★★

    def start_distro(self):
        """選択されたWSLインスタンスを起動します。"""
        selected_items = self.tree.selection()
        if not selected_items: return
        distro_name = self.tree.item(selected_items[0])['values'][0]
        try:
            command_to_run = ["wsl", "-d", distro_name, "--cd", "~"]
            subprocess.Popen(command_to_run, creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.after(1500, self.populate_wsl_list)
        except FileNotFoundError:
            messagebox.showerror(self.get_string("error_title"), self.get_string("error_wsl_not_found"))

    def terminate_distro(self):
        selected_items = self.tree.selection()
        if not selected_items: return
        distro_name = self.tree.item(selected_items[0])['values'][0]
        if messagebox.askyesno(self.get_string("confirm_stop_title"), self.get_string("confirm_stop_message", distro_name=distro_name)):
            self.run_command(["wsl", "--terminate", distro_name])
            self.populate_wsl_list()

    def shutdown_all(self):
        if messagebox.askyesno(self.get_string("confirm_shutdown_title"), self.get_string("confirm_shutdown_message")):
            self.run_command(["wsl", "--shutdown"])
            self.populate_wsl_list()
    
    def rename_distro(self):
        selected_items = self.tree.selection()
        if not selected_items: return
        old_name, state, _ = self.tree.item(selected_items[0])['values']
        if state != "Stopped":
            messagebox.showerror(self.get_string("error_title"), self.get_string("error_rename_stopped"))
            return
        new_name = simpledialog.askstring(self.get_string("rename_dialog_title"), self.get_string("rename_dialog_prompt", old_name=old_name), initialvalue=old_name, parent=self)
        if not new_name or not new_name.strip() or new_name == old_name: return
        if ' ' in new_name:
            messagebox.showerror(self.get_string("error_title"), self.get_string("error_rename_no_space"))
            return
        current_names = [self.tree.item(i)['values'][0] for i in self.tree.get_children()]
        if new_name in current_names:
            messagebox.showerror(self.get_string("error_title"), self.get_string("error_rename_duplicate", new_name=new_name))
            return
        if not messagebox.askyesno(self.get_string("rename_confirm_title"), self.get_string("rename_confirm_message", old_name=old_name, new_name=new_name)): return
        self.show_progress_window()
        self.rename_thread = threading.Thread(target=self._rename_worker, args=(old_name, new_name))
        self.rename_thread.start()
        self.check_rename_status()

    def _rename_worker(self, old_name, new_name):
        temp_dir = tempfile.gettempdir()
        export_file = os.path.join(temp_dir, f"{old_name}_export.tar")
        result = self.run_command(["wsl", "--export", old_name, export_file])
        if result and result.startswith("Error:"):
            self.rename_result = f"Export failed:\n{result}"
            return
        result = self.run_command(["wsl", "--unregister", old_name])
        if result and result.startswith("Error:"):
            self.rename_result = f"Unregister failed:\n{result}"
            os.remove(export_file)
            return
        docs_path = os.path.join(os.path.expanduser('~'), 'Documents')
        import_dir = os.path.join(docs_path, 'WSL_Distros', new_name)
        os.makedirs(import_dir, exist_ok=True)
        result = self.run_command(["wsl", "--import", new_name, import_dir, export_file])
        if result and result.startswith("Error:"):
            self.rename_result = f"Import failed:\n{result}"
            os.remove(export_file)
            return
        os.remove(export_file)
        self.rename_result = self.get_string("rename_success_message", new_name=new_name)

    def show_progress_window(self):
        self.progress_win = tk.Toplevel(self)
        self.progress_win.title(self.get_string("rename_progress_title"))
        self.progress_win.geometry("300x100")
        self.progress_win.resizable(False, False)
        self.progress_win.transient(self)
        self.progress_win.grab_set()
        label = ttk.Label(self.progress_win, text=self.get_string("rename_progress_message"), font=("Yu Gothic UI", 10))
        label.pack(expand=True, pady=10)
        prog_bar = ttk.Progressbar(self.progress_win, mode='indeterminate')
        prog_bar.pack(fill='x', padx=20, pady=5)
        prog_bar.start(10)

    def check_rename_status(self):
        if self.rename_thread.is_alive():
            self.after(100, self.check_rename_status)
        else:
            self.progress_win.destroy()
            if hasattr(self, 'rename_result'):
                if "failed" in self.rename_result.lower():
                     messagebox.showerror(self.get_string("error_title"), self.rename_result)
                else:
                     messagebox.showinfo("Success", self.rename_result)
            self.populate_wsl_list()

    def show_usb_guide(self):
        title = self.get_string("usb_guide_title")
        message = self.get_string("usb_guide_message")
        messagebox.showinfo(title, message)

if __name__ == "__main__":
    app = WSLOrchestrator()
    app.mainloop()