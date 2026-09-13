import os
import requests

def test_download():
    # Setup .netrc
    netrc_content = f"machine urs.earthdata.nasa.gov\nlogin yashbadhe\npassword yash2005@nasawala\n"
    with open(os.path.expanduser("~/.netrc"), "w") as f:
        f.write(netrc_content)
    os.chmod(os.path.expanduser("~/.netrc"), 0o600)
    
    url = "https://sedac.ciesin.columbia.edu/downloads/data/sdei/sdei-global-annual-avg-pm2-5-modvrs-2001-2022/sdei-global-annual-avg-pm2-5-modvrs-2001-2022-2022-geotiff.zip"
    
    # Needs to handle EarthData redirects with cookies
    session = requests.Session()
    # EarthData redirect auth handling
    def get_data(url):
        response = session.get(url, stream=True)
        if response.status_code == 401:
            print("401 Unauthorized")
            return response
        return response
        
    print(f"Fetching {url}")
    resp = get_data(url)
    print("Status:", resp.status_code)
    print("Headers:", resp.headers)
    if resp.status_code == 200:
        print("Success! Size:", resp.headers.get("Content-Length"))

if __name__ == "__main__":
    test_download()
