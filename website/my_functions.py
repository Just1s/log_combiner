import os
import pandas as pd
import requests
import json
from io import BytesIO
from zipfile import ZipFile


def check_links(logs):
    """ Funkcija gauna mačų statistikos puslapių nuorodas,
        jei nuorodos tikamos naudojant API gražinami mačų duomenys. """
    links_ok = False
    stats = []
    for log in logs:
        if 'logs.tf/' == log[:8] or 'https://logs.tf/' == log[:16]:
            link = log.replace('logs.tf/', 'logs.tf/json/')
            r = requests.get(link)
            data = json.loads(r.text)
            if data['success']:
                links_ok = True
                stats.append(data)
            else:
                return False, stats
        else:
            return False, stats
    return links_ok, stats


def remove_keys(p_stats):
    """ Funkcija iš mačų duomenų pašalinti žaidėjam neaktualias statistikos kategorijas ir
        gražinti duomenis tik su aktualiom kategorijom. """
    unneeded_keys = ['class_stats', 'suicides', 'medicstats', 'dmg_real', 'dt_real', 'lks', 'as', 'dapd', 'dapm',
                     "ubertypes", "drops", "medkits", "medkits_hp", "backstabs", "headshots", "headshots_hit",
                     "sentries", "heal", "cpc", "ic"]
    for player in p_stats:
        p_stats[player]['class'] = p_stats[player]['class_stats'][0]['type']
        for key in unneeded_keys:
            p_stats[player].pop(key, None)
    p_stats = fix_kapd(p_stats)
    return p_stats


def fix_kapd(p_stats):
    """ Funkcija perskaičuoti KA/D ir K/D kategorijų duomenis, nes juos skaičiuojant naudojama dalyba,
        todėl sudėjus kategorijų duomenis jie būtų neteisingi. """
    for player in p_stats:
        p_stats[player]['kapd'] = round(
            (p_stats[player]['kills'] + p_stats[player]['assists']) / p_stats[player]['deaths'], 2)
        p_stats[player]['kpd'] = round(p_stats[player]['kills'] / p_stats[player]['deaths'], 2)
    return p_stats


def make_df(stats, names):
    """ Funkcija iš json formatu gautos statistikos padaryti pandas dataframe ir vietoj statistikoje esančių
        žaidėjų steamID įrašyti jų slapyvardžius. """
    df = pd.DataFrame(stats).transpose()
    df.rename(index=names, inplace=True)
    cols = df.columns.tolist()
    cols = cols[:1] + cols[-1:] + cols[1:-1]
    df = df[cols]
    df.sort_values(by=['team', 'class'], inplace=True)
    return df


def combine_stats(p_stats, p_stats2):
    """ Funkcija sujungti dviejų mačų duomenis į vieną bendrą. """
    for player, stats in p_stats2.items():
        for stat, value in stats.items():
            if isinstance(value, int):
                p_stats[player][stat] += p_stats2[player][stat]
    return p_stats


def etf2l_data(steamid):
    """ Funkcija gauna vartotojo įvestą steamID ir jį panaudijant grąžina žaidėjo lygos avatar'ą ir lygos ID. """
    try:
        r = requests.get(f'https://api.etf2l.org/player/{steamid}.json')
        info = json.loads(r.text)
        if info['status']['message'] == 'OK':
            profile_pic = info['player']['steam']['avatar']
            etf2l_id = info['player']['id']
            return profile_pic, etf2l_id
        else:
            return None, None
    except:
        return None, None


def get_logs_ids(logs):
    """ Funkcija iš duotų nuorodų iškirpti tik Logs.tf mačo statistikos ID. """
    logs_ids = []
    for log in logs:
        logs_ids.append(log[log.find('tf/')+3:])
    return logs_ids


def combine_logs_files(logs_ids):
    """ Funkcija gavus mačų statistikos ID atsiunčia mačų .log failus ir sujungti juos į vieną. """
    path = './website/log_files/'
    log_file = f'{logs_ids[0]}.log'
    full_path = os.path.join(path, log_file)

    f = open(full_path, 'ab')

    for log_id in logs_ids:
        r = requests.get(f"https://logs.tf/logs/log_{log_id}.log.zip")
        if r.ok:
            myzip = ZipFile(BytesIO(r.content))
            for line in myzip.open(f'log_{log_id}.log').readlines():
                f.write(line)
        else:
            return False
    f.close()
    return True
