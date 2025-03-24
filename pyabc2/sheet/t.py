from pathlib import Path
from textwrap import indent

from nodejs_wheel import node, npm

HERE = Path(__file__).parent

# Build the project
# TODO: skip if already built recently-ish
rc = npm(["install", HERE.as_posix()])

abc = """\
K: G
M: 6/8
BAG AGE | GED GBd | edB dgb | age dBA |
"""

# Run the script
cp = node(
    [(HERE / "cli.cjs").as_posix(), "--staffwidth=500", "--scale=0.85"],
    return_completed_process=True,
    input=abc,
    capture_output=True,
    text=True,
)
if cp.returncode != 0:
    info = indent(cp.stderr, "| ", lambda _: True)
    raise RuntimeError(f"Failed to render sheet music:\n{info}")

svg = cp.stdout
print(svg[:500])

with open(HERE / "output.svg", "w") as f:
    f.write(cp.stdout)
