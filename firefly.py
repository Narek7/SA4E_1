# firefly.py

import threading
import time
import math
import random
from concurrent import futures
import grpc
import firefly_pb2
import firefly_pb2_grpc
import logging
import csv
import os

# Konfiguration des Loggings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [Firefly %(id)s] %(message)s',
    style='%'
)

class Firefly(firefly_pb2_grpc.FireflyServiceServicer):
    """
    Repräsentiert ein einzelnes Glühwürmchen, das über gRPC mit anderen Glühwürmchen kommuniziert.
    """

    def __init__(self, id, port, neighbors, K=10.0, dt=0.1, max_retries=5):
        self.id = id
        self.port = port
        self.neighbors = neighbors  # Liste von (neighbor_id, neighbor_address)
        self.phase = random.uniform(0, 2 * math.pi)
        self.omega = 1
        self.neighbor_phases = {}
        self.lock = threading.Lock()
        self.K = K
        self.dt = dt
        self.running = True
        self.max_retries = max_retries  # Maximale Anzahl von Wiederholungsversuchen

        # Initialisiere die CSV-Datei für das Logging der Phasen
        self.log_file = f'logs/firefly_{self.id}_phase.csv'
        if not os.path.exists('logs'):
            os.makedirs('logs')
        with open(self.log_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['timestamp', 'phase'])

    # gRPC-Methoden
    def SendPhase(self, request, context):
        """
        Wird von Nachbarn aufgerufen, um ihre Phase zu senden.
        """
        try:
            with self.lock:
                self.neighbor_phases[request.id] = request.phase
            print(f'Firefly {self.id}: Received phase from neighbor {request.id}: {request.phase}')
            return firefly_pb2.Empty()
        except Exception as e:
            print(f'Firefly {self.id}: Error in SendPhase: {e}')
            import traceback
            traceback.print_exc()
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return firefly_pb2.Empty()

    def RequestPhase(self, request, context):
        """
        Nachbarn können die Phase dieses Glühwürmchens anfordern.
        """
        return firefly_pb2.PhaseMessage(id=self.id, phase=self.phase)

    def start_server(self):
        """
        Startet den gRPC-Server, um Anfragen von Nachbarn zu empfangen.
        """
        try:
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            firefly_pb2_grpc.add_FireflyServiceServicer_to_server(self, server)
            server.add_insecure_port(f'0.0.0.0:{self.port}')  # Binde an alle IPv4-Adressen
            server.start()
            print(f'Firefly {self.id} server started on port {self.port}')
            return server
        except Exception as e:
            print(f'Firefly {self.id}: Error starting server: {e}')
            import traceback
            traceback.print_exc()
            self.running = False
            return None

    def send_phase_to_neighbors(self):
        for neighbor in self.neighbors:
            neighbor_id, neighbor_address = neighbor
            success = False
            attempts = 0
            while not success and attempts < self.max_retries:
                try:
                    with grpc.insecure_channel(neighbor_address) as channel:
                        stub = firefly_pb2_grpc.FireflyServiceStub(channel)
                        message = firefly_pb2.PhaseMessage(id=self.id, phase=self.phase)
                        stub.SendPhase(message, timeout=5)  # Füge einen Timeout hinzu
                    success = True
                    print(f'Firefly {self.id}: Sent phase to neighbor {neighbor_id}')
                except Exception as e:
                    attempts += 1
                    print(f'Firefly {self.id}: Error sending phase to neighbor {neighbor_id}: {e}')
                    if attempts == self.max_retries:
                        print(f'Firefly {self.id}: Failed to send phase to neighbor {neighbor_id} after {self.max_retries} attempts.')
                    time.sleep(0.2)

    def update_phase(self):
        """
        Aktualisiert die Phase basierend auf den Phasen der Nachbarn.
        """
        with self.lock:
            neighbor_phases = list(self.neighbor_phases.values())

        print(f'Firefly {self.id}: Number of neighbor phases received: {len(neighbor_phases)}')
        print(f'Firefly {self.id}: Neighbor phases: {neighbor_phases}')

        if neighbor_phases:
            sum_sin = sum(math.sin(phase - self.phase) for phase in neighbor_phases)
            dtheta = self.omega + (self.K / len(neighbor_phases)) * sum_sin
        else:
            dtheta = self.omega

        self.phase += dtheta * self.dt
        self.phase = self.phase % (2 * math.pi)
        print(f'Firefly {self.id}: Updated phase to {self.phase}')

    def run(self):
        server = self.start_server()

        # Starte die Phasenaktualisierung in einem separaten Thread
        logic_thread = threading.Thread(target=self.phase_update_loop)
        logic_thread.start()

        try:
            # Warte darauf, dass der Server beendet wird
            server.wait_for_termination()
        except KeyboardInterrupt:
            print(f'Firefly {self.id} shutting down.')
        finally:
            self.running = False
            logic_thread.join()
            server.stop(0)

    def phase_update_loop(self):
        # Verzögerung, um sicherzustellen, dass alle Server gestartet sind
        time.sleep(2)

        start_time = time.time()
        while self.running:
            self.send_phase_to_neighbors()
            self.update_phase()

            # Logge die Phase mit einem Zeitstempel
            elapsed_time = time.time() - start_time
            with open(self.log_file, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([elapsed_time, self.phase])

            time.sleep(self.dt)

    def stop(self):
        """
        Stoppt das Glühwürmchen.
        """
        self.running = False
