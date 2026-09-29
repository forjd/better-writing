Pushed a41f9c2: the export now reads rows in batches of 5,000 and streams each batch to the file. On the 180,000-row staging account it finishes in 11 seconds; the query alone used to take 94.

Exports that failed in the last week will be re-run by the backfill job tonight, so affected customers get their files without doing anything.

Could you take another look when you get a chance?
