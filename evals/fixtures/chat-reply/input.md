Great question! To recap the issue for everyone: the migration failed on the `orders` table last night because the lock timeout was too short for a table that size, which means staging can't be deployed until the migration has run.

**Status:** Yes, the staging deploy is currently blocked.

**Next steps:**
- Jonas is rerunning migration 0042 with the lock timeout raised to 5 minutes
- It should be done by 3pm
- I'll post in this thread once it has finished

Hope this helps! Let me know if you have any other questions.
