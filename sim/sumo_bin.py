"""Locate the SUMO binary whether installed via pip (eclipse-sumo), SUMO_HOME or PATH."""
import os
import shutil
import sys


def find_sumo(gui=False):
    name = "sumo-gui" if gui else "sumo"
    try:
        import sumolib
        return sumolib.checkBinary(name)
    except Exception:
        pass
    path = shutil.which(name)
    if path:
        return path
    # pip eclipse-sumo: binaries sit next to the sumolib/sumo packages
    try:
        import sumolib  # noqa
        pkg_dir = os.path.dirname(os.path.dirname(sumolib.__file__))
        cand = os.path.join(pkg_dir, "sumo", "bin", name + (".exe" if os.name == "nt" else ""))
        if os.path.exists(cand):
            return cand
    except ImportError:
        pass
    raise RuntimeError(
        f"SUMO binary '{name}' not found. Run: pip install eclipse-sumo  "
        f"or set SUMO_HOME. Python: {sys.executable}"
    )
