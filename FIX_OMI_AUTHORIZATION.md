# How to Fix OMI 403/401 Authorization Errors

## Problem
```
WARNING:⚠️  Direct download failed: 403 Client Error: Forbidden
WARNING:⚠️  Direct download failed: 401 Client Error: Unauthorized
ERROR:❌ Real OMI data fetch failed: No working OMI products found
```

## Root Cause
Your NASA Earthdata account needs explicit authorization to access **GES DISC** (Goddard Earth Sciences Data and Information Services Center) collections. Even with a valid Earthdata token, GES DISC requires separate approval.

---

## Solution (5-10 minutes)

### Step 1: Approve GES DISC Application
1. **Login** to NASA Earthdata:
   - Go to: https://urs.earthdata.nasa.gov
   - Use your existing credentials

2. **Approve GES DISC**:
   - Visit: https://disc.gsfc.nasa.gov/earthdata-login
   - OR go to "My Applications" in your Earthdata profile
   - Find "GES DISC DATA ACCESS" application
   - Click **"Approve"** or **"Authorize"**

### Step 2: Accept Collection EULAs
Visit each collection page and accept the terms:

1. **OMNO2 (NO2 Column Density)**:
   - URL: https://disc.gsfc.nasa.gov/datasets/OMNO2_003/summary
   - Click **"Accept"** or **"Agree to Terms"**

2. **OMSO2 (SO2 Column Density)**:
   - URL: https://disc.gsfc.nasa.gov/datasets/OMSO2_004/summary
   - Click **"Accept"** or **"Agree to Terms"**

3. **Optional - OMNO2d (Daily Gridded NO2)**:
   - URL: https://disc.gsfc.nasa.gov/datasets/OMNO2d_003/summary
   - This is a Level-3 product that's often easier to download
   - Click **"Accept"** or **"Agree to Terms"**

### Step 3: Refresh Your Session
1. **Log out** of NASA Earthdata
2. **Log back in**
3. Your token will now include GES DISC permissions

### Step 4: Verify It Works
Run your analysis:
```bash
python start.py analysis
```

**Expected output:**
```
INFO:🎉 Found 88 OMNO2 granules!
INFO:📁 Downloaded OMI file: OMI-Aura_L2-OMNO2_...he5
INFO:🎉 REAL OMI DATA LOADED! Variables: ['ColumnAmountNO2Trop', ...]
INFO:✅ Successfully ingested aura_omi data
INFO:Using real OMI air quality data
```

---

## Why This Happens

NASA Earthdata uses a **multi-tier authorization system**:

1. **EDL (Earthdata Login)**: Your account credentials
2. **DAAC Authorization**: Each Data Archive Center (DAAC) requires separate approval
3. **Collection EULA**: Individual datasets may have terms to accept

**GES DISC** is one of several DAACs. Others include:
- **LPDAAC** (Land Processes) - for MODIS, Landsat (already working ✅)
- **GES DISC** (Atmospheric) - for OMI, AIRS (needs approval ⚠️)
- **NSIDC** (Snow/Ice) - for ice/snow data
- **PO.DAAC** (Ocean) - for ocean data

---

## Alternative: Use Level-3 Gridded Data

If Level-2 swath data continues to fail, the code can be enhanced to use Level-3 daily gridded products:

- **OMNO2d**: Daily gridded NO2 (easier to download and process)
- **OMSO2e**: Daily gridded SO2

These are often more accessible and don't require swath-to-grid conversion.

---

## Current System Behavior

**Without OMI authorization:**
- ✅ System continues to work
- ✅ Uses synthetic air quality data
- ✅ Generates 72 air quality recommendations
- ✅ All other features work normally

**With OMI authorization:**
- ✅ Downloads real OMI satellite data
- ✅ Processes real NO2 and SO2 measurements
- ✅ Generates recommendations based on actual observations
- ✅ More accurate air quality scores

---

## Troubleshooting

### Still getting 403/401 after authorization?
1. **Clear browser cache** and log out/in again
2. **Wait 5-10 minutes** for permissions to propagate
3. **Regenerate your Earthdata token**:
   - Go to: https://urs.earthdata.nasa.gov/users/YOUR_USERNAME/user_tokens
   - Delete old token
   - Generate new token
   - Update `.env` file with new token

### How to check if authorization worked?
Try downloading a file manually:
```bash
wget --header="Authorization: Bearer YOUR_TOKEN" \
  "https://data.gesdisc.earthdata.nasa.gov/data/Aura_OMI_Level2/OMNO2.003/2025/253/OMI-Aura_L2-OMNO2_2025m0910t2239-o112550_v003-2025m0911t203900.he5"
```

If it downloads successfully, your authorization is working!

---

## Summary

1. ✅ **MODIS data**: Already working with real satellite temperatures
2. ⚠️ **OMI data**: Needs one-time GES DISC authorization
3. ✅ **System**: Fully operational with synthetic air quality fallback
4. 🎯 **Goal**: Complete authorization to use 100% real NASA data

**Estimated time to fix**: 5-10 minutes  
**Code changes needed**: None (system auto-detects when real data is available)
