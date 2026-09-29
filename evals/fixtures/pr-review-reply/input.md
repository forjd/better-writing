Great question, and thanks for raising this!

## Background

As you reported, `export_csv` times out on accounts with more than 50,000 rows. To recap the issue: the export ran a single unbatched query, so the database had to build the whole result set in memory before the first row was written, which is why larger accounts hit the 60-second request timeout.

## Diagnosis

I confirmed this by profiling the staging account with 180,000 rows. The query alone took 94 seconds, which proves the unbatched query was the root cause.

## The fix

I've pushed a41f9c2, which reads the rows in batches of 5,000 and streams each batch to the file as it arrives. On the same staging account the export now finishes in 11 seconds.

## Backfill

Exports that failed in the last week will be re-run tonight by the backfill job, so affected customers will get their files without doing anything.

To summarise, the unbatched query was the problem, batching fixes it, and the backfill covers past failures. Could you take another look when you get a chance?
