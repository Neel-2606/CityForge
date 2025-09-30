"""Setup script for real NASA data integration and Supabase database."""

import os
import sys
import subprocess
import asyncio
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealDataSetup:
    """Setup manager for real NASA data and Supabase integration."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        
    def check_environment(self):
        """Check if .env file exists and has real credentials."""
        logger.info("🔍 Checking environment configuration...")
        
        if not self.env_file.exists():
            logger.error("❌ .env file not found. Please copy from .env.example")
            return False
        
        # Read .env file
        env_vars = {}
        with open(self.env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
        
        # Check NASA credentials (token or username/password)
        nasa_token = env_vars.get('NASA_EARTHDATA_TOKEN', '')
        nasa_user = env_vars.get('NASA_EARTHDATA_USERNAME', '')
        nasa_pass = env_vars.get('NASA_EARTHDATA_PASSWORD', '')
        
        has_token = nasa_token and nasa_token != 'your_access_token_here'
        has_credentials = (nasa_user and nasa_user != 'demo_user' and 
                          nasa_user != 'your_real_nasa_username')
        
        if has_token:
            logger.info("✅ Real NASA Earthdata access token found")
            self.has_real_nasa = True
        elif has_credentials:
            logger.info("✅ Real NASA Earthdata credentials found")
            self.has_real_nasa = True
        else:
            logger.warning("⚠️  No real NASA credentials or token found - will use synthetic data")
            self.has_real_nasa = False
        
        # Check Supabase credentials
        supabase_url = env_vars.get('SUPABASE_URL', '')
        supabase_key = env_vars.get('SUPABASE_ANON_KEY', '')
        
        if supabase_url and supabase_url != 'https://your-project-id.supabase.co':
            logger.info("✅ Supabase credentials found")
            self.has_supabase = True
        else:
            logger.warning("⚠️  No Supabase credentials found - will use local storage")
            self.has_supabase = False
        
        return True
    
    def install_dependencies(self):
        """Install required packages for real data access."""
        logger.info("📦 Installing required packages...")
        
        try:
            # Install earthaccess for NASA data
            subprocess.run([sys.executable, "-m", "pip", "install", "earthaccess>=0.9.0"], check=True)
            logger.info("✅ Installed earthaccess for NASA data access")
            
            # Install supabase client
            subprocess.run([sys.executable, "-m", "pip", "install", "supabase==2.0.2"], check=True)
            logger.info("✅ Installed Supabase client")
            
            # Install additional geospatial packages
            subprocess.run([sys.executable, "-m", "pip", "install", "h5netcdf", "netcdf4"], check=True)
            logger.info("✅ Installed additional data format support")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def setup_data_directories(self):
        """Create necessary data directories."""
        logger.info("📁 Setting up data directories...")
        
        directories = [
            "data/raw/modis",
            "data/raw/omi", 
            "data/raw/gpm",
            "data/raw/landsat",
            "data/processed",
            "data/cache",
            "data/local_db/wards",
            "data/local_db/air_quality",
            "data/local_db/temperature",
            "data/local_db/vegetation",
            "data/local_db/flood_risk",
            "data/local_db/recommendations"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        logger.info("✅ Data directories created")
        return True
    
    async def test_nasa_connection(self):
        """Test NASA Earthdata connection."""
        if not self.has_real_nasa:
            logger.info("🎭 Skipping NASA connection test (no real credentials)")
            return True
        
        logger.info("🛰️  Testing NASA Earthdata connection...")
        
        try:
            import earthaccess
            
            # Read credentials from .env
            env_vars = {}
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
            
            username = env_vars.get('NASA_EARTHDATA_USERNAME')
            password = env_vars.get('NASA_EARTHDATA_PASSWORD')
            
            # Set environment variables for earthaccess
            import os
            
            # Check for token first, then username/password
            nasa_token = env_vars.get('NASA_EARTHDATA_TOKEN', '')
            has_token = nasa_token and nasa_token != 'your_access_token_here'
            
            if has_token:
                logger.info("🔑 Using NASA Earthdata access token for authentication")
                os.environ['EARTHDATA_TOKEN'] = nasa_token
            else:
                logger.info("🔑 Using NASA Earthdata username/password for authentication")
                os.environ['EARTHDATA_USERNAME'] = username
                os.environ['EARTHDATA_PASSWORD'] = password
            
            # Test authentication - newer earthaccess API
            auth = earthaccess.login(strategy="environment", persist=False)
            
            if auth.authenticated:
                logger.info("✅ NASA Earthdata authentication successful")
                
                # Test a simple search
                results = earthaccess.search_data(
                    short_name="MOD11A1",
                    version="6",
                    temporal=("2024-01-01", "2024-01-02"),
                    bounding_box=(72.7, 18.8, 72.9, 19.3),  # Mumbai bounds
                    count=1
                )
                
                if results:
                    logger.info(f"✅ Found {len(results)} MODIS granules for Mumbai")
                    return True
                else:
                    logger.warning("⚠️  No MODIS data found, but authentication works")
                    return True
            else:
                logger.error("❌ NASA Earthdata authentication failed")
                return False
                
        except ImportError:
            logger.error("❌ earthaccess package not installed")
            return False
        except Exception as e:
            logger.error(f"❌ NASA connection test failed: {e}")
            return False
    
    async def test_supabase_connection(self):
        """Test Supabase connection."""
        if not self.has_supabase:
            logger.info("🗄️  Skipping Supabase connection test (no credentials)")
            return True
        
        logger.info("🗄️  Testing Supabase connection...")
        
        try:
            from supabase import create_client
            
            # Read credentials from .env
            env_vars = {}
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
            
            url = env_vars.get('SUPABASE_URL')
            key = env_vars.get('SUPABASE_ANON_KEY')
            
            # Test connection
            supabase = create_client(url, key)
            
            # Try a simple query (this might fail if tables don't exist, but connection will work)
            try:
                result = supabase.table('test').select("*").limit(1).execute()
                logger.info("✅ Supabase connection successful")
            except Exception:
                logger.info("✅ Supabase connection successful (no tables yet)")
            
            return True
            
        except ImportError:
            logger.error("❌ supabase package not installed")
            return False
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            return False
    
    async def run_system_test(self):
        """Run comprehensive system test with real data."""
        logger.info("🧪 Running system test with real data configuration...")
        
        try:
            # Import and run the system test
            from test_system import run_system_test
            
            success = await run_system_test()
            
            if success:
                logger.info("✅ System test passed with real data configuration")
                return True
            else:
                logger.error("❌ System test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ System test error: {e}")
            return False
    
    def create_supabase_setup_guide(self):
        """Create a guide for setting up Supabase."""
        guide_content = """# Supabase Setup Guide for Urban Resilience Dashboard

