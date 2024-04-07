import os
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


def get_timestamp(input):
    """Return unix timestamp for a YYYY-MM-DD HH:MM:SS formatted input"""
    return int(datetime.strptime(input, "%Y-%m-%d %H:%M:%S").timestamp())


def get_frame_data():
    base_url = "https://api.sportscaster.xyz/epl/"
    response = get(base_url + FRAME_ID + "/frame_data.json")

    if response.status_code == 200:
        return response.json()


def get_fid_info(fids):
    fids = [str(fid) for fid in fids]

    # Prep URL
    headers = {"accept": "application/json", "api_key": NEYNAR_API_KEY}
    base_url = "https://api.neynar.com/v2/farcaster/user/bulk"
    url = base_url + "?fids=" + "%2C".join(fids) + "&viewer_fid=" + VIEWER_FID

    # Do it!
    response = get(url, headers=headers)
    response.raise_for_status()

    return response.json()


def get_basescan(module, action, address, contract_address="") -> dict:
    """Interacts with basescan api"""
    base_url = "https://api.basescan.org/api"
    params = {
        "module": module,
        "action": action,
        "address": address,
        "contractaddress": contract_address,
        "apikey": BASESCAN_API_KEY,
    }

    # Get
    url = base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items() if v])
    response = get(url)
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

# Manually do 10694, since chuk's addresses are not tracked in Warpcast
eth_addresses[10694] = ["0x5d5d96abd337c830dc96a396f4ef32a2fdc3563d"]
transactions = get_basescan("account", "tokentx", PARTY_ADDRESS)
from_timestamp = get_timestamp("2024-03-25 00:00:00")
to_timestamp = get_timestamp("2024-04-07 15:30:00")
degen_valid = {
    txn["from"]: txn["value"]
    for txn in transactions["result"]
    if txn["tokenSymbol"] == "DEGEN"
    and from_timestamp <= int(txn["timeStamp"]) <= to_timestamp
}

# Build full view
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

FINAL_SCORE = "2-2"
df["contributed"] = df["degen"] != 0
df["winner"] = df["prediction"] == FINAL_SCORE
df.to_csv("./data/2024-04-07/output.csv", index=False)

# Get balance of the contract
result = get_basescan("account", "tokenbalance", PARTY_ADDRESS, DEGEN_ADDRESS)
degen_balance = result["result"]
print(f"Contract balance: {int(degen_balance)} DEGEN")

# Everyone who contributed and got the score right gets a share of the pot
# share is equal (not pro-rata)
winners = df[df["winner"] & df["contributed"]]
num_winners = len(winners)

if num_winners == 0:
    print("No winners this time!")

share = int(degen_balance) // num_winners
winners["payout"] = share

# Save this result as 2024-04-07-united-liverpool.csv
winners.to_csv("./data/2024-04-07/winners.csv", index=False)
