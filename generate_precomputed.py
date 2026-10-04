"""Rechnet die teure Studie vor (Build-Zeit, nicht in der App): `python generate_precomputed.py [Prozesse]` schreibt
`precomputed_sweep.json`.

  study  Zahl der Spuren × Auslastung × Zahl der angesehenen Schlangen: mittlere Wartezeit (Mittel und Standardfehler aus je 4
         Wiederholungen à 800 000 Lkw), Schwanzanteile s_1 … s_8, Anteil Lkw mit freier Spur"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pod_constants as C
from pod_evaluation import PRECOMPUTED_PATH, study_cell_run


def _task(args):
    n, rho, d, idx = args
    return study_cell_run(n, rho, d, C.STUDY_CUSTOMERS, seed=10_000 + 97 * idx, reps=C.STUDY_REPS)


def main(workers):
    t0 = time.time()
    jobs, idx = [], 0
    for n in C.STUDY_N:
        for rho in C.STUDY_RHO:
            for d in C.STUDY_D:
                jobs.append((n, rho, d, idx))
                idx += 1
    with ProcessPoolExecutor(max_workers=workers) as ex:
        study = list(ex.map(_task, jobs))
    out = {"study_customers": C.STUDY_CUSTOMERS, "study_reps": C.STUDY_REPS, "warmup_fraction": C.WARMUP_FRACTION, "study": study}
    Path(PRECOMPUTED_PATH).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"fertig in {time.time() - t0:.0f} s -> {PRECOMPUTED_PATH}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else min(6, os.cpu_count() or 1))
