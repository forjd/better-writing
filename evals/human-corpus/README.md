# Human corpus

Human prose written long before ChatGPT, used by `python3 evals/run_evals.py --corpus evals/human-corpus` to show which checks fire on text no model wrote. A hit here means a check is broader than the tell it targets. The report is for reading, not a gate: a human writer can use a contrast scaffold, and the check still belongs on rewrites.

The idea comes from vale-ai-tells, which counts candidate phrases against pre-2022 human prose before promoting them to rules.

| File | Source | Written | Licence |
| --- | --- | --- | --- |
| `pep8-foolish-consistency.txt` | PEP 8, "A Foolish Consistency is the Hobgoblin of Little Minds", python/peps at commit `434a032b` (2021-09-01) | 2001 to 2021 | Public domain (stated in the PEP) |
| `strunk-omit-needless-words.txt` | William Strunk Jr., *The Elements of Style*, rule 13, Project Gutenberg #37134 | 1918 | Public domain |
| `twain-cooper-offences.txt` | Mark Twain, "Fenimore Cooper's Literary Offences", opening, Project Gutenberg #3172 | 1895 | Public domain |
| `jerome-three-men-ch1.txt` | Jerome K. Jerome, *Three Men in a Boat*, chapter 1 opening, Project Gutenberg #308 | 1889 | Public domain |

Excerpts are verbatim apart from carriage returns and one `[Picture: …]` illustration marker removed from the Jerome text. Keep new additions to text published before November 2022, with a stable source and a licence that allows redistribution.
