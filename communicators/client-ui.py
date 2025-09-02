import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tested_communicator import TestedMachineCommunicator


class AgentUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tested Machine Agent")
        self.geometry("900x600")

        self.communicator: TestedMachineCommunicator | None = None
        self.event_consumer_thread: threading.Thread | None = None
        self.running = False
        self.wrap_var = tk.BooleanVar(value=True)

        self._build_widgets()
        self._apply_theme()
        self._build_menubar()

    def _build_widgets(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(header, text="Tested Machine Agent", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)

        # Controls
        control_frame = ttk.LabelFrame(self, text="Controls")
        control_frame.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(control_frame, text="Port:").grid(row=0, column=0, padx=4, pady=4, sticky=tk.W)
        self.port_var = tk.StringVar(value="8888")
        ttk.Entry(control_frame, textvariable=self.port_var, width=8).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(control_frame, text="Machine ID:").grid(row=0, column=2, padx=4, pady=4, sticky=tk.W)
        self.mid_var = tk.StringVar(value="ui_machine_001")
        ttk.Entry(control_frame, textvariable=self.mid_var, width=20).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(control_frame, text="Apps (space separated):").grid(row=0, column=4, padx=4, pady=4, sticky=tk.W)
        self.apps_var = tk.StringVar(value="")
        ttk.Entry(control_frame, textvariable=self.apps_var, width=28).grid(row=0, column=5, padx=4, pady=4)

        self.preload_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Preload Components", variable=self.preload_var).grid(row=0, column=6, padx=8)

        ttk.Button(control_frame, text="Start", command=self.start_agent).grid(row=0, column=7, padx=6)
        ttk.Button(control_frame, text="Stop", command=self.stop_agent).grid(row=0, column=8, padx=6)

        cfg_frame = ttk.Frame(control_frame)
        cfg_frame.grid(row=1, column=0, columnspan=9, sticky=tk.W, padx=4, pady=4)
        self.config_path_var = tk.StringVar(value=os.path.join(os.path.dirname(__file__), "preload", "common_components.json"))
        ttk.Label(cfg_frame, text="Components JSON:").pack(side=tk.LEFT)
        ttk.Entry(cfg_frame, textvariable=self.config_path_var, width=80).pack(side=tk.LEFT, padx=6)
        ttk.Button(cfg_frame, text="Browse", command=self._browse_json).pack(side=tk.LEFT)

        # Events view
        events_frame = ttk.LabelFrame(self, text="Events")
        events_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # Events toolbar
        events_toolbar = ttk.Frame(events_frame)
        events_toolbar.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(events_toolbar, text="Clear", command=self._clear_events).pack(side=tk.RIGHT)
        ttk.Checkbutton(events_toolbar, text="Word wrap", variable=self.wrap_var, command=self._toggle_wrap).pack(side=tk.LEFT)

        # Events text
        self.events_text = scrolledtext.ScrolledText(
            events_frame,
            height=25,
            state=tk.DISABLED,
            wrap=(tk.WORD if self.wrap_var.get() else tk.NONE)
        )
        self.events_text.pack(fill=tk.BOTH, expand=True)
        # Tag styles
        self.events_text.tag_configure("ui", foreground="#0066cc")
        self.events_text.tag_configure("server_request", foreground="#aa6600")
        self.events_text.tag_configure("server_response", foreground="#228833")
        self.events_text.tag_configure("client_request", foreground="#aa0066")
        self.events_text.tag_configure("client_response", foreground="#2a7f62")
        self.events_text.tag_configure("error", foreground="#cc0000", font=(None, 9, "bold"))

        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="Idle")
        self.preload_status_var = tk.StringVar(value="Preload: off")
        ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W).pack(side=tk.LEFT, padx=8, pady=4)
        ttk.Label(status_frame, textvariable=self.preload_status_var, anchor=tk.E).pack(side=tk.RIGHT, padx=8, pady=4)

    def _apply_theme(self):
        try:
            style = ttk.Style()
            themes = style.theme_names()
            if "vista" in themes:
                style.theme_use("vista")
            elif "clam" in themes:
                style.theme_use("clam")
            style.configure("TLabel", padding=(2, 2))
            style.configure("TButton", padding=(6, 2))
            style.configure("TEntry", padding=(2, 2))
            style.configure("TLabelframe", padding=(6, 6))
            style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        except Exception:
            pass

    def _build_menubar(self):
        menubar = tk.Menu(self)
        menu_file = tk.Menu(menubar, tearoff=0)
        menu_file.add_command(label="Start", command=self.start_agent)
        menu_file.add_command(label="Stop", command=self.stop_agent)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=menu_file)

        menu_view = tk.Menu(menubar, tearoff=0)
        menu_view.add_checkbutton(label="Word wrap", onvalue=True, offvalue=False, variable=self.wrap_var, command=self._toggle_wrap)
        menubar.add_cascade(label="View", menu=menu_view)

        menu_help = tk.Menu(menubar, tearoff=0)
        menu_help.add_command(label="About", command=lambda: messagebox.showinfo("About", "Tested Machine Agent\nUI for controlling agent"))
        menubar.add_cascade(label="Help", menu=menu_help)
        self.config(menu=menubar)

    def _browse_json(self):
        path = filedialog.askopenfilename(title="Select components JSON", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            self.config_path_var.set(path)

    def start_agent(self):
        if self.communicator and self.running:
            messagebox.showinfo("Info", "Agent already running")
            return
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port")
            return

        self.communicator = TestedMachineCommunicator(bind_port=port, machine_id=self.mid_var.get())
        self.running = True

        # Load config if preload enabled (scan preload when path missing)
        if self.preload_var.get():
            cfg = self.config_path_var.get()
            if not cfg or not os.path.exists(cfg):
                preload_dir = os.path.join(os.path.dirname(__file__), "preload")
                candidates = []
                try:
                    if os.path.isdir(preload_dir):
                        for fname in os.listdir(preload_dir):
                            if fname.lower().endswith(".json"):
                                candidates.append(os.path.join(preload_dir, fname))
                except Exception:
                    candidates = []
                if candidates:
                    cfg = candidates[0]
                    self.config_path_var.set(cfg)
                    self._append_event_line({"type": "ui", "data": {"msg": f"Auto-selected config: {os.path.basename(cfg)}"}})
                else:
                    self._append_event_line({"type": "ui", "data": {"msg": "No JSON found under preload; disable preload"}})
                    self.preload_var.set(False)
            if self.preload_var.get() and os.path.exists(cfg):
                ok = self.communicator.load_common_components(cfg)
                self._append_event_line({"type": "ui", "data": {"msg": f"Load components: {'OK' if ok else 'FAILED'}"}})

        # Start agent in background
        apps = [x.strip() for x in self.apps_var.get().split() if x.strip()]
        t = threading.Thread(target=self.communicator.start, args=(apps,), daemon=True)
        t.start()

        # Start event consumer
        self.event_consumer_thread = threading.Thread(target=self._consume_events, daemon=True)
        self.event_consumer_thread.start()

        # Trigger preload after start
        if self.preload_var.get():
            def _pre():
                time.sleep(1.0)
                res = self.communicator.preload_all_components()
                self._append_event_line({"type": "ui", "data": {"msg": f"Preload done: {res}"}})
            threading.Thread(target=_pre, daemon=True).start()

        self.status_var.set("Running")
        self.preload_status_var.set(f"Preload: {'on' if self.preload_var.get() else 'off'}")
        self._append_event_line({"type": "ui", "data": {"msg": "Agent started"}})

    def stop_agent(self):
        if self.communicator:
            self.communicator.stop()
            self.running = False
            self.status_var.set("Stopped")
            self.preload_status_var.set("Preload: off")
            self._append_event_line({"type": "ui", "data": {"msg": "Agent stopped"}})

    def _consume_events(self):
        q = self.communicator.ui_event_queue
        while self.running:
            try:
                evt = q.get(timeout=0.5)
                self._append_event_line(evt)
            except Exception:
                pass

    def _append_event_line(self, evt: dict):
        ts = time.strftime("%H:%M:%S", time.localtime(evt.get("timestamp", time.time())))
        et = evt.get("type", "event")
        data = evt.get("data", {})
        line = f"[{ts}] {et}: {data}\n"
        tag = et if et in {"ui", "server_request", "server_response", "client_request", "client_response"} else None
        if isinstance(data, dict) and ("error" in data or et.endswith("error")):
            tag = "error"
        self.events_text.configure(state=tk.NORMAL)
        if tag:
            self.events_text.insert(tk.END, line, tag)
        else:
            self.events_text.insert(tk.END, line)
        self.events_text.configure(state=tk.DISABLED)
        self.events_text.see(tk.END)

    def _clear_events(self):
        self.events_text.configure(state=tk.NORMAL)
        self.events_text.delete("1.0", tk.END)
        self.events_text.configure(state=tk.DISABLED)

    def _toggle_wrap(self):
        try:
            self.events_text.configure(wrap=(tk.WORD if self.wrap_var.get() else tk.NONE))
        except Exception:
            pass


if __name__ == "__main__":
    app = AgentUI()
    app.mainloop()


