# football pot

an experiment in betting via the football channel on warpcast. 

## Purpose

uses the frame API, Neynar, and basescan to retrieve:

- who predicted what
- how much DEGEN they sent

> We only consider $DEGEN right now. ETH transfers, such as the one yours truly sent are irrelevant. 

## Usage

`python main.py`

dumps out the `output.csv`

> Note that `contributed` is ideally how we'd track whether someone is eligible. But since, the scope of this one is the last two rounds, it's a bit more complicated (gotta track who contributed last round as well).

## Improvements

- add predictions to the frame
- make this a frame