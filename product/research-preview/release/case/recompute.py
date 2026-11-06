"""Recompute the historical FE comparison using the two public curve files."""
from bisect import bisect_left
from pathlib import Path
from math import isclose, sqrt
import csv

root = Path(__file__).resolve().parent
def curve(name):
    with (root / name).open(encoding="utf-8-sig", newline="") as f:
        return [(float(r["displacement_model_length"]), float(r["force_model_force"])) for r in csv.DictReader(f)]

def main():
    old, new = curve("Sanity.csv"), curve("run_014.csv")
    positions = [x for x, _ in old]
    delta = []
    for x, f in new:
        i = bisect_left(positions, x)
        if i < len(old) and old[i][0] == x:
            ref = old[i][1]
        else:
            if not 0 < i < len(old):
                raise ValueError("Historical curve does not cover candidate displacement")
            x0, f0 = old[i - 1]
            x1, f1 = old[i]
            ref = f0 + (f1 - f0) * (x - x0) / (x1 - x0)
        delta.append(f - ref)
    with (root / "difference.csv").open(encoding="utf-8", newline="") as f:
        recorded = list(csv.DictReader(f))
    if (len(recorded) != len(new) or any(
        float(row["displacement_model_length"]) != x or not isclose(float(row["difference_model_force"]), v, abs_tol=1e-9)
        for row, (x, _), v in zip(recorded, new, delta)
    )):
        raise ValueError("Pointwise difference check failed")
    peak = max(range(len(delta)), key=lambda j: abs(delta[j]))
    print(f"Sanity {len(old)}, run_014 {len(new)} samples")
    print(f"Endpoint delta {delta[-1]:.8f} ({100 * delta[-1] / old[-1][1]:.8f}%)")
    print(f"Equal-sample RMS {sqrt(sum(v*v for v in delta)/len(delta)):.8f}")
    print(f"Max abs delta {abs(delta[peak]):.8f} at {new[peak][0]:.12g} model length")
    print("Units: model force, model length")

if __name__ == "__main__":
    main()
