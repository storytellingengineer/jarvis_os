"""Import local text or Markdown files into JARVIS knowledge."""

import argparse
from pathlib import Path

from app.config import settings
from app.core.knowledge import KnowledgeStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a document into JARVIS local knowledge.")
    parser.add_argument("path", help="Path to a UTF-8 text or Markdown file")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.is_file():
        parser.error(f"File not found: {path}")
    KnowledgeStore(settings.knowledge_path).add_document(str(path), path.read_text(encoding="utf-8"))
    print(f"Imported: {path}")


if __name__ == "__main__":
    main()
