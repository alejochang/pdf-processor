"""
PDF parsing implementations for different extraction methods.

This module provides three parser implementations:
1. PyPDF: Fast text extraction using PyPDF library + Gemini summary
2. Gemini: Full AI-powered extraction with structured output
3. Mistral: OCR-based extraction for scanned documents

Each parser returns a consistent structure: list of pages and a summary.
"""

import logging
import re
import base64
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time

# PDF Processing
from pypdf import PdfReader
from pdf2image import convert_from_path
from PIL import Image

# AI APIs
import google.generativeai as genai
from mistralai import Mistral

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ========== Base Parser Interface ==========

class PDFParser:
    """
    Base class for PDF parsers.

    All parsers should return the same structure for consistency.
    """

    def parse(self, pdf_path: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Parse PDF and extract content.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (pages, summary) where:
            - pages: List of dicts with 'page' number and 'content' text
            - summary: AI-generated summary of the document

        Raises:
            Exception: If parsing fails
        """
        raise NotImplementedError("Subclasses must implement parse method")


# ========== PyPDF Parser ==========

class PyPDFParser(PDFParser):
    """
    Fast text extraction using PyPDF library.

    This parser:
    1. Extracts text page-by-page using PyPDF
    2. Uses Gemini to generate a summary of the full document
    """

    def __init__(self):
        """Initialize PyPDF parser with Gemini for summaries."""
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")
            logger.info("PyPDF parser initialized with Gemini 2.0 for summaries")
        else:
            self.gemini_model = None
            logger.warning("PyPDF parser initialized without Gemini (no API key)")

    def parse(self, pdf_path: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Extract text using PyPDF and generate summary with Gemini.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (pages, summary)

        Raises:
            Exception: If PDF reading or summary generation fails
        """
        try:
            logger.info(f"Starting PyPDF extraction for {pdf_path}")
            start_time = time.time()

            # Extract text page by page
            reader = PdfReader(pdf_path)
            pages = []
            full_text = []

            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                pages.append({
                    "page": str(page_num),
                    "content": text.strip()
                })
                full_text.append(text)

            # Generate summary using Gemini
            summary = None
            if self.gemini_model:
                try:
                    combined_text = "\n\n".join(full_text)
                    prompt = f"""You are a professional document analyst.

Please provide a concise, professional summary of the following document.
Focus on the key points, main topics, and important details.
Keep the summary to 3-5 sentences.

Document content:
{combined_text[:50000]}  # Limit to avoid token limits
"""
                    response = self.gemini_model.generate_content(prompt)
                    summary = response.text.strip()
                    logger.info(f"Generated summary using Gemini")
                except Exception as e:
                    logger.error(f"Failed to generate summary with Gemini: {e}")
                    summary = "Summary generation failed."

            elapsed = time.time() - start_time
            logger.info(
                f"PyPDF extraction completed in {elapsed:.2f}s "
                f"({len(pages)} pages)"
            )

            return pages, summary

        except Exception as e:
            logger.error(f"PyPDF parsing failed for {pdf_path}: {e}")
            raise


# ========== Gemini Parser ==========

class GeminiParser(PDFParser):
    """
    AI-powered PDF extraction using Google Gemini.

    This parser:
    1. Uploads the entire PDF to Gemini
    2. Uses a structured prompt to extract content with page boundaries
    3. Parses the response to separate pages and summary
    """

    def __init__(self):
        """Initialize Gemini parser."""
        if not settings.google_api_key:
            raise ValueError("Google API key required for Gemini parser")

        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        logger.info("Gemini 2.0 parser initialized")

    def parse(self, pdf_path: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Extract text using Gemini AI with structured output.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (pages, summary)

        Raises:
            Exception: If Gemini API call fails
        """
        try:
            logger.info(f"Starting Gemini extraction for {pdf_path}")
            start_time = time.time()

            # Upload PDF to Gemini
            pdf_file = genai.upload_file(pdf_path)
            logger.debug(f"Uploaded PDF to Gemini: {pdf_file.uri}")

            # Structured prompt for page-by-page extraction
            prompt = """You are a PDF processing expert.

Your task:
1. Extract all text from this document.
2. Structure the output in markdown.
3. Maintain clear page boundaries by inserting '---Page X---' (e.g., '---Page 1---', '---Page 2---') before the content of each page.
4. After all page content, provide a concise, professional summary of the entire document under a '## Summary' heading.

Example format:
---Page 1---
Content of page 1...

---Page 2---
Content of page 2...

## Summary
Your concise summary here (3-5 sentences).

Begin extraction now:"""

            # Generate content
            response = self.model.generate_content([pdf_file, prompt])
            content = response.text

            # Parse response to extract pages and summary
            pages, summary = self._parse_gemini_response(content)

            elapsed = time.time() - start_time
            logger.info(
                f"Gemini extraction completed in {elapsed:.2f}s "
                f"({len(pages)} pages)"
            )

            return pages, summary

        except Exception as e:
            logger.error(f"Gemini parsing failed for {pdf_path}: {e}")
            raise

    def _parse_gemini_response(
        self,
        content: str
    ) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Parse Gemini's structured response into pages and summary.

        Args:
            content: Raw response from Gemini

        Returns:
            Tuple of (pages, summary)
        """
        pages = []
        summary = None

        # Extract summary first (everything after ## Summary)
        summary_match = re.search(r'## Summary\s*\n(.*)', content, re.DOTALL | re.IGNORECASE)
        if summary_match:
            summary = summary_match.group(1).strip()
            # Remove summary from content for page parsing
            content = content[:summary_match.start()]

        # Extract pages (split by ---Page X--- markers)
        page_pattern = r'---Page (\d+)---\s*\n(.*?)(?=---Page \d+---|$)'
        page_matches = re.finditer(page_pattern, content, re.DOTALL)

        for match in page_matches:
            page_num = match.group(1)
            page_content = match.group(2).strip()
            pages.append({
                "page": page_num,
                "content": page_content
            })

        # If no pages found with markers, treat entire content as single page
        if not pages:
            logger.warning("No page markers found in Gemini response, treating as single page")
            pages.append({
                "page": "1",
                "content": content.strip()
            })

        logger.debug(f"Parsed {len(pages)} pages and summary from Gemini response")
        return pages, summary


# ========== Mistral Parser (OCR) ==========

class MistralParser(PDFParser):
    """
    OCR-based extraction using Mistral AI.

    This parser is designed for scanned PDFs where text extraction
    isn't possible with standard methods. Mistral's vision capabilities
    are used to perform OCR on each page.
    """

    def __init__(self):
        """Initialize Mistral parser."""
        if not settings.mistral_api_key:
            raise ValueError("Mistral API key required for Mistral parser")

        self.client = Mistral(api_key=settings.mistral_api_key)
        self.model = "pixtral-12b-2409"  # Mistral's vision model
        logger.info("Mistral OCR parser initialized")

    def parse(self, pdf_path: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
        """
        Extract text using Mistral OCR.

        This implementation:
        1. Converts PDF pages to images
        2. Encodes images as base64
        3. Sends each image to Mistral's vision API for OCR
        4. Collects text from all pages
        5. Generates a summary using Mistral

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (pages, summary)

        Raises:
            Exception: If Mistral API call fails
        """
        try:
            logger.info(f"Starting Mistral OCR extraction for {pdf_path}")
            start_time = time.time()

            # Check file size to prevent memory issues
            file_size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
            if file_size_mb > 50:
                raise RuntimeError(
                    f"PDF file too large for OCR ({file_size_mb:.1f}MB). "
                    f"Maximum size for Mistral OCR is 50MB. "
                    f"Please use PyPDF or Gemini parser instead."
                )

            # Convert PDF pages to images
            logger.info(f"Converting PDF to images (file size: {file_size_mb:.1f}MB)...")
            try:
                # Use lower DPI and limit first_page/last_page to prevent crashes
                images = convert_from_path(
                    pdf_path,
                    dpi=150,  # Reduced from 200 to prevent memory issues
                    fmt='jpeg',
                    jpegopt={'quality': 85, 'progressive': True, 'optimize': True}
                )
                logger.info(f"Converted PDF to {len(images)} image(s)")

                # Limit number of pages to prevent excessive processing
                if len(images) > 50:
                    logger.warning(f"PDF has {len(images)} pages, limiting to first 50 for OCR")
                    images = images[:50]

            except Exception as conv_error:
                logger.error(f"PDF to image conversion failed: {conv_error}", exc_info=True)
                raise RuntimeError(f"Failed to convert PDF to images: {str(conv_error)}")

            # Process each page with OCR
            pages = []
            full_text = []

            for page_num, image in enumerate(images, start=1):
                logger.info(f"Processing page {page_num}/{len(images)} with OCR...")

                # Convert PIL Image to base64
                image_base64 = self._image_to_base64(image)

                # Extract text using Mistral vision API
                text = self._extract_text_from_image(image_base64, page_num)

                pages.append({
                    "page": str(page_num),
                    "content": text
                })
                full_text.append(text)

                logger.info(f"Page {page_num} OCR completed ({len(text)} characters)")

            # Generate summary using Mistral
            logger.info("Generating summary with Mistral...")
            summary = self._generate_summary(full_text)

            elapsed = time.time() - start_time
            logger.info(
                f"Mistral OCR extraction completed in {elapsed:.2f}s "
                f"({len(pages)} pages)"
            )

            return pages, summary

        except Exception as e:
            logger.error(f"Mistral OCR parsing failed for {pdf_path}: {e}")
            raise

    def _image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string.

        Args:
            image: PIL Image object

        Returns:
            Base64-encoded image string
        """
        # Convert to RGB if necessary (remove alpha channel)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background

        # Save to bytes buffer
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        # Encode as base64
        return base64.b64encode(buffer.read()).decode('utf-8')

    def _extract_text_from_image(self, image_base64: str, page_num: int) -> str:
        """
        Extract text from image using Mistral vision API.

        Args:
            image_base64: Base64-encoded image
            page_num: Page number for context

        Returns:
            Extracted text from the image
        """
        try:
            # Create message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract all text from this image.

Please provide:
1. All visible text exactly as it appears
2. Maintain formatting and structure
3. Include headings, paragraphs, lists, etc.
4. If the image contains tables, preserve their structure

Output only the extracted text, no additional commentary."""
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    ]
                }
            ]

            # Call Mistral vision API
            response = self.client.chat.complete(
                model=self.model,
                messages=messages
            )

            # Extract text from response
            text = response.choices[0].message.content.strip()
            return text

        except Exception as e:
            logger.error(f"Failed to extract text from page {page_num}: {e}")
            return f"[OCR failed for page {page_num}: {str(e)}]"

    def _generate_summary(self, full_text: List[str]) -> str:
        """
        Generate summary using Mistral text model.

        Args:
            full_text: List of text from all pages

        Returns:
            AI-generated summary
        """
        try:
            combined_text = "\n\n".join(full_text)

            # Limit text length to avoid token limits
            max_chars = 50000
            if len(combined_text) > max_chars:
                combined_text = combined_text[:max_chars] + "..."
                logger.info(f"Truncated text to {max_chars} characters for summary")

            # Create summary prompt
            messages = [
                {
                    "role": "user",
                    "content": f"""You are a professional document analyst.

Please provide a concise, professional summary of the following document.
Focus on the key points, main topics, and important details.
Keep the summary to 3-5 sentences.

Document content:
{combined_text}"""
                }
            ]

            # Call Mistral chat API for summary
            response = self.client.chat.complete(
                model="mistral-small-latest",  # Use text model for summary
                messages=messages
            )

            summary = response.choices[0].message.content.strip()
            logger.info("Generated summary using Mistral")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary with Mistral: {e}")
            return "Summary generation failed."


# ========== Parser Factory ==========

def get_parser(parser_type: str) -> PDFParser:
    """
    Factory function to get the appropriate parser instance.

    Args:
        parser_type: Parser type ('pypdf', 'gemini', or 'mistral')

    Returns:
        Parser instance

    Raises:
        ValueError: If parser type is invalid or API key is missing
    """
    parser_type = parser_type.lower()

    if parser_type == "pypdf":
        return PyPDFParser()
    elif parser_type == "gemini":
        return GeminiParser()
    elif parser_type == "mistral":
        return MistralParser()
    else:
        raise ValueError(
            f"Invalid parser type: {parser_type}. "
            f"Must be one of: pypdf, gemini, mistral"
        )


# ========== Utility Functions ==========

def validate_pdf(pdf_path: str) -> bool:
    """
    Validate that the file exists and is a PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        True if valid, False otherwise
    """
    path = Path(pdf_path)

    if not path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return False

    if not path.is_file():
        logger.error(f"Path is not a file: {pdf_path}")
        return False

    if path.suffix.lower() != '.pdf':
        logger.error(f"File is not a PDF: {pdf_path}")
        return False

    return True
