from pathlib import Path


def load_document(path: str) -> str:
    """Load the runbook from the local filesystem."""
    return Path(path).read_text(encoding="utf-8")


def chunk_by_words(
    text: str,
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[str]:
    """Split text into fixed-size overlapping word chunks."""

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    words = text.split()
    chunks = []

    step_size = chunk_size - overlap

    for start in range(0, len(words), step_size):
        end = start + chunk_size
        chunk_words = words[start:end]

        if not chunk_words:
            break

        chunks.append(" ".join(chunk_words))

    return chunks


if __name__ == "__main__":

    document = load_document(
        "data/aws-serverless-architecture-runbook.md"
    )

    chunks = chunk_by_words(
        document,
        chunk_size=200,
        overlap=40,
    )

    print(f"Total chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        print("\n" + "=" * 70)
        print(f"CHUNK {index}")
        print("=" * 70)
        print(chunk)