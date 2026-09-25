# Experiment 02 — Structure-Aware Chunking

## Objective

Evaluate whether the existing Markdown document structure can be used
to preserve meaningful troubleshooting sections as complete chunks.

## Strategy

The runbook uses level-2 Markdown headings (`##`) to identify logical
architecture and troubleshooting sections.

The chunking implementation therefore uses each `##` heading as the
start of a new chunk.

Level-3 headings (`###`) such as Symptoms, Possible Causes, Diagnosis,
and Resolution remain within their parent chunk.

## Results

### Lambda Throttling

Word count: 180

The complete Lambda Throttling section remained in one chunk:

- Symptoms
- Possible Causes
- Diagnosis
- Resolution

In the fixed-size experiment, the same troubleshooting procedure was
split across multiple chunks.

### S3 AccessDenied

Word count: 190

The complete S3 AccessDenied troubleshooting procedure remained in one
chunk:

- Symptoms
- Possible Causes
- Diagnosis
- Resolution

The chunk did not contain unrelated SNS, DynamoDB, or IAM sections.

In the fixed-size experiment, this information was distributed across
chunks 8 and 9 and mixed with unrelated topics.

## Key Finding

Both troubleshooting sections contained fewer than 200 words:

- Lambda Throttling: 180 words
- S3 AccessDenied: 190 words

However, the 200-word fixed-size strategy still split these sections.

This occurred because fixed-size chunking determines boundaries based
on word position in the complete document rather than the logical
boundaries of individual sections.

Structure-aware chunking aligned the chunk boundaries with the
document's existing heading hierarchy.

## Advantages Observed

- Preserved complete troubleshooting procedures.
- Reduced unrelated topic mixing.
- Did not require arbitrary chunk boundaries.
- Used existing document structure without requiring an LLM.

## Limitations

The strategy depends on consistent and meaningful document headings.

Chunk sizes are not controlled directly and may vary significantly.

A very large section under a single `##` heading could produce an
excessively large chunk.

Documents with poor or inconsistent structure may not benefit from
this approach.

## Conclusion

For this structured AWS serverless runbook, structure-aware chunking
produced cleaner logical retrieval units than the tested fixed-size
configuration.

This does not establish that structure-aware chunking is universally
better. Its effectiveness depends on the quality and consistency of
the source document structure.

The next experiment will evaluate semantic chunking, where boundaries
are determined using changes in meaning rather than fixed size or
explicit document headings.