import json
import time
import requests

from datetime import date, datetime
from lxml import etree

teamDict = dict()               #hat später die Form {kickName, fbrefName}
playerDict = dict()
currMatchDay = None

kickHeader = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
kickURL = "https://api.kickbase.com/"
kickSeasonID = 20

refURL = "/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures"

def getNumbers(tree) -> dict:
    result = dict()
    field = tree.xpath("//*[@id='field_wrap']")
    divs = field[0].xpath(".//div")
    homeDiv = None
    awayDiv = None
    i = 0
    while homeDiv is None or awayDiv is None:
        if divs[i].get("id") == 'a':
            homeDiv = divs[i]
        elif divs[i].get("id") == 'b':
            awayDiv = divs[i]
        i = i + 1

    homeTable = homeDiv.xpath(".//table")
    homeTableInner = homeTable[0].xpath(".")
    homeList = homeTableInner[0].xpath(".//tr")
    awayList = awayDiv.xpath(".//table")[0].xpath(".")[0].xpath(".//tr")

    for i in range(1, len(homeList)):
        row = homeList[i].xpath(".//td")
        if len(row) > 0:
            result[row[1].xpath(".//a")[0].text] = row[0].text

    for i in range(1, len(awayList)):
        row = awayList[i].xpath(".//td")
        if len(row) > 0:
            result[row[1].xpath(".//a")[0].text] = row[0].text

    return result

def findLastMatchDay(site):
    week = 0
    try:
        table = site.xpath("//*[@id='sched_2023-2024_20_1']")[0]
    except IndexError:
        print(etree.tostring(site, pretty_print=True, encoding='unicode'))
        raise ConnectionError("fbref nervt")
    tableBody = table.xpath('.//tbody')[0]
    rows = tableBody.xpath('.//tr')
    for row in rows:
        cells = row.xpath('.//td | .//th')
        dateCell = cells[2].xpath('.//a')
        currWeekCell = cells[0].text
        if len(dateCell) > 0:
            matchDay = dateCell[0].text
            dateObj = datetime.strptime(matchDay, "%Y-%m-%d").date()
            if dateObj >= date.today():
                break
            if currWeekCell is not None:
                week = int(currWeekCell)
    return week

def getRefSite(link=refURL):
    resp = requests.request("GET", "https://fbref.com/" + link)
    tree = etree.HTML(resp.text)
    return tree
def getMatchData(link) -> list:
    tree = getRefSite(link)
    tables = tree.xpath("//table")
    numberDict = getNumbers(tree)
    t2 = list()
    for t in tables:
        name = str(t.get('id'))
        if "stats_" in name and "_summary" in name:
            t2.append(t)
    try:
        tableCaption = t2[0].xpath('.//caption')
    except IndexError:
        print(tree)
        raise ConnectionError("fbref nervt")
    teamName = tableCaption[0].text.replace(" Player Stats Table", "")

    scoreBox = tree.xpath("//div[contains(@class, 'scorebox')]")[0]
    homeBox = scoreBox.xpath('.//div')[0]
    logoBox = homeBox.xpath('.//div')[0]
    nameBox = logoBox.xpath('.//strong')[0]
    homeName = nameBox.xpath('.//a')[0].text

    #if teamName != homeName:
    #    t2.reverse()
    #    print(homeName)
    #    print(teamName)

    result = list()
    team = 1
    for table in t2:
        rows = table.xpath('.//tbody')[0].xpath('.//tr')
        for row in rows:
            name = row[0].xpath('.//a')[0].text
            number = numberDict[name]
            position = row[3].text
            minutes = row[5].text
            result.append(name + ";" + position + ";" + minutes + ";" + str(team) + ";" + str(number))
        team = 2
    return result

