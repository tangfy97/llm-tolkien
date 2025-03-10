from typing import Generator, Tuple, Iterator
from pathlib import Path
import requests
import io
import logging
import json
from tqdm import tqdm

import pdfplumber
from pdfplumber.page import Page
from pdfplumber.pdf import PDF
from memory_profiler import profile

from llm import config


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def extract(file_path: str, start_page: int, end_page: int, 
            header_height: int, footer_height: int, 
            extraction_path: Path) -> None:
    LOGGER.info(f'Start extracting pages from {file_path}')
    with pdfplumber.open(file_path) as pdf:
        pages = list(extract_text_from_pdf(pdf, start_page, end_page, header_height, footer_height))
    LOGGER.info(f'Finished extracting texts from {file_path}')
    to_jsonl(pages=pages, path=extraction_path)



def to_jsonl(pages: Iterator[Tuple[int, str]], path: Path) -> None:
    LOGGER.info(f'Start writing to {path}')
    # We append text to the existing file with "a" mode (append)
    with open(path, 'a') as f:
        for page_number, text in tqdm(pages):    
            dict_page = {page_number: text}
            json.dump(dict_page, f)
            f.write('\n')
    LOGGER.info(f'Finished writing to {path}')


def extract_cropped_text_from_page(page: Page, header_height: int, footer_height: int) -> str:
    bbox = (0, header_height, page.width, footer_height) # Top-left corner, bottom-right corner
    text = page.crop(bbox=bbox).extract_text()
    return text


def extract_text_from_pdf(pdf: PDF, start_page: int, end_page: int, 
                          header_height: int, footer_height: int) -> Generator[Tuple[int, str], None, None]:
    for page in tqdm(pdf.pages):
        if page.page_number >= start_page and page.page_number <= end_page:
            yield page.page_number, extract_cropped_text_from_page(page=page, header_height=header_height, 
                                                                   footer_height=footer_height)
            # By default, pdfplumber keeps in cache to avoid to reprocess the same page, leading to memory issues.
            page.flush_cache()


if __name__ == "__main__":
    # The following block of code should be placed inside the if __name__ == "__main__": block
    books_dir = config.books_dir  # Replace with the actual path to your 'books' directory
    for file_path in books_dir.glob('*.pdf'):
        extract(file_path=str(file_path), 
                start_page=config.start_page, 
                end_page=config.end_page, 
                header_height=config.header_height, 
                footer_height=config.footer_height,
                extraction_path=config.extraction_path)

 #   extract(url=config.url, 
 #           start_page=config.start_page, 
 #           end_page=config.end_page, 
 #           header_height=config.header_height, 
 #           footer_height=config.footer_height,
 #           extraction_path=config.extraction_path)