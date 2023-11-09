Authors introduce **SignverOD**, a curated dataset of 2576 (2765 in current) scanned document images with 7103 (8022 in current) bounding box annotations, across 4 categories (*signature*, *initials*, *redaction*, *date*). SignverOD cover a diverse set of document types including memos, emails, bank cheques, lease agreements and letters, memos, invoices. Detecting the presence and location of hand written artifacts such as signatures, dates, initials can be critical for scanned (offline)document processing systems. This capability can support multiple downstream tasks such as signature verification, document tagging and categorization.

<i>Please note that this is the updated version of the dataset, with an increased number of original images.</i>

## Dataset Source

Images of documents in this dataset are sourced from 4 main locations and then annotated:

- [Tobacco800](https://www.kaggle.com/sprytte/tobacco-800-dataset)

Tobacco800 is a publicly accessible document image collection with realistic scope and complexity is important to the document image analysis and search community.

- [NIST.gov Special Database](https://www.nist.gov/srd/nist-special-database-2)

The NIST.gov structured Forms Database consists of 5,590 pages of binary, black-and-white images of synthesized documents. The documents in this database are 12 different tax forms from the IRS 1040 Package X for the year 1988.

- [Bank Cheques](https://www.kaggle.com/saifkhichi96/bank-checks-signatures-segmentation-dataset)

The bank cheques dataset is a collection of xx colored images of bank checks. They consist of scanned realistic checks as well as examplar signatures with signatures.

- [GSA.gov Lease Documents](https://www.gsa.gov/real-estate/real-estate-services/leasing/executed-lease-documents)

GSA provides electronic copies of GSA lease documents for general public viewing. The lease documents are sorted by region and contain, for the most part, GSA Lease Forms and Lease Amendments (LA) from selected GSA leases across the nation.