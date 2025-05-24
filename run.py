#!/usr/bin/env python3
"""
Quick start script for the Lead Enrichment Bot
"""
import sys
import os
import argparse
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        'pandas', 'requests', 'beautifulsoup4', 'streamlit'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            # Handle package name differences
            if package == 'beautifulsoup4':
                try:
                    import bs4
                except ImportError:
                    missing_packages.append(package)
            else:
                missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_api_key():
    """Check if Gemini API key is configured"""
    # API key is now hardcoded in the application
    print("✅ Gemini API key is hardcoded in the application")
    return True

def create_sample_csv():
    """Create a sample input CSV if it doesn't exist"""
    sample_file = "sample_companies.csv"
    if not Path(sample_file).exists():
        sample_data = """company_name
OpenAI
DeepMind
Zoho
Freshworks
Stripe"""
        
        with open(sample_file, 'w') as f:
            f.write(sample_data)
        
        print(f"📄 Created sample CSV: {sample_file}")
        return sample_file
    
    return sample_file

def run_cli_mode(input_file, output_file):
    """Run the bot in CLI mode"""
    try:
        from lead_enrichment_bot import LeadEnrichmentBot
        
        print(f"🚀 Starting enrichment process...")
        print(f"📂 Input file: {input_file}")
        print(f"📂 Output file: {output_file}")
        
        # Initialize bot with hardcoded API key
        bot = LeadEnrichmentBot()
        
        # Process CSV
        result_df = bot.process_csv(input_file, output_file)
        
        print(f"\n✅ Enrichment completed!")
        print(f"📊 Processed {len(result_df)} companies")
        print(f"💾 Results saved to: {output_file}")
        
        # Show summary
        successful = len(result_df[result_df['website'] != ''])
        print(f"🎯 Success rate: {successful}/{len(result_df)} ({successful/len(result_df)*100:.1f}%)")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure lead_enrichment_bot.py is in the same directory")
    except Exception as e:
        print(f"❌ Error during processing: {e}")

def run_streamlit_mode():
    """Run the Streamlit web interface"""
    try:
        import streamlit.web.cli as stcli
        import sys
        
        print("🌐 Starting Streamlit web interface...")
        print("📱 The app will open in your browser automatically")
        print("🔧 Use Ctrl+C to stop the server")
        
        sys.argv = ["streamlit", "run", "streamlit_app.py"]
        sys.exit(stcli.main())
        
    except ImportError:
        print("❌ Streamlit not found")
        print("📦 Install with: pip install streamlit")
    except FileNotFoundError:
        print("❌ streamlit_app.py not found")
        print("💡 Make sure streamlit_app.py is in the same directory")

def main():
    parser = argparse.ArgumentParser(
        description="AI Lead Enrichment Bot - Transform company lists into enriched leads"
    )
    
    parser.add_argument(
        '--mode', 
        choices=['cli', 'web'], 
        default='web',
        help='Run mode: cli for command line, web for Streamlit interface'
    )
    
    parser.add_argument(
        '--input', 
        default='sample_companies.csv',
        help='Input CSV file (CLI mode only)'
    )
    
    parser.add_argument(
        '--output', 
        default='enriched_companies.csv',
        help='Output CSV file (CLI mode only)'
    )
    
    parser.add_argument(
        '--setup-only', 
        action='store_true',
        help='Only check setup and create sample files'
    )
    
    args = parser.parse_args()
    
    print("🤖 AI Lead Enrichment Bot")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Create sample CSV
    sample_file = create_sample_csv()
    
    if args.setup_only:
        print("✅ Setup complete!")
        print(f"📄 Sample file: {sample_file}")
        print("🔑 Don't forget to set your GEMINI_API_KEY!")
        return 0
    
    # Check API key for actual processing
    if not check_api_key():
        print("\n💡 Run with --setup-only to just create sample files")
        return 1
    
    # Run in selected mode
    if args.mode == 'cli':
        run_cli_mode(args.input, args.output)
    else:
        run_streamlit_mode()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())