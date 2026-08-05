# Validate the example manifest (from repo root)
app-factory validate manifests/examples/dorfladen-hutthurm.yaml

# Plan against local Customer App checkout
app-factory plan manifests/examples/dorfladen-hutthurm.yaml `
  --customer-app "..\BusinessForge FlutterApp"

# Dry-run — writes build report without Flutter
app-factory build-android manifests/examples/dorfladen-hutthurm.yaml --dry-run

# Run unit tests
pytest -q
