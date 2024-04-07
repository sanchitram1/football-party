import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import pandas as pd

load_dotenv()

# dotenv stuff
NEYNAR_API_KEY = os.getenv("NEYNAR_API_KEY")
VIEWER_FID = os.getenv("VIEWER_FID")
FRAME_ID = os.getenv("FRAME_ID")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")


def get_timestamp(input):
    """Return unix timestamp for a YYYY-MM-DD HH:MM:SS formatted input"""
    return int(datetime.strptime(input, "%Y-%m-%d %H:%M:%S").timestamp())


def get_frame_data():
    base_url = "https://api.sportscaster.xyz/epl/"
    response = requests.get(base_url + FRAME_ID + "/frame_data.json")

    if response.status_code == 200:
        return response.json()


def get_fid_info(fids):
    fids = [str(fid) for fid in fids]

    # Prep URL
    headers = {"accept": "application/json", "api_key": NEYNAR_API_KEY}
    base_url = "https://api.neynar.com/v2/farcaster/user/bulk"
    url = base_url + "?fids=" + "%2C".join(fids) + "&viewer_fid=" + VIEWER_FID

    # Do it!
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def get_transactions(contract_address):
    base_url = "https://api.basescan.org/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "address": contract_address,
        # "page": 1,
        # "offset": 10,
        # "sort": "desc",
        "apikey": BASESCAN_API_KEY,
    }
    url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    response = requests.get(url)

    response.raise_for_status()
    return response.json()


frame_data = get_frame_data()
fids = [prediction["fid"] for prediction in frame_data]
predictions = {
    prediction["fid"]: f"{prediction['home-score']}-{prediction['away-score']}"
    for prediction in frame_data
}

fid_info = get_fid_info(fids)
eth_addresses = {
    user["fid"]: user["verified_addresses"]["eth_addresses"]
    for user in fid_info["users"]
}

transactions = get_transactions(CONTRACT_ADDRESS)
from_timestamp = get_timestamp("2024-03-25 00:00:00")
to_timestamp = get_timestamp("2024-04-07 12:00:00")
degen_valid = {
    txn["from"]: txn["value"]
    for txn in transactions["result"]
    if txn["tokenSymbol"] == "DEGEN"
    and from_timestamp <= int(txn["timeStamp"]) <= to_timestamp
}

final = []

for fid in fids:
    if not eth_addresses[fid]:
        final.append(
            {
                "fid": fid,
                "username": fid_info["users"][fids.index(fid)]["username"],
                "prediction": predictions[fid],
                "address": None,
                "degen": 0,
            }
        )
    for address in eth_addresses[fid]:
        final.append(
            {
                "fid": fid,
                "username": fid_info["users"][fids.index(fid)]["username"],
                "prediction": predictions[fid],
                "address": address,
                "degen": degen_valid.get(address, 0),
            }
        )

df = pd.DataFrame(final)

FINAL_SCORE = "2-2"
df["contributed"] = (
    df["degen"] != 0
)  # ideally, but we have last time's pot to consider as well
df["winner"] = df["prediction"] == FINAL_SCORE

df.to_csv("output.csv", index=False)
