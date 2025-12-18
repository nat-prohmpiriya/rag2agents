"""Document processing service for text extraction and chunking."""

import csv
import io
import logging
from dataclasses import dataclass

import fitz  # PyMuPDF
from docx import Document as DocxDocument

from app.core.telemetry import traced

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""

    index: int
    char_start: int
    char_end: int
    page_number: int | None = None


@dataclass
class TextChunk:
    """A chunk of text with metadata."""

    content: str
    metadata: ChunkMetadata


class TextExtractor:
    """Extract text from various document formats."""

    @traced()
    async def extract(self, file_content: bytes, file_type: str) -> str:
        """
        Extract text from a document.

        Args:
            file_content: Raw file bytes
            file_type: File extension (pdf, docx, txt, md, csv)

        Returns:
            Extracted text content
        """
        file_type = file_type.lower().lstrip(".")

        extractors = {
            "pdf": self._extract_pdf,
            "docx": self._extract_docx,
            "txt": self._extract_text,
            "md": self._extract_text,
            "csv": self._extract_csv,
        }

        extractor = extractors.get(file_type)
        if not extractor:
            raise ValueError(f"Unsupported file type: {file_type}")

        return extractor(file_content)

    def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF using PyMuPDF."""
        text_parts = []
        with fitz.open(stream=content, filetype="pdf") as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n\n".join(text_parts)

    def _extract_docx(self, content: bytes) -> str:
        """Extract text from DOCX using python-docx."""
        doc = DocxDocument(io.BytesIO(content))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)

    def _extract_text(self, content: bytes) -> str:
        """Extract text from plain text files."""
        return content.decode("utf-8")

    def _extract_csv(self, content: bytes) -> str:
        """Extract text from CSV files."""
        text_content = content.decode("utf-8")
        reader = csv.reader(io.StringIO(text_content))
        rows = []
        for row in reader:
            rows.append(" | ".join(row))
        return "\n".join(rows)


class TextChunker:
    """Split text into overlapping chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 2000,  # ~512 tokens
        chunk_overlap: int = 200,  # ~50 tokens
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    @traced()
    async def chunk(self, text: str) -> list[TextChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to split

        Returns:
            List of TextChunk objects
        """
        chunks = self._recursive_split(text)
        return self._create_chunks_with_metadata(chunks, text)

    def _recursive_split(self, text: str) -> list[str]:
        """Recursively split text using separators."""
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # Try each separator
        for separator in self.separators:
            if separator and separator in text:
                return self._split_by_separator(text, separator)

        # If no separator works, split by character
        return self._split_by_size(text)

    def _split_by_separator(self, text: str, separator: str) -> list[str]:
        """Split text by separator and merge into appropriate chunks."""
        parts = text.split(separator)
        chunks = []
        current_chunk = ""

        for part in parts:
            part_with_sep = part + separator if separator else part

            if len(current_chunk) + len(part_with_sep) <= self.chunk_size:
                current_chunk += part_with_sep
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                if len(part_with_sep) > self.chunk_size:
                    # Recursively split large parts
                    sub_chunks = self._recursive_split(part)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap(current_chunk)
                    current_chunk = overlap_text + part_with_sep

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_size(self, text: str) -> list[str]:
        """Split text by size when no separator is found."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - self.chunk_overlap

        return chunks

    def _get_overlap(self, text: str) -> str:
        """Get the overlap portion from the end of text."""
        if len(text) <= self.chunk_overlap:
            return text
        return text[-self.chunk_overlap:]

    def _create_chunks_with_metadata(
        self, chunks: list[str], original_text: str
    ) -> list[TextChunk]:
        """Create TextChunk objects with metadata."""
        result = []
        current_pos = 0

        for index, chunk_content in enumerate(chunks):
            # Find chunk position in original text
            char_start = original_text.find(chunk_content, current_pos)
            if char_start == -1:
                char_start = current_pos

            char_end = char_start + len(chunk_content)

            metadata = ChunkMetadata(
                index=index,
                char_start=char_start,
                char_end=char_end,
            )

            result.append(TextChunk(content=chunk_content, metadata=metadata))
            current_pos = char_start + 1

        return result


class DocumentProcessor:
    """Orchestrate document processing: extract -> chunk."""

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize document processor.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks in characters
        """
        self.extractor = TextExtractor()
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    @traced()
    async def process(self, file_content: bytes, file_type: str) -> list[TextChunk]:
        """
        Process a document: extract text and split into chunks.

        Args:
            file_content: Raw file bytes
            file_type: File extension (pdf, docx, txt, md, csv)

        Returns:
            List of TextChunk objects
        """
        # Extract text
        text = await self.extractor.extract(file_content, file_type)

        # Chunk text
        chunks = await self.chunker.chunk(text)

        return chunks

    @traced()
    async def extract_only(self, file_content: bytes, file_type: str) -> str:
        """
        Extract text without chunking.

        Args:
            file_content: Raw file bytes
            file_type: File extension

        Returns:
            Extracted text
        """
        return await self.extractor.extract(file_content, file_type)
