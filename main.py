import os
import sys
from dotenv import load_dotenv
from datetime import datetime
from requests import get
import pandas as pd

load_dotenv()

# dotenv stuff
NEYNAR_API_KEY = os.getenv("NEYNAR_API_KEY")
VIEWER_FID = os.getenv("VIEWER_FID")
FRAME_ID = os.getenv("FRAME_ID")
PARTY_ADDRESS = os.getenv("PARTY_ADDRESS")
DEGEN_ADDRESS = os.getenv("DEGEN_ADDRESS")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")


def get_timestamp(input) -> int:
    """return unix timestamp for a YYYY-MM-DD HH:MM:SS formatted input"""
    return int(datetime.strptime(input, "%Y-%m-%d %H:%M:%S").timestamp())


def get_wrapper(url, headers={}) -> dict:
    """wrapper for making get requests"""
    response = get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_frame_data() -> dict:
    """get frame data from Josh's API"""
    base_url = "https://api.sportscaster.xyz/epl/"
    url = base_url + FRAME_ID + "/frame_data.json"
    return get_wrapper(url)


def get_fid_info(fids) -> dict:
    """get farcaster information for fids from Neynar"""

    # Ensure strings
    fids = [str(fid) for fid in fids]

    # Prep URL
    headers = {"accept": "application/json", "api_key": NEYNAR_API_KEY}
    base_url = "https://api.neynar.com/v2/farcaster/user/bulk"
    url = base_url + "?fids=" + "%2C".join(fids) + "&viewer_fid=" + VIEWER_FID

    # Do it!
    return get_wrapper(url, headers)


def get_basescan(module, action, address, contract_address="") -> dict:
    """Interacts with basescan api"""
    params = {
        "module": module,
        "action": action,
        "address": address,
        "contractaddress": contract_address,
        "apikey": BASESCAN_API_KEY,
    }
    base_url = "https://api.basescan.org/api"
    url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items() if v])

    return get_wrapper(url)


# Grab frame data
frame_data = get_frame_data()
fids = [prediction["fid"] for prediction in frame_data]
predictions = {
    prediction["fid"]: f"{prediction['home-score']}-{prediction['away-score']}"
    for prediction in frame_data
}

# Get connected addresses for confirming contributions
fid_info = get_fid_info(fids)
eth_addresses = {
    user["fid"]: user["verified_addresses"]["eth_addresses"]
    for user in fid_info["users"]
}

# Manually do 10694, since chuk's addresses are not tracked in Warpcast...
eth_addresses[10694] = ["0x5d5d96abd337c830dc96a396f4ef32a2fdc3563d"]

# Grab contributions into pot from the last successful bet
transactions = get_basescan("account", "tokentx", PARTY_ADDRESS)
from_timestamp = get_timestamp("2024-04-20 00:00:00")  # El clasico
to_timestamp = get_timestamp("2024-04-28 14:00:00")  # To NLD start
degen_valid = {
    txn["from"]: txn["value"]
    for txn in transactions["result"]
    if txn["tokenSymbol"] == "DEGEN"
    and from_timestamp <= int(txn["timeStamp"]) <= to_timestamp
}
print(f"{len(degen_valid)} made contribution between from and to timestamps")

# Alright, so...
final = []
for fid in fids:
    if not eth_addresses[fid]:
        raise
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
print(f"{df[df.degen != 0].shape[0]} are eligible")

# And find the winners
FINAL_SCORE = "2-3"
df["contributed"] = df["degen"] != 0
df["winner"] = df["prediction"] == FINAL_SCORE
df.to_csv("./data/2024-04-28/output.csv", index=False)

# What about the payout?
result = get_basescan("account", "tokenbalance", PARTY_ADDRESS, DEGEN_ADDRESS)
degen_balance = result["result"]
print(f"Contract balance: {int(degen_balance) / 1e18:.2f} DEGEN")

# Everyone who contributed and got the score right gets a share of the pot
# share is equal (not pro-rata)
winners = df[df["winner"] & df["contributed"]]
num_winners = len(winners)

if num_winners == 0:
    print("No winners this time!")
    sys.exit()

share = int(degen_balance) // num_winners
winners["payout"] = share / 1e18  # friggin wei

# Save this result as 2024-04-07-united-liverpool.csv
winners.to_csv("./data/2024-04-28/winners.csv", index=False)
