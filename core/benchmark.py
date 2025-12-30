import time
from datetime import datetime
from db.connection import get_connection
from core.models import clear_all_examens

from core.generator import generate_edt as generate_edt_v1
from core.test import generate_edt as generate_edt_v2

RUNS = 1
SLEEP_TIME = 2

def run_benchmark(generate_edt_func, conn, version_name):
    durations = []
    for i in range(1, RUNS + 1):
        print(f"{version_name} - Run {i}...")
        clear_all_examens(conn)
        start = datetime.now()
        generate_edt_func(conn)
        end = datetime.now()
        duration = (end - start).total_seconds()
        durations.append(duration)
        print(f"Run {i} finished in {duration:.2f}s\n")
        time.sleep(SLEEP_TIME)
    avg_duration = sum(durations) / RUNS
    print(f"{version_name} average execution time over {RUNS} runs: {avg_duration:.2f}s\n")
    return avg_duration

def benchmark():
    conn = get_connection()

    print("Starting benchmark...\n")
    avg_v1 = run_benchmark(generate_edt_v1, conn, "Version 1")
    avg_v2 = run_benchmark(generate_edt_v2, conn, "Version 2")

    print("Benchmark comparison:")
    if avg_v1 < avg_v2:
        print(f"Version 1 is faster on average by {avg_v2 - avg_v1:.2f}s")
    elif avg_v2 < avg_v1:
        print(f"Version 2 is faster on average by {avg_v1 - avg_v2:.2f}s")
    else:
        print("Both versions have the same average execution time.")

if __name__ == "__main__":
    benchmark()
