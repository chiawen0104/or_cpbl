import json
from tkinter import N
import pandas as pd
import gurobipy as gp
import operator
from datetime import datetime, timedelta

# Parameters
OBP_AVG = 0.327
SLG_AVG = 0.365

FPCT_AVG = {
    '2': 0.992,
    '3': 0.993,
    '4': 0.977, 
    '5': 0.929,
    '6': 0.964,
    '7': 0.977,
    '8': 0.988,
    '9': 0.976
}

POSITION_WEIGHT = {
    '2': {"batting": 0.95, "fielding": 1.05},
    '3': {"batting": 1.21, "fielding": 0.83},
    '4': {"batting": 0.97, "fielding": 1.03},
    '5': {"batting": 0.96, "fielding": 1.04},
    '6': {"batting": 0.94, "fielding": 1.06},
    '7': {"batting": 1.02, "fielding": 0.98},
    '8': {"batting": 1.04, "fielding": 0.96},
    '9': {"batting": 1.17, "fielding": 0.85},
}

OPPONENT_WEIGHT = {
    "中信兄弟": 1.15,
    "統一7-ELEVEn獅": 1.11,
    "樂天桃猿": 0.96, 
    "富邦悍將": 0.93,
    "味全龍": 0.85
}

dataRoot = "./CPBL_OR/clean/clean_all_"
playerRoot = "./CPBL_OR/球員異動/"

teamNameMap = {
    "中信兄弟": "brothers", 
    "味全龍": "dragons",
    "富邦悍將": "guardians", 
    "統一7-ELEVEn獅": "lions",
    "樂天桃猿": "monkeys"
}

class Player:
    def __init__(self, name, data):
        self.name = name
        self.data = data

allData = {}
for team in teamNameMap.keys():
    with open(dataRoot + team + ".json", encoding="utf-8") as f:
        temp = []
        for line in f:
            player = json.loads(line)
            temp.append(Player(player["name"], player["data"]))
        allData[teamNameMap[team]] = temp

brothers = allData["brothers"]
dragons = allData["dragons"]
guardians = allData["guardians"]
lions = allData["lions"]
monkeys = allData["monkeys"]

playerList = {}

for team in teamNameMap.keys():
    tempDict = pd.read_csv(playerRoot + team + ".csv", header=0, index_col=0).to_dict()
    tempDict = {
        datetime.strptime(key, "%Y-%m-%d").date(): list(filter(lambda d: pd.isna(d) == False, list(value.values())))
        for key, value in tempDict.items()
    }
    playerList[teamNameMap[team]] = tempDict


def createDate(mm, dd):
    return datetime(2022, mm, dd, 0, 0, 0).date()

gameN = 1
aTeam = "樂天桃猿"
aMonth = "May"
aGame = {
        1:{"date":createDate(5, 24),"field":"台東","oppo":"中信兄弟","pitcher":"德保拉","bao":{"1":"蔡鎮宇","2":"成晉","3":"藍寅倫","4":"朱育賢","5":"馮健庭","6":"梁家榮","7":"張閔勛","8":"林澤彬","9":"陳晨威"},"pos":{"7":"蔡鎮宇","9":"成晉","1":"藍寅倫","3":"朱育賢","6":"馮健庭","5":"梁家榮","2":"張閔勛","4":"林澤彬","8":"陳晨威"}}
    }


# 比賽當天 27 人名單去除投手
def findPlayerList(team, date):
    minDelta = timedelta(days=100)
    playerDay = date
    for key in playerList[teamNameMap[aTeam]].keys():
        if date > key:
            break
        if key - date < minDelta:
            minDelta = key - date
            playerDay = key
    
    withoutPitcherList = []
    for data in allData[teamNameMap[team]]:
        withoutPitcherList.append(data.name)
    return list(filter(lambda d: d in withoutPitcherList, playerList[teamNameMap[team]][playerDay]))


# A_{ij}
def calcA(player, pos):
    if str(pos) in player.data["fielding"]["pos"].keys():
        return 1
    else:
        return 0

# F_{ij}
def calcF(player, pos):
    if str(pos) in player.data["fielding"]["pos"].keys():
        F = float(player.data["fielding"]["pos"][str(pos)]["FPCT"]) / FPCT_AVG[str(pos)]
        return F
    else:
        return 0


# B_i
def calcOPS(OBP, SLG):
    return OBP / OBP_AVG + SLG / SLG_AVG - 1

