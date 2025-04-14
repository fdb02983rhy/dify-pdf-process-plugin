import io
from collections.abc import Generator
from typing import Any, Optional

import PyPDF2
from dify_plugin.entities import I18nObject
from dify_plugin.entities.tool import ToolInvokeMessage, ToolParameter
from dify_plugin import Tool
from dify_plugin.file.file import File

class PDFSpecificPagesExtractorTool(Tool):
    """
    A tool for extracting specific pages from PDF files.
    This tool takes a PDF file and a comma-separated list of page numbers as input,
    and returns a new PDF containing only the specified pages in the order they were specified.
    
    Parameters:
        pdf_content (File): PDF file to extract pages from
        page_numbers (str): Comma-separated list of page numbers (e.g., "1,3,5,2")
    """
    
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        app_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        try:
            # Get and validate PDF content
            pdf_content = tool_parameters.get("pdf_content")
            if not isinstance(pdf_content, File):
                raise ValueError("PDF content must be a File object")
            
            # Get and validate page numbers
            page_numbers_str = tool_parameters.get("page_numbers")
            if not page_numbers_str:
                raise ValueError("Missing required parameter: page_numbers")
            
            try:
                # Parse page numbers and remove duplicates while maintaining order
                page_numbers = []
                seen = set()
                for num in page_numbers_str.split(','):
                    num = num.strip()
                    if not num:
                        continue
                    page = int(num)
                    if page < 1:
                        raise ValueError(f"Page number must be at least 1. Found: {page}")
                    if page not in seen:
                        page_numbers.append(page)
                        seen.add(page)
                
                if not page_numbers:
                    raise ValueError("No valid page numbers provided")
                
            except ValueError as e:
                if str(e).startswith("Page number must"):
                    raise
                raise ValueError("Invalid page numbers format. Please provide comma-separated integers (e.g., '1,3,5,2')")
            
            # Get the PDF content from the File object
            pdf_bytes = pdf_content.blob
            original_filename = pdf_content.filename or "document"
            
            pdf_file = io.BytesIO(pdf_bytes)
            
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
            except Exception as e:
                raise ValueError(f"Invalid PDF file: {str(e)}")
            
            total_pages = len(pdf_reader.pages)
            
            # Validate all page numbers
            invalid_pages = [p for p in page_numbers if p > total_pages]
            if invalid_pages:
                raise ValueError(
                    f"Invalid page numbers: {invalid_pages}. "
                    f"The PDF has {total_pages} pages (pages 1 to {total_pages})."
                )
            
            # Create new PDF with specified pages
            output = PyPDF2.PdfWriter()
            for page_num in page_numbers:
                output.add_page(pdf_reader.pages[page_num - 1])
            
            # Write to buffer
            page_buffer = io.BytesIO()
            output.write(page_buffer)
            page_buffer.seek(0)
            
            # Generate output filename
            if original_filename.lower().endswith('.pdf'):
                base_filename = original_filename[:-4]
            else:
                base_filename = original_filename
            
            # Create a compact representation of page numbers for filename
            pages_str = '_'.join(str(p) for p in page_numbers)
            output_filename = f"{base_filename}_pages_{pages_str}.pdf"
            
            # Send success message
            yield self.create_text_message(
                f"Successfully extracted pages {', '.join(str(p) for p in page_numbers)} from PDF"
            )
            
            # Send the PDF file
            yield self.create_blob_message(
                blob=page_buffer.getvalue(),
                meta={
                    "mime_type": "application/pdf",
                    "file_name": output_filename
                },
            )
            
        except ValueError as e:
            raise
        except Exception as e:
            raise Exception(f"Error extracting pages from PDF: {str(e)}")
    
    def get_runtime_parameters(
        self,
        conversation_id: Optional[str] = None,
        app_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> list[ToolParameter]:
        """
        Get the runtime parameters for the PDF specific pages extractor tool.
        
        Returns:
            list[ToolParameter]: List of tool parameters.
        """
        parameters = [
            ToolParameter(
                name="pdf_content",
                label=I18nObject(en_US="PDF Content", zh_Hans="PDF 内容"),
                human_description=I18nObject(
                    en_US="PDF file content",
                    zh_Hans="PDF 文件内容",
                ),
                type=ToolParameter.ToolParameterType.FILE,
                form=ToolParameter.ToolParameterForm.FORM,
                required=True,
                file_accepts=["application/pdf"],
            ),
            ToolParameter(
                name="page_numbers",
                label=I18nObject(en_US="Page Numbers", zh_Hans="页码列表"),
                human_description=I18nObject(
                    en_US="Comma-separated list of page numbers to extract (e.g., '1,3,5,2')",
                    zh_Hans="要提取的页码列表，用逗号分隔（例如：'1,3,5,2'）",
                ),
                type=ToolParameter.ToolParameterType.STRING,
                form=ToolParameter.ToolParameterForm.FORM,
                required=True,
            ),
        ]
        return parameters