def crawlRef(numberOfMatchdays: int) -> dict:
    tree = getRefSite()
    try:
        table = tree.xpath("//*[@id='sched_2023-2024_20_1']")[0]
    except IndexError:
        print(etree.tostring(tree, pretty_print=True, encoding='unicode'))
        raise ConnectionError("fbref nervt")
    seasonObj = tree.xpath("//*[@id='all_sched']")[0].xpath(".//div")[0].xpath(".//h2")[0].xpath(".//span")[0].text
    season = seasonObj.replace(" Bundesliga", "")
    tableBody = table.xpath('.//tbody')[0]
    rows = tableBody.xpath('.//tr')
    global currMatchDay
    currMatchDay = findLastMatchDay(getRefSite())
    firstMatchDayRow: int = ((currMatchDay - numberOfMatchdays) * 10)
    lastMatchDayRow: int = (currMatchDay * 10) + 1
    result = dict()
    for row in rows[firstMatchDayRow:lastMatchDayRow]:
        cells = row.xpath('.//td | .//th')
        linkCell = cells[-2].xpath('.//a')
        if len(linkCell) > 0:
            link = linkCell[0].get('href')
            home = cells[4].xpath('.//a')[0].text
            away = cells[8].xpath('.//a')[0].text
            matchDay = cells[0].text
            if (currMatchDay - numberOfMatchdays + 1) <= int(matchDay) <= currMatchDay:
                index = matchDay + ";" + teamDict[home] + ";" + teamDict[away] + ";" + season
                print(index)
                result[index] = getMatchData(link)
            time.sleep(4)
    return result

def findPlayer(name: str) -> int:           #name = firstname;lastname
    firstName, lastName = name.split(";")
    response = requests.request("GET", kickURL + "competition/search?t=" + lastName, headers=kickHeader)
    players = json.loads(response.text)["p"]
    for p in players:
        if p["lastName"] == lastName and p["firstName"] == firstName:
            return p["i"]
    return None


def kickLogin():

    body = {
        "email": "reireu3@gmail.com",
        "password": "Froggi123",
        "ext": False
    }
    response = requests.request("POST", kickURL + "user/login", headers=kickHeader, json=body)
    kickHeader['Authorization'] = f'Bearer ' + response.json().get('token')


def getPlayerIds(teamID:int) -> list:
    #findet PlayerIDs eines Teams mit geg. teamID

    response = requests.request("GET", kickURL + "competition/teams/" + str(teamID) + "/players", headers=kickHeader)
    players: list = json.loads(response.text)["p"]
    result = list()

    for p in players:
        result.append((p.get("firstName") + " " + p.get("lastName") + ";" + p.get("id") + ";" + str(p.get("number"))))

    return result

def getTeamIds() -> dict:
    #findet teamids der bundesligisten
    response = requests.request("GET", kickURL + "/v3/competitions/1/table", headers=kickHeader)

    teams = json.loads(response.text)["e"]
    result = dict()
    for t in teams:
        result[t.get("n")] = t.get("i")
    return result


def getPlayerPoints(playerID:int, numberOfMatchdays) -> list:
    response = requests.request("GET", kickURL + "players/" + str(playerID) + "/points", headers=kickHeader)
    pointList: dict = json.loads(response.text)["s"]
    try:
        currPoints = pointList[-1].get("m")
    except IndexError:
        return [0]*numberOfMatchdays

    low = currMatchDay - numberOfMatchdays + 1
    pointer = len(currPoints) - 1
    actPoints = list()
    for i in range(currMatchDay, low - 1, -1):
        foundDay = currPoints[pointer].get("d")
        if foundDay == i:
            actPoints.append(currPoints[pointer].get("p"))
            if pointer != 0:
                pointer = pointer - 1
        else:
            actPoints.append(0)
    actPoints.reverse()
    return actPoints
def translateTeams():
    response = requests.request("GET", kickURL + "/v3/competitions/1/table", headers=kickHeader)
    table = json.loads(response.text)["e"]

    tableList = dict()
    kickmp = int(json.loads(response.text)["day"])
    for team in table:
        tableList[team["cpl"]] = team["n"]

    response2 = requests.request("GET", "https://fbref.com/en/comps/20/Bundesliga-Stats")
    tree = etree.HTML(response2.text)
    try:
        tableElement = tree.xpath('//*[@id="results2023-2024201_overall"]')[0]
    except IndexError:
        print(response2.text)
        raise ConnectionError("fbref nervt")

    tableBody = tableElement.xpath('.//tbody')[0]
    rows = tableBody.xpath('.//tr')
    fbMp = int(rows[0].xpath('.//td')[1].text)
    if kickmp != fbMp:
        print("please try again later")
    else:
        place = 1
        tableList2 = dict()
        for row in rows:
            tableList2[place] = row.xpath('.//td')[0].xpath('.//a')[0].text
            place = place + 1

        for p in tableList.keys():
            teamDict[tableList2[p]] = tableList[p]

#kickLogin()
#findPlayer("Lewandowski")
#getTeamIds()
#getPlayerIds(9)
#getPlayerPoints(2068)
#translateTeams()
#getKickMatches()

