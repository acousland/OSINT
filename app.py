import mapStructure as ms
import scrape as sc
import streamlit as st
import os

st.title('OSintel UI')

start_url = st.text_input('Start URL', ' ')
max_depth = st.number_input('Max Depth', min_value=1, max_value=1000, value=100)

if st.button('Run Map'):
    with st.spinner('Running Map...'):
        ms.map(start_url, max_depth)
    st.success('Map Completed')

if st.button('Run Scrape'):
    with st.spinner('Running Scrape...'):
        sc.scrape(start_url)
    st.success('Scrape Completed')

# Assuming PDFs are saved in a directory called 'pdfs'
pdf_directory = os.path.abspath('downloads')
st.write(f"PDFs are being saved to: {pdf_directory}")