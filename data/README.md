# Data

Data Extraction:
Data is extracted from the GitHub REST API and using the pystackt library, which encapsulates interactions through PyGitHub. The extraction process covers multiple heterogeneous entities, including issues, commits, events, users, and labels. The retrieved data is materialized in a DuckDB database and organized according to an Object-Centric Event Data (OCED) model. This representation captures both event and object perspectives, as well as their interrelations. The schema includes object tables (e.g., types, instances, attributes), event tables (e.g., event types and attributes), and relational mappings (e.g., event-to-object and object-to-object relationships).

Replication help:
- give a token from github 
- choose a repository
- extract the data

for furthur examples and tutorial look at this cool repo: pystackt