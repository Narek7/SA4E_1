# Firefly_Simulation.py

import tkinter as tk
from tkinter import messagebox
import time
import random
import math
import threading
from Firefly_1 import Firefly  # Importiert die Firefly-Klasse

class FireflySimulation:
    """
    Verwaltet die Glühwürmchen-Simulation und deren GUI. Stellt die Parameterkontrolle,
    Statusanzeigen und die Steuerung (Start/Stop/Restart) der Simulation bereit.
    """

    def __init__(self, root):
        """
        Initialisiert die GUI und legt Standardwerte für die Simulation fest.
        """
        self.root = root
        self.root.title("Glühwürmchen-Simulation")
        self.default_K = 0.5
        self.default_dt = 0.1
        self.default_N = 10
        self.sync_tolerance = 0.01  # Toleranz für 100% Synchronisation , geht auch 0.02 für 2% Abweichung
        """
        Disclaimer:Der Synchronisationsgrad bleibt oft bei 99%, da minimale numerische Rundungsfehler 
        in den Phasenberechnungen auftreten. Diese Abweichungen verhindern oft dass exakt 100% erreicht wird. 
        In der Praxis bedeutet 99% nahezu vollständige Synchronisation.
        """
        self.create_widgets()
        self.fireflies = []
        self.threads = []
        self.running = False
        self.start_time = 0
        self.sync_time = None
        self.paused_time = 0  # Speichert die gestoppte Zeit

    def create_widgets(self):
        """
        Erstellt alle GUI-Elemente: Parameter-Slider, Buttons und Statusanzeigen.
        """
        param_frame = tk.Frame(self.root)
        param_frame.pack(pady=10)

        tk.Label(param_frame, text="K (Kopplungskonstante):").grid(row=0, column=0, sticky='e')
        self.K_slider = tk.Scale(param_frame, from_=0.0, to=10.0, resolution=0.1, orient=tk.HORIZONTAL)
        self.K_slider.set(self.default_K)
        self.K_slider.grid(row=0, column=1)

        tk.Label(param_frame, text="dt (Zeitschritt):").grid(row=1, column=0, sticky='e')
        self.dt_slider = tk.Scale(param_frame, from_=0.01, to=0.5, resolution=0.01, orient=tk.HORIZONTAL)
        self.dt_slider.set(self.default_dt)
        self.dt_slider.grid(row=1, column=1)

        tk.Label(param_frame, text="N (Gittergröße NxN):").grid(row=2, column=0, sticky='e')
        self.N_slider = tk.Scale(param_frame, from_=5, to=25, resolution=1, orient=tk.HORIZONTAL)
        self.N_slider.set(self.default_N)
        self.N_slider.grid(row=2, column=1)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="Start", command=self.start_simulation)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop", command=self.stop_simulation, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=5)

        self.restart_button = tk.Button(button_frame, text="Restart", command=self.restart_simulation, state='disabled')
        self.restart_button.grid(row=0, column=2, padx=5)

        self.quit_button = tk.Button(button_frame, text="Quit", command=self.on_closing)
        self.quit_button.grid(row=0, column=3, padx=5)

        self.canvas = tk.Canvas(self.root, width=500, height=500)
        self.canvas.pack()

        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=10)

        tk.Label(status_frame, text="Simulation Zeit:").grid(row=0, column=0)
        self.time_label = tk.Label(status_frame, text="0.00 s")
        self.time_label.grid(row=0, column=1)

        tk.Label(status_frame, text="Synchronisationsgrad:").grid(row=1, column=0)
        self.sync_label = tk.Label(status_frame, text="0%")
        self.sync_label.grid(row=1, column=1)

        self.sync_time_label = tk.Label(status_frame, text="")
        self.sync_time_label.grid(row=2, column=0, columnspan=2)

    def start_simulation(self):
        """
        Startet die Simulation oder setzt sie nach einer Pause fort. Initialisiert
        die Glühwürmchen, falls sie zum ersten Mal gestartet wird.
        """
        if not self.running:
            try:
                K = float(self.K_slider.get())
                dt = float(self.dt_slider.get())
                N = int(self.N_slider.get())
            except ValueError:
                messagebox.showerror("Ungültige Eingabe", "Bitte geben Sie gültige Zahlenwerte ein.")
                return

            self.params = {'K': K, 'dt': dt, 'N': N}
            self.initialize_fireflies()
            self.running = True

            if self.paused_time == 0:  # Neu starten
                self.start_time = time.time()
            else:  # Fortsetzen
                self.start_time = time.time() - self.paused_time

            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.restart_button.config(state='normal')
            threading.Thread(target=self.update_status).start()
        else:
            for thread in self.threads:
                thread.resume()
            self.stop_button.config(state='normal')
            self.start_button.config(text="Start", state='disabled')

    def update_status(self):
        """
        Aktualisiert kontinuierlich die Statusanzeigen (Simulation Zeit und Synchronisationsgrad).
        """
        while self.running:
            elapsed_time = (time.time() - self.start_time) + self.paused_time
            self.time_label.config(text=f"{elapsed_time:.2f} s")
            sync_degree = self.calculate_sync_degree()
            self.sync_label.config(text=f"{sync_degree:.0f}%")

            if sync_degree >= 100 - self.sync_tolerance and self.sync_time is None:
                self.sync_time = elapsed_time
                self.sync_time_label.config(
                    text=f"100% Synchronisation nach {self.sync_time:.2f} Sekunden erreicht!"
                )

            time.sleep(0.1)

    def calculate_sync_degree(self):
        """
        Berechnet den aktuellen Synchronisationsgrad basierend auf den Phasen der Glühwürmchen.
        """
        N = self.params['N']
        phases = [firefly.phase for row in self.fireflies for firefly in row]
        mean_phase = sum(phases) / len(phases)
        sync_degree = sum(math.cos(phase - mean_phase) for phase in phases) / len(phases)

        phase_diff = max(abs(phase - mean_phase) for phase in phases)
        if phase_diff < self.sync_tolerance:
            return 100
        return int(sync_degree * 100)

    def stop_simulation(self):
        """
        Pausiert die Simulation und stoppt die Berechnung der Glühwürmchen.
        """
        self.paused_time += time.time() - self.start_time
        for thread in self.threads:
            thread.pause()
        self.running = False
        self.stop_button.config(state='disabled')
        self.start_button.config(text="Continue", state='normal')

    def restart_simulation(self):
        """
        Startet die Simulation mit den aktuellen Parametern neu und setzt alle Zustände zurück.
        """
        self.stop_simulation()
        self.clear_fireflies()
        self.sync_time = None  # Nachricht zurücksetzen
        self.sync_time_label.config(text="")  # GUI zurücksetzen
        self.start_simulation()

    def initialize_fireflies(self):
        """
        Erstellt das Gitter aus Glühwürmchen und verknüpft sie mit der GUI.
        """
        N = self.params['N']
        self.fireflies = [[None for _ in range(N)] for _ in range(N)]
        self.threads = []
        self.canvas.delete("all")
        canvas_size = 500
        cell_size = canvas_size // N

        for i in range(N):
            for j in range(N):
                x0 = j * cell_size
                y0 = i * cell_size
                x1 = x0 + cell_size
                y1 = y0 + cell_size
                rect = self.canvas.create_rectangle(x0, y0, x1, y1, fill="black", outline="white")
                phase = random.uniform(0, 2 * math.pi)
                omega = 1
                firefly = Firefly(i, j, phase, omega, self.canvas, rect, self.fireflies, self.params)
                self.fireflies[i][j] = firefly
                self.threads.append(firefly)

        for firefly in self.threads:
            firefly.start()

    def clear_fireflies(self):
        """
        Beendet alle Threads und entfernt die Glühwürmchen aus dem Gitter.
        """
        for firefly in self.threads:
            firefly.stop()
        self.fireflies = []
        self.threads = []
        self.canvas.delete("all")
        self.running = False
        self.start_time = 0
        self.paused_time = 0

    def on_closing(self):
        """
        Beendet die Simulation und schließt das Fenster.
        """
        self.clear_fireflies()
        self.root.destroy()


def main():
    """
    Startet die Hauptanwendung.
    """
    root = tk.Tk()
    app = FireflySimulation(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
