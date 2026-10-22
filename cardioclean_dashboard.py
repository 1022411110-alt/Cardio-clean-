import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# CardioClean DSP: dashboard for simulated ECG noise-removal results.
# Load ECG_Results.csv exported by the MATLAB script, or use Demo Mode.
# Educational simulation only; not for medical diagnosis.

BG = "#0b1220"
PANEL = "#121d30"
PANEL2 = "#17253b"
TEXT = "#eaf1ff"
MUTED = "#93a4bf"
CYAN = "#48d7e8"
BLUE = "#6c8cff"
ORANGE = "#ffb454"
GREEN = "#53dfa2"
RED = "#ff6b7a"


def make_demo_data():
    """Fallback demo if MATLAB CSV is not yet available."""
    fs = 250
    duration = 10
    t = np.arange(0, duration, 1 / fs)
    clean = np.zeros_like(t)
    for beat in np.arange(0.5, duration, 1.0):
        clean += 0.12 * np.exp(-((t - (beat - 0.20)) / 0.045) ** 2)
        clean -= 0.16 * np.exp(-((t - (beat - 0.045)) / 0.012) ** 2)
        clean += 1.00 * np.exp(-((t - beat) / 0.015) ** 2)
        clean -= 0.25 * np.exp(-((t - (beat + 0.040)) / 0.015) ** 2)
        clean += 0.30 * np.exp(-((t - (beat + 0.25)) / 0.070) ** 2)

    rng = np.random.default_rng(1)
    noisy = clean + 0.20 * np.sin(2 * np.pi * 50 * t) + 0.12 * rng.standard_normal(len(t))

    # Toolbox-free FIR low-pass filter, matching the MATLAB approach
    order = 80
    cutoff = 35
    n = np.arange(-order // 2, order // 2 + 1)
    h = np.zeros_like(n, dtype=float)
    h[n == 0] = 2 * cutoff / fs
    nz = n != 0
    h[nz] = np.sin(2 * np.pi * cutoff * n[nz] / fs) / (np.pi * n[nz])
    window = 0.54 - 0.46 * np.cos(2 * np.pi * np.arange(order + 1) / order)
    h *= window
    h /= np.sum(h)
    filtered = np.convolve(noisy, h, mode="same")
    return t, clean, noisy, filtered, fs, "Built-in demo data"


def snr_db(clean, observed):
    error = observed - clean
    return 10 * np.log10((np.sum(clean**2) + 1e-12) / (np.sum(error**2) + 1e-12))


class CardioCleanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CardioClean DSP | ECG Noise Reduction Studio")
        self.root.geometry("1200x820")
        self.root.minsize(950, 680)
        self.root.configure(bg=BG)

        self.data = None
        self.source_label = "No data loaded"
        self._build_ui()
        self.load_demo()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 12))

        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left", fill="x", expand=True)
        tk.Label(brand, text="♥  CARDIOCLEAN DSP", bg=BG, fg=CYAN,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(brand, text="ECG SIGNAL NOISE REDUCTION STUDIO",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 0))

        actions = tk.Frame(header, bg=BG)
        actions.pack(side="right")
        self._button(actions, "Load MATLAB CSV", self.load_csv, BLUE).pack(side="left", padx=5)
        self._button(actions, "Demo Mode", self.load_demo, PANEL2).pack(side="left", padx=5)
        self._button(actions, "Save Graph", self.save_graph, GREEN, dark_text=True).pack(side="left", padx=5)

        self.status = tk.Label(self.root, text="", bg=BG, fg=MUTED,
                               font=("Segoe UI", 9))
        self.status.pack(anchor="w", padx=27, pady=(0, 10))

        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill="x", padx=24, pady=(0, 14))
        self.metric_vars = {}
        for title, key, accent in [
            ("SNR BEFORE", "before", ORANGE),
            ("SNR AFTER", "after", GREEN),
            ("IMPROVEMENT", "improve", CYAN),
            ("SAMPLE RATE", "rate", BLUE),
        ]:
            card = tk.Frame(cards, bg=PANEL, highlightbackground="#263650", highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=5)
            tk.Label(card, text=title, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
            var = tk.StringVar(value="—")
            self.metric_vars[key] = var
            tk.Label(card, textvariable=var, bg=PANEL, fg=accent,
                     font=("Segoe UI", 19, "bold")).pack(anchor="w", padx=14, pady=(0, 12))

        plot_frame = tk.Frame(self.root, bg=PANEL, highlightbackground="#263650", highlightthickness=1)
        plot_frame.pack(fill="both", expand=True, padx=29, pady=(0, 14))

        self.fig = Figure(figsize=(10, 6.0), dpi=100, facecolor=PANEL)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.fig.subplots_adjust(left=0.08, right=0.97, top=0.94, bottom=0.10, hspace=0.38)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=27, pady=(0, 15))
        tk.Label(footer,
                 text="DSP pipeline: Simulated ECG  →  Noise addition  →  FIR low-pass filter  →  SNR analysis",
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(footer,
                 text="Educational simulation only • Not a medical diagnostic tool",
                 bg=BG, fg="#f0b7a7", font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(4, 0))

    def _button(self, parent, label, command, color, dark_text=False):
        return tk.Button(parent, text=label, command=command, bg=color,
                         fg=BG if dark_text else TEXT, activebackground=color,
                         activeforeground=BG if dark_text else TEXT,
                         relief="flat", bd=0, padx=12, pady=9,
                         font=("Segoe UI", 9, "bold"), cursor="hand2")

    def load_demo(self):
        self.data = make_demo_data()
        self.source_label = "Built-in demo data (Python fallback)"
        self.update_dashboard()

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Select ECG_Results.csv exported by MATLAB",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            arr = np.loadtxt(path, delimiter=",")
            if arr.ndim != 2 or arr.shape[1] < 4 or arr.shape[0] < 10:
                raise ValueError("CSV must contain at least four columns: time, clean ECG, noisy ECG, filtered ECG.")
            t, clean, noisy, filtered = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]
            dt = np.median(np.diff(t))
            if dt <= 0:
                raise ValueError("Time column must be increasing.")
            fs = int(round(1 / dt))
            self.data = (t, clean, noisy, filtered, fs, os.path.basename(path))
            self.source_label = os.path.basename(path)
            self.update_dashboard()
        except Exception as exc:
            messagebox.showerror("Could not load CSV", str(exc))

    def update_dashboard(self):
        t, clean, noisy, filtered, fs, source = self.data
        # Ignore edge samples to reduce convolution-boundary effects in the metric.
        margin = min(80, max(1, len(t) // 10))
        sl = slice(margin, len(t) - margin)
        before = snr_db(clean[sl], noisy[sl])
        after = snr_db(clean[sl], filtered[sl])

        self.metric_vars["before"].set(f"{before:.2f} dB")
        self.metric_vars["after"].set(f"{after:.2f} dB")
        self.metric_vars["improve"].set(f"{after-before:+.2f} dB")
        self.metric_vars["rate"].set(f"{fs} Hz")
        self.status.config(text=f"DATA SOURCE: {source}     |     DURATION: {t[-1]-t[0]:.2f} s     |     SAMPLES: {len(t):,}")

        for ax in (self.ax1, self.ax2):
            ax.clear()
            ax.set_facecolor(PANEL)
            ax.tick_params(colors=MUTED, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#33445e")
            ax.grid(True, color="#263650", alpha=0.8, linewidth=0.7)

        # Show the first three seconds so heartbeat shape is easy to see.
        mask = t <= min(3.0, t[-1])
        self.ax1.plot(t[mask], clean[mask], color=CYAN, lw=1.5, label="Clean reference")
        self.ax1.plot(t[mask], noisy[mask], color=ORANGE, lw=0.8, alpha=0.85, label="Noisy input")
        self.ax1.plot(t[mask], filtered[mask], color=GREEN, lw=1.2, label="Filtered output")
        self.ax1.set_title("TIME DOMAIN  |  ECG BEFORE AND AFTER FILTERING",
                           color=TEXT, loc="left", fontsize=10, fontweight="bold")
        self.ax1.set_xlabel("Time (seconds)", color=MUTED)
        self.ax1.set_ylabel("Amplitude", color=MUTED)
        self.ax1.legend(facecolor=PANEL2, edgecolor="#33445e", labelcolor=TEXT,
                        fontsize=8, loc="upper right")

        nfft = min(4096, max(256, 2 ** int(np.floor(np.log2(len(t))))))
        freq = np.fft.rfftfreq(nfft, d=1 / fs)
        for signal, color, label in [
            (noisy, ORANGE, "Noisy input"),
            (filtered, GREEN, "Filtered output"),
        ]:
            spec = np.abs(np.fft.rfft(signal, n=nfft))
            spec_db = 20 * np.log10(spec / (np.max(spec) + 1e-12) + 1e-6)
            self.ax2.plot(freq, spec_db, color=color, lw=1.2, label=label)
        self.ax2.set_xlim(0, fs / 2)
        self.ax2.set_ylim(-80, 5)
        self.ax2.set_title("FREQUENCY DOMAIN  |  SPECTRUM COMPARISON",
                           color=TEXT, loc="left", fontsize=10, fontweight="bold")
        self.ax2.set_xlabel("Frequency (Hz)", color=MUTED)
        self.ax2.set_ylabel("Relative magnitude (dB)", color=MUTED)
        self.ax2.legend(facecolor=PANEL2, edgecolor="#33445e", labelcolor=TEXT,
                        fontsize=8, loc="lower left")

        self.canvas.draw_idle()

    def save_graph(self):
        path = filedialog.asksaveasfilename(
            title="Save dashboard graph",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")]
        )
        if not path:
            return
        try:
            self.fig.savefig(path, dpi=180, facecolor=self.fig.get_facecolor(), bbox_inches="tight")
            messagebox.showinfo("Saved", f"Graph saved successfully:\n{path}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    app = CardioCleanApp(root)
    root.mainloop()
