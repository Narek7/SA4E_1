import matplotlib.pyplot as plt
import csv
import glob


def plot_phases():
    plt.figure(figsize=(12, 8))
    for log_file in glob.glob('logs/firefly_*_phase.csv'):
        firefly_id = log_file.split('_')[1]
        times = []
        phases = []
        with open(log_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                times.append(float(row['timestamp']))
                phases.append(float(row['phase']))
        plt.plot(times, phases, label=f'Firefly {firefly_id}')

    plt.xlabel('Zeit (Sekunden)')
    plt.ylabel('Phase (Bogenmaß)')
    plt.title('Phasen-Synchronisation der Fireflies')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    plot_phases()
