import planetary_computer as pc
import pystac_client
import stackstac
import xarray as xr

bbox_list = [72.75, 18.87, 73.10, 19.28] # Mumbai approx
catalog = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
search = catalog.search(collections=["modis-11A2-061"], bbox=bbox_list, datetime="2020-01-01/2020-01-31")
items = list(search.item_collection())
print("Items found:", len(items))

stack = stackstac.stack(items, assets=["LST_Day_1km"], bounds_latlon=bbox_list, resolution=0.01, dtype="float64", rescale=False, epsg=4326)
print(stack)
lst_k = stack.sel(band="LST_Day_1km").median(dim="time", skipna=True)
print("Median computed")
lst_c = lst_k * 0.02 - 273.15
print("NaN count:", lst_c.isnull().sum().compute().item())
print("Total elements:", lst_c.size)
