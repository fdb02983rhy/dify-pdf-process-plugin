import io
import pymupdf
from collections import OrderedDict
from dify_plugin.entities import I18nObject
from dify_plugin.entities.tool import ToolInvokeMessage, ToolParameter, ToolParameterOption
from dify_plugin import Tool
from dify_plugin.file.file import File
from collections.abc import Generator
from typing import Any, Optional

class PDFPageCounterTool(Tool):
    """
    A tool for counting the total number of pages in a PDF file.
    This tool takes a PDF file (Dify file object) as input,
    and returns both text and JSON formats containing the total number of pages.
    """

    def _invoke(
        self,
        tool_parameters: dict[str, Any],
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        app_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Count the total number of pages in a PDF file and return both text and JSON formats.

        Args:
            tool_parameters (dict[str, Any]): Parameters for the tool
                - pdf_content (File): Dify File object containing the PDF
            user_id (Optional[str], optional): The ID of the user invoking the tool. Defaults to None.
            conversation_id (Optional[str], optional): The conversation ID. Defaults to None.
            app_id (Optional[str], optional): The app ID. Defaults to None.
            message_id (Optional[str], optional): The message ID. Defaults to None.

        Returns:
            Generator[ToolInvokeMessage, None, None]: Generator yielding text and JSON page counts

        Raises:
            ValueError: If the PDF content format is invalid or required parameters are missing
            Exception: For any other errors during PDF processing
        """
        doc = None
        try:
            pdf_content = tool_parameters.get("pdf_content")

            if not isinstance(pdf_content, File):
                raise ValueError("Invalid PDF content format. Expected File object.")

            try:
                # Wrap the bytes in BytesIO to provide seek capability
                pdf_file = io.BytesIO(pdf_content.blob)
                doc = pymupdf.open(stream=pdf_file, filetype="pdf")
            except Exception as e:
                raise ValueError(f"Invalid PDF file: {str(e)}")

            total_pages = doc.page_count

            # Output text format
            yield self.create_text_message(str(total_pages))

            # Output JSON format with page numbers
            page_dict = OrderedDict()
            # Dynamic padding based on total pages (e.g., 3 digits for 100-999 pages)
            padding = len(str(total_pages))
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
            
    def get_runtime_parameters(
        self,
        conversation_id: Optional[str] = None,
        app_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> list[ToolParameter]:
        """
        Get the runtime parameters for the PDF page counter tool.
        
        Returns:
            list[ToolParameter]: List of tool parameters
        """
        parameters = [
            ToolParameter(
                name="pdf_content",
                label=I18nObject(en_US="PDF Content", zh_Hans="PDF 内容"),
                human_description=I18nObject(
                    en_US="PDF file content (base64 encoded)",
                    zh_Hans="PDF 文件内容（base64 编码）",
                ),
                type=ToolParameter.ToolParameterType.FILE,
                form=ToolParameter.ToolParameterForm.FORM,
                required=True,
                file_accepts=["application/pdf"],
            ),
        ]
        return parameters 