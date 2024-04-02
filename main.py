import json
import pandas as pd

# Read the JSON file
with open("predictions.json", "r") as json_file:
    predictions = json.load(json_file)

# Create a DataFrame from the JSON data
betters = pd.DataFrame(predictions)

# explode the eth column, so that each element in the list is a new row
betters = betters.explode("eth")

print("betters: ", betters.shape)

# Read in the football_party_erc20_transfers.csv
football_party_erc20_transfers = pd.read_csv("football_party_erc20_transfers.csv")
print("football_party_erc20_transfers: ", football_party_erc20_transfers.shape)

# make df which is the football_party.From, TokenSymbol, TokenValue and betters.username, and eth
df = pd.merge(football_party_erc20_transfers, betters, left_on="From", right_on="eth")
df = df[["From", "TokenSymbol", "TokenValue", "username"]]
print(df.shape)

# aggregate on From
df = (
    df.groupby(["From", "TokenSymbol"])
    .agg({"TokenValue": "sum", "username": "first"})
    .reset_index()
)
