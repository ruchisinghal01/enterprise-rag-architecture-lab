# Enterprise AWS Serverless Architecture Runbook

## Purpose

This runbook provides architecture, operational, security, and troubleshooting
guidance for teams building serverless applications on AWS.

The platform primarily uses:

- Amazon API Gateway
- AWS Lambda
- Amazon EventBridge
- Amazon SQS
- Amazon SNS
- Amazon S3
- Amazon DynamoDB
- AWS KMS
- Amazon CloudWatch

The document is intended for cloud architects, platform engineers, DevOps
engineers, and application teams operating workloads across development,
testing, and production environments.

---

# 1. Serverless Compute

## 1.1 AWS Lambda Architecture

AWS Lambda is the primary compute service for serverless workloads.

Lambda functions are used for synchronous API processing, asynchronous event
processing, scheduled workloads, and integration between AWS services.

Functions should remain focused on a clearly defined business capability.
Application teams should avoid creating large functions containing unrelated
business logic.

Lambda execution roles should follow least-privilege principles and contain
only the permissions required by the function.

Operational logs and application metrics must be published to Amazon
CloudWatch.

---

## 1.2 Lambda Concurrency

AWS Lambda uses concurrency to represent the number of function executions
running simultaneously.

Applications with high event volumes should consider expected concurrency,
downstream system capacity, and account-level concurrency limits.

Reserved concurrency may be configured when a workload requires predictable
capacity or when the platform team needs to prevent one application from
consuming excessive account concurrency.

Concurrency configuration must also consider downstream dependencies. A
Lambda function capable of running hundreds of concurrent executions can
overload a database or external API that supports significantly fewer
connections.

---

## 1.3 Lambda Throttling

### Symptoms

Lambda invocations are rejected or delayed.

CloudWatch Lambda metrics show an increase in the Throttles metric.

SQS queue depth may increase when throttled Lambda functions consume messages
more slowly than messages arrive.

API Gateway clients may also experience increased latency or errors when
synchronous Lambda functions are throttled.

### Possible Causes

Lambda throttling may occur when:

- Account concurrency is exhausted.
- Reserved concurrency has been reached.
- A function has insufficient concurrency available.
- Another workload is consuming a large portion of shared concurrency.
- Downstream capacity restrictions require intentionally limited concurrency.

### Diagnosis

Review the Lambda ConcurrentExecutions and Throttles metrics in CloudWatch.

Check whether reserved concurrency is configured for the affected function.

Compare function concurrency with account-level concurrency usage.

For SQS-triggered functions, also review queue depth, message age, Lambda
errors, and processing duration.

### Resolution

Adjust reserved concurrency when appropriate.

Investigate other workloads consuming significant account concurrency.

Optimize function execution time when long-running executions are consuming
concurrency unnecessarily.

Before increasing concurrency, verify that downstream systems can handle the
additional request volume.

---

## 1.4 Lambda Timeout

### Symptoms

Lambda execution terminates before processing completes.

CloudWatch Logs may contain a message indicating that the task timed out after
the configured timeout period.

For event-driven applications, repeated timeouts may result in retries and an
increasing SQS backlog.

### Possible Causes

Common causes include:

- Slow downstream APIs.
- Database connection delays.
- Large file processing.
- Network connectivity problems.
- Incorrect timeout configuration.
- Application code waiting indefinitely for an external dependency.

### Diagnosis

Review Lambda duration metrics and CloudWatch Logs.

Determine which operation is consuming the majority of the execution time.

Check downstream API latency and network connectivity.

For SQS workloads, review ApproximateAgeOfOldestMessage to determine whether
processing delays are creating a backlog.

### Resolution

Resolve the slow downstream dependency where possible.

Configure appropriate client-side connection and request timeouts.

Increase the Lambda timeout only when the workload legitimately requires
additional processing time.

Increasing the timeout should not be used to hide an unresolved dependency or
application performance problem.

---