def calcB(game, player):
    if game["date"].month == 4:
        aMonth = "Apr"
    if game["date"].month == 5:
        aMonth = "May"
    if game["date"].month == 6:
        aMonth = "Jun"
    aOppo = game["oppo"]
    aPitcher = game["pitcher"]
    aField = game["field"]

    OPSseason = float(player.data["batting"]["season"]["OPS+"])
    PAseason = int(player.data["batting"]["season"]["PA"])
    
    if "month" in player.data["batting"].keys():
        if aMonth in player.data["batting"]["month"].keys():
            if float(player.data["batting"]["month"][aMonth]["AB"]) == 0:
                OPSmonth = calcOPS(float(player.data["batting"]["month"][aMonth]["OBP"]),0)
            else:
                OPSmonth = calcOPS(
                float(player.data["batting"]["month"][aMonth]["OBP"]), 
                float(player.data["batting"]["month"][aMonth]["TB"]) / float(player.data["batting"]["month"][aMonth]["AB"]))
            PAmonth = int(player.data["batting"]["month"][aMonth]["PA"])
        else:
            OPSmonth = OPSseason
            PAmonth = 0
    else:
        OPSmonth = OPSseason
        PAmonth = 0

    if "field" in player.data["batting"]:
        if aField in player.data["batting"]["field"].keys():
            if float(player.data["batting"]["field"][aField]["AB"]) == 0:
                OPSfield = calcOPS(float(player.data["batting"]["field"][aField]["OBP"]),0)
                PAfield = int(player.data["batting"]["field"][aField]["PA"])
            else:
                OPSfield = calcOPS(
                    float(player.data["batting"]["field"][aField]["OBP"]), 
                    float(player.data["batting"]["field"][aField]["TB"]) / float(player.data["batting"]["field"][aField]["AB"])
                )
                PAfield = int(player.data["batting"]["field"][aField]["PA"])
        else:
            OPSfield = OPSseason
            PAfield = 0
    else:
        OPSfield = OPSseason
        PAfield = 0
    
    if "vsP" in player.data["batting"].keys():
        if aOppo in player.data["batting"]["vsP"]["data"].keys():
            if aPitcher in player.data["batting"]["vsP"]["data"][aOppo].keys():
                if player.data["batting"]["vsP"]["data"][aOppo][aPitcher]["AB"] != "0":
                    OPSvsp = calcOPS(
                        float(player.data["batting"]["vsP"]["data"][aOppo][aPitcher]["OBP"]), 
                        float(player.data["batting"]["vsP"]["data"][aOppo][aPitcher]["TB"]) / float(player.data["batting"]["vsP"]["data"][aOppo][aPitcher]["AB"])
                    )
                    PAvsp = int(player.data["batting"]["vsP"]["data"][aOppo][aPitcher]["PA"])
                else:
                    OPSvsp = OPSseason
                    PAvsp = 0
            else:
                OPSvsp = OPSseason
                PAvsp = 0
        else:
            OPSvsp = OPSseason
            PAvsp = 0
    else:
        OPSvsp = OPSseason
        PAvsp = 0

    B = (OPSseason * PAseason + OPSmonth * PAmonth + OPSfield * PAfield + OPSvsp * PAvsp) / (PAseason + PAmonth + PAfield + PAvsp)
    return B

# V_{ij}
def calcV(game, player, pos):
    B = calcB(game, player)
    F = calcF(player, pos)
    return (POSITION_WEIGHT[str(pos)]["batting"] * B + POSITION_WEIGHT[str(pos)]["fielding"] * F)

def calcwOBA (nm, k):
    thisPlayer = list(filter(lambda d: d.name == nm, allData[teamNameMap[aTeam]]))[0]
    if "baorder" in thisPlayer.data["batting"].keys():
        if str(k) in thisPlayer.data["batting"]["baorder"].keys():
            thisOrderData = thisPlayer.data["batting"]["baorder"][str(k)]
            PA = int(thisOrderData["PA"])
            if PA >= 30:
                O = (int(thisOrderData["IBB"][1]) * 0.72 + int(thisOrderData["HBP"]) * 0.75 
                + (int(thisOrderData["H"]) - int(thisOrderData["2B"]) - int(thisOrderData["3B"]) - int(thisOrderData["HR"])) * 0.9
                + int(thisOrderData["2B"]) * 1.24 + int(thisOrderData["3B"]) * 1.56 + int(thisOrderData["HR"]) * 1.95) / PA
                return O
            else:
                return thisPlayer.data["batting"]["season"]["wOBA"]
        else:
            return thisPlayer.data["batting"]["season"]["wOBA"]
    else:
        return thisPlayer.data["batting"]["season"]["wOBA"]



# Stage 1

sum1 = 0
Zlist = []
for n in range(gameN):
    Zg = OPPONENT_WEIGHT[aGame[n+1]['oppo']]
    Zlist.append(Zg)
    # print(aＧame[n+1]['pos'])
    for j in range(2,10):
        # print(n+1, j)
        ply = list(filter(lambda d: d.name == aＧame[n+1]['pos'][str(j)], allData[teamNameMap[aTeam]]))[0]
        sum1 += calcV(aGame[n+1], ply, j) * Zg

print(sum1)
print(sum1/sum(Zlist))

# Stage 2
sum2 = 0
for n in range(gameN):
    sum2 = 0
    for k in range(1,10):
        # print(n+1, k)
        sum2 += calcwOBA(aＧame[n+1]['bao'][str(k)], k)
    print(sum2)

