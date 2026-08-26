"""
Storage Initialization Utility for PragyanAI DemandX.
Creates storage folder hierarchy and bootstraps pragyanai.db.
"""

import os
from config.database import init_db
from config.settings import settings


def setup_storage():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(base_dir, "documents")
    vectors_dir = os.path.join(base_dir, "vectors")

    # Create subdirectories if they do not exist
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(vectors_dir, exist_ok=True)

    # Ensure .gitkeep files exist
    for directory in [docs_dir, vectors_dir]:
        gitkeep_path = os.path.join(directory, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("# Preserves directory structure in Git\n")

    # Initialize pragyanai.db with all schemas
    init_db(settings.DATABASE_PATH)
    print(f"✅ Storage directories verified at: {base_dir}")
    print(f"✅ Database initialized at: {settings.DATABASE_PATH}")


if __name__ == "__main__":
    setup_storage()
