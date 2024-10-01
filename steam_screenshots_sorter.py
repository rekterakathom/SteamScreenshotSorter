"""
Sorts a folder full of Steam screenshots into named folders
"""

import os
import argparse
import json
from functools import cache
import requests

# Parse arguments
parser = argparse.ArgumentParser("steam_screenshots_sorter")
parser.add_argument("screenshot_dir",
                    help="Screenshots directory (absolute OR relative path)",
                    type=str)
args = parser.parse_args()

appid_cache_path = os.path.join(args.screenshot_dir, "appid_cache.json")

# Runtime cache
appid_cache_dict = {}

# If the cache file exists, load it as the runtime cache
if os.path.isfile(appid_cache_path):
    with open(appid_cache_path, "rb") as appid_cache_file:
        appid_cache_dict = json.load(appid_cache_file)


@cache
def appid_to_string(appid: int):
    """
    Turns a Steam appid to game name.
    Uses a cache located in the screenshots dir as well as a memoize cache.

    Example: 440 -> Team Fortress 2
    """
    try:
        appid = int(appid) # Cast to int to verify that it's valid
    except ValueError:
        #print(f"Error AppID {appid} is not a valid AppId")
        return "Unknown"
    appid = str(appid) # Now that we know it's valid, turn it into a str

    if appid in appid_cache_dict:
        return appid_cache_dict[appid]

    app_request = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}",
                                timeout=10)

    if app_request.status_code == 200:
        request_json = app_request.json()
        if request_json[appid]["success"]:
            app_name = request_json[appid]["data"]["name"]
            appid_cache_dict[appid] = app_name
            return app_name

        print(f"AppId {appid} not found on Steam")
        return "Unknown"

    print(f"Steam API request failed with code {app_request.status_code}")
    return "Unknown"

@cache
def sanitize_appname(appname: str):
    """
    Sanitizes the appname so it can be used as a folder name.
    Sanitization happens according to Windows' rules.
    """
    bad_chars = '/\\:*?"<>|'
    for char in bad_chars:
        appname = appname.replace(char, "")
    return appname

def main():
    """
    Get appids for all screenshots in provided folder
    and sort them into named folders
    """
    print("Sorting start")
    for file in os.listdir(args.screenshot_dir):
        filepath = os.path.join(args.screenshot_dir, file)
        if not os.path.isfile(os.path.join(args.screenshot_dir, file)):
            continue
        if file == "appid_cache.json":
            continue

        appid = file.split("_")[0]

        print(f"Checking: {appid}")
        app_name = sanitize_appname(appid_to_string(appid))
        print(f"Result: {app_name}")

        if not os.path.isdir(args.screenshot_dir + f"/{app_name}"):
            os.mkdir(args.screenshot_dir + f"/{app_name}")

        os.replace(filepath, args.screenshot_dir + f"/{app_name}/{file}")

    print("Sorting complete. Saving appid_cache.json...")

    # Write everything that we know to the cache file
    with open(appid_cache_path, "w", -1, "utf-8") as appid_cache_file:
        json.dump(appid_cache_dict, appid_cache_file, indent = 4, sort_keys = True)


if __name__ == "__main__":
    main()
