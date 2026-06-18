"""Domain errors for the embedding pipeline."""


class DuplicateDocumentError(Exception):
    def __init__(self, document_id: int) -> None:
        self.document_id = document_id
        super().__init__(f"Document already ingested: {document_id}")
