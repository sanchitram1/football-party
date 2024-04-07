# football pot

an experiment in betting via the football channel on warpcast. 

## Purpose

uses the frame API, Neynar, and basescan to retrieve:

- who predicted what
- how much DEGEN they sent

## Data (redundant now)

raw files come from:

- [gist](https://gist.github.com/joshuamiller/f64969760aad0e1365e76867f1295ac4) for who bet from the prediction frame
- [erc20 token transfers](https://basescan.org/exportData?type=addresstokentxns&a=0x917cD75e2009E6193eEc3b23Cc89cF0cd59a28Ed) for the football party
- [eth token transfers](https://basescan.org/address/0x917cD75e2009E6193eEc3b23Cc89cF0cd59a28Ed) for the football party (not used so far)

## Usage

`python main.py`

## Improvements

- add predictions to the frame
- add winner
- make this a frame