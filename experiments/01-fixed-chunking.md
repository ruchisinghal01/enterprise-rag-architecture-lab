# Experiment 01 — Fixed-Size Chunking

## Objective

Evaluate how fixed-size chunking behaves when applied to a structured
AWS serverless architecture and troubleshooting runbook.

## Configuration

- Chunk size: 200 words
- Overlap: 40 words
- Input format: Markdown
- Implementation: Python
- AWS services used for experiment: None

This initial experiment uses word-based chunking rather than model
tokens so that the chunk boundaries can be inspected easily.

## Document Structure

The source document contains serverless architecture and operational
guidance covering areas such as:

- AWS Lambda
- Amazon EventBridge
- Amazon SQS and SNS
- Amazon S3 and DynamoDB
- IAM and AWS KMS
- API Gateway
- CloudWatch
- Troubleshooting procedures

Troubleshooting sections generally contain:

- Symptoms
- Possible Causes
- Diagnosis
- Resolution

## Observations

### Lambda Throttling

The Lambda Throttling troubleshooting procedure was split across
multiple chunks.

One chunk contained the symptoms, possible causes, and the beginning
of the diagnosis, while the remaining diagnostic information and
resolution continued into another chunk.

This demonstrated that fixed-size chunking does not understand the
logical boundaries of a troubleshooting procedure.

### S3 AccessDenied

The S3 AccessDenied section was also divided between chunks 8 and 9.

Chunk 8 contained:

- Previous SNS-related content
- S3 overview
- S3 AccessDenied symptoms
- Possible causes
- Part of the diagnosis

Chunk 9 contained:

- Overlapping S3 AccessDenied content
- Remaining diagnosis
- Resolution
- DynamoDB content
- IAM execution-role content

This demonstrated both information fragmentation and topic mixing.

## Effect of Overlap

The 40-word overlap preserved some context between consecutive chunks.

For example, part of the S3 AccessDenied diagnosis appeared in both
chunks 8 and 9.

Overlap therefore reduced information loss at the chunk boundary.

However, overlap did not preserve the complete logical troubleshooting
section as a single retrieval unit.

## Architectural Risk

If these chunks were later embedded and used for RAG retrieval, a
query could retrieve only part of a troubleshooting procedure.

A retrieved chunk could also contain unrelated topics, which may
introduce unnecessary context into the information supplied to the
LLM.

## Conclusion

Fixed-size chunking is simple and predictable, but the tested
200-word chunk size with 40-word overlap does not align well with the
logical structure of this runbook.

The experiment does not establish that fixed-size chunking is
universally unsuitable. Different chunk sizes or overlap settings
could produce different results.

A structure-aware approach should therefore be evaluated against the
same document.

## Next Experiment

Use the Markdown heading hierarchy to create chunks around meaningful
document sections and compare the resulting boundaries with the
fixed-size approach.