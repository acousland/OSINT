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
st.sidebar.header("⚙️ Configuration")

# Processing parameters
st.sidebar.markdown("### 📊 Processing Settings")
chunk_size = st.sidebar.slider("Chunk Size", 500, 2000, 1000, 100)
chunk_overlap = st.sidebar.slider("Chunk Overlap", 100, 500, 200, 50)
max_clusters = st.sidebar.slider("Max Topic Clusters", 3, 15, 8, 1)

# Advanced options
with st.sidebar.expander("Advanced Options"):
    max_context_tokens = st.number_input("Max Context Tokens", 2000, 8000, 4000, 500)

# Content Source Selection in main window
st.markdown("### 📁 Select Content Source")

# Mode selection
processing_mode = st.radio(
    "Choose your content source:",
    ["Scraped Companies", "Custom Document Directory"],
    help="Select whether to use content from scraped companies or browse for a custom directory",
    horizontal=True
)

# Initialize variables
selected_company = None
custom_pdf_dir = None
company_display_name = None

if processing_mode == "Scraped Companies":
    st.markdown("#### 🏢 Select Scraped Company")
    
    # Check for available companies (domains with content)
    downloads_dir = Path("downloads")
    available_companies = []
    if downloads_dir.exists():
        for domain_dir in downloads_dir.iterdir():
            if domain_dir.is_dir():
                pdf_dir = domain_dir / "pdfs"
                html_dir = domain_dir / "html_pages"
                
                # Count available content
                pdf_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
                html_count = len(list(html_dir.glob("*.html"))) if html_dir.exists() else 0
                
                if pdf_count > 0 or html_count > 0:
                    available_companies.append({
                        'name': domain_dir.name,
                        'pdf_count': pdf_count,
                        'html_count': html_count,
                        'total_count': pdf_count + html_count
                    })

    if not available_companies:
        st.warning("🚫 No companies with content found in downloads directory.")
        st.info("💡 Please run the scraper first or switch to 'Custom Document Directory' mode.")
    else:
        # Company selection with details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            company_names = [comp['name'] for comp in available_companies]
            selected_company = st.selectbox(
                "Select Company Domain:",
                company_names,
                help="Choose a company domain that has been scraped"
            )
            company_display_name = selected_company
        
        with col2:
            # Show details for selected company
            if selected_company:
                selected_comp_data = next(comp for comp in available_companies if comp['name'] == selected_company)
                st.metric("PDF Files", selected_comp_data['pdf_count'])
                st.metric("HTML Pages", selected_comp_data['html_count'])
                st.metric("Total Documents", selected_comp_data['total_count'])

else:  # Custom Document Directory mode
    st.markdown("#### � Browse for Content Directory")
    
    # Initialize session state for directory navigation
    if 'current_directory' not in st.session_state:
        st.session_state.current_directory = str(Path.home())
    if 'selected_directory' not in st.session_state:
        st.session_state.selected_directory = None
    
    def get_directories(path):
        """Get list of directories in the given path"""
        try:
            path_obj = Path(path)
            if not path_obj.exists() or not path_obj.is_dir():
                return []
            
            directories = []
            # Add parent directory option (except for root)
            if path_obj.parent != path_obj:
                directories.append("📁 .. (Parent Directory)")
            
            # Add subdirectories
            for item in sorted(path_obj.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if directory contains content
                    pdf_count = len(list(item.glob("*.pdf")))
                    html_count = len(list(item.glob("*.html")))
                    total_count = pdf_count + html_count
                    
                    if total_count > 0:
                        directories.append(f"📁 {item.name} ({total_count} files)")
                    else:
                        directories.append(f"📁 {item.name}")
            
            return directories
        except PermissionError:
            return ["❌ Permission denied"]
        except Exception:
            return ["❌ Error reading directory"]
    
    # Directory navigation in main window
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Current directory display
        st.markdown("**Current Directory:**")
        st.code(st.session_state.current_directory)
        
        # Directory browser
        directories = get_directories(st.session_state.current_directory)
        
        if directories:
            selected_dir = st.selectbox(
                "📂 Select Directory:",
                ["Select a directory..."] + directories,
                key="directory_browser",
                help="Navigate through directories to find your content"
            )
            
            if selected_dir != "Select a directory...":
                if selected_dir == "📁 .. (Parent Directory)":
                    # Navigate to parent directory
                    st.session_state.current_directory = str(Path(st.session_state.current_directory).parent)
                    st.rerun()
                elif selected_dir.startswith("📁"):
                    # Extract directory name and navigate
                    dir_name = selected_dir.split(" ")[1]
                    if "(" in dir_name:
                        dir_name = dir_name.split(" (")[0]
                    new_path = Path(st.session_state.current_directory) / dir_name
                    st.session_state.current_directory = str(new_path)
                    st.rerun()
    
    with col2:
        # Quick navigation buttons
        st.markdown("**Quick Navigation:**")
        
        if st.button("🏠 Home", help="Go to home directory"):
            st.session_state.current_directory = str(Path.home())
            st.rerun()
        
        if st.button("📥 Downloads", help="Go to Downloads folder"):
            downloads_path = Path.home() / "Downloads"
            if downloads_path.exists():
                st.session_state.current_directory = str(downloads_path)
                st.rerun()
        
        if st.button("📄 Project", help="Go to project directory"):
            st.session_state.current_directory = str(Path.cwd())
            st.rerun()
    
    # Current directory content analysis
    current_path = Path(st.session_state.current_directory)
    if current_path.exists():
        pdf_count = len(list(current_path.glob("*.pdf")))
        html_count = len(list(current_path.glob("*.html")))
        total_count = pdf_count + html_count
        
        # Show content summary
        if total_count > 0:
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            
            with col1:
                st.metric("PDF Files", pdf_count)
            with col2:
                st.metric("HTML Pages", html_count)
            with col3:
                st.metric("Total Documents", total_count)
            with col4:
                # Use current directory button
                if st.button("📋 Use This Directory", type="primary"):
                    st.session_state.selected_directory = st.session_state.current_directory
                    st.rerun()
        else:
            st.info("ℹ️ No PDF or HTML files found in current directory")
    
    # Show selected directory (if any)
    if st.session_state.selected_directory:
        st.success(f"✅ **Selected Directory:** {st.session_state.selected_directory}")
        custom_pdf_dir = st.session_state.selected_directory
        
        # Company name input
        col1, col2 = st.columns([2, 1])
        with col1:
            company_display_name = st.text_input(
                "Company Name:",
                value=Path(st.session_state.selected_directory).name,
                help="Enter a name for this company/organization"
            )
        with col2:
            # Clear selection button
            if st.button("🗑️ Clear Selection"):
                st.session_state.selected_directory = None
                st.rerun()
    
    # Manual path input (as backup)
    with st.expander("💻 Manual Path Entry"):
        manual_path = st.text_input(
            "Enter directory path directly:",
            placeholder="/path/to/your/documents",
            help="Enter the full path to a directory containing PDF or HTML files"
        )
        
        if manual_path and Path(manual_path).exists():
            col1, col2 = st.columns([3, 1])
            with col1:
                path_pdf_count = len(list(Path(manual_path).glob("*.pdf")))
                path_html_count = len(list(Path(manual_path).glob("*.html")))
                st.info(f"Found {path_pdf_count} PDF files and {path_html_count} HTML pages")
            with col2:
                if st.button("✅ Use Manual Path"):
                    st.session_state.selected_directory = manual_path
                    st.rerun()
        elif manual_path:
            st.error("❌ Directory not found or inaccessible")

# Processing parameters (show only if we have a valid source)
if (processing_mode == "Scraped Companies" and selected_company) or (processing_mode == "Custom Document Directory" and custom_pdf_dir):
    st.sidebar.subheader("Processing Parameters")
    chunk_size = st.sidebar.slider("Chunk Size", 500, 2000, 1000, 100)
    chunk_overlap = st.sidebar.slider("Chunk Overlap", 100, 500, 200, 50)
    max_clusters = st.sidebar.slider("Max Topic Clusters", 3, 15, 8, 1)
    
    # Advanced options
    with st.sidebar.expander("Advanced Options"):
        max_context_tokens = st.number_input("Max Context Tokens", 2000, 8000, 4000, 500)
        st.markdown("**Business Intelligence Proforma**")
        st.markdown("All 9 sections are included by default:")
        st.markdown("• Company Identity & Purpose")
        st.markdown("• Products & Services")
        st.markdown("• Customer & Stakeholder Landscape")
        st.markdown("• Business Activities & Processes")
        st.markdown("• Organisational Structure")
        st.markdown("• Channels & Interactions")
        st.markdown("• Compliance & Regulatory")
        st.markdown("• Technology Landscape")
        st.markdown("• Strategic Priorities")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if processing_mode == "Scraped Companies":
            st.subheader(f"Generate Dossier for: {selected_company}")
            
            # Show content counts
            company_dir = downloads_dir / selected_company
            pdf_dir = company_dir / "pdfs"
            html_dir = company_dir / "html_pages"
            
            pdf_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
            html_count = len(list(html_dir.glob("*.html"))) if html_dir.exists() else 0
            total_count = pdf_count + html_count
            
            source_info = f"Found {pdf_count} PDF files and {html_count} HTML pages ({total_count} total documents)"
            
        else:
            st.subheader(f"Generate Dossier for: {company_display_name}")
            
            # Show content count from custom directory
            pdf_count = len(list(Path(custom_pdf_dir).glob("*.pdf"))) if custom_pdf_dir else 0
            html_count = len(list(Path(custom_pdf_dir).glob("*.html"))) if custom_pdf_dir else 0
            total_count = pdf_count + html_count
            
            source_info = f"Found {pdf_count} PDF files and {html_count} HTML pages ({total_count} total documents)"
        
        st.info(source_info)
        
        # Show source path
        if processing_mode == "Scraped Companies" and selected_company:
            st.code(f"Sources: downloads/{selected_company}/pdfs/ and downloads/{selected_company}/html_pages/")
        elif custom_pdf_dir:
            st.code(f"Source: {custom_pdf_dir}")
        
        # Generate button
        if st.button("🚀 Generate Enhanced Dossier", type="primary", use_container_width=True):
            if total_count == 0:
                st.error("No documents found in the selected source.")
            else:
                # Initialize progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Initialize generator
                    status_text.text("Initializing enhanced dossier generator...")
                    generator = DossierGenerator(
                        downloads_dir="downloads",
                        chunk_size=chunk_size,
                        overlap=chunk_overlap,
                        max_context_tokens=max_context_tokens
                    )
                    progress_bar.progress(20)
                    
                    # Process documents based on mode
                    status_text.text("Processing PDF and HTML content...")
                    if processing_mode == "Scraped Companies":
                        dossier = generator.generate_company_dossier(company_domain=selected_company)
                    else:
                        dossier = generator.generate_company_dossier(
                            pdf_directory=custom_pdf_dir,
                            html_directory=custom_pdf_dir,  # Same directory for both
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
    st.info("👆 Please select a content source in the sidebar to begin")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Scraped Companies Mode")
        st.markdown("""
        Use content from scraped companies:
        - **PDF Documents**: Annual reports, presentations, financial statements
        - **HTML Pages**: Website content, news, about pages, product information
        - **Automatic organization** by domain
        - **Integrated analysis** of all content types
        """)
        
    with col2:
        st.subheader("📁 Custom Document Directory Mode") 
        st.markdown("""
        Use any collection of documents:
        - **Mixed content**: PDFs and HTML files
        - **Browse your file system** for any document collection
        - **Custom company naming** and analysis
        - **Flexible source management**
        """)

# Right column - Quick Actions and Info
if (processing_mode == "Scraped Companies" and available_companies) or (processing_mode == "Custom Document Directory"):
    with col2:
        st.subheader("Quick Actions")
        
        # Current mode info
        st.markdown(f"**Mode:** {processing_mode}")
        if processing_mode == "Scraped Companies" and selected_company:
            st.markdown(f"**Source:** {selected_company}")
        elif processing_mode == "Custom Document Directory" and custom_pdf_dir:
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
    
    # Display business intelligence proforma
    st.subheader("� Business Intelligence Proforma")
    st.markdown("*Comprehensive 9-Section Analysis*")
    
    # Create tabs for the 9 sections  
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Identity & Purpose", 
        "�️ Products & Services", 
        "👥 Customers & Stakeholders", 
        "⚙️ Business Activities", 
        "🏗️ Organisation & Structure"
    ])
    
    tab6, tab7, tab8, tab9 = st.tabs([
        "📡 Channels & Interactions",
        "⚖️ Compliance & Regulatory", 
        "💻 Technology Landscape", 
        "🎯 Strategic Priorities"
    ])
    
    with tab1:
        st.markdown("#### Company Identity and Purpose")
        st.write(dossier.company_identity_and_purpose)
    
    with tab2:
        st.markdown("#### Products and Services Offered")
        st.write(dossier.products_and_services_offered)
    
    with tab3:
        st.markdown("#### Customer and Stakeholder Landscape")
        st.write(dossier.customer_and_stakeholder_landscape)
    
    with tab4:
        st.markdown("#### Core Business Activities and Processes")
        st.write(dossier.core_business_activities_and_processes)
    
    with tab5:
        st.markdown("#### Organisational Structure and Functions")
        st.write(dossier.organisational_structure_and_functions)
    
    with tab6:
        st.markdown("#### Channels and Customer Interactions")
        st.write(dossier.channels_and_customer_interactions)
    
    with tab7:
        st.markdown("#### Compliance and Regulatory Context")
        st.write(dossier.compliance_and_regulatory_context)
    
    with tab8:
        st.markdown("#### Technology Landscape")
        st.write(dossier.technology_landscape)
    
    with tab9:
        st.markdown("#### Strategic Priorities and Data Challenges")
        st.write(dossier.strategic_priorities_and_data_challenges)
    
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
    - **Sections Include**: 9-section business intelligence proforma covering identity, products, customers, activities, structure, channels, compliance, technology, and strategy
    
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
