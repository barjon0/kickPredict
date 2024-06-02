import unicodedata


import DataHandler
import DataScrapper

def initialFill(matchDays):

    DataHandler.setUp()
    DataScrapper.kickLogin()
    teamIds: dict = DataScrapper.getTeamIds()               #gets dict of form {name, id}
    DataScrapper.translateTeams()
    print("Retrieved team data from kickbase")

    playerIds = dict()
    for t in teamIds.keys():                     #create dict of form {teamname;id, list of playername;id;number)}
        playerIds[t + ";" + teamIds[t]] = DataScrapper.getPlayerIds(teamIds.get(t))
    print("Retrieved player Ids from kickbase")
    #DataHandler add players and team
    DataHandler.storeBasics(playerIds)
    print("Stored Basics in database")
    data = DataScrapper.crawlRef(matchDays)               # returns dict {gamedetail, list player data}
    print("Crawled through fbref")
    #DataHandler add matchups and stats to database
    DataHandler.storeMatches(data)
    print("Stored matchdata in database")
    playerPoints = dict()
    for playerList in playerIds.values():
        for player in playerList:
            playId = player.split(";")[1]
            points = DataScrapper.getPlayerPoints(playId, matchDays)
            playerPoints[playId] = points
    print("Retrieved point lists of players")
    DataHandler.storePoints(playerPoints)
    print("Stored points in database")
    #DataHanlder add player points to database

def addLastMatchday():
    DataScrapper.kickLogin()
    DataScrapper.translateTeams()
    lastMatchDay = DataScrapper.findLastMatchDay(DataScrapper.getRefSite())
    lastStored = DataHandler.getLastMatchDay()

    if lastStored != lastMatchDay:
        data = DataScrapper.crawlRef(lastMatchDay - lastStored)
        players: list = DataHandler.storeMatches(data)               #[teamId;firstname;lastname]

        pointDict = dict()
        for p in players:
            points = DataScrapper.getPlayerPoints(p, lastMatchDay - lastStored)
            pointDict[p] = points
        DataHandler.storePoints(pointDict)

def predict():
    return None

def printAvg():
    players = DataHandler.getPlayers()
    for p in players:
        DataHandler.getPoints(p)

#initialFill(10)