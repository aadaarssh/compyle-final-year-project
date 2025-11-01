"""OpenAI Vision API integration for text extraction"""
import base64
import time
import io
from pdf2image import convert_from_bytes
from openai import OpenAI
from config.config import get_config
from utils.errors import OCRException
from services import gridfs_service

config = get_config()

# Initialize OpenAI client
client = OpenAI(api_key=config.OPENAI_API_KEY)


def extract_text_from_pdf(pdf_file_id):
    """
    Extract text from PDF using OpenAI Vision API

    Args:
        pdf_file_id: GridFS file ID for PDF

    Returns:
        Extracted text as string

    Raises:
        OCRException: If OCR process fails
    """
    try:
        # Download PDF from GridFS
        grid_out = gridfs_service.download_file(pdf_file_id)
        pdf_bytes = grid_out.read()

        # Convert PDF to images (300 DPI for better OCR)
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
        except Exception as e:
            raise OCRException(f"Failed to convert PDF to images: {str(e)}")

        if not images:
            raise OCRException("PDF contains no pages")

        # Extract text from each page
        all_text = []

        for page_num, image in enumerate(images, start=1):
            try:
                # Convert image to base64
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_bytes = buffered.getvalue()
                base64_image = base64.b64encode(img_bytes).decode('utf-8')

                # Call OpenAI Vision API with retry logic
                page_text = extract_text_from_image(base64_image, page_num)
                all_text.append(page_text)

            except Exception as e:
                # Log error but continue with other pages
                print(f"Error processing page {page_num}: {str(e)}")
                all_text.append(f"[Error extracting text from page {page_num}]")

        # Combine all pages' text
        combined_text = "\n\n".join(all_text)

        return combined_text

    except OCRException:
        raise
    except Exception as e:
        raise OCRException(f"OCR process failed: {str(e)}")


def extract_text_from_image(base64_image, page_num=1):
    """
    Extract text from a single image using OpenAI Vision API

    Args:
        base64_image: Base64 encoded image string
        page_num: Page number for logging

    Returns:
        Extracted text from the image

    Raises:
        OCRException: If API call fails after retries
    """
    retries = 0
    max_retries = config.OPENAI_MAX_RETRIES
    retry_delay = config.OPENAI_RETRY_DELAY_SECONDS

    while retries < max_retries:
        try:
            response = client.chat.completions.create(
                model=config.OPENAI_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this answer sheet image. Preserve structure and formatting. Return only the extracted text without any additional commentary."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )

            # Extract text from response
            extracted_text = response.choices[0].message.content

            return extracted_text

        except Exception as e:
            retries += 1
            error_message = str(e)

            # Check if it's a rate limit error
            if 'rate_limit' in error_message.lower() or 'quota' in error_message.lower():
                if retries < max_retries:
                    wait_time = retry_delay * (2 ** (retries - 1))  # Exponential backoff
                    print(f"Rate limit hit, retrying in {wait_time} seconds... (Attempt {retries}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise OCRException("OpenAI API rate limit exceeded")

            # For other errors, retry with exponential backoff
            if retries < max_retries:
                wait_time = retry_delay * (2 ** (retries - 1))
                print(f"API error on page {page_num}, retrying in {wait_time} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise OCRException(f"OpenAI API call failed after {max_retries} retries: {error_message}")

    raise OCRException(f"Failed to extract text from page {page_num} after {max_retries} retries")