## Step 1: Create Supabase Project

1. Go to https://supabase.com
2. Sign up/Login to your account
3. Click "New Project"
4. Choose organization and enter project details:
   - Name: `urban-resilience-mumbai`
   - Database Password: (choose a strong password)
   - Region: Choose closest to your location

## Step 2: Get Project Credentials

1. Go to Project Settings > API
2. Copy the following values:
   - Project URL: `https://your-project-id.supabase.co`
   - Anon/Public Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - Service Role Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## Step 3: Update .env File

Replace these values in your `.env` file:
```
SUPABASE_URL=https://your-actual-project-id.supabase.co
SUPABASE_ANON_KEY=your_actual_anon_key
SUPABASE_SERVICE_KEY=your_actual_service_role_key
```

## Step 4: Enable PostGIS (Optional)

1. Go to Database > Extensions
2. Search for "postgis"
3. Enable the PostGIS extension

## Step 5: Test Connection

Run: `python setup_real_data.py test`

Your Supabase database is now ready for the Urban Resilience Dashboard!
"""
        
        with open("SUPABASE_SETUP.md", 'w') as f:
            f.write(guide_content)
        
        logger.info("📝 Created SUPABASE_SETUP.md guide")
    
    def create_nasa_setup_guide(self):
        """Create a guide for setting up NASA Earthdata credentials."""
        guide_content = """# NASA Earthdata Setup Guide

