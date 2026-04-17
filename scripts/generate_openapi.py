"""Generate static openapi.json for the Borg site.

Run from the Borg project root:
    python -m scripts.generate_openapi

Outputs to site/public/openapi.json
"""

import json
import os
import sys

# Add src to path so we can import borg
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Prevent database connection on import
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/fake")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://localhost/fake")
os.environ.setdefault("ENTRA_TENANT_ID", "00000000-0000-0000-0000-000000000000")
os.environ.setdefault("ENTRA_CLIENT_ID", "00000000-0000-0000-0000-000000000000")
os.environ.setdefault("ENTRA_AUDIENCE", "api://00000000-0000-0000-0000-000000000000")
os.environ.setdefault("BORG_ENABLE_DOCS", "true")

from borg.main import app

schema = app.openapi()
output_path = os.path.join(os.path.dirname(__file__), "..", "site", "public", "openapi.json")

with open(output_path, "w") as f:
    json.dump(schema, f, indent=2)

print(f"Written to {output_path}")
print(f"  Paths: {len(schema.get('paths', {}))}")
print(f"  Schemas: {len(schema.get('components', {}).get('schemas', {}))}")
