# Firefly_1.py


import threading
import time
import math


class Firefly(threading.Thread):
    """
    Repräsentiert ein einzelnes Glühwürmchen im Simulation. Jedes Glühwürmchen hat eine Phase,
    eine natürliche Frequenz und kann mit seinen Nachbarn interagieren, um Synchronisation zu erreichen.

    Diese Klasse erbt von `threading.Thread`, um die Simulation in separaten Threads auszuführen.
    """

    def __init__(self, i, j, phase, omega, canvas, rect, fireflies, params):
        """
        Initialisiert ein Glühwürmchen mit seiner Position, Phase und Frequenz. Verknüpft es mit
        der GUI und den Nachbarn im Gitter.

        - `i, j`: Position des Glühwürmchens im Gitter.
        - `phase`: Aktuelle Phase des Glühwürmchens.
        - `omega`: Natürliche Frequenz des Glühwürmchens.
        - `canvas`: GUI-Canvas zur Darstellung des Glühwürmchens.
        - `rect`: Rechteck auf dem Canvas, das dieses Glühwürmchen darstellt.
        - `fireflies`: Referenz auf das Gitter aller Glühwürmchen.
        - `params`: Parameter wie Kopplungskonstante `K` und Zeitschritt `dt`.
        """
        threading.Thread.__init__(self)
        self.i = i
        self.j = j
        self.phase = phase
        self.omega = omega
        self.canvas = canvas
        self.rect = rect
        self.fireflies = fireflies
        self.params = params
        self.running = True
        self.paused = False

    def run(self):
        """
        Hauptschleife des Glühwürmchen-Threads. Aktualisiert die Phase des Glühwürmchens
        basierend auf dem Kuramoto-Modell und ändert die Darstellung im GUI.
        """
        while self.running:
            if not self.paused:
                K = self.params['K']
                dt = self.params['dt']
                sum_sin = 0
                neighbors = self.get_neighbors()
                for neighbor in neighbors:
                    delta_theta = neighbor.phase - self.phase
                    sum_sin += math.sin(delta_theta)
                dtheta = self.omega + (K / len(neighbors)) * sum_sin
                self.phase += dtheta * dt
                self.phase = self.phase % (2 * math.pi)
                color = self.phase_to_color()
                self.canvas.itemconfig(self.rect, fill=color)
                time.sleep(dt)
            else:
                time.sleep(0.1)

    def get_neighbors(self):
        """
        Gibt die direkten Nachbarn des Glühwürmchens im Gitter zurück (Torus-Logik).
        """
        N = self.params['N']
        neighbors = []
        positions = [((self.i - 1) % N, self.j),
                     ((self.i + 1) % N, self.j),
                     (self.i, (self.j - 1) % N),
                     (self.i, (self.j + 1) % N)]
        for pos in positions:
            neighbor = self.fireflies[pos[0]][pos[1]]
            neighbors.append(neighbor)
        return neighbors

    def phase_to_color(self):
        """
        Wandelt die Phase in eine Graustufe um. Glühwürmchen mit ähnlichen Phasen
        haben ähnliche Helligkeiten.
        """
        intensity = int((1 - (self.phase / (2 * math.pi))) * 255)
        hex_intensity = f'{intensity:02x}'
        return f'#{hex_intensity}{hex_intensity}{hex_intensity}'

    def stop(self):
        """Stoppt den Thread, indem die `running`-Variable auf `False` gesetzt wird."""
        self.running = False

    def pause(self):
        """Pausiert die Berechnungen des Glühwürmchens."""
        self.paused = True

    def resume(self):
        """Setzt die Berechnungen des Glühwürmchens fort."""
        self.paused = False
