from playwright.sync_api import sync_playwright

file_name = "users.txt"
username_links = []


def parse_user(file):
    with open(file) as f:
        username_links = list(f)
        return(username_links)


def get_user(url):
    return url.rsplit("/", 1)[-1]


def total_listens(page, user):
    response = page.goto(
        "https://www.last.fm/user/" + user + "/listening-report", wait_until="domcontentloaded"
    )

    if response.status == 404:
        raise Exception("Invalid username!")

    weekly_stats_all = page.query_selector_all("div.header-metadata-display")

    # weekly_stats is an array with entry 0 as total scrobbles, and entry 1 as total listening time
    weekly_stats = []
    weekly_stats.append(weekly_stats_all[0].inner_text())
    weekly_stats.append(weekly_stats_all[2].inner_text())

    return weekly_stats


def ave_song_length(listens, time):
    scrobbles = listens.split(" ")

    times = time.split(",")
    times_copy = time.split(",")
    ave_min = 0

    for t in times:
        sub_t = " ".join(t.split()).split(" ")

        if len(times_copy) == 1:
            if sub_t[1] == "day":
                ave_min = ave_min + (int(sub_t[0]) * 60 * 24)
            else:
                ave_min = ave_min + (int(sub_t[0]) * 60)
        elif len(times_copy) == 2:
            ave_min = int(int(sub_t[0])) * 24 * 60
            times_copy.remove(times_copy[0])

    ave_min = ave_min / int(scrobbles[0])

    return ave_min


u = parse_user("users.txt")
users = []

for link in u:
    users.append(get_user(link).rstrip())

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    all_users_stats = {}

    for user in users:
        stats = total_listens(page, user)
        ave_song_len = ave_song_length(stats[0], stats[1])

        all_stats = []
        all_stats.append(stats[0])
        all_stats.append(stats[1])
        all_stats.append(ave_song_length(stats[0], stats[1]))

        all_users_stats[user] = all_stats

    browser.close()

    for key, value in all_users_stats.items():
        print(
            key + ":\nTotal Scrobbles: {}\nTotal Listening Time: {}\nAverage Song Length: {} minutes\n".format(
            value[0], value[1], str(round(value[2], 2)))
        )