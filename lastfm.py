from playwright.sync_api import sync_playwright
import sys

# Intro documentation
# https://playwright.dev/python/docs/intro#interactive-mode-repl

# with stops playwright at the end
# if testing in the console, dont use with
# start with => playwright = sync_playwright.start()
# stop with playwright.stop()


def get_user(url):
    return url.rsplit("/", 1)[-1]


# Detect whether or not the username results in a 404 error (valid username)
# def failed(page, user):
#     page.goto("https://www.last.fm/user/" + user)
#     temp = page.query_selector_all('div.col-sm-7 col-sm-push-4')
#     temp = temp.split()
#     print(temp)
#     if len(temp) > 0:
#         return True
#     else:
#         return False


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


valid_user = False

try:
    user = get_user(sys.argv[1])
    valid_user = True
except:
    print("Enter a valid last.fm link")

if valid_user:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        stats = total_listens(page, user)
        ave_song_len = ave_song_length(stats[0], stats[1])

        browser.close()

        scrobbles = stats[0]
        total_time = stats[1]

        print(
            "Total Scrobbles: {}\nTotal Listening Time: {}\nAverage Song Length: {} minutes".format(
                scrobbles, total_time, str(round(ave_song_len, 2))
            )
        )
