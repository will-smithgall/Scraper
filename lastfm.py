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

    # check if any music has been listened to
    if len(weekly_stats_all) == 0:
        weekly_stats.append(0)
        weekly_stats.append("0 Hours")
    else:
        weekly_stats.append(int(weekly_stats_all[0].inner_text().split(" ")[0]))

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
                
        weekly_stats.append(str(hours) + " Hours")

    return weekly_stats



#Calculates average song length from total listens and total time
def ave_song_length(listens, time):
    time_split = time.split(" ")

    ave_min = (int(time_split[0]) * 60) / listens

    return str(round(ave_min, 2)) + " Minutes"



#finds the users most popular song of the last week, as well as how many times they listened to it
#possible for the future -> grab album art somehow?
def top_song(page, user):
    #Do i need to check for 404 error here if i already did in the first method?
    #This method will be called after the method with checks, and since im calling it on the same users?

    page.goto("https://www.last.fm/user/" + user + "/library/tracks?date_preset=LAST_7_DAYS", timeout=0)
    
    try:
        #Grab first song name
        song = page.query_selector_all("td.chartlist-name")[0].inner_text()

        #Grab first artist name
        artist = page.query_selector_all("td.chartlist-artist")[0].inner_text()

        #Try to get amount of listens for that top song

        summary = song + " by " + artist
        return summary

    except IndexError as error:
        #If no music is found, set each value as none
        song = "None"
        artist = "None"
        return "None"


def curr_week():
    
    day = datetime.now()
    curr_day = day.weekday()

    if (curr_day >= 5):
        last_friday = (day.date() - timedelta(days=day.weekday()) + timedelta(days=4, weeks=-1))
    else:
        last_friday = (day.date() - timedelta(days=day.weekday()) + timedelta(days=4, weeks=-2))

    time = last_friday.strftime("%m/%d/%Y")

    return time

def sort_dict(dc):
    return dict(sorted(dc.items(), reverse=True))

u = parse_user("users.txt")
users = []

#Converts list of links to valid users
for link in u:
    users.append(get_user(link).rstrip())

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    all_users_stats = {}

    #use first user in users to get the week, as it is the same for everyone
    #no need to calculate this value multiple times when it is constant
    this_week = curr_week()

    #For each user, go through and grab the statistics
    #Add them each to the dictionary all_user_stats, with the key being the user name
    #and the value being the list of associated statistics
    for user in users:
        stats = total_listens(page, user)
        popular_song = top_song(page, user)

        #Check for zero to avoid divide by zero error
        if (stats[0] == 0):
            ave_song_len = "0 Minutes"
        else:
            ave_song_len = ave_song_length(stats[0], stats[1])

        all_stats = []
        all_stats.append(user)
        all_stats.append(stats[1])
        all_stats.append(ave_song_len)
        all_stats.append(popular_song)
        all_stats.append(this_week)

        all_users_stats[stats[0]] = all_stats

    all_users_stats = sort_dict(all_users_stats)

    stats_kv = list(all_users_stats.items())
    all_users_stats.clear()
    for k, v in stats_kv:
        all_users_stats[str(k) + " Scrobbles"] = v

    print(all_users_stats)

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
