import tkinter as tk
from tkinter import ttk, font, messagebox
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# --- Database setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "stats.db")
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
Base = declarative_base()
Session = sessionmaker(bind=ENGINE, future=True)


class Stats(Base):
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    score = Column(Integer, default=0)
    most_consecutive_flips = Column(Integer, default=0)
    objects_destroyed = Column(Integer, default=0)
    air_time = Column(Float, default=0.0)
    tasks_completed = Column(Integer, default=0)
    trophies_collected = Column(Integer, default=0)

    def as_dict(self):
        return {
            "score": self.score,
            "most_consecutive_flips": self.most_consecutive_flips,
            "objects_destroyed": self.objects_destroyed,
            "air_time": self.air_time,
            "tasks_completed": self.tasks_completed,
            "trophies_collected": self.trophies_collected,
            "timestamp": self.timestamp,
        }


Base.metadata.create_all(ENGINE)


# --- App UI ---
class StatsDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stats Dashboard")
        self.geometry("980x480")

        SKY_BLUE = "#87CEEB"
        self.configure(bg=SKY_BLUE)

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except:
            pass

        self.style.configure("Green.TButton", background="#28a745", foreground="white", padding=6)
        self.style.map("Green.TButton", background=[("active", "#1e7e34")])

        self.title_font = font.Font(family="Segoe UI", size=20, weight="bold")
        self.value_font = font.Font(family="Segoe UI", size=22, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)

        # --- Blue panels ---
        self.input_frame = tk.Frame(self, bg=SKY_BLUE, padx=20, pady=20)
        self.input_frame.grid(row=0, column=0, sticky="nsew")

        self.display_frame = tk.Frame(self, bg=SKY_BLUE, padx=20, pady=20)
        self.display_frame.grid(row=0, column=1, sticky="nsew")

        self._build_input_panel(SKY_BLUE)
        self._build_display_panel(SKY_BLUE)

        self.session = Session()
        self.load_list()
        self.load_latest()

    def _build_input_panel(self, bg):
        tk.Label(self.input_frame, text="Enter Stats", font=self.title_font, bg=bg).pack(anchor="w", pady=(0, 15))

        self.entries = {}
        fields = [
            ("score", "Score", int),
            ("most_consecutive_flips", "Most Consecutive Flips", int),
            ("objects_destroyed", "Objects Destroyed", int),
            ("air_time", "Air Time (s)", float),
            ("tasks_completed", "Tasks Completed", int),
            ("trophies_collected", "Trophies Collected", int),
        ]

        form = tk.Frame(self.input_frame, bg=bg)
        form.pack(fill="x", pady=(5, 15))

        for key, txt, _type in fields:
            row = tk.Frame(form, bg=bg)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=txt, width=22, anchor="w", font=self.label_font, bg=bg).pack(side="left")
            var = tk.StringVar()
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
            self.entries[key] = (var, _type)

        # Buttons
        btn_frame = tk.Frame(self.input_frame, bg=bg)
        btn_frame.pack(fill="x", pady=(10, 10))

        ttk.Button(btn_frame, text="Create", style="Green.TButton", command=self.save_to_db).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear Inputs", style="Green.TButton", command=self.clear_inputs).pack(side="left", padx=5)

        tk.Label(self.input_frame, text="Records:", font=self.label_font, bg=bg).pack(anchor="w", pady=(10, 5))
        self.record_list = tk.Listbox(self.input_frame, height=12)
        self.record_list.pack(fill="both", expand=True)
        self.record_list.bind("<<ListboxSelect>>", self.on_select_record)

        action_frame = tk.Frame(self.input_frame, bg=bg)
        action_frame.pack(fill="x", pady=10)

        ttk.Button(action_frame, text="Refresh Records", style="Green.TButton", command=self.load_list).pack(side="left", padx=4)
        ttk.Button(action_frame, text="Edit Selected", style="Green.TButton", command=self.update_record).pack(side="left", padx=4)
        ttk.Button(action_frame, text="Delete Selected", style="Green.TButton", command=self.delete_record).pack(side="left", padx=4)

        self.msg_label = tk.Label(self.input_frame, text="", bg=bg)
        self.msg_label.pack(anchor="w", pady=(8, 0))

    def _build_display_panel(self, bg):
        tk.Label(self.display_frame, text="Stats", font=self.title_font, bg=bg).pack(anchor="w")
        self.timestamp_label = tk.Label(self.display_frame, text="(no data yet)", bg=bg)
        self.timestamp_label.pack(anchor="e", pady=(0, 20))

        grid = tk.Frame(self.display_frame, bg=bg)
        grid.pack(fill="both", expand=True)

        self.tiles = {}
        stats = [
            ("score", "Score"),
            ("most_consecutive_flips", "Most Consecutive Flips"),
            ("objects_destroyed", "Objects Destroyed"),
            ("air_time", "Air Time (s)"),
            ("tasks_completed", "Tasks Completed"),
            ("trophies_collected", "Trophies Collected"),
        ]

        # Stat tiles
        for r, (key, text) in enumerate(stats):
            frame = tk.Frame(grid, bg="#28a745", bd=0, relief="flat")
            frame.grid(row=r, column=0, sticky="ew", pady=3, ipadx=6, ipady=6)
            grid.columnconfigure(0, weight=1)

            tk.Label(frame, text=text, font=self.label_font, bg="#28a745", fg="white").pack(anchor="w")
            lbl = tk.Label(frame, text="—", font=self.value_font, bg="#28a745", fg="white")
            lbl.pack(anchor="w")
            self.tiles[key] = lbl

    # CRUD logic
    def clear_inputs(self):
        for var, _ in self.entries.values():
            var.set("")
        self.msg_label.config(text="Inputs cleared.")

    def load_list(self):
        self.record_list.delete(0, tk.END)
        for rec in self.session.query(Stats).order_by(Stats.timestamp.desc()).all():
            self.record_list.insert(tk.END, f"ID {rec.id} | {rec.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    def on_select_record(self, e=None):
        sel = self.record_list.curselection()
        if not sel:
            return
        rec_id = int(self.record_list.get(sel[0]).split()[1])
        record = self.session.get(Stats, rec_id)
        self.current_id = rec_id
        for key, (var, _) in self.entries.items():
            var.set(str(getattr(record, key)))

    def save_to_db(self):
        data = {k: cast(var.get() or 0) for k, (var, cast) in self.entries.items()}
        new = Stats(timestamp=datetime.utcnow(), **data)
        self.session.add(new)
        self.session.commit()
        self.msg_label.config(text="Created new record.")
        self.load_list()
        self.load_latest()

    def update_record(self):
        if not hasattr(self, "current_id"):
            self.msg_label.config(text="Select a record first.")
            return
        record = self.session.get(Stats, self.current_id)
        for key, (var, cast) in self.entries.items():
            setattr(record, key, cast(var.get() or 0))
        self.session.commit()
        self.msg_label.config(text=f"Updated record ID {self.current_id}.")
        self.load_list()
        self.load_latest()

    def delete_record(self):
        sel = self.record_list.curselection()
        if not sel:
            self.msg_label.config(text="Nothing selected.")
            return
        rec_id = int(self.record_list.get(sel[0]).split()[1])
        if messagebox.askyesno("Confirm Delete", f"Delete record ID {rec_id}?"):
            self.session.delete(self.session.get(Stats, rec_id))
            self.session.commit()
            self.msg_label.config(text=f"Deleted record ID {rec_id}.")
            self.load_list()
            self.load_latest()

    def load_latest(self):
        latest = self.session.query(Stats).order_by(Stats.timestamp.desc()).first()
        if not latest:
            for lbl in self.tiles.values():
                lbl.config(text="—")
            self.timestamp_label.config(text="(no data yet)")
            return

        d = latest.as_dict()
        self.tiles["score"].config(text=d["score"])
        self.tiles["most_consecutive_flips"].config(text=d["most_consecutive_flips"])
        self.tiles["objects_destroyed"].config(text=d["objects_destroyed"])
        self.tiles["air_time"].config(text=f"{d['air_time']:.1f}s")
        self.tiles["tasks_completed"].config(text=d["tasks_completed"])
        self.tiles["trophies_collected"].config(text=d["trophies_collected"])
        self.timestamp_label.config(text=latest.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))


if __name__ == "__main__":
    app = StatsDashboard()
    app.mainloop()
