# Indexer

The indexer component is used to index the journal entries to a json file. This file holds meta-data infromation about all the entries in the system.

The main purpose of the indexer component is to provide a faster way to search for specific entries.

Instead of needing to access each entry file and parse its content, we can simply access the index file and search for the entries in this list. This reduces the I/O complexity of searching for specific records from O(n) to O(1 + k), where k is the number of records that match the search query.

Index entries are defined in the `IndexRecord` type. Each index entry comprises of the following fields:

- id: The unique identifier of the entry.
- filename: The filename of the entry.
- title: The title of the entry.
- date: The date of the entry.
- tags: The tags associated with the entry.
- mood: The mood associated with the entry.
- location: The location associated with the entry.
- word_count: The word count of the entry.
- checksum: The checksum of the entry.
- indexed_at: The time at which the entry was indexed.


