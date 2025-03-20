# Overview
PDF Process is a group of tools for working with PDF files, allowing you to perform PDF operations.

# Author
Created by [fdb02983rhy](https://github.com/fdb02983rhy)

# Repository
https://github.com/fdb02983rhy/dify-pdf-process-plugin

# Configure
## PDF Extractor
PDF Extractor tool extracts a specific page from a PDF file and saves it as a new PDF.

The tool requires two parameters:
- **PDF Content**: The input PDF file to be extracted
- **Page Number**: The page number to extract (1-indexed)
![](./_assets/pdf_extractor.png)

## PDF Page Counter
PDF Page Counter tool counts the total number of pages in a PDF file and returns the count as a number.

The tool requires one parameter:
- **PDF Content**: The input PDF file to be analyzed
![](./_assets/pdf_page_counter.png)

## PDF Splitter
PDF Splitter tool divides a PDF file into multiple individual PDF files, with each page becoming a separate file.

The tool requires one parameter:
- **PDF Content**: The input PDF file to be split
![](./_assets/pdf_splitter.png)