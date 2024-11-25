# main.py

import argparse
from firefly import Firefly


def get_neighbors(id, N):
    """
    Berechnet die Nachbarn für ein Glühwürmchen in einem NxN-Torus-Gitter.

    Args:
        id (int): ID des Glühwürmchens (1 bis N*N).
        N (int): Größe des Gitters (NxN).

    Returns:
        List[Tuple[str, str]]: Liste der Nachbarn als (neighbor_id, address).
    """
    id = int(id)
    i = (id - 1) // N
    j = (id - 1) % N

    positions = [((i - 1) % N, j),  # Oben
                 ((i + 1) % N, j),  # Unten
                 (i, (j - 1) % N),  # Links
                 (i, (j + 1) % N)]  # Rechts

    neighbors = []
    for pos in positions:
        neighbor_i, neighbor_j = pos
        neighbor_id = neighbor_i * N + neighbor_j + 1  # IDs von 1 bis N*N

        # Vermeide, dass ein Firefly sich selbst als Nachbar hat
        if neighbor_id == id:
            continue

        neighbor_port = 5000 + neighbor_id
        neighbor_address = f'127.0.0.1:{neighbor_port}'  # Verwende 127.0.0.1 für IPv4
        neighbors.append((str(neighbor_id), neighbor_address))
    return neighbors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True, help='ID des Glühwürmchens')
    parser.add_argument('--N', required=True, type=int, help='Größe des Gitters (NxN)')
    parser.add_argument('--K', type=float, default=0.5, help='Kopplungskonstante')
    parser.add_argument('--dt', type=float, default=0.1, help='Zeitschritt')
    parser.add_argument('--max_retries', type=int, default=5, help='Maximale Anzahl von Wiederholungsversuchen')
    args = parser.parse_args()

    # Berechne die Nachbarn basierend auf der ID und Gittergröße N
    neighbors = get_neighbors(args.id, args.N)

    # Setze den Port für dieses Glühwürmchen
    port = 5000 + int(args.id)

    # Erstelle das Glühwürmchen mit den berechneten Nachbarn
    firefly = Firefly(
        id=args.id,
        port=port,
        neighbors=neighbors,
        K=args.K,
        dt=args.dt,
        max_retries=args.max_retries
    )
    firefly.run()

if __name__ == '__main__':
    main()
