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
        self.minsize(900, 520)
        self.style = ttk.Style(self)

        # Use system theme
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=28, weight="bold")
        self.value_font = font.Font(family="Segoe UI", size=36, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=12)
        self.small_font = font.Font(family="Segoe UI", size=10)

        # Fullscreen state
        self.fullscreen = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        # Layout proportions
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        # Left input panel
        self.input_frame = ttk.Frame(self, padding=(18, 18, 12, 18))
        self.input_frame.grid(row=0, column=0, sticky="nsew")
        self.input_frame.rowconfigure(1, weight=1)
        self._build_input_panel()

        # Right display panel
        self.display_frame = ttk.Frame(self, padding=(12, 18, 18, 18))
        self.display_frame.grid(row=0, column=1, sticky="nsew")
        self.display_frame.rowconfigure(1, weight=1)
        self._build_display_panel()

        # Session
        self.session = Session()

        # Load latest automatically
        self.load_latest()

    def _build_input_panel(self):
        header = ttk.Label(self.input_frame, text="Enter Stats", font=self.title_font)
        header.pack(anchor="w", pady=(0, 10))

        # Input fields
        self.entries = {}
        fields = [
            ("score", "Score", int),
            ("most_consecutive_flips", "Most Consecutive Flips", int),
            ("objects_destroyed", "Objects Destroyed", int),
            ("air_time", "Air Time (s)", float),
            ("tasks_completed", "Tasks Completed", int),
            ("trophies_collected", "Trophies Collected", int),
        ]

        form_frame = ttk.Frame(self.input_frame)
        form_frame.pack(fill="both", expand=True, pady=(5, 15))

        for key, label_text, _type in fields:
            row = ttk.Frame(form_frame)
            row.pack(fill="x", pady=6)
            lbl = ttk.Label(row, text=label_text, width=20, anchor="w", font=self.label_font)
            lbl.pack(side="left", padx=(0, 5))
            ent_var = tk.StringVar()
            ent = ttk.Entry(row, textvariable=ent_var, font=self.label_font)
            ent.pack(side="left", fill="x", expand=True)
            self.entries[key] = (ent_var, _type)

        # Buttons (Save + Clear only)
        btn_frame = ttk.Frame(self.input_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        for text, cmd in [
            ("Save", self.save_to_db),
            ("Clear", self.clear_inputs),
        ]:
            btn = tk.Button(
                btn_frame,
                text=text,
                command=cmd,
                bg="#32CD32",  # Green
                fg="white",
                activebackground="#2EB82E",
                activeforeground="white",
                font=self.label_font,
                relief="flat",
                padx=10,
                pady=4,
            )
            btn.pack(side="left", padx=5, ipadx=6)

        self.msg_label = ttk.Label(self.input_frame, text="", font=self.small_font)
        self.msg_label.pack(anchor="w", pady=(8, 0))

    def _build_display_panel(self):
        # Header
        top = ttk.Frame(self.display_frame)
        top.pack(fill="x", pady=(0, 10))
        title = ttk.Label(top, text="Stats", font=self.title_font)
        title.pack(side="left")
        self.timestamp_label = ttk.Label(top, text="(no data yet)", font=self.small_font)
        self.timestamp_label.pack(side="right")

        # Stats grid
        grid = ttk.Frame(self.display_frame)
        grid.pack(fill="both", expand=True, pady=(10, 0))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        for i in range(3):
            grid.rowconfigure(i, weight=1)

        self.tiles = {}
        tile_info = [
            ("score", "Score"),
            ("most_consecutive_flips", "Most Consecutive Flips"),
            ("objects_destroyed", "Objects Destroyed"),
            ("air_time", "Air Time (s)"),
            ("tasks_completed", "Tasks Completed"),
            ("trophies_collected", "Trophies Collected"),
        ]

        r, c = 0, 0
        for key, title_text in tile_info:
            tile = tk.Frame(
                grid,
                bg="#32CD32",  # Green
                bd=0,
                relief="flat",
                highlightbackground="#228B22",
                highlightthickness=1,
            )
            tile.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
            lbl = tk.Label(tile, text=title_text, bg="#32CD32", fg="white", font=self.label_font)
            lbl.pack(anchor="w", pady=(4, 0), padx=8)
            val = tk.Label(tile, text="—", bg="#32CD32", fg="white", font=self.value_font)
            val.pack(anchor="w", padx=8, pady=(6, 4))
            self.tiles[key] = val

            c += 1
            if c > 1:
                c = 0
                r += 1

    # --- Actions ---
    def clear_inputs(self):
        for var, _ in self.entries.values():
            var.set("")
        self.msg_label.config(text="Inputs cleared.")

    def save_to_db(self):
        data = {}
        for key, (var, _type) in self.entries.items():
            txt = var.get().strip()
            if txt == "":
                val = 0.0 if _type == float else 0
            else:
                try:
                    val = _type(txt)
                except ValueError:
                    self.msg_label.config(text=f"Error: '{txt}' is not valid for {key}.")
                    return
            data[key] = val

        try:
            stat = Stats(
                score=int(data.get("score", 0)),
                most_consecutive_flips=int(data.get("most_consecutive_flips", 0)),
                objects_destroyed=int(data.get("objects_destroyed", 0)),
                air_time=float(data.get("air_time", 0.0)),
                tasks_completed=int(data.get("tasks_completed", 0)),
                trophies_collected=int(data.get("trophies_collected", 0)),
                timestamp=datetime.utcnow(),
            )
            self.session.add(stat)
            self.session.commit()
            self.msg_label.config(text=f"Saved at {stat.timestamp.isoformat()} UTC")
            self.load_latest()
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("DB Error", str(e))

    def load_latest(self):
        try:
            latest = self.session.query(Stats).order_by(Stats.timestamp.desc()).first()
            if not latest:
                self._display_empty()
                self.msg_label.config(text="No records found.")
                return
            self._update_tiles(latest.as_dict())
            self.timestamp_label.config(text=latest.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))
            self.msg_label.config(text=f"Loaded Record ID = {latest.id}")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def _display_empty(self):
        for lbl in self.tiles.values():
            lbl.config(text="—")
        self.timestamp_label.config(text="(no data yet)")

    def _update_tiles(self, data: dict):
        self.tiles["score"].config(text=f"{int(data.get('score', 0))}")
        self.tiles["most_consecutive_flips"].config(text=f"{int(data.get('most_consecutive_flips', 0))}")
        self.tiles["objects_destroyed"].config(text=f"{int(data.get('objects_destroyed', 0))}")
        self.tiles["air_time"].config(text=f"{float(data.get('air_time', 0.0)):.1f}s")
        self.tiles["tasks_completed"].config(text=f"{int(data.get('tasks_completed', 0))}")
        self.tiles["trophies_collected"].config(text=f"{int(data.get('trophies_collected', 0))}")

    # --- Fullscreen controls ---
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self, event=None):
        if self.fullscreen:
            self.fullscreen = False
            self.attributes("-fullscreen", False)


if __name__ == "__main__":
    app = StatsDashboard()
    app.mainloop()
