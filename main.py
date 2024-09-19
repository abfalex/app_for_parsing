from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from time import sleep
import pandas as pd

SPORTS = {
    "ИЗБРАННОЕ": 0,
    "ФУТБОЛ": 1,
    "ХОККЕЙ": 2,
    "ТЕННИС": 3,
    "БАСКЕТБОЛ": 4,
    "ВОЛЕЙБОЛ": 5,
    "ГАНДБОЛ": 6,
}


def get_sport_id(sport_name):
    return SPORTS.get(sport_name, "")


def move_to_sport_page(driver, sport_name, menu_class_name):
    all_sports = driver.find_elements(By.CLASS_NAME, menu_class_name)
    sport_id = get_sport_id(sport_name)
    if not sport_id:
        raise ValueError(f"Sport {sport_name} not found in SPORTS dictionary")
    return all_sports[sport_id].click()


def get_matches(driver, match_class_name):
    return driver.find_elements(By.CLASS_NAME, match_class_name)


def extract_math_urls(driver, match_class_name, base_url):
    matches = get_matches(driver, match_class_name)
    match_urls = []
    for match in matches:
        match_id = match.get_attribute("id")[4:]
        match_urls.append(urljoin(base_url, f"/match/{match_id}"))
    return match_urls


def get_match_elements(driver):
    league_name = driver.find_element(By.CLASS_NAME, "tournamentHeader__country").text
    first_team = driver.find_element(By.CLASS_NAME, "duelParticipant__home").text
    second_team = driver.find_element(By.CLASS_NAME, "duelParticipant__away").text
    start_time = driver.find_element(By.CLASS_NAME, "duelParticipant__startTime").text
    status = driver.find_element(By.CLASS_NAME, "detailScore__status").text
    total_score = driver.find_element(
        By.CLASS_NAME, "detailScore__wrapper"
    ).text.splitlines()

    if status == "not started":
        total_score = ['-', '-']

    return {
        "league_name": league_name,
        "first_team": first_team,
        "second_team": second_team,
        "start_time": start_time,
        "total_score": total_score,
        "status": status,
    }


def get_more_statistics(driver):
    stats = {
        element.text.splitlines()[1]: [element.text.splitlines()[0], element.text.splitlines()[2]] if element else ['-', '-']
        for element in driver.find_elements(By.CLASS_NAME, "_row_ciop9_8")
    }
    print(stats)
    return stats


def format_to_excel(dataframe, filename):
    dataframe.to_excel(filename, index=False)


def main():
    custom_options = Options()
    custom_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=custom_options)

    url = "https://www.flashscorekz.com/"
    driver.get(url)

    menu_class_name = "menuTop__item"
    match_class_name = "event__match.event__match--withRowLink.event__match--scheduled.event__match--last.event__match--twoLine"

    move_to_sport_page(driver, "ХОККЕЙ", menu_class_name)
    match_urls = extract_math_urls(driver, match_class_name, url)

    matches = []

    for match_url in match_urls:
        # match_url = "https://www.flashscorekz.com/match/QuRVp6fC/"
        full_url = urljoin(match_url, "#/match-summary/match-statistics/0")
        driver.get(full_url)

        match_statistics = get_match_elements(driver)
        more_statistics = get_more_statistics(driver)

        match_info = pd.DataFrame([[match_statistics.values()]], columns=[match_statistics.keys()])
        df = pd.DataFrame(more_statistics)

        # final_dop_info = pd.merge(first_team_info, second_team_info, left_index=True, right_index=True)
        final_stat = pd.merge(match_info, final_dop_info, left_index=True, right_index=True)

        matches.append(final_stat)

    final_df = pd.concat(matches)
    format_to_excel(final_df, "output_data.xlsx")

if __name__ == "__main__":
    main()
