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

## SQLite DataBase File

The file ```lastfm.py``` will output a .db file called ```stats.db```. This file will contain the information of the most recent week's last.fm data.

This data will look like this

| week_of | name | total_scrobbles | listening_time | song_length | top_song |
| --- | --- | --- | --- | --- | --- |
| week one | user one | entry one | entry one | entry one | entry one |
| week one | user two | entry two | entry two | entry two | entry two |
| ... | ... | ... | ... | ... | ... |

Each time ```lastfm.py``` is run, it will add the next weeks data onto the pre-existing database, where ```week_of``` will be the next week

## Future
1. In the highest_song() method, get the number of listens for the top song
2. When adding data to the SQLite database, add them in pre-sorted order, such that each seperate week will have the user with the top scrobbles at the top (for that week), and then decrementing downwards.