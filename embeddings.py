import os
from PyPDF2 import PdfReader

def get_pdf_text(directory):
    text = " "
    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        # Check if the file is a PDF
        if filename.endswith('.pdf'):
            # Create a PdfReader object for the current PDF document
            pdf_reader = PdfReader(os.path.join(directory, filename))
            # Iterate through each page in the PDF document
            for page in pdf_reader.pages:
                # Try to extract text from the current page
                try:
                    page_text = page.extract_text()
                except TypeError:
                    # If a TypeError occurs, ignore it and continue with the next page
                    continue
                # Append the extracted text to the 'text' string
                text += page_text

    # Return the concatenated text from all PDF documents
    return text

print(get_pdf_text("downloads/www.rfs.nsw.gov.au/pdfs"))