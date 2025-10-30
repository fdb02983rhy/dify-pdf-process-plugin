# TODO: Migrate from PyPDF2 to PyMuPDF

## Overview

Migrate all PDF processing tools from PyPDF2 to PyMuPDF for better performance, consistency, and feature access.

## Status

- **pdf_to_png.py**: ✅ Already using PyMuPDF (improved with proper cleanup)
- **pdf_page_counter.py**: ✅ Migrated and tested
- **pdf_single_page_extractor.py**: ✅ Migrated and tested
- **pdf_multi_pages_extractor.py**: ✅ Migrated and tested
- **pdf_splitter.py**: ✅ Migrated and tested

______________________________________________________________________

## Migration Checklist

### Phase 1: Preparation ✅

- [x] Backup current codebase (git commit)
- [x] Update `requirements.txt`: Replace `PyPDF2~=3.0.1` with `PyMuPDF~=1.26.5`
- [x] Install PyMuPDF: `pip install PyMuPDF~=1.26.5`
- [x] Uninstall PyPDF2: `pip uninstall PyPDF2`

### Phase 2: Code Migration

#### 2.0 pdf_to_png.py (Already using PyMuPDF - Improvements) ✅

- [x] Add `doc = None` initialization before try block for proper cleanup
- [x] Add `filetype="pdf"` parameter to `pymupdf.open()` for explicit type handling
- [x] Add `pix = None` after pixmap usage to release memory (Context7 best practice)
- [x] Remove unnecessary "Converting PDF..." initial message
- [x] Add cleanup in exception handlers (close `doc` if it exists)
- [x] Move `doc.close()` to proper location with conditional check

#### 2.1 pdf_page_counter.py (Simplest - Read-only) ✅

- [x] Line 2: Change `import PyPDF2` → `import pymupdf`
- [x] Line 52-57: Replace try-except block with:
  ```python
  try:
      pdf_file = io.BytesIO(pdf_content.blob)
      doc = pymupdf.open(stream=pdf_file, filetype="pdf")
  except Exception as e:
      raise ValueError(f"Invalid PDF file: {str(e)}")
  ```
- [x] Line 59: Change `len(pdf_reader.pages)` → `doc.page_count`
- [x] Add proper cleanup: Insert `doc.close()` after line 68 (after both yield statements)
  - **Best Practice**: Add in finally block or before each yield/return
  - **Alternative**: Use context manager (requires restructuring)
- [x] Update variable names: `pdf_reader` → `doc` throughout
- [x] Fix JSON padding: Change from `:02d` to dynamic padding based on total pages
  - Supports PDFs with 100+ pages (e.g., 3 digits for 100-999 pages)
- [x] Remove output_format option: Always output both text and JSON formats
  - Removed output_format parameter from Python code and YAML configuration
  - Tool now always yields both create_text_message() and create_json_message()
- [x] Test with various PDFs (1 page, multiple pages, large PDFs)
- [x] Verify error messages are still clear and helpful

**Complete Migration Pattern for pdf_page_counter.py:**

```python
# Lines 45-73 should look like:
doc = None
try:
    pdf_content = tool_parameters.get("pdf_content")

    if not isinstance(pdf_content, File):
        raise ValueError("Invalid PDF content format. Expected File object.")

    try:
        pdf_file = io.BytesIO(pdf_content.blob)
        doc = pymupdf.open(stream=pdf_file, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Invalid PDF file: {str(e)}")

    total_pages = doc.page_count

    # Output text format
    yield self.create_text_message(str(total_pages))

    # Output JSON format with page numbers
    page_dict = OrderedDict()
    padding = len(str(total_pages))  # Dynamic padding
    for i in range(total_pages):
        page_dict[f"page{i+1:0{padding}d}"] = i+1
    yield self.create_json_message(page_dict)

    # Clean up
    if doc:
        doc.close()

except ValueError as e:
    if doc:
        doc.close()
    raise
except Exception as e:
    if doc:
        doc.close()
    raise Exception(f"Error counting pages in PDF: {str(e)}")
```

#### 2.2 pdf_single_page_extractor.py (Single Page Extract) ✅

