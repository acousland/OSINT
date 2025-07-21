import mapStructure as ms
import scrape as sc
import streamlit as st
import os

st.title('🚀 High-Speed OSintel UI')

start_url = st.text_input('Start URL', ' ')
max_depth = st.number_input('Max Depth', min_value=1, max_value=1000, value=100)

# Speed mode selection
speed_mode = st.selectbox(
    'Speed Mode',
    ['Fast', 'Turbo', 'Respectful'],
    index=0,
    help="Fast: 50 concurrent, Turbo: 100 concurrent (aggressive), Respectful: 30 concurrent"
)

col1, col2 = st.columns(2)

with col1:
    if st.button('🗺️ Run High-Speed Map', type="primary"):
        with st.spinner('🚀 High-speed mapping in progress...'):
            if speed_mode == "Turbo":
                result = ms.turbo_map(start_url, max_depth)
            elif speed_mode == "Fast":
                result = ms.fast_map(start_url, max_depth)
            else:  # Respectful
                result = ms.map(start_url, max_depth, max_concurrent=30, request_delay=0.2)
            
            if result:
                st.success(f'✅ High-speed mapping completed! Found {result.get("total_urls", 0)} URLs in {result.get("total_time", 0):.2f}s')
                st.write(f"Speed: {result.get('urls_per_second', 0):.1f} URLs/second")
            else:
                st.success('✅ Mapping completed!')

with col2:
    speed_mode = st.selectbox(
        'Scraping Speed',
        ['Fast', 'Turbo', 'Normal'],
        index=0,
        help="Fast: 30 concurrent, Turbo: 50 concurrent (aggressive), Normal: 20 concurrent"
    )
    
    if st.button('📄 Run High-Speed Scraping', type="primary"):
        with st.spinner('🚀 High-speed content scraping in progress...'):
            if speed_mode == "Turbo":
                result = sc.turbo_scrape(start_url)
            elif speed_mode == "Fast":
                result = sc.fast_scrape(start_url)
            else:  # Normal
                result = sc.scrape(start_url)
            
            if result:
                st.success(f'✅ High-speed scraping completed! Processed {result.get("total_processed", 0)} files in {result.get("total_time", 0):.2f}s')
                st.write(f"Speed: {result.get('files_per_second', 0):.1f} files/second")
                st.write(f"HTML pages: `{result.get('html_dir', 'N/A')}`")
                st.write(f"PDF files: `{result.get('pdf_dir', 'N/A')}`")
            else:
                st.success('✅ Scraping completed!')

# Directory info
pdf_directory = os.path.abspath('downloads')
st.info(f"📁 Files are saved to: {pdf_directory}")