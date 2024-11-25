#!/bin/bash

# Anzahl der Glühwürmchen in einer Reihe/Spalte
N=2  # Beispiel für ein 2x2 Gitter

# Erstelle das logs-Verzeichnis, falls es nicht existiert
mkdir -p logs

# Speichere die Prozess-IDs
pids=()

# Starte die Glühwürmchen
for (( id=1; id<=N*N; id++ ))
do
    # Starte jedes Glühwürmchen und leite die Ausgabe in eine eigene Logdatei
    python main.py --id $id --N $N --K 0.1 --dt 0.1 --max_retries 5 > logs/firefly_$id.log 2>&1 &
    pid=$!
    pids+=($pid)
    echo "Started Firefly $id with PID $pid"
    sleep 0.1
done

echo "All Fireflies started."

# Warte auf Benutzereingabe, um die Glühwürmchen zu stoppen
read -p "Press Enter to stop all Fireflies..."

# Beende alle Glühwürmchen
for pid in "${pids[@]}"
do
    kill $pid
    echo "Stopped Firefly with PID $pid"
done

echo "All Fireflies stopped."