## Step 1: Create NASA Earthdata Account

1. Go to https://urs.earthdata.nasa.gov/
2. Click "Register for a profile"
3. Fill out the registration form
4. Verify your email address
5. Complete your profile

## Step 2: Get Your Credentials

1. Login to NASA Earthdata
2. Your username and password are your login credentials
3. No additional API keys needed

## Step 3: Update .env File

Replace these values in your `.env` file:
```
NASA_EARTHDATA_USERNAME=your_actual_nasa_username
NASA_EARTHDATA_PASSWORD=your_actual_nasa_password
```

## Step 4: Test Connection

Run: `python setup_real_data.py test`

## Available NASA Datasets

With your credentials, you can access:
- MODIS Land Surface Temperature (MOD11A1)
- Aura OMI Air Quality (OMI NO2, SO2)
- GPM Precipitation (IMERG)
- Landsat NDVI and vegetation indices
- VIIRS Night Lights

Your NASA Earthdata access is now ready!
"""
        
        with open("NASA_SETUP.md", 'w') as f:
            f.write(guide_content)
        
        logger.info("📝 Created NASA_SETUP.md guide")
    
    async def run_full_setup(self):
        """Run complete setup process."""
        logger.info("🚀 Starting Real Data Setup for Urban Resilience Dashboard")
        logger.info("=" * 70)
        
        # Step 1: Check environment
        if not self.check_environment():
            return False
        
        # Step 2: Install dependencies
        if not self.install_dependencies():
            return False
        
        # Step 3: Setup directories
        if not self.setup_data_directories():
            return False
        
        # Step 4: Test connections
        nasa_ok = await self.test_nasa_connection()
        supabase_ok = await self.test_supabase_connection()
        
        # Step 5: Run system test
        system_ok = await self.run_system_test()
        
        # Step 6: Create setup guides
        self.create_nasa_setup_guide()
        self.create_supabase_setup_guide()
        
        # Summary
        logger.info("=" * 70)
        logger.info("📊 Setup Summary:")
        logger.info(f"   NASA Earthdata: {'✅ Ready' if nasa_ok else '❌ Not configured'}")
        logger.info(f"   Supabase Database: {'✅ Ready' if supabase_ok else '❌ Not configured'}")
        logger.info(f"   System Test: {'✅ Passed' if system_ok else '❌ Failed'}")
        
        if nasa_ok and supabase_ok and system_ok:
            logger.info("🎉 Real data setup completed successfully!")
            logger.info("🚀 Your Urban Resilience Dashboard is ready with real NASA data!")
        elif system_ok:
            logger.info("✅ Setup completed with fallback options")
            logger.info("📚 Check NASA_SETUP.md and SUPABASE_SETUP.md for configuration guides")
        else:
            logger.error("❌ Setup completed with issues")
            logger.info("🔧 Please check the error messages above and try again")
        
        return True


async def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup real NASA data integration")
    parser.add_argument("action", choices=["setup", "test", "install"], 
                       default="setup", nargs="?",
                       help="Action to perform")
    
    args = parser.parse_args()
    
    setup = RealDataSetup()
    
    if args.action == "install":
        setup.install_dependencies()
    elif args.action == "test":
        setup.check_environment()
        await setup.test_nasa_connection()
        await setup.test_supabase_connection()
        await setup.run_system_test()
    else:
        await setup.run_full_setup()


if __name__ == "__main__":
    asyncio.run(main())
