import datetime
import json
import re
import sys

import requests


def get_latest_version():
    response = requests.get("https://api.github.com/repos/Kengxxiao/ArknightsGameData_YoStar/commits")
    for commit in response.json():
        if "[EN UPDATE]" not in commit["commit"]["message"]:
            continue

        return commit["commit"]["message"].split("Data:")[1]


latest_version = get_latest_version()

with open("src/data/events.json", "r") as f:
    local_data = json.load(f)

print(f"Latest version: {latest_version}")
print(f"Local version : {local_data['version']}")
if local_data["version"] == latest_version:
    print("Version up to date")
    sys.exit()

print("Version mismatch, updating...")

print("Updating events.json...")
activity_table = requests.get("https://github.com/Kengxxiao/ArknightsGameData_YoStar/raw/refs/heads/main/en_US/gamedata/excel/activity_table.json").json()
local_events_names = {
    event["name"].lower(): {
        "event": event["event"],
        "rerun": event["rerun"] if "rerun" in event else False
    }
    for section in ["en", "future"]
    for year in local_data[section]
    for event in local_data[section][year]
}
today = datetime.datetime.now()

for activity_id, activity_data in activity_table["basicInfo"].items():
    if activity_data["type"] in [
        'CHECKIN_ALL_PLAYER', 'UNIQUE_ONLY', 'COLLECTION',
        'FLIP_ONLY', 'CHECKIN_VS', 'MISSION_ONLY',
        'FLOAT_PARADE', 'PRAY_ONLY', 'LOGIN_ONLY', 'BLESS_ONLY',
        'GRID_GACHA', 'CHECKIN_ACCESS', 'SWITCH_ONLY', 'MAIN_BUFF', 'MAINLINE_BP',
        'CHECKIN_ONLY', 'GRID_GACHA_V2'
    ]:
        continue

    start_time = datetime.datetime.fromtimestamp(activity_data["startTime"])
    end_time = datetime.datetime.fromtimestamp(activity_data["endTime"])
    event_section = "en" if start_time < today else "future"

    if activity_data["name"].lower() not in local_events_names.keys():
        local_data[event_section][str(start_time.year)].append({
            "event": activity_id,
            "duration": (end_time - start_time).days + 1,
            "start": [start_time.month, start_time.day],
            "name": activity_data["name"]
        })
        local_events_names[activity_data["name"].lower()] = {
            "event": activity_id,
            "rerun": False
        }
        print(f"New event: {activity_data['name']}")

    if not local_events_names[activity_data["name"].lower()]["rerun"]:
        if any([rerun_text in activity_data["name"] for rerun_text in ["Rerun", "Retrospection"]]):
            event_name = activity_data["name"].split(" - ")[0].lower()
            rerun_id = local_events_names[event_name]["event"]

            for event in local_data[event_section][str(start_time.year)]:
                if event["event"] == activity_id:
                    event["rerun"] = rerun_id
                    print(f"Updated rerun event: {activity_data['name']}")
                    break
        continue

# TODO: Integrated Strategy and Contingency Crisis

for section in ["en", "future"]:
    for year in local_data[section].keys():
        local_data[section][year] = sorted(local_data[section][year], key=lambda x: (x["start"][0], x["start"][1]))

local_data["version"] = latest_version
with open("src/data/events.json", "w") as f:
    json.dump(local_data, f, indent=4, sort_keys=True)


print("Updating mats.json...")

with open("src/data/mats.json", "r") as f:
    local_mats = json.load(f)

stage_table = requests.get("https://github.com/Kengxxiao/ArknightsGameData_YoStar/raw/refs/heads/main/en_US/gamedata/excel/stage_table.json").json()
item_table = requests.get("https://github.com/Kengxxiao/ArknightsGameData_YoStar/raw/refs/heads/main/en_US/gamedata/excel/item_table.json").json()
stage_ids = [stage_id for stage_id in stage_table["stages"].keys()]

for year in local_data["future"].keys():
    for event in local_data["future"][year]:
        event_id = event["rerun"] if "rerun" in event else event["event"]
        event_stages = [stage_id for stage_id in stage_ids if stage_id.startswith(event_id)]
        event_stage_filtered = []
        for stage_id in event_stages:
            if re.match(f"{event_id}_\\d+", stage_id):
                event_stage_filtered.append(stage_id)

        if len(event_stage_filtered) == 0:
            continue

        if event_id not in local_mats.keys():
            local_mats[event_id] = {}

        for stage_id in event_stage_filtered[-3:]:
            stage_data = stage_table["stages"][stage_id]
            if stage_data["code"] in local_mats[event_id].keys():
                continue

            for drop in stage_data["stageDropInfo"]["displayDetailRewards"]:
                if drop["type"] == "MATERIAL":
                    local_mats[event_id][stage_data["code"]] = item_table["items"][drop["id"]]["name"].replace(" ", "")
                    print(f"Stage {stage_data['code']} - New material: {local_mats[event_id][stage_data['code']]}")

with open("src/data/mats.json", "w") as f:
    json.dump(local_mats, f, indent=4, sort_keys=True)
