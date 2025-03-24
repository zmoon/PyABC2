from pathlib import Path
from textwrap import indent

from nodejs_wheel import node, npm

HERE = Path(__file__).parent

# Build the project
# TODO: skip if already built recently-ish
rc = npm(["install", HERE.as_posix()])

# Run the script
cp = node(
    ["render.js"],
    return_completed_process=True,
    capture_output=True,
    text=True,
)
if cp.returncode != 0:
    info = indent(cp.stderr, "| ", lambda line: True)
    raise RuntimeError(f"Failed to render sheet music:\n{info}")
else:
    print(cp.stdout[:100])
