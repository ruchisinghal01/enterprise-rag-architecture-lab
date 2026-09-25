from pathlib import Path


def load_document(path: str) -> str:
    """Load the runbook from the local filesystem."""
    return Path(path).read_text(encoding="utf-8")


def chunk_by_section(text: str) -> list[str]:
    """
    Split a Markdown document using level-2 headings (##)
    as logical section boundaries.

    Level-3 headings (###) remain inside their parent section.
    """

    lines = text.splitlines()

    chunks = []
    current_chunk = []

    for line in lines:

        if line.startswith("## "):

            if current_chunk:
                chunks.append("\n".join(current_chunk).strip())

            current_chunk = [line]

        else:
            current_chunk.append(line)

    if current_chunk:
        chunks.append("\n".join(current_chunk).strip())

    return [chunk for chunk in chunks if chunk]


if __name__ == "__main__":

    document = load_document(
        "data/aws-serverless-architecture-runbook.md"
    )

    chunks = chunk_by_section(document)

    print(f"Total chunks: {len(chunks)}")

for index, chunk in enumerate(chunks, start=1):

    if "Lambda Throttling" in chunk:

        word_count = len(chunk.split())

        print("\n" + "=" * 70)
        print(f"CHUNK {index}")
        print(f"Word count: {word_count}")
        print("=" * 70)
        print(chunk)