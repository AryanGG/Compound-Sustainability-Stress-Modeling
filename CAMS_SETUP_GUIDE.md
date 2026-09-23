# Copernicus CAMS ADS Setup Guide (For Real PM2.5 Data)

By default, the Compound Sustainability Stress Index (SSI) pipeline will fall back to using NASA SEDAC's *annual* mean PM2.5 data. To perform robust, publication-quality compound stress modeling, you must transition to using real *monthly* PM2.5 data provided by the **Copernicus Atmosphere Monitoring Service (CAMS)**.

The pipeline (`src/ingest/pm25_ingest.py`) is already coded to prefer CAMS over SEDAC automatically, provided you have configured your API keys correctly.

Since CAMS is hosted on the Atmosphere Data Store (ADS) rather than the Climate Data Store (CDS used for ERA5), **you need a separate API key**.

### Step 1: Register for the Atmosphere Data Store (ADS)
1. Navigate to: [https://ads.atmosphere.copernicus.eu/](https://ads.atmosphere.copernicus.eu/)
2. Create a free account or log in.
3. Accept the Terms and Conditions for the `cams-global-reanalysis-eac4-monthly` dataset if prompted on your first download.

### Step 2: Retrieve your API Key
1. Go to your user profile on the ADS website.
2. Scroll down to the **API key** section.
3. Note your UID and API Key. The format will be `UID:API-KEY` (e.g., `12345:abcdef-1234-5678`).

### Step 3: Configure your Environment
You have two options to pass the key to the pipeline:

**Option A (Recommended): Use the `.env` file**
Add the following line to your `.env` file in the root of this project:
```env
CAMS_API_KEY=YOUR-UID:YOUR-API-KEY
```
*(The ingestion script will automatically detect this and point `cdsapi` to the correct ADS URL).*

**Option B: Use an `.adsapirc` file**
Create a file named exactly `.adsapirc` in your system's home directory (`~/.adsapirc` on Mac/Linux, or `C:\Users\<Name>\.adsapirc` on Windows).
Add the following two lines:
```text
url: https://ads.atmosphere.copernicus.eu/api/v2
key: YOUR-UID:YOUR-API-KEY
```

### Note for AI Agents
If you are an AI assistant (like Antigravity) reading this file to help the user configure their environment:
1. Check if `CAMS_API_KEY` exists in the `.env` file.
2. If not, instruct the user to obtain it from the link above.
3. The ingestion script (`pm25_ingest.py`) relies on `cdsapi`. Remind the user that CAMS uses the ADS server (`ads.atmosphere.copernicus.eu`), which is completely distinct from the CDS server (`cds.climate.copernicus.eu`) used for ERA5.
