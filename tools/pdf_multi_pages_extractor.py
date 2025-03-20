import io
from collections.abc import Generator
from typing import Any, Optional

import PyPDF2
from dify_plugin.entities import I18nObject
from dify_plugin.entities.tool import ToolInvokeMessage, ToolParameter
from dify_plugin import Tool
from dify_plugin.file.file import File

class PDFMultiPagesExtractorTool(Tool):
    """
    A tool for extracting multiple pages from PDF files.
    This tool takes a PDF file (base64 encoded or Dify file object) and two page ranges as input.
    One range (fixed_start_page to fixed_end_page) is optional and specifies fixed pages to always include.
    The other range (start_page to end_page) specifies the dynamic pages to extract.
    When fixed pages are provided, for each page in the dynamic range a new PDF will be produced which
    contains the fixed pages followed by that dynamic page.
    If no fixed range is provided, the resulting PDF will simply contain the dynamic pages in sequence.
    
    Parameters:
        pdf_content (str or File): Base64 encoded PDF content or Dify File object.
        fixed_start_page (int): Starting page number of the fixed range (1-indexed).
        fixed_end_page (int): Ending page number of the fixed range (1-indexed). Must be greater than or equal to fixed_start_page.
        start_page (int): Starting page number for dynamic extraction (1-indexed).
        end_page (int): Ending page number for dynamic extraction (1-indexed). Must be greater than or equal to start_page.
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
            
            # Fetch dynamic extraction range parameters
            start_page_param = tool_parameters.get("start_page")
            if start_page_param is None:
                raise ValueError("Missing required parameter: start_page")
            end_page_param = tool_parameters.get("end_page")
            if end_page_param is None:
                raise ValueError("Missing required parameter: end_page")
            
            # Fetch fixed page range parameters (optional)
            fixed_start_page_param = tool_parameters.get("fixed_start_page")
            fixed_end_page_param = tool_parameters.get("fixed_end_page")
            use_fixed = False
            if fixed_start_page_param is not None or fixed_end_page_param is not None:
                if fixed_start_page_param is None or fixed_end_page_param is None:
                    raise ValueError("Both fixed_start_page and fixed_end_page must be provided together.")
                use_fixed = True
            
            try:
                # Convert and validate dynamic page range parameters
                user_start_page = int(start_page_param)
                user_end_page = int(end_page_param)
                if user_start_page < 1:
                    raise ValueError(f"Start page must be at least 1. You entered: {user_start_page}")
                if user_end_page < user_start_page:
                    raise ValueError(f"End page ({user_end_page}) must be greater than or equal to start page ({user_start_page}).")
                dynamic_start_index = user_start_page - 1
                dynamic_end_index = user_end_page - 1
                
                if use_fixed:
                    user_fixed_start_page = int(fixed_start_page_param)
                    user_fixed_end_page = int(fixed_end_page_param)
                    if user_fixed_start_page < 1:
                        raise ValueError(f"Fixed start page must be at least 1. You entered: {user_fixed_start_page}")
                    if user_fixed_end_page < user_fixed_start_page:
                        raise ValueError(f"Fixed end page ({user_fixed_end_page}) must be greater than or equal to fixed start page ({user_fixed_start_page}).")
                    fixed_start_index = user_fixed_start_page - 1
                    fixed_end_index = user_fixed_end_page - 1
            except (ValueError, TypeError):
                raise ValueError("Invalid page range format. 'start_page', 'end_page', 'fixed_start_page' and 'fixed_end_page' must be integers when provided.")
            
            # Get the PDF content directly from the File object
            pdf_bytes = pdf_content.blob
            original_filename = pdf_content.filename or "document"
            
            pdf_file = io.BytesIO(pdf_bytes)
            
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
            except Exception as e:
                raise ValueError(f"Invalid PDF file: {str(e)}")
            
            total_pages = len(pdf_reader.pages)
            # Validate dynamic range
            if dynamic_start_index < 0 or dynamic_end_index >= total_pages:
                raise ValueError(f"Invalid dynamic page range. The PDF has {total_pages} pages (pages 1 to {total_pages}). You requested pages {user_start_page} to {user_end_page}.")
            
            if use_fixed:
                # Validate fixed range boundaries
                if fixed_start_index < 0 or fixed_end_index >= total_pages:
                    raise ValueError(f"Invalid fixed page range. The PDF has {total_pages} pages (pages 1 to {total_pages}). You requested fixed pages {user_fixed_start_page} to {user_fixed_end_page}.")
                
                # Create a single PDF with fixed pages followed by dynamic pages
                output = PyPDF2.PdfWriter()
                
                # Add all pages from the fixed range
                for page in range(fixed_start_index, fixed_end_index + 1):
                    output.add_page(pdf_reader.pages[page])
                
                # Add all pages from the dynamic range
                for page in range(dynamic_start_index, dynamic_end_index + 1):
                    output.add_page(pdf_reader.pages[page])
                
                page_buffer = io.BytesIO()
                output.write(page_buffer)
                page_buffer.seek(0)
                
                if original_filename.lower().endswith('.pdf'):
                    base_filename = original_filename[:-4]
                else:
                    base_filename = original_filename
                output_filename = f"{base_filename}_fixed_{user_fixed_start_page}_to_{user_fixed_end_page}_plus_{user_start_page}_to_{user_end_page}.pdf"
                
                yield self.create_text_message(
                    f"Successfully extracted fixed pages {user_fixed_start_page} to {user_fixed_end_page} followed by pages {user_start_page} to {user_end_page}"
                )
                
                yield self.create_blob_message(
                    blob=page_buffer.getvalue(),
                    meta={
                        "mime_type": "application/pdf",
                        "file_name": output_filename
                    },
                )
            else:
                # Original behavior: extract a contiguous dynamic page range
                output = PyPDF2.PdfWriter()
                for page in range(dynamic_start_index, dynamic_end_index + 1):
                    output.add_page(pdf_reader.pages[page])
                
                page_buffer = io.BytesIO()
                output.write(page_buffer)
                page_buffer.seek(0)
                
                if original_filename.lower().endswith('.pdf'):
                    base_filename = original_filename[:-4]
                else:
                    base_filename = original_filename
                output_filename = f"{base_filename}_pages{user_start_page}_to_{user_end_page}.pdf"
                
                yield self.create_text_message(f"Successfully extracted pages {user_start_page} to {user_end_page} from PDF")
                
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
        Get the runtime parameters for the PDF multi-pages extractor tool.
        
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
                name="fixed_start_page",
                label=I18nObject(en_US="Fixed Start Page", zh_Hans="固定起始页码"),
                human_description=I18nObject(
                    en_US="Starting page number of the fixed range (starting from 1). Leave empty if not using fixed pages.",
                    zh_Hans="固定页范围的起始页码（从1开始），如果不使用固定页可留空。",
                ),
                type=ToolParameter.ToolParameterType.NUMBER,
                form=ToolParameter.ToolParameterForm.FORM,
                required=False,
                default=1,
            ),
            ToolParameter(
                name="fixed_end_page",
                label=I18nObject(en_US="Fixed End Page", zh_Hans="固定结束页码"),
                human_description=I18nObject(
                    en_US="Ending page number of the fixed range (must be greater than or equal to fixed start page). Leave empty if not using fixed pages.",
                    zh_Hans="固定页范围的结束页码（必须大于或等于固定起始页码），如果不使用固定页可留空。",
                ),
                type=ToolParameter.ToolParameterType.NUMBER,
                form=ToolParameter.ToolParameterForm.FORM,
                required=False,
                default=1,
            ),
            ToolParameter(
                name="start_page",
                label=I18nObject(en_US="Dynamic Start Page", zh_Hans="动态起始页码"),
                human_description=I18nObject(
                    en_US="Starting page number for dynamic extraction (starting from 1)",
                    zh_Hans="动态提取的起始页码（从1开始）",
                ),
                type=ToolParameter.ToolParameterType.NUMBER,
                form=ToolParameter.ToolParameterForm.FORM,
                required=True,
                default=1,
            ),
            ToolParameter(
                name="end_page",
                label=I18nObject(en_US="Dynamic End Page", zh_Hans="动态结束页码"),
                human_description=I18nObject(
                    en_US="Ending page number for dynamic extraction (must be greater than or equal to dynamic start page)",
                    zh_Hans="动态提取的结束页码（必须大于或等于动态起始页码）",
                ),
                type=ToolParameter.ToolParameterType.NUMBER,
                form=ToolParameter.ToolParameterForm.FORM,
                required=True,
                default=1,
            ),
        ]
        return parameters