- [x] Line 5: Change `import PyPDF2` → `import pymupdf`
- [x] Line 70: Change `PyPDF2.PdfReader(pdf_file)` → `doc = pymupdf.open(stream=pdf_file, filetype="pdf")`
- [x] Line 74: Change `len(pdf_reader.pages)` → `doc.page_count`
- [x] Add resource cleanup: Initialize `doc = None` and `output = None` before try blocks
- [x] Lines 78-82: Replace PdfWriter logic with PyMuPDF's `insert_pdf()` method
  ```python
  output = pymupdf.Document()
  output.insert_pdf(doc, from_page=page_number, to_page=page_number)
  page_buffer = io.BytesIO()
  output.save(page_buffer)
  page_buffer.seek(0)  # CRITICAL: Reset buffer position for reading
  output.close()
  doc.close()
  ```
- [x] Update variable names: `pdf_reader` → `doc` throughout
- [x] Add cleanup in exception handlers (close both `doc` and `output` if they exist)
- [x] Test edge cases: first page, last page, middle page, invalid page numbers

#### 2.3 pdf_splitter.py (Split All Pages) ✅

- [x] Line 5: Change `import PyPDF2` → `import pymupdf`
- [x] Line 54: Change `PyPDF2.PdfReader(pdf_bytes_io)` → `doc = pymupdf.open(stream=pdf_bytes_io, filetype="pdf")`
- [x] Line 58: Change `len(pdf_reader.pages)` → `doc.page_count`
- [x] Add resource cleanup: Initialize `doc = None` before try block (line 44)
- [x] Lines 74-94: Replace page extraction loop with PyMuPDF's approach:
  ```python
  for page_idx in range(total_pages):
      # Create a new PDF with just this page
      output = pymupdf.Document()
      output.insert_pdf(doc, from_page=page_idx, to_page=page_idx)

      # Write to a buffer
      page_buffer = io.BytesIO()
      output.save(page_buffer)
      page_buffer.seek(0)  # CRITICAL: Reset buffer position for reading

      # Create filename for this page
      output_filename = f"{base_filename}_page{page_idx + 1}.pdf"

      # Add to our list of files
      page_files.append({
          "blob": page_buffer.getvalue(),
          "meta": {
              "mime_type": "application/pdf",
              "file_name": output_filename
          }
      })

      # Clean up output document for this page
      output.close()
  ```
- [x] Add `doc.close()` after loop completes (before line 97)
- [x] Update variable names: `pdf_reader` → `doc` throughout
- [x] Add cleanup in exception handlers (close `doc` if it exists)
- [x] Remove unnecessary "Splitting PDF into..." message, keep only success message
- [x] Test with PDFs of various sizes (1, 5, 10, 50+ pages)

#### 2.4 pdf_multi_pages_extractor.py (Complex - Multiple Pages with Ranges) ✅

- [x] Line 5: Change `import PyPDF2` → `import pymupdf`
- [x] Line 108: Change `PyPDF2.PdfReader(pdf_file)` → `doc = pymupdf.open(stream=pdf_file, filetype="pdf")`
- [x] Line 112: Change `len(pdf_reader.pages)` → `doc.page_count`
- [x] Add resource cleanup: Initialize `doc = None` and `output = None` before try block (line 87)
- [x] Lines 127-136: Replace page extraction logic:
  ```python
  # Create the output PDF
  output = pymupdf.Document()

  # Add fixed pages first, preserving order and duplicates
  if use_fixed:
      for index in fixed_page_indices:
          output.insert_pdf(doc, from_page=index, to_page=index)

  # Add dynamic pages, preserving order and duplicates
  for index in dynamic_page_indices:
      output.insert_pdf(doc, from_page=index, to_page=index)
  ```
- [x] Line 138: Remove check for `len(output.pages)` (PyMuPDF uses `output.page_count`)
- [x] Line 142: Change `output.write(page_buffer)` → `output.save(page_buffer)`
- [x] Add `page_buffer.seek(0)` after save (CRITICAL for buffer reading)
- [x] Add cleanup before yields: `output.close()` and `doc.close()` (after line 143)
- [x] Update variable names: `pdf_reader` → `doc` throughout
- [x] Add cleanup in exception handlers (close both `doc` and `output` if they exist)
- [x] Test complex scenarios:
  - [x] Single page: `"1"`
  - [x] Range: `"1-3"`
  - [x] Multiple ranges: `"1-3,5-7"`
  - [x] Duplicates: `"1,3,1-2"`
  - [x] Fixed + dynamic: `"1-2"` + `"3-5"`
  - [x] Order preservation
