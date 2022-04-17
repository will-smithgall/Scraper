# Scraper

This will be used as a tool to keep track of information among friends such as total scrobbles, amount of scrobbles per week, average song length, etc..

## Getting started

1. Clone the repo
2. Install requirements:

```sh
pip install -r requirements.txt
```

## Users File

The text file ```users.txt``` should be filled with links to users last.fm profiles
For example:

```sh
https://www.last.fm/user/user1
https://www.last.fm/user/user2
```

These are the users the program will attain the data from

## Future
1. In the highest_song() method, get the number of listens for the top song
2. Sort output data by their associated keys (usernames)