# 2. Event-Driven Architecture

## 2.1 Amazon EventBridge

Amazon EventBridge is used for event routing between loosely coupled
applications.

Producers publish business or system events without requiring knowledge of
individual consumers.

EventBridge rules evaluate event patterns and route matching events to
configured targets.

Applications should use clearly defined event schemas and avoid unnecessary
dependencies between event producers and consumers.

---

## 2.2 EventBridge Delivery Failure

### Symptoms

An event is successfully published but the expected target does not process
the event.

The target Lambda function may show no corresponding invocation.

### Possible Causes

Possible causes include:

- The EventBridge rule pattern does not match the event.
- The rule is disabled.
- The target configuration is incorrect.
- EventBridge does not have permission to invoke the target.
- Target processing repeatedly fails.

### Diagnosis

Verify that the event matches the configured EventBridge event pattern.

Check whether the rule is enabled.

Review EventBridge monitoring metrics and target configuration.

Verify permissions between EventBridge and the target service.

If a dead-letter queue is configured for the target, inspect failed events in
the DLQ.

### Resolution

Correct the event pattern or target configuration.

Restore the required target permissions.

Investigate events placed in the dead-letter queue before redriving them.

---

## 2.3 Amazon SQS

Amazon SQS is used to decouple asynchronous producers and consumers.

Queues protect downstream systems from temporary spikes in traffic and allow
messages to remain available when consumers are temporarily unavailable.

Consumers must be designed to handle duplicate message delivery where
applicable.

Visibility timeout should be configured according to expected processing
duration.

---

## 2.4 SQS Queue Backlog

### Symptoms

The number of visible messages in an SQS queue continuously increases.

ApproximateAgeOfOldestMessage increases over time.

Business processing becomes delayed.

### Possible Causes

Common causes include:

- Consumer Lambda errors.
- Lambda throttling.
- Insufficient Lambda concurrency.
- Processing duration increasing.
- Downstream dependency failures.
- Incoming message volume exceeding processing capacity.

### Diagnosis

Review the following CloudWatch metrics:

- ApproximateNumberOfMessagesVisible
- ApproximateAgeOfOldestMessage
- Lambda Invocations
- Lambda Errors
- Lambda Duration
- Lambda Throttles
- ConcurrentExecutions

Compare message arrival rate with processing throughput.

Review consumer Lambda logs for repeated application errors.

### Resolution

Resolve application errors before increasing processing capacity.

If the consumer is healthy but under-provisioned, evaluate Lambda concurrency.

Verify that downstream systems can support increased processing throughput
before increasing concurrency.

---

## 2.5 Retry and Dead-Letter Queue Strategy

Transient failures should normally be retried when another attempt may
reasonably succeed.

Permanent failures should not be retried indefinitely.

Dead-letter queues provide isolation for messages that cannot be successfully
processed after the configured retry policy.

DLQ monitoring should generate an operational alert when failed messages are
detected.

Messages should not automatically be redriven without understanding the
original failure because doing so may reproduce the same error.

---

## 2.6 Amazon SNS

Amazon SNS is used when one event or notification must be delivered to
multiple subscribers.

Typical subscribers may include SQS queues, Lambda functions, HTTPS endpoints,
or other supported destinations.

SNS is appropriate for fan-out scenarios where multiple independent consumers
need the same message.

SQS should generally be placed between SNS and workloads that require durable
asynchronous processing.

---

# 3. Storage and Data

## 3.1 Amazon S3

Amazon S3 is used for durable object storage.

Serverless applications may use S3 for source files, generated documents,
application artifacts, reports, or other object-based data.

S3 buckets should block public access unless a documented business requirement
explicitly requires public access.

Sensitive objects should use encryption and appropriate access controls.

---

## 3.2 S3 AccessDenied

### Symptoms

A Lambda function attempts to read or write an S3 object and receives an
AccessDenied response.

CloudWatch Logs may show an authorization failure for operations such as:

