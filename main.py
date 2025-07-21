import streamlit as st
import os
import json
from pathlib import Path
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import modules for different functionalities
import mapStructure as ms
import scrape as sc
from dossier_generator import DossierGenerator, CompanyDossier

st.set_page_config(
    page_title="OSINT Toolkit",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
    }
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .feature-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #2c3e50;
    }
    .feature-desc {
        color: #6c757d;
        font-size: 0.9rem;
    }
    .sidebar-section {
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">🔍 OSINT Toolkit</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #6c757d; margin-bottom: 3rem;">Complete Open Source Intelligence gathering and analysis platform</p>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("🧭 Navigation")
    
    # Mode selection
    app_mode = st.sidebar.radio(
        "Choose Tool:",
        ["🏠 Home", "🗺️ Website Mapping", "📄 Content Scraping", "📋 Dossier Generation"],
        help="Select the OSINT tool you want to use"
    )
    
    # Add some info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.markdown("""
    **OSINT Toolkit** provides:
    - Website structure mapping
    - Content scraping and downloading
    - AI-powered dossier generation
    - Comprehensive company analysis
    """)
    
    # Main content based on selection
    if app_mode == "🏠 Home":
        show_home_page()
    elif app_mode == "🗺️ Website Mapping":
        show_mapping_page()
    elif app_mode == "📄 Content Scraping":
        show_scraping_page()
    elif app_mode == "📋 Dossier Generation":
        show_dossier_page()

def show_home_page():
    """Display the home page with feature overview"""
    st.markdown("## Choose Your OSINT Tool")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🗺️</div>
            <div class="feature-title">Website Mapping</div>
            <div class="feature-desc">Discover and map website structure, find hidden pages and analyze site architecture</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗺️ Start Mapping", use_container_width=True, type="primary"):
            st.session_state.app_mode = "🗺️ Website Mapping"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <div class="feature-title">Content Scraping</div>
            <div class="feature-desc">Extract and download website content including HTML pages and PDFs</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📄 Start Scraping", use_container_width=True, type="primary"):
            st.session_state.app_mode = "📄 Content Scraping"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📋</div>
            <div class="feature-title">Dossier Generation</div>
            <div class="feature-desc">Generate comprehensive company intelligence reports from collected documents</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📋 Generate Dossier", use_container_width=True, type="primary"):
            st.session_state.app_mode = "📋 Dossier Generation"
            st.rerun()
    
    # Workflow overview
    st.markdown("---")
    st.markdown("## 🔄 Typical Workflow")
    
    workflow_col1, workflow_col2, workflow_col3 = st.columns(3)
    
    with workflow_col1:
        st.markdown("""
        ### Step 1: Map Website
        - Enter target website URL
        - Set crawling depth
        - Discover site structure
        - Identify PDF resources
        """)
    
    with workflow_col2:
        st.markdown("""
        ### Step 2: Scrape Content  
        - Download discovered PDFs
        - Organize by domain
        - Extract documents
        - Prepare for analysis
        """)
    
    with workflow_col3:
        st.markdown("""
        ### Step 3: Generate Dossier
        - Process collected PDFs
        - AI-powered analysis
        - Generate comprehensive report
        - Export results
        """)
    
    # Recent activity
    st.markdown("---")
    st.markdown("## 📊 Recent Activity")
    
    recent_col1, recent_col2 = st.columns(2)
    
    with recent_col1:
        st.markdown("### 🗂️ Scraped Companies")
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            companies = []
            for domain_dir in downloads_dir.iterdir():
                if domain_dir.is_dir():
                    pdf_dir = domain_dir / "pdfs"
                    if pdf_dir.exists():
                        pdf_count = len(list(pdf_dir.glob("*.pdf")))
                        if pdf_count > 0:
                            companies.append(f"{domain_dir.name} ({pdf_count} PDFs)")
            
            if companies:
                for company in companies[:5]:  # Show last 5
                    st.write(f"• {company}")
                if len(companies) > 5:
                    st.write(f"... and {len(companies) - 5} more")
            else:
                st.write("No scraped companies found")
        else:
            st.write("No downloads directory found")
    
    with recent_col2:
        st.markdown("### 📋 Generated Dossiers")
        dossier_dir = Path("dossiers")
        if dossier_dir.exists():
            dossiers = list(dossier_dir.glob("*.json"))
            if dossiers:
                for dossier in dossiers[-5:]:  # Show last 5
                    name = dossier.stem.replace("_dossier", "")
                    st.write(f"• {name}")
                if len(dossiers) > 5:
                    st.write(f"... and {len(dossiers) - 5} more")
            else:
                st.write("No dossiers generated yet")
        else:
            st.write("No dossiers directory found")

def show_mapping_page():
    """Display the website mapping interface"""
    st.markdown("## 🗺️ Website Structure Mapping")
    st.markdown("Discover and map website architecture to identify resources and hidden content.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Target Configuration")
        start_url = st.text_input(
            'Target Website URL', 
            value='',
            placeholder='https://www.example.com',
            help="Enter the full URL of the website to map"
        )
        
        max_depth = st.number_input(
            'Maximum Crawl Depth', 
            min_value=1, 
            max_value=1000, 
            value=100,
            help="How deep to crawl the website structure"
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            speed_mode = st.select_slider(
                "Speed Mode",
                options=["Respectful", "Fast", "Turbo"],
                value="Fast",
                help="Respectful: 30 concurrent requests, Fast: 50 concurrent, Turbo: 100 concurrent (aggressive)"
            )
            delay = st.slider("Delay between requests (seconds)", 0.05, 2.0, 0.1, 0.05)
            max_concurrent = st.slider("Maximum concurrent requests", 10, 100, 50, 10)
        
        if st.button('🚀 Start Mapping', type="primary", use_container_width=True):
            if not start_url:
                st.error("Please enter a valid URL")
            else:
                with st.spinner('🚀 High-speed mapping in progress...'):
                    try:
                        # Use the appropriate mapping function based on speed mode
                        if speed_mode == "Turbo":
                            result = ms.turbo_map(start_url, max_depth)
                        elif speed_mode == "Fast":
                            result = ms.fast_map(start_url, max_depth) 
                        else:  # Respectful
                            result = ms.map(start_url, max_depth, max_concurrent=30, request_delay=delay)
                        
                        st.success('✅ High-speed website mapping completed!')
                        
                        # Show results summary
                        if result:
                            st.markdown("### 📊 High-Speed Mapping Results")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("URLs Discovered", result.get('total_urls', 0))
                            with col2:
                                st.metric("Total Time", f"{result.get('total_time', 0):.2f}s")
                            with col3:
                                st.metric("Speed", f"{result.get('urls_per_second', 0):.1f} URLs/sec")
                            
                            st.write(f"**Target:** {start_url}")
                            st.write(f"**Output File:** `{result.get('output_file', 'N/A')}`")
                            
                            st.info("💡 Mapping complete! You can now proceed to content scraping to download all discovered pages.")
                            
                    except Exception as e:
                        st.error(f"❌ Error during mapping: {str(e)}")
    
    with col2:
        st.markdown("### 📋 High-Speed Mapping Guide")
        st.markdown("""
        **🚀 Speed Modes:**
        - **Respectful**: 30 concurrent requests
        - **Fast**: 50 concurrent requests  
        - **Turbo**: 100 concurrent requests (aggressive)
        
        **What mapping discovers:**
        - All accessible pages
        - PDF documents
        - Site structure
        - Hidden resources
        
        **Performance Tips:**
        - Fast mode is recommended for most sites
        - Turbo mode for maximum speed (use carefully)
        - Lower concurrent requests for smaller servers
        - Be respectful with crawl delays
        """)
        
        # Show mapping history
        st.markdown("### 📈 Recent Mappings")
        # This could be enhanced to show actual mapping history
        st.info("Mapping history will appear here after running mappings")

def show_scraping_page():
    """Display the high-speed content scraping interface"""
    st.markdown("## 📄 High-Speed Content Scraping")
    st.markdown("Download content from mapped websites for analysis and intelligence gathering.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Scraping Configuration")
        
        # URL input
        scrape_url = st.text_input(
            'Website URL to Scrape', 
            value='',
            placeholder='https://www.example.com',
            help="Enter the website URL that was previously mapped"
        )
        
        # Scraping options
        with st.expander("⚙️ Scraping Options"):
            speed_mode = st.select_slider(
                "Speed Mode",
                options=["Normal", "Fast", "Turbo"],
                value="Fast",
                help="Normal: 20 concurrent, Fast: 30 concurrent, Turbo: 50 concurrent"
            )
            save_html = st.checkbox("Save HTML pages", True, help="Save full HTML content for analysis")
            save_pdfs = st.checkbox("Download PDF files", True, help="Download any PDF files found")
            max_concurrent = st.slider("Max concurrent downloads", 10, 50, 20)
        
        if st.button('🚀 Start High-Speed Scraping', type="primary", use_container_width=True):
            if not scrape_url:
                st.error("Please enter a valid URL")
            else:
                with st.spinner('🚀 High-speed scraping in progress...'):
                    try:
                        # Use appropriate scraping function based on speed mode
                        if speed_mode == "Turbo":
                            result = sc.turbo_scrape(scrape_url)
                        elif speed_mode == "Fast":
                            result = sc.fast_scrape(scrape_url)
                        else:  # Normal
                            result = sc.scrape(scrape_url, max_concurrent=max_concurrent)
                        
                        if result:
                            st.success('✅ High-speed scraping completed!')
                            
                            # Show detailed results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Files Processed", result.get('total_processed', 0))
                            with col2:
                                st.metric("Successful", result.get('successful', 0))
                            with col3:
                                st.metric("Speed", f"{result.get('files_per_second', 0):.1f} files/sec")
                            
                            # Show file locations
                            if result.get('html_dir'):
                                st.info(f"📁 HTML pages saved to: `{result['html_dir']}`")
                            if result.get('pdf_dir'):
                                st.info(f"� PDF files saved to: `{result['pdf_dir']}`")
                            
                            # Quick action to generate dossier
                            html_count = len(list(Path(result.get('html_dir', '')).glob("*.html"))) if result.get('html_dir') else 0
                            if html_count > 0:
                                st.markdown("### 🚀 Next Steps")
                                if st.button("📋 Generate Dossier from Scraped Content", use_container_width=True):
                                    domain = scrape_url.replace("https://", "").replace("http://", "").split("/")[0]
                                    st.session_state.app_mode = "📋 Dossier Generation"
                                    st.session_state.suggested_company = domain
                                    st.rerun()
                        else:
                            st.success('✅ Scraping completed!')
                        
                    except Exception as e:
                        st.error(f"❌ Error during scraping: {str(e)}")
    
    with col2:
        st.markdown("### 📋 High-Speed Scraping Guide")
        st.markdown("""
        **🚀 Speed Modes:**
        - **Normal**: 20 concurrent (safe)
        - **Fast**: 30 concurrent (recommended)
        - **Turbo**: 50 concurrent (aggressive)
        
        **What scraping does:**
        - Downloads all mapped HTML pages
        - Extracts PDF documents
        - Saves page content with metadata
        - Prepares for AI analysis
        
        **Performance Tips:**
        - Ensure website was mapped first
        - Fast mode works for most sites
        - Turbo mode for maximum speed
        - Use reasonable download limits
        - Be mindful of server load
        - Respect rate limits
        """)
        
        # Show scraped content
        st.markdown("### 📁 Scraped Content")
        downloads_dir = Path("downloads")
        if downloads_dir.exists():
            for domain_dir in downloads_dir.iterdir():
                if domain_dir.is_dir():
                    pdf_dir = domain_dir / "pdfs"
                    if pdf_dir.exists():
                        pdf_count = len(list(pdf_dir.glob("*.pdf")))
                        if pdf_count > 0:
                            st.write(f"📁 {domain_dir.name}: {pdf_count} PDFs")
        else:
            st.info("No scraped content yet")

def show_dossier_page():
    """Display the dossier generation interface (embedded from dossier_ui.py)"""
    st.markdown("## 📋 Company Dossier Generation")
    st.markdown("Generate comprehensive intelligence reports from collected PDF documents using AI analysis.")
    
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

    # Check API status
    api_configured = check_api_status()
    
    # Only show interface if API is configured or user wants to proceed anyway
    if not api_configured:
        if st.button("⚠️ Continue Without API (Limited Functionality)", type="secondary"):
            st.warning("Dossier generation will show placeholder text instead of AI analysis")
            api_configured = True
    
    if not api_configured:
        return  # Exit early if API not configured
    
    # Check if there's a suggested company from scraping
    suggested_company = st.session_state.get('suggested_company', None)
    if suggested_company:
        st.info(f"💡 Suggestion: Generate dossier for recently scraped company: **{suggested_company}**")
        if st.button("✨ Use Suggested Company", type="secondary"):
            st.session_state.dossier_selected_company = suggested_company
            st.session_state.dossier_processing_mode = "Scraped Companies"
    
    # Sidebar for dossier configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Dossier Settings")
    
    # Mode selection
    processing_mode = st.sidebar.radio(
        "PDF Source:",
        ["Scraped Companies", "Custom PDF Directory"],
        help="Select whether to use PDFs from scraped companies or browse for a custom directory",
        key="dossier_processing_mode"
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
            st.sidebar.warning("No companies with PDFs found.")
            st.sidebar.info("Run the scraper first or use Custom PDF Directory mode.")
        else:
            # Company selection
            default_index = 0
            if suggested_company and suggested_company in available_companies:
                default_index = available_companies.index(suggested_company)
            
            selected_company = st.sidebar.selectbox(
                "Select Company Domain",
                available_companies,
                index=default_index,
                help="Choose a company domain that has been scraped",
                key="dossier_selected_company"
            )
            company_display_name = selected_company

    else:  # Custom PDF Directory mode
        st.sidebar.markdown("#### 📁 Browse for PDF Directory")
        
        # Text input for manual path entry
        manual_path = st.sidebar.text_input(
            "Enter PDF Directory Path:",
            placeholder="/path/to/your/pdfs",
            help="Enter the full path to a directory containing PDF files",
            key="dossier_manual_path"
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
                help="Enter a name for this company/organization",
                key="dossier_company_name"
            )
        elif manual_path:
            st.sidebar.error("❌ Directory not found or inaccessible")
        
        # Quick selection for common directories
        common_dirs = [
            str(Path.home() / "Desktop"),
            str(Path.home() / "Downloads"), 
            str(Path.home() / "Documents"),
            str(Path.cwd())
        ]
        
        quick_dir = st.sidebar.selectbox(
            "Quick select:",
            ["Select a location..."] + common_dirs,
            help="Choose from common directory locations",
            key="dossier_quick_dir"
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
                            f"Folders with PDFs:",
                            ["Select a folder..."] + subdirs_with_pdfs,
                            key="dossier_subdir"
                        )
                        
                        if selected_subdir != "Select a folder...":
                            folder_name = selected_subdir.split(" (")[0]
                            custom_pdf_dir = str(quick_path / folder_name)
                            if 'dossier_company_name' not in st.session_state:
                                company_display_name = folder_name
                    else:
                        # Check if current directory has PDFs
                        pdf_count = len(list(quick_path.glob("*.pdf")))
                        if pdf_count > 0:
                            if st.sidebar.button(f"Use {quick_path.name} ({pdf_count} PDFs)"):
                                custom_pdf_dir = str(quick_path)
                                company_display_name = quick_path.name
                        else:
                            st.sidebar.info(f"No PDFs found in {quick_path.name}")
                            
                except PermissionError:
                    st.sidebar.error("❌ Permission denied accessing this directory")

    # Processing parameters (show only if we have a valid source)
    if (processing_mode == "Scraped Companies" and selected_company) or (processing_mode == "Custom PDF Directory" and custom_pdf_dir):
        st.sidebar.markdown("#### ⚙️ Processing Parameters")
        chunk_size = st.sidebar.slider("Chunk Size", 500, 2000, 1000, 100, key="dossier_chunk_size")
        chunk_overlap = st.sidebar.slider("Chunk Overlap", 100, 500, 200, 50, key="dossier_chunk_overlap")
        max_clusters = st.sidebar.slider("Max Topic Clusters", 3, 15, 8, 1, key="dossier_max_clusters")
        
        # Advanced options
        with st.sidebar.expander("Advanced Options"):
            max_context_tokens = st.number_input("Max Context Tokens", 2000, 8000, 4000, 500, key="dossier_max_tokens")
        
        # Main dossier interface
        dossier_col1, dossier_col2 = st.columns([2, 1])
        
        with dossier_col1:
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
            if st.button("🚀 Generate Dossier", type="primary", use_container_width=True, key="generate_dossier_btn"):
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
        
        with dossier_col2:
            st.markdown("### ⚡ Quick Actions")
            
            # View existing dossiers
            dossier_dir = Path("dossiers")
            if dossier_dir.exists():
                existing_dossiers = list(dossier_dir.glob("*.json"))
                if existing_dossiers:
                    st.write("**Recent Dossiers:**")
                    for dossier_file in existing_dossiers[-3:]:  # Show last 3
                        name = dossier_file.stem.replace("_dossier", "")
                        if st.button(f"📄 {name}", key=f"load_{dossier_file.stem}"):
                            # Load and display dossier
                            with open(dossier_file, 'r') as f:
                                dossier_data = json.load(f)
                            st.session_state.current_dossier = CompanyDossier(**dossier_data)
                            st.rerun()
            
            # Current settings
            st.write("**Settings:**")
            st.write(f"Chunk Size: {chunk_size}")
            st.write(f"Overlap: {chunk_overlap}")
            st.write(f"Clusters: {max_clusters}")
    
    else:
        # Show instructions when no valid source is selected
        st.info("👆 Please select a PDF source in the sidebar to begin")
        
        inst_col1, inst_col2 = st.columns(2)
        
        with inst_col1:
            st.markdown("### 📊 Scraped Companies Mode")
            st.markdown("""
            Use PDFs from scraped companies:
            - Automatic organization by domain
            - Integrated with mapping/scraping tools
            - Quick company identification
            """)
            
        with inst_col2:
            st.markdown("### 📁 Custom PDF Directory Mode") 
            st.markdown("""
            Use any collection of PDF files:
            - Browse your file system
            - Analyze documents from any source
            - Custom company naming
            """)

    # Display dossier if available
    if 'current_dossier' in st.session_state:
        st.markdown("---")
        st.markdown("## 📊 Generated Dossier")
        
        dossier = st.session_state.current_dossier
        
        # Download buttons
        download_col1, download_col2, download_col3 = st.columns([1, 1, 2])
        with download_col1:
            if 'dossier_paths' in st.session_state:
                with open(st.session_state.dossier_paths['json'], 'r') as f:
                    st.download_button(
                        "📥 Download JSON",
                        f.read(),
                        file_name=f"{dossier.company_name}_dossier.json",
                        mime="application/json"
                    )
        
        with download_col2:
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
        st.markdown("### 📋 Executive Summary")
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

if __name__ == "__main__":
    main()
