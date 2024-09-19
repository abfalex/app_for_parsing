import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


SPORTS = {
    "ИЗБРАННОЕ": 0,
    "ФУТБОЛ": 1,
    "ХОККЕЙ": 2,
    "ТЕННИС": 3,
    "БАСКЕТБОЛ": 4,
    "ВОЛЕЙБОЛ": 5,
    "ГАНДБОЛ": 6,
}

STAT_PARAMS = ["Выиграно на подаче", "Выиграно очков у сетки"]


def get_sport_id(sport_name):
    return SPORTS.get(sport_name, "")


def navigate_to_sport_page(driver, sport_name, menu_class_name):
    sport_id = get_sport_id(sport_name)
    if not sport_id:
        raise ValueError(f"Sport {sport_name} not found in SPORTS dictionary")

    driver.find_elements(By.CLASS_NAME, menu_class_name)[sport_id].click()


def get_match_info(driver):
    return {
        "league_name": driver.find_element(By.CLASS_NAME, "tournamentHeader__country").text,
        "first_team": driver.find_element(By.CLASS_NAME, "duelParticipant__home").text.splitlines()[0],
        "second_team": driver.find_element(By.CLASS_NAME, "duelParticipant__away").text.splitlines()[0],
        "start_time": driver.find_element(By.CLASS_NAME, "duelParticipant__startTime").text,
        "total_score": driver.find_element(By.CLASS_NAME, "detailScore__wrapper").text.splitlines(),
        "status": driver.find_element(By.CLASS_NAME, "detailScore__status").text,
    }


def get_additional_statistics(driver):
    statistics_elements = driver.find_elements(By.CLASS_NAME, "_row_1y0py_8")
    statistics = {}
    for element in statistics_elements:
        element_text = element.text.splitlines()
        param_name = element_text[1]
        first_team_stat = element_text[0]
        second_team_stat = element_text[-1]

        if param_name in STAT_PARAMS:
            statistics[param_name] = [first_team_stat, second_team_stat]

    for param in STAT_PARAMS:
        if param not in statistics:
            statistics[param] = ['-', '-']

    return statistics


def process_match(driver, match_id):
    """Обрабатывает данные для одного матча и возврает DataFrame с его статистикой"""
    match_url = f"https://www.flashscorekz.com/match/{match_id}/#/match-summary/match-statistics/0"
    driver.get(match_url)

    match_info = get_match_info(driver)
    if match_info["status"] == "not started":
        match_info["total_score"] = ['-', '-']

    additional_stats = get_additional_statistics(driver)

    match_info_df = pd.DataFrame([[
        match_info["league_name"],
        match_info["start_time"],
        match_info["status"],
        match_info["first_team"],
        match_info["second_team"],
        match_info["total_score"][0],
        match_info["total_score"][-1],
    ]], columns=["Лига", "Время", "Статус", "Первая команда", "Вторая команда", "Счет первой комнады", "Счет второй команды"])

    additional_stats_df = pd.DataFrame(additional_stats)
    first_team_stats = additional_stats_df.loc[[0]].add_suffix(" 1")
    second_team_stats = additional_stats_df.loc[[1]].add_suffix(" 2").reset_index(drop=True)
    
    return pd.merge(first_team_stats, second_team_stats, left_index=True, right_index=True) \
        .merge(match_info_df, left_index=True, right_index=True)


def extract_match_ids(driver, match_class):
    """Извлекает ID матчей с главной страницы"""
    matches = driver.find_elements(By.CLASS_NAME, match_class)
    return [match.get_attribute("id")[4:] for match in matches]


def setup_webdriver():
    options = Options()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def main():
    url = "https://www.flashscorekz.com"
    match_class = "event__match.event__match--withRowLink.event__match--scheduled.event__match--twoLine"
    
    driver = setup_webdriver()
    driver.get(url)

    sport = "ТЕННИС"
    navigate_to_sport_page(driver, sport, "menuTop__item")

    match_ids = extract_match_ids(driver, match_class)
    all_matches = []

    for match_id in match_ids:
        match_data = process_match(driver, match_id)
        all_matches.append(match_data)
        
    if all_matches:    
        final_df = pd.concat(all_matches)
        final_df.to_excel("output_data.xlsx", index=False)
   
    driver.quit()


if __name__ == "__main__":
    main()