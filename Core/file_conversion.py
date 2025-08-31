# ============================================================================
# file_conversion.py - File Conversion Utility for LegalTTSV2
#
# This module provides functions for normalizing file paths and converting DOCX
# files to PDF using Microsoft Word automation. It is used by the main workflow
# and Gemini handler to ensure files are in the correct format for processing and upload.
# ============================================================================

import os
import urllib.parse
import win32com.client

def normalize_path(path):
    # Normalizes a file path by removing URL encoding, normalizing slashes, and returning the absolute path.
    # urllib.parse is used to decode URL-encoded paths.
    return os.path.abspath(os.path.normpath(urllib.parse.unquote(path)))


def convert_docx_to_pdf(docx_path, pdf_path=None):
    # Converts a DOCX file to PDF using Microsoft Word automation (win32com.client).
    # Returns the path to the generated PDF for further processing or upload.
    docx_path_clean = normalize_path(docx_path)
    if not os.path.exists(docx_path_clean):
        raise FileNotFoundError(f"DOCX file not found: {docx_path_clean}")
    if pdf_path is None:
        pdf_path = docx_path_clean.replace('.docx', '_for_gemini.pdf')
    # win32com.client is used to automate Word for DOCX to PDF conversion
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(docx_path_clean)
        doc.SaveAs(pdf_path, FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
    finally:
        word.Quit()
    return pdf_path

def convert_rtf_to_docx(rtf_path):
    #Converts an RTF file to DOCX using pypandoc. Returns the path to the new DOCX file.
    try:
        import pypandoc
    except ImportError:
        raise ImportError("pypandoc is required for RTF to DOCX conversion. Install with 'pip install pypandoc'.")
    docx_path = os.path.splitext(rtf_path)[0] + ".docx"
    output = pypandoc.convert_file(rtf_path, 'docx', outputfile=docx_path)
    if not os.path.exists(docx_path):
        raise RuntimeError(f"Failed to convert {rtf_path} to DOCX.")
    return docx_path
