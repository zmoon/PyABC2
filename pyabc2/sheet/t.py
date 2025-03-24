from pathlib import Path

from nodejs_wheel import node, npm

HERE = Path(__file__).parent

# Build the project
# TODO: skip if already built recently-ish
ret = npm(["install", HERE.as_posix()])

# Run the script
ret = node(["render.js"])
