import sqlite3
import os
from unidecode import unidecode

fileName = "Database/kickDB"
teamsDict = {}

def setUp():
    if os.path.exists(fr'{fileName}' + ".db"):
        os.remove(fr'{fileName}' + ".db")
        conn = sqlite3.connect(fileName + ".db")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY, name TEXT)''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT, teamId INTEGER, shirtNumber INTEGER, FOREIGN KEY (teamId) REFERENCES teams (id))''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS matches (id INTEGER NOT NULL AUTO_INCREMENT, homeId INTEGER, awayId INTEGER, matchDay INTEGER, season TEXT, FOREIGN KEY (homeId) REFERENCES teams (id), FOREIGN KEY (awayId) REFERENCES teams (id))''')
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS matchData (matchId INTEGER, playerId INTEGER, teamId INTEGER, minutes INTEGER, position TEXT, points INTEGER, FOREIGN KEY (matchId) REFERENCES matches (id), FOREIGN KEY (playerId) REFERENCES players (id), FOREIGN KEY (teamId) REFERENCES team (id))''')
        conn.close()
def getLastMatchDay():
    conn = sqlite3.connect(fileName + ".db")
    cursor = conn.cursor()
    day = cursor.execute("SELECT MAX(matchDay) FROM matches").fetchall()[0][0]
    return day
def storeBasics(playerIds: dict):               #gets dict = {teamname;id, list of (playername, id)}
    conn = sqlite3.connect(fileName + ".db")
    cursor = conn.cursor()
    for t in playerIds.keys():
        teamName, teamId = t.split(";")
        teamsDict[teamName] = teamId
        cursor.execute("INSERT INTO teams (id, name) VALUES (?, ?)", (teamId, teamName))
        for player in playerIds[t]:
            name, playId, shirtNumb = player.split(";")
            firstName, lastName = handleName(name)
            cursor.execute("INSERT INTO players (id, firstName, lastName, teamId, shirtNumber) VALUES (?, ?, ?, ?, ?)", (int(playId), firstName, lastName, teamId, int(shirtNumb)))
    conn.commit()
    conn.close()

def storeMatches(data: dict):           #gets data in form: {matchday;hometeam;awayteam : list with name;position;minuten;team}
    conn = sqlite3.connect(fileName + ".db")
    cursor = conn.cursor()
    playerList = list()
    nextId = cursor.execute("SELECT MAX(id) FROM matches").fetchall()[0][0] + 1
    for match in data.keys():
        matchDay, homeTeam, awayTeam, season = match.split(";")
        homeId = cursor.execute("SELECT id FROM teams WHERE name = ?", (homeTeam,)).fetchall()[0][0]
        awayId = cursor.execute("SELECT id FROM teams WHERE name = ?", (awayTeam,)).fetchall()[0][0]
        cursor.execute("INSERT INTO matches (id, homeId, awayId, matchDay, season) VALUES (?, ?, ?, ?, ?)", (nextId, homeId, awayId, matchDay, season))
        for players in data[match]:
            name, position, minutes, team, number = players.split(";")
            firstName, lastName = handleName(name)
            teamId = homeId
            if int(team) == 2:
                teamId = awayId
            selObj = cursor.execute("SELECT id FROM players WHERE shirtNumber = ? AND teamId = ?", (number, teamId)).fetchall()
            playerId = None
            if len(selObj) > 0:
                playerId = selObj[0][0]
                playerList.append(playerId)
            else:
                print("The player with name: " + firstName + " " + lastName + ", shirtnumber: " + str(number) + ", teamid: " + str(teamId) + ", was not found.")
            cursor.execute(
                "INSERT INTO matchData (matchId, playerId, teamId, minutes, position, points) VALUES (?, ?, ?, ?, ?, NULL)",
                (nextId, playerId, teamId, minutes, position))
        nextId = nextId + 1
    conn.commit()
    conn.close()

    return playerList

def storePoints(pointList: dict):           #gets dict in form {playerId, list of points in last x games}
    conn = sqlite3.connect(fileName + ".db")
    cursor = conn.cursor()
    currMatchDay = cursor.execute("SELECT MAX(matchDay) FROM matches").fetchall()[0][0]

    for player in pointList.keys():
        matchday = currMatchDay - len(pointList[player]) + 1
        for points in pointList[player]:
            cursor.execute("UPDATE matchData SET points = ? WHERE playerId = ? AND matchId IN (SELECT id FROM matches WHERE matchDay = ?)", (points, player, matchday))
            matchday = matchday + 1

    conn.commit()
    conn.close()

def handleName(fullName: str) -> tuple:

    norm = unidecode.unidecode(fullName)
    names = norm.split(" ")
    if len(names) == 1:
        firstName = ""
        lastName = fullName
    else:
        firstName = names[0]
        lastName = names[-1]

    return firstName, lastName


def storePlayers(unknownPlayers):
    conn = sqlite3.connect(fileName + ".db")
    cursor = conn.cursor()

    for player in unknownPlayers:
        cursor.execute("INSERT INTO players (id, firstName, lastName, teamId) VALUES (?, ?, ?, ?)", player.split(";"))

    conn.commit()
    conn.close()


def getLostPlayers() -> list:
    conn = sqlite3.connect(fileName + ".db")
    cursor = conn.cursor()

    playersFetch = cursor.execute("SELECT playerId FROM matchData WHERE points = NULL and playerId != NULL").fetchall()
    players = [x[0] for x in playersFetch]
    conn.commit()
    conn.close()

    return players

def getPlayers() -> list:
    conn = sqlite3.connect(fileName + ".db")
    cursor = conn.cursor()

    playersFetch = cursor.execute("SELECT DISTINCT playerId FROM players").fetchall()
    players = [x[0] for x in playersFetch]
    conn.commit()
    conn.close()

    return players

def getPoints(player):
    conn = sqlite3.connect(fileName + ".db")
    cursor = conn.cursor()

    points = []
    pointsFetch = cursor.execute("SELECT points, minutes FROM matchData WHERE playerId = ?", (player)).fetchall()
    print(pointsFetch)
    conn.commit()
    conn.close()