- s3:GetObject
- s3:PutObject
- s3:ListBucket

### Possible Causes

Access may be denied because:

- The Lambda execution role does not contain the required S3 permission.
- The S3 bucket policy denies the request.
- The resource ARN in the IAM policy is incorrect.
- The object is encrypted with a KMS key the caller cannot use.
- An organizational security policy restricts the requested operation.

### Diagnosis

Identify the exact failed API operation from CloudWatch Logs.

Determine which IAM principal made the request.

Review the Lambda execution role and relevant S3 bucket policy.

Verify that resource ARNs reference the correct bucket and object paths.

If the object uses KMS encryption, also review KMS permissions.

### Resolution

Grant only the required S3 permissions to the execution role.

Correct incorrect bucket or object ARNs.

Update the bucket policy when required.

If KMS encryption caused the failure, resolve the KMS authorization separately
rather than granting unnecessary S3 permissions.

---

## 3.3 Amazon DynamoDB

Amazon DynamoDB is used for serverless workloads requiring low-latency
key-value or document data access.

Partition key design should reflect application access patterns.

Applications should avoid designs that create highly concentrated access to a
small number of partition keys.

CloudWatch metrics should be monitored for throttling and operational issues.

---

# 4. Security and Encryption

## 4.1 IAM Execution Roles

Each Lambda function should use an IAM execution role appropriate for its
specific workload.

Execution roles should follow least privilege.

A function that only reads from one S3 bucket should not receive unrestricted
S3 access across the AWS account.

Permissions should be restricted by action and resource wherever practical.

---

## 4.2 Least Privilege

Least privilege means granting only the permissions required to perform the
intended operation.

Policies using broad permissions such as Action "*" or Resource "*" should
be avoided unless there is a justified and reviewed requirement.

Permissions should be reviewed as applications evolve because old permissions
may remain after functionality has been removed.

---

## 4.3 AWS KMS

AWS KMS is used to manage encryption keys protecting sensitive AWS resources
and application data.

Using an AWS service does not automatically mean the application has
permission to use the KMS key protecting the underlying resource.

Both service-level permissions and KMS authorization may need to be evaluated
when troubleshooting encrypted resources.

---

## 4.4 KMS AccessDenied

### Symptoms

A Lambda function has permission to access an AWS resource but still receives
an AccessDenied or decrypt-related error.

For example, the Lambda role may have s3:GetObject permission but may still
fail to read an encrypted S3 object.

### Possible Causes

Possible causes include:

- Missing kms:Decrypt permission.
- The KMS key policy does not allow the required principal.
- The application references the wrong KMS key.
- Cross-account key access has not been correctly configured.

### Diagnosis

First verify that the underlying AWS service permission is correct.

For an encrypted S3 object, confirm that s3:GetObject is already allowed.

Then identify the KMS key protecting the object.

Review the Lambda execution role and KMS key policy.

Check CloudWatch Logs or CloudTrail information for the denied KMS operation
when available.

### Resolution

Grant the required KMS operation to the appropriate principal.

Update the key policy when necessary.

Do not solve a KMS authorization problem by granting broad permissions to
unrelated AWS services.

---

# 5. API and Integration

## 5.1 Amazon API Gateway

Amazon API Gateway provides managed HTTP endpoints for serverless
applications.

API Gateway commonly integrates with AWS Lambda for request processing.

APIs should implement appropriate authentication, authorization, throttling,
logging, and monitoring controls.

---

## 5.2 API Gateway and Lambda Errors

### Symptoms

Clients receive HTTP 5xx responses from an API.

The API may become slow or intermittently unavailable.

### Possible Causes

Possible causes include:

- Lambda function errors.
- Lambda timeout.
- Lambda throttling.
- Incorrect API integration configuration.
- Invalid application responses.
- Downstream dependency failure.

### Diagnosis

Review API Gateway access and execution logs where configured.

Correlate the request with the corresponding Lambda invocation.

