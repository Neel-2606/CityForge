# NASA Earthdata Access Token Setup Guide

## 🔑 Using Your NASA Earthdata Access Token

If you have a NASA Earthdata access token, this is the **preferred method** for authentication as it often provides better access to datasets than username/password.

### Step 1: Add Token to .env File

Open your `.env` file and add your access token:

```bash
# NASA API Authentication - Option 2: Access Token (Preferred)
NASA_EARTHDATA_TOKEN=your_actual_access_token_here

# You can keep username/password as backup
NASA_EARTHDATA_USERNAME=your_username
NASA_EARTHDATA_PASSWORD=your_password
```

### Step 2: How the System Uses Your Token

The system will automatically:
1. **Check for token first** - If `NASA_EARTHDATA_TOKEN` is set, it uses token authentication
2. **Fall back to credentials** - If no token, it uses username/password
3. **Use synthetic data** - If neither works, it falls back to synthetic data

### Step 3: Test Your Token

Run the authentication test:
```bash
python test_earthaccess.py
```

Expected output:
```
🧪 Testing NASA Earthdata authentication...
🔑 Using NASA Earthdata access token
✅ NASA Earthdata authentication successful!
```

### Step 4: Run Full System Test

```bash
python test_system.py
```

Look for these log messages:
```
INFO:data_ingestion.real_nasa_apis:🔑 Using NASA Earthdata access token
INFO:earthaccess.auth:You're now authenticated with NASA Earthdata Login
```

### Step 5: Benefits of Token Authentication

✅ **Better Access**: Tokens often have broader dataset permissions
✅ **More Reliable**: Less likely to hit rate limits
✅ **Secure**: No password transmission
✅ **Long-lived**: Tokens typically last longer than session cookies

### Troubleshooting

**If you still get "No granules found":**

1. **Dataset Permissions**: Ensure your token has access to:
   - MODIS Land Products (MOD11A1)
   - Aura OMI datasets
   - LAADS DAAC collections

2. **Token Validity**: Check if your token is still valid at https://urs.earthdata.nasa.gov/

3. **Regional Coverage**: Some datasets may not cover Mumbai region

4. **Date Range**: The system now uses dates from 2+ weeks ago to account for processing delays

### System Behavior

- **With Token**: System attempts real NASA data download
- **Without Token**: Falls back to username/password
- **No Credentials**: Uses synthetic data (system still works perfectly)

Your Urban Resilience Dashboard will work regardless of data source!
