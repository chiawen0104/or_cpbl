import json
import re
from turtle import pos
import pandas as pd

# 中信兄弟 味全龍 富邦悍將 統一7-ELEVEn獅 樂天桃猿
# 林琨笙

team = '味全龍'

with open('player_{}.json'.format(team), 'r') as player_file:
    player_list = list(player_file)

with open('fight_{}.json'.format(team), 'r') as fight_file:
    fight_list = list(fight_file)

fielding = pd.read_excel("cpbl_2021.xlsx",sheet_name="fielding")

season_data = pd.read_excel("cpbl_2021.xlsx",sheet_name="batting")

month_dict = {"一月": "Jan", "二月": "Feb", "三月": "Mar", "四月": "Apr", "五月": "May", "六月": "Jun",
              "七月": "Jul", "八月": "Aug", "九月": "Spe", "十月": "Oct", "十一月": "Nov", "十二月": "Dec"}

score_dict = {'打席': 'PA', '打數': 'AB', '安打': 'H', '二安': '2B', '三安': '3B',
              '全壘打': 'HR', '壘打數': 'TB', '四壞': 'BB', '（故四）': 'IBB', '死球': 'HBP', '上壘率': 'OBP'}

field_dict = {'台中洲際棒球場': '洲際', '台南市立棒球場': '台南', '花蓮縣立棒球場': '花蓮',
              '桃園國際棒球場': '桃園', '高雄市澄清湖棒球場': '澄清湖',
              '雲林縣斗六棒球場': '斗六', '新北市立新莊棒球場': '新莊', '天母棒球場': '天母',
              '樂天桃園棒球場': '桃園','嘉義市立體育棒球場': '嘉義'}

position_dict = {'P':1,'C':2, '1B':3, '2B':4, '3B':5, 'SS':6, 'LF':7, 'CF':8 , 'RF':9}

order_dict = {'第一棒': '1', '第二棒': '2', '第三棒': '3', '第四棒': '4',
              '第五棒': '5', '第六棒': '6', '第七棒': '7', '第八棒': '8', '第九棒': '9'}



def fight_reshape(player_data):
    player_dict = {}
    txt = player_data["name"]
    name = re.sub("[0-9]", "", txt)
    name = name.strip("*")
    name = name.strip("◎")
    data = player_data["detail"]
    fight_OBP = {}
    for i in data:
        if i[0] == '對戰球員':
            continue
        fight_name = i[0].split("\n")
        if fight_name[0] not in fight_OBP:
            fight_OBP[fight_name[0]] = {}
        
        fight_OBP[fight_name[0]][fight_name[1]] = i[13]

    player_dict["name"] = name
    player_dict["data"] = fight_OBP
    return player_dict

def clean_detail(data):
    sample = {'PA': data[1], 'AB': data[2], 'H': data[4], '2B': data[5], '3B': data[6],
              'HR': data[7], 'TB': data[8], 'BB': data[10], 'IBB': data[11], 'HBP': data[12], 'OBP': data[14]}
    return sample


def filter_data(data_dict, target_dict):
    target = {}
    for key in data_dict:
        if key in target_dict:
            target[target_dict[key]] = data_dict[key]

    return target

# 'fielding': {'pos': [4, 5, 6], 'FPCT': {'4': 000, '5': 000, '6': 000}}
def find_fielding(name):
    global fielding
    fielding_clean = {}
    target= (fielding['Name']== name)
    filtered_df = fielding[target]
    pos_list = filtered_df["POS"].to_list()
    pos_list_num = []
    for i in pos_list:
        pos_list_num.append(position_dict[i])
    fielding_clean['pos'] = pos_list_num

    FPCT_score = filtered_df["FPCT"].to_list()
    FPCT_score_clean = {}
    for ind in range(len(pos_list_num)):
        FPCT_score_clean[pos_list_num[ind]] = FPCT_score[ind]

    fielding_clean['FPCT'] = FPCT_score_clean

    return fielding_clean

# 'season': {'OPS+': 000, 'OBP': 000}
def find_season(name):
    global season_data
    season = {}
    # 處理改名問題
    if name == '林琨笙':
        name = '林宥穎'
    if name == '拿莫．伊漾':
        name = '朱祥麟'
    target= (season_data['NAME']==name)
    filtered_df = season_data[target]
    season['OPS+'] = filtered_df["OPS+"].to_list()[0]
    season['OBP'] = filtered_df["OBP"].to_list()[0]
    
    return season

def reshape_player(player_data):
    player_dict = {}
    data = player_data["detail"]
    txt = player_data["name"]
    
    name = re.sub("[0-9]", "", txt)
    name = name.strip("*")
    name = name.strip("◎")

    data_dict = {}
    for detail in data[1:]:
        data_dict[detail[0]] = clean_detail(detail)

    data = {}
    batting = {}

    batting["season"] = find_season(name)
    batting["month"] = filter_data(data_dict, month_dict)
    batting["field"] = filter_data(data_dict, field_dict)
    batting["baorder"] = filter_data(data_dict, order_dict)
    batting["vsP"] = find_fight(name)
    data["batting"] = batting

    fielding_dict = find_fielding(name)
    data["fielding"] = fielding_dict

    player_dict["name"] = name
    player_dict["data"] = data

    return player_dict

def find_fight(name):
    global new_fight
    target = ""
    for player in new_fight:
        if player['name']==name:
            target = player
    
    return target

new_fight = []
for player in fight_list:
    result = json.loads(player)
    player_dict = fight_reshape(result)
    new_fight.append(player_dict)

player_dict_list = []
for player in player_list:
    result = json.loads(player)
    player_dict = reshape_player(result)
    player_dict_list.append(player_dict)

print(len(player_dict_list))

df = pd.DataFrame(player_dict_list)
print(df.head())
df.to_json("clean_all_{}.json".format(team),orient = 'records', lines=True, force_ascii=False)