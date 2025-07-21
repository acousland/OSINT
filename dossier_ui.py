import streamlit as st
import os
import json
from pathlib import Path
from dossier_generator import DossierGenerator, CompanyDossier
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="OSINT Dossier Generator",
    page_icon="📋",
    layout="wide"
)

st.title("📋 OSINT Dossier Generator")
st.markdown("Generate comprehensive company dossiers from scraped PDFs or custom PDF directories")

# API Configuration Check
def check_api_status():
    """Check and display API configuration status"""
    generator = DossierGenerator()
    api_status = generator.check_api_configuration()
    
    if not api_status["configured"]:
        st.error("🔑 API Configuration Required")
        with st.expander("⚙️ How to Configure Your API Key", expanded=True):
            st.markdown(f"**Status:** {api_status['status']}")
            st.markdown("**Steps to configure:**")
            for i, suggestion in enumerate(api_status["suggestions"], 1):
                st.markdown(f"{i}. {suggestion}")
            
            st.markdown("---")
            st.markdown("### 📝 Quick Setup Guide:")
            st.code("""
# 1. Create a .env file in your project directory
# 2. Add your API key:
OPENAI_API_KEY=sk-your-actual-api-key-here

# 3. Save the file and restart the application
            """)
            
            # Check if .env file exists
            env_file = Path(".env")
            if env_file.exists():
                st.success("✅ .env file found")
            else:
                st.warning("⚠️ .env file not found - you need to create one")
        
        return False
    else:
        st.success("✅ API Configuration Valid")
        return True

# Check API status at the top
api_configured = check_api_status()

# Sidebar configuration
st.sidebar.header("PDF Source Selection")

# Mode selection
processing_mode = st.sidebar.radio(
    "Choose PDF Source:",
    ["Scraped Companies", "Custom PDF Directory"],
    help="Select whether to use PDFs from scraped companies or browse for a custom directory"
)

# Initialize variables
selected_company = None
custom_pdf_dir = None
company_display_name = None

if processing_mode == "Scraped Companies":
    # Check for available companies (domains with PDFs)
    downloads_dir = Path("downloads")
    available_companies = []
    if downloads_dir.exists():
        for domain_dir in downloads_dir.iterdir():
            if domain_dir.is_dir():
                pdf_dir = domain_dir / "pdfs"
                if pdf_dir.exists() and list(pdf_dir.glob("*.pdf")):
                    available_companies.append(domain_dir.name)

    if not available_companies:
        st.sidebar.warning("No companies with PDFs found in downloads directory.")
        st.sidebar.info("Please run the scraper first or switch to 'Custom PDF Directory' mode.")
    else:
        # Company selection
        selected_company = st.sidebar.selectbox(
            "Select Company Domain",
            available_companies,
            help="Choose a company domain that has been scraped"
        )
        company_display_name = selected_company

else:  # Custom PDF Directory mode
    st.sidebar.markdown("### 📁 Browse for PDF Directory")
    
    # Text input for manual path entry
    manual_path = st.sidebar.text_input(
        "Enter PDF Directory Path:",
        placeholder="/path/to/your/pdfs",
        help="Enter the full path to a directory containing PDF files"
    )
    
    # File browser simulation using selectbox
    if manual_path and Path(manual_path).exists():
        custom_pdf_dir = manual_path
        pdf_count = len(list(Path(manual_path).glob("*.pdf")))
        st.sidebar.success(f"✅ Found {pdf_count} PDF files")
        
        # Company name input
        company_display_name = st.sidebar.text_input(
            "Company Name:",
            value=Path(manual_path).name,
            help="Enter a name for this company/organization"
        )
    elif manual_path:
        st.sidebar.error("❌ Directory not found or inaccessible")
    
    # Alternative: Common directories quick selection
    st.sidebar.markdown("#### Quick Selection")
    common_dirs = [
        str(Path.home() / "Desktop"),
        str(Path.home() / "Downloads"), 
        str(Path.home() / "Documents"),
        str(Path.cwd())
    ]
    
    quick_dir = st.sidebar.selectbox(
        "Or browse common locations:",
        ["Select a location..."] + common_dirs,
        help="Choose from common directory locations"
    )
    
    if quick_dir != "Select a location...":
        quick_path = Path(quick_dir)
        if quick_path.exists():
            # Show subdirectories that contain PDFs
            subdirs_with_pdfs = []
            try:
                for subdir in quick_path.iterdir():
                    if subdir.is_dir():
                        pdf_count = len(list(subdir.glob("*.pdf")))
                        if pdf_count > 0:
                            subdirs_with_pdfs.append(f"{subdir.name} ({pdf_count} PDFs)")
                
                if subdirs_with_pdfs:
                    selected_subdir = st.sidebar.selectbox(
                        f"Folders with PDFs in {quick_path.name}:",
                        ["Select a folder..."] + subdirs_with_pdfs
                    )
                    
                    if selected_subdir != "Select a folder...":
                        folder_name = selected_subdir.split(" (")[0]
                        custom_pdf_dir = str(quick_path / folder_name)
                        company_display_name = folder_name
                else:
                    # Check if current directory has PDFs
                    pdf_count = len(list(quick_path.glob("*.pdf")))
                    if pdf_count > 0:
                        if st.sidebar.button(f"Use {quick_path.name} ({pdf_count} PDFs)"):
                            custom_pdf_dir = str(quick_path)
                            company_display_name = quick_path.name
                    else:
                        st.sidebar.info(f"No PDFs found in {quick_path.name} or its subdirectories")
                        
            except PermissionError:
                st.sidebar.error("❌ Permission denied accessing this directory")

# Processing parameters (show only if we have a valid source)
if (processing_mode == "Scraped Companies" and selected_company) or (processing_mode == "Custom PDF Directory" and custom_pdf_dir):
    st.sidebar.subheader("Processing Parameters")
    chunk_size = st.sidebar.slider("Chunk Size", 500, 2000, 1000, 100)
    chunk_overlap = st.sidebar.slider("Chunk Overlap", 100, 500, 200, 50)
    max_clusters = st.sidebar.slider("Max Topic Clusters", 3, 15, 8, 1)
    
    # Advanced options
    with st.sidebar.expander("Advanced Options"):
        max_context_tokens = st.number_input("Max Context Tokens", 2000, 8000, 4000, 500)
        include_financial = st.checkbox("Include Financial Analysis", True)
        include_personnel = st.checkbox("Include Personnel Analysis", True)
        include_locations = st.checkbox("Include Location Analysis", True)
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if processing_mode == "Scraped Companies":
            st.subheader(f"Generate Dossier for: {selected_company}")
            # Show PDF count
            pdf_dir = downloads_dir / selected_company / "pdfs"
            pdf_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
            source_info = f"Found {pdf_count} PDF files from scraped data"
        else:
            st.subheader(f"Generate Dossier for: {company_display_name}")
            # Show PDF count from custom directory
            pdf_count = len(list(Path(custom_pdf_dir).glob("*.pdf"))) if custom_pdf_dir else 0
            source_info = f"Found {pdf_count} PDF files in custom directory"
        
        st.info(source_info)
        
        # Show source path
        if processing_mode == "Scraped Companies" and selected_company:
            st.code(f"Source: downloads/{selected_company}/pdfs/")
        elif custom_pdf_dir:
            st.code(f"Source: {custom_pdf_dir}")
        
        # Generate button
        if st.button("🚀 Generate Dossier", type="primary", use_container_width=True):
            if pdf_count == 0:
                st.error("No PDF files found in the selected source.")
            else:
                # Initialize progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Initialize generator
                    status_text.text("Initializing dossier generator...")
                    generator = DossierGenerator(
                        downloads_dir="downloads",
                        chunk_size=chunk_size,
                        overlap=chunk_overlap,
                        max_context_tokens=max_context_tokens
                    )
                    progress_bar.progress(20)
                    
                    # Process PDFs based on mode
                    status_text.text("Processing PDF files...")
                    if processing_mode == "Scraped Companies":
                        dossier = generator.generate_company_dossier(company_domain=selected_company)
                    else:
                        dossier = generator.generate_company_dossier(
                            pdf_directory=custom_pdf_dir,
                            company_name=company_display_name
                        )
                    progress_bar.progress(80)
                    
                    # Save results
                    status_text.text("Saving dossier...")
                    output_dir = Path("dossiers")
                    output_dir.mkdir(exist_ok=True)
                    
                    # Create safe filename
                    safe_name = "".join(c for c in company_display_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_name = safe_name.replace(' ', '_').lower()
                    
                    json_path = output_dir / f"{safe_name}_dossier.json"
                    html_path = output_dir / f"{safe_name}_dossier.html"
                    
                    generator.save_dossier(dossier, str(json_path))
                    generator.export_dossier_html(dossier, str(html_path))
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Dossier generation complete!")
                    
                    st.success(f"Dossier generated successfully! Files saved to: {output_dir}")
                    
                    # Store dossier in session state for display
                    st.session_state.current_dossier = dossier
                    st.session_state.dossier_paths = {
                        'json': str(json_path),
                        'html': str(html_path)
                    }
                    
                except Exception as e:
                    st.error(f"Error generating dossier: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
else:
    # Show instructions when no valid source is selected
    st.info("👆 Please select a PDF source in the sidebar to begin")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Scraped Companies Mode")
        st.markdown("""
        Use PDFs that were scraped from company websites:
        - Select from available scraped companies
        - PDFs are organized by domain
        - Automatic company identification
        """)
        
    with col2:
        st.subheader("📁 Custom PDF Directory Mode") 
        st.markdown("""
        Use any directory containing PDF files:
        - Browse your file system
        - Analyze any collection of PDFs
        - Customize company name
        """)

# Right column - Quick Actions and Info
if (processing_mode == "Scraped Companies" and available_companies) or (processing_mode == "Custom PDF Directory"):
    with col2:
        st.subheader("Quick Actions")
        
        # Current mode info
        st.markdown(f"**Mode:** {processing_mode}")
        if processing_mode == "Scraped Companies" and selected_company:
            st.markdown(f"**Source:** {selected_company}")
        elif processing_mode == "Custom PDF Directory" and custom_pdf_dir:
            st.markdown(f"**Directory:** {Path(custom_pdf_dir).name}")
        
        # View existing dossiers
        dossier_dir = Path("dossiers")
        if dossier_dir.exists():
            existing_dossiers = list(dossier_dir.glob("*.json"))
            if existing_dossiers:
                st.write("**Existing Dossiers:**")
                for dossier_file in existing_dossiers:
                    col_name, col_download = st.columns([3, 1])
                    with col_name:
                        st.text(dossier_file.stem.replace("_dossier", ""))
                    with col_download:
                        if st.button("📄", key=f"view_{dossier_file.stem}"):
                            # Load and display dossier
                            with open(dossier_file, 'r') as f:
                                dossier_data = json.load(f)
                            st.session_state.current_dossier = CompanyDossier(**dossier_data)
        
        # Settings info
        if (processing_mode == "Scraped Companies" and selected_company) or (processing_mode == "Custom PDF Directory" and custom_pdf_dir):
            st.subheader("Current Settings")
            st.write(f"**Chunk Size:** {chunk_size}")
            st.write(f"**Overlap:** {chunk_overlap}")
            st.write(f"**Max Clusters:** {max_clusters}")

# Display dossier if available
if 'current_dossier' in st.session_state:
    st.divider()
    st.header("📊 Generated Dossier")
    
    dossier = st.session_state.current_dossier
    
    # Download buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if 'dossier_paths' in st.session_state:
            with open(st.session_state.dossier_paths['json'], 'r') as f:
                st.download_button(
                    "📥 Download JSON",
                    f.read(),
                    file_name=f"{dossier.company_name}_dossier.json",
                    mime="application/json"
                )
    
    with col2:
        if 'dossier_paths' in st.session_state:
            with open(st.session_state.dossier_paths['html'], 'r') as f:
                st.download_button(
                    "📥 Download HTML",
                    f.read(),
                    file_name=f"{dossier.company_name}_dossier.html",
                    mime="text/html"
                )
    
    # Display dossier content
    st.subheader(f"Company: {dossier.company_name}")
    
    # Executive Summary
    st.subheader("📋 Executive Summary")
    st.write(dossier.executive_summary)
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Business Overview", 
        "💰 Financial Highlights", 
        "👥 Key Personnel", 
        "📍 Locations", 
        "🛍️ Products & Services"
    ])
    
    with tab1:
        st.write(dossier.business_overview)
    
    with tab2:
        st.write(dossier.financial_highlights)
    
    with tab3:
        if dossier.key_personnel:
            for person in dossier.key_personnel:
                st.write(f"• {person}")
        else:
            st.write("No key personnel information found.")
    
    with tab4:
        if dossier.locations:
            for location in dossier.locations:
                st.write(f"• {location}")
        else:
            st.write("No location information found.")
    
    with tab5:
        if dossier.products_services:
            for item in dossier.products_services[:10]:  # Limit display
                st.write(f"• {item}")
            if len(dossier.products_services) > 10:
                st.write(f"... and {len(dossier.products_services) - 10} more items")
        else:
            st.write("No products/services information found.")
    
    # Metadata
    with st.expander("📊 Metadata"):
        st.write(f"**Sources:** {len(set(dossier.sources))} unique documents")
        st.write(f"**Last Updated:** {dossier.last_updated}")
        if dossier.sources:
            st.write("**Source Files:**")
            for source in list(set(dossier.sources))[:5]:  # Show first 5
                st.write(f"• {Path(source).name}")
            if len(set(dossier.sources)) > 5:
                st.write(f"• ... and {len(set(dossier.sources)) - 5} more files")

# Help section
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    ### Step-by-step Guide:
    
    #### Option 1: Scraped Companies Mode
    1. **Scrape Company Data**: First, use the main OSINT tool to scrape a company's website and download PDFs
    2. **Select Company**: Choose a company domain from the dropdown (only domains with PDFs will appear)
    3. **Configure Settings**: Adjust processing parameters in the sidebar
    4. **Generate Dossier**: Click the "Generate Dossier" button to start processing
    
    #### Option 2: Custom PDF Directory Mode
    1. **Prepare PDFs**: Collect PDF documents in a single directory on your computer
    2. **Browse Directory**: Use the sidebar to browse and select your PDF directory
       - Enter a manual path, or
       - Use quick selection from common locations
    3. **Name Company**: Enter a name for the company/organization
    4. **Configure Settings**: Adjust processing parameters in the sidebar
    5. **Generate Dossier**: Click the "Generate Dossier" button to start processing
    
    ### Processing Parameters:
    - **Chunk Size**: How much text to process at once (larger = more context, slower)
    - **Chunk Overlap**: Overlap between chunks to maintain context
    - **Max Clusters**: Number of topic clusters to identify
    
    ### Directory Structure Examples:
    
    **For Scraped Mode:**
    ```
    downloads/
    └── www.company.com/
        └── pdfs/
            ├── annual_report.pdf
            ├── investor_deck.pdf
            └── sustainability_report.pdf
    ```
    
    **For Custom Directory Mode:**
    ```
    /your/custom/path/
    ├── company_overview.pdf
    ├── financial_statements.pdf
    ├── product_catalog.pdf
    └── press_releases.pdf
    ```
    
    ### Output:
    - **JSON Format**: Structured data for further processing
    - **HTML Format**: Human-readable report with formatting
    - **Sections Include**: Executive summary, business overview, financials, personnel, locations, products/services
    
    ### Technical Approach:
    - **Hierarchical Summarization**: PDFs are chunked, embedded, and clustered by topic
    - **Semantic Search**: Relevant information is extracted using semantic similarity
    - **Context Management**: Large documents are processed in chunks to respect AI model limits
    - **Multi-format Output**: Results available as structured JSON and formatted HTML
    
    ### Requirements:
    - Configure your AI API key in the `.env` file
    - Install required dependencies: `pip install -r requirements.txt`
    - Have PDF files in either scraped structure or custom directory
    """)
