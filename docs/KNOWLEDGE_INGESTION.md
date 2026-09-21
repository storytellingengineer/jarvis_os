# Knowledge ingestion

`KnowledgeStore.ingest_file()` supports `.txt`, `.md`, `.pdf`, and `.docx` sources.

## Optional dependencies

The base installation supports TXT/Markdown files. Install format-specific dependencies only when needed:

```bash
pip install pypdf python-docx
```

## Example

```python
from app.core.knowledge import KnowledgeStore

store = KnowledgeStore()
metadata = store.ingest_file("docs/architecture.pdf")
print(metadata.document_id)
```

Ingestion validates the file type and extracted text before writing. A stable SHA-256 document ID is generated from normalized extracted content. Re-ingesting the same source replaces its previous content atomically within one SQLite transaction.