Review Lambda Errors, Duration, Throttles, and CloudWatch Logs.

Determine whether the error originated in API Gateway, Lambda, or a downstream
dependency.

### Resolution

Resolve the underlying Lambda or integration problem.

Do not increase API or Lambda timeouts without identifying the source of the
latency.

Configure appropriate alarms for elevated API error rates.

---

# 6. Observability

## 6.1 Amazon CloudWatch Logs

Serverless applications should publish structured operational logs to
CloudWatch.

Logs should contain sufficient information to correlate a request across
multiple components.

Useful fields may include:

- timestamp
- environment
- application
- requestId
- correlationId
- eventType
- errorCode
- severity

Sensitive information should not be written to application logs.

---

## 6.2 CloudWatch Metrics

Operational dashboards should monitor both technical and business-relevant
metrics.

Typical serverless technical metrics include:

- Lambda Errors
- Lambda Duration
- Lambda Throttles
- ConcurrentExecutions
- SQS queue depth
- SQS message age
- API Gateway latency
- API Gateway 4xx and 5xx responses

Metrics should be evaluated together rather than in isolation.

For example, increasing SQS queue depth combined with Lambda throttling
provides more diagnostic information than either metric alone.

---

## 6.3 CloudWatch Alarms

Alarms should identify conditions requiring operational attention.

Alert thresholds should be based on expected application behaviour and
business impact.

An alarm should provide enough context for an engineer to begin diagnosis.

Avoid creating excessive low-value alarms that generate alert fatigue.

---

# 7. Troubleshooting Approach

## 7.1 General Serverless Troubleshooting

When investigating a serverless incident, first identify the affected business
operation and application component.

Determine whether the failure is occurring at the entry point, compute layer,
event-processing layer, storage layer, or downstream dependency.

Use correlation identifiers where available to trace the request through the
system.

Review logs and metrics together.

Avoid changing capacity, permissions, or timeout values until the actual
failure mode has been identified.

---

## 7.2 Troubleshooting AccessDenied

AccessDenied does not automatically mean that the application's IAM execution
role is missing a permission.

Authorization may involve multiple layers including:

- IAM identity policies
- Resource policies
- S3 bucket policies
- KMS key policies
- Organizational controls
- Cross-account permissions

Identify the exact denied API operation and resource before changing
permissions.

For encrypted S3 objects, both S3 authorization and KMS authorization may need
to succeed.

Least privilege should still be maintained while resolving authorization
failures.

---

## 7.3 Troubleshooting Event Processing Delays

When event processing becomes delayed, determine whether events are arriving
faster than they are being processed.

For SQS-based workloads, review queue depth and message age.

Then review Lambda concurrency, throttling, errors, and duration.

If Lambda appears healthy, investigate downstream dependencies.

Increasing Lambda concurrency may improve throughput, but it may also increase
load on databases and external systems.

Capacity changes should therefore consider the complete processing chain.

---

# 8. Architecture Principles

## 8.1 Prefer Loose Coupling

Event-driven applications should minimize direct dependencies between
producers and consumers.

Services such as EventBridge, SNS, and SQS can be used to separate application
components where asynchronous processing is appropriate.

---

## 8.2 Design for Failure

Distributed systems should assume that individual components may temporarily
fail.

Use retries for appropriate transient failures.

Use dead-letter queues to isolate repeatedly failing asynchronous messages.

Monitor failures and define operational recovery procedures.

---

## 8.3 Apply Least Privilege

AWS workloads should receive only the permissions required for their intended
operations.

Avoid solving authorization problems by granting broad administrator or
wildcard permissions.

---

## 8.4 Observe Before Scaling

Increasing concurrency, memory, timeout, or queue-processing capacity should
not be the first response to every performance problem.

Use CloudWatch metrics and logs to identify the actual bottleneck.

Scaling one component without considering downstream capacity can move the
failure elsewhere in the architecture.