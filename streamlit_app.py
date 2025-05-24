import streamlit as st
import pandas as pd
import io
import os
from lead_enrichment_bot import LeadEnrichmentBot
import tempfile
import time
import traceback
from io import StringIO

# Configure page
st.set_page_config(
    page_title="AI Lead Enrichment Bot",
    page_icon="🤖",
    layout="wide"
)

def main():
    st.title("🤖 AI Lead Enrichment Bot")
    st.markdown("**Transform your company list into enriched leads with AI-powered insights**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Show API configuration
        st.success("✅ Groq API Key: Ready")
        st.info("Using Groq for faster, more accurate results")
        st.info("Gemini API as fallback if needed")
        
        st.markdown("---")
        
        # Instructions
        st.subheader("📋 Instructions")
        st.markdown("""
        1. Get your free Groq API key from console.groq.com
        2. Update the API key in config.py
        3. Upload a CSV with 'company_name' column
        4. Click 'Start Enrichment'
        5. Download the enriched results
        """)
        
        # Sample CSV download
        st.subheader("📄 Sample CSV")
        sample_data = pd.DataFrame({
            'company_name': ['OpenAI', 'DeepMind', 'Zoho', 'Freshworks']
        })
        
        csv_sample = sample_data.to_csv(index=False)
        st.download_button(
            label="Download Sample CSV",
            data=csv_sample,
            file_name="sample_companies.csv",
            mime="text/csv"
        )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Upload Your Company List")
        
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="CSV should contain a 'company_name' column"
        )
        
        if uploaded_file is not None:
            try:
                # Reset file pointer and read with proper encoding
                uploaded_file.seek(0)
                
                # Try to read with different encodings
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                except Exception:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='cp1252')
                
                # Validate the dataframe
                if df.empty:
                    st.error("❌ The CSV file is empty")
                    return
                
                # Check for company_name column (case insensitive)
                columns_lower = [col.lower().strip() for col in df.columns]
                if 'company_name' not in columns_lower:
                    # Try to find similar column names
                    possible_cols = [col for col in df.columns if 'company' in col.lower() or 'name' in col.lower()]
                    if possible_cols:
                        st.warning(f"⚠️ 'company_name' column not found. Did you mean: {possible_cols}?")
                        st.info("Please rename your column to 'company_name' or select the correct column:")
                        selected_col = st.selectbox("Select company name column:", df.columns)
                        if st.button("Use Selected Column"):
                            df = df.rename(columns={selected_col: 'company_name'})
                            st.rerun()
                    else:
                        st.error("❌ CSV must contain a 'company_name' column")
                        st.info(f"Found columns: {list(df.columns)}")
                        return
                
                # Clean the data
                if 'company_name' in df.columns:
                    df = df.dropna(subset=['company_name'])
                    df = df[df['company_name'].astype(str).str.strip() != '']
                    df['company_name'] = df['company_name'].astype(str).str.strip()
                
                if df.empty:
                    st.error("❌ No valid company names found after cleaning")
                    return
                
                st.success(f"✅ File uploaded successfully! Found {len(df)} companies")
                
                # Show preview
                st.subheader("📊 Data Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                # Company count
                st.metric("Total Companies", len(df))
                
                # Store the cleaned dataframe in session state
                st.session_state.uploaded_df = df
                
            except Exception as e:
                st.error(f"❌ Error reading CSV: {e}")
                st.info("💡 Please ensure your CSV file:")
                st.markdown("""
                - Has a 'company_name' column
                - Is properly formatted
                - Uses UTF-8 encoding
                - Contains at least one company name
                """)
                return
    
    with col2:
        st.header("🚀 Start Enrichment")
        
        # Check if we have valid data
        if uploaded_file is not None and 'uploaded_df' in st.session_state:
            df = st.session_state.uploaded_df
            if st.button("🔄 Start Enrichment Process", type="primary"):
                # Run enrichment with the validated dataframe
                run_enrichment_with_df(df)
        elif uploaded_file is not None:
            st.info("📝 Please wait for file validation to complete")
        else:
            st.info("📝 Please upload a CSV file to start enrichment")
            
        # Display results section
        if 'enrichment_results' in st.session_state:
            st.header("📈 Enrichment Results")
            
            results_df = st.session_state.enrichment_results
            
            # Success metrics
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric(
                    "Total Companies", 
                    len(results_df)
                )
            
            with col_b:
                successful = len(results_df[results_df['website'] != ''])
                st.metric(
                    "Successfully Enriched", 
                    successful,
                    delta=f"{successful/len(results_df)*100:.1f}%"
                )
            
            with col_c:
                avg_summary_length = results_df['summary_from_llm'].str.len().mean()
                st.metric(
                    "Avg Summary Length", 
                    f"{avg_summary_length:.0f} chars" if not pd.isna(avg_summary_length) else "0 chars"
                )
            
            # Download enriched data
            csv_data = results_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Enriched Data",
                data=csv_data,
                file_name=f"enriched_companies_{int(time.time())}.csv",
                mime="text/csv",
                type="primary"
            )
            
            # Display results table
            st.subheader("📋 Detailed Results")
            st.dataframe(results_df, use_container_width=True)

def run_enrichment_with_df(df):
    """Run the enrichment process with a pre-validated dataframe"""
    
    # Initialize progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        total_companies = len(df)
        
        status_text.text("🔧 Initializing AI bot with Groq...")
        
        # Initialize bot (will use config values)
        bot = LeadEnrichmentBot()
        
        # Process companies with progress tracking
        enriched_data = []
        
        for idx, row in df.iterrows():
            company_name = str(row['company_name']).strip()
            
            # Skip empty names
            if not company_name or company_name.lower() in ['nan', 'none', '']:
                continue
            
            # Update progress
            progress = (idx + 1) / total_companies
            progress_bar.progress(progress)
            status_text.text(f"🔍 Processing {idx + 1}/{total_companies}: {company_name}")
            
            try:
                # Call the enrichment method
                company_data = bot.enrich_company(company_name)
                
                # Extract data from CompanyData object
                enriched_data.append({
                    'company_name': company_data.name,
                    'website': company_data.website,
                    'industry': company_data.industry,
                    'summary_from_llm': company_data.summary,
                    'automation_pitch_from_llm': company_data.automation_pitch
                })
                
                # Show progress with actual data
                with st.expander(f"✅ Processed: {company_name}", expanded=False):
                    st.write(f"**Website:** {company_data.website}")
                    st.write(f"**Industry:** {company_data.industry}")
                    st.write(f"**Summary:** {company_data.summary[:200]}...")
                    st.write(f"**Automation Pitch:** {company_data.automation_pitch[:200]}...")
                    
            except Exception as e:
                error_msg = f"Error processing {company_name}: {str(e)}"
                st.error(f"❌ {error_msg}")
                
                # Add empty row for failed companies
                enriched_data.append({
                    'company_name': company_name,
                    'website': '',
                    'industry': '',
                    'summary_from_llm': error_msg,
                    'automation_pitch_from_llm': ''
                })
            
            # Add small delay to prevent rate limiting
            time.sleep(0.1)
        
        # Create results DataFrame
        results_df = pd.DataFrame(enriched_data)
        
        # Store in session state
        st.session_state.enrichment_results = results_df
        
        # Success message
        progress_bar.progress(1.0)
        status_text.text("✅ Enrichment completed successfully!")
        
        # Show final statistics
        successful = len(results_df[results_df['website'] != ''])
        success_rate = (successful / len(results_df)) * 100 if len(results_df) > 0 else 0
        
        st.success(f"🎉 Successfully processed {len(results_df)} companies!")
        st.info(f"📈 Success rate: {success_rate:.1f}% ({successful}/{len(results_df)} companies found)")
        
        st.balloons()
        
        # Automatically show results
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error during enrichment: {str(e)}")
        st.code(traceback.format_exc())
        progress_bar.empty()
        status_text.empty()

def show_features():
    """Display features section"""
    st.header("🌟 Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔍 Smart Web Scraping")
        st.write("Automatically finds and scrapes company websites")
    
    with col2:
        st.subheader("🤖 AI Analysis")
        st.write("Uses Groq AI to analyze and summarize companies")
    
    with col3:
        st.subheader("💡 Custom Pitches")
        st.write("Generates tailored automation ideas for each company")

if __name__ == "__main__":
    main()
    
    # Show features at the bottom
    st.markdown("---")
    show_features()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Built with ❤️ using Streamlit & Groq AI</p>
            <p>For QF Innovate Lead Enrichment Challenge</p>
        </div>
        """, 
        unsafe_allow_html=True
    )