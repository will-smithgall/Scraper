from socket import timeout
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import sqlite3

file_name = "users.txt"
username_links = []

#This method gets all the lastfm links from the file
def parse_user(file):
    with open(file) as f:
        username_links = list(f)
        return(username_links)



#Takes the user portion from the url
def get_user(url):
    return url.rsplit("/", 1)[-1]



#This method gets both the number of scrobbles from the week, as well as the total listening hours
def total_listens(page, user):
    response = page.goto(
        "https://www.last.fm/user/" + user + "/listening-report", wait_until="domcontentloaded", timeout=0
    )

    if response.status == 404:
        raise Exception("Invalid username!")

    weekly_stats_all = page.query_selector_all("div.header-metadata-display")

    # weekly_stats is an array with entry 0 as total scrobbles, and entry 1 as total listening time
    weekly_stats = []
    weekly_stats.append(weekly_stats_all[0].inner_text())

    times = weekly_stats_all[2].inner_text().split(",")
    times_copy = weekly_stats_all[2].inner_text().split(",")
    hours = 0

    for t in times:
        sub_t = " ".join(t.split()).split(" ")

        if len(times_copy) == 1:
            if sub_t[1] == "day":
                hours = hours + (int(sub_t[0]) * 24)
            else:
                hours = hours + (int(sub_t[0]))
        elif len(times_copy) == 2:
            hours = int(int(sub_t[0])) * 24
            times_copy.remove(times_copy[0])
            
    weekly_stats.append(str(hours) + " hours")
    return weekly_stats



#Calculates average song length from total listens and total time
def ave_song_length(listens, time):
    scrobbles = listens.split(" ")
    time_split = time.split(" ")

    ave_min = (int(time_split[0]) * 60) / int(scrobbles[0])

    return str(round(ave_min, 2)) + " minutes"



#finds the users most popular song of the last week, as well as how many times they listened to it
#possible for the future -> grab album art somehow?
def top_song(page, user):
    #Do i need to check for 404 error here if i already did in the first method?
    #This method will be called after the method with checks, and since im calling it on the same users?

    page.goto("https://www.last.fm/user/" + user + "/library/tracks?date_preset=LAST_7_DAYS", timeout=0)
    
    #Grab first song name
    song = page.query_selector_all("td.chartlist-name")[0].inner_text()

    #Grab first artist name
    artist = page.query_selector_all("td.chartlist-artist")[0].inner_text()

    #Try to get amount of listens for that top song
    
    summary = song + " by " + artist

    return summary



def curr_week():
    
    day = datetime.now()
    curr_day = day.weekday()

    if (curr_day == 5):
        last_friday = (day.date() - timedelta(days=day.weekday()) + timedelta(days=4, weeks=-1))
    else:
        last_friday = (day.date() - timedelta(days=day.weekday()) + timedelta(days=4, weeks=-2))

    time = last_friday.strftime("%m/%d/%Y")

    return time

def sort_dict(dc):
    return dict(sorted(dc.items(), reverse=True))

def first_n_dict(dc, n):
    return dict(list(dc.items())[0:n])


u = parse_user("users.txt")
users = []

#Converts list of links to valid users
for link in u:
    users.append(get_user(link).rstrip())

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    all_users_stats = {}
    leaderboard_scrobbles = {}
    leaderboard_time = {}
    leaderboard_ave = {}

    #use first user in users to get the week, as it is the same for everyone
    #no need to calculate this value multiple times when it is constant
    this_week = curr_week()

    #For each user, go through and grab the statistics
    #Add them each to the dictionary all_user_stats, with the key being the user name
    #and the value being the list of associated statistics
    for user in users:
        stats = total_listens(page, user)
        popular_song = top_song(page, user)
        ave_song_len = ave_song_length(stats[0], stats[1])

        all_stats = []
        all_stats.append(user)
        all_stats.append(stats[1])
        all_stats.append(ave_song_len)
        all_stats.append(popular_song)
        all_stats.append(this_week)

        all_users_stats[stats[0]] = all_stats

        l_scrobbles = []
        l_scrobbles.append(user)
        leaderboard_scrobbles[stats[0]] = l_scrobbles

        l_time = []
        l_time.append(user)
        leaderboard_time[int(stats[1].split(" ")[0])] = l_time

        l_ave = []
        l_ave.append(user)
        leaderboard_ave[ave_song_len] = l_ave

    all_users_stats = sort_dict(all_users_stats)

    leaderboard_ave = sort_dict(leaderboard_ave)
    leaderboard_ave = first_n_dict(leaderboard_ave, 5)
    leaderboard_ave = list(leaderboard_ave.values())

    leaderboard_scrobbles = sort_dict(leaderboard_scrobbles)
    leaderboard_scrobbles = first_n_dict(leaderboard_scrobbles, 5)
    leaderboard_scrobbles = list(leaderboard_scrobbles.values())

    leaderboard_time = sort_dict(leaderboard_time)
    leaderboard_time = first_n_dict(leaderboard_time, 5)
    leaderboard_time = list(leaderboard_time.values())

    #close browser
    browser.close()

# SQLITE - - - -
def insert_db(week_of, name, total_scrobbles, listening_time, song_length, top_song):
    connection = sqlite3.connect("stats.db")
    cursor = connection.cursor()

    data = (week_of, name, total_scrobbles, listening_time, song_length, top_song)
    insert_data = """INSERT INTO scrobbles 
        (week_of, name, total_scrobbles, listening_time, song_length, top_song)
        VALUES (?, ?, ?, ?, ?, ?);"""
    
    cursor.execute(insert_data, data)
    connection.commit()

    cursor.close()

connection = sqlite3.connect("stats.db")
cursor = connection.cursor()

try:
    cursor.execute("CREATE TABLE scrobbles (week_of TEXT, name TEXT, total_scrobbles TEXT, listening_time TEXT, song_length TEXT, top_song TEXT)")

    for key, value in all_users_stats.items():
        insert_db(value[4], value[0], key, value[1], value[2], value[3])
except sqlite3.OperationalError as error:
    for key, value in all_users_stats.items():
        insert_db(value[4], value[0], key, value[1], value[2], value[3])