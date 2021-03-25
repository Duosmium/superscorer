import requests
import sys
import pandas
import yaml
import re

pandas.options.mode.chained_assignment = None

tournament: str = ""
try:
    tournament: str = sys.argv[1]
except IndexError:
    print("No tournament (e.g. 2019-06-01_nationals_c) provided!")
    exit(1)
r = requests.get(f"https://duosmium.org/results/{tournament}")
comp_yaml = requests.get(f"https://duosmium.org/data/{tournament}.yaml")
p = pandas.read_html(r.text)
table = p[0]
events = table.columns[5:-1]
trials = [e for e in events if "  T" in e or "  Td" in e]
events = [e for e in events if e not in trials]
full = ["School", "Rank", "Score"] + events + trials + ["Team Penalties"]
loaded = yaml.safe_load(comp_yaml.text)
try:
    drops = int(loaded["Tournament"]["worst placings dropped"])
except KeyError:
    drops = 0
mins: dict[str, dict[str, int]] = {}
for idx in table.index:
    school_list = table["Team"][idx].split("  ")
    school = school_list[0]
    if re.search(r"[A-Z][a-z]", school_list[-1]):
        state = school_list[-2]
    else:
        state = school_list[-1]
    if f"{school} ({state})" not in mins.keys():
        mins[f"{school} ({state})"] = {}
    for evt in events + trials + ["Team Penalties"]:
        if evt not in mins[f"{school} ({state})"].keys():
            mins[f"{school} ({state})"][evt] = table[evt][idx]
        else:
            mins[f"{school} ({state})"][evt] = min(
                table[evt][idx], mins[f"{school} ({state})"][evt]
            )
input_list = [
    [school, "0", "0"]
    + [str(mins[school][evt]).replace("*", "") for evt in events]
    + [str(mins[school][evt]).replace("*", "") for evt in trials]
    + [str(mins[school]["Team Penalties"])]
    for school in mins
]
df = pandas.DataFrame(input_list, columns=full)
for idx in df.index:

    def calculate_score():
        counted = [int(df[evt][idx].replace("*", "")) for evt in events]
        score = sum(counted)
        if drops > 0:
            score -= sum(sorted(counted)[:-(drops)])
        return score

    df["Score"][idx] = str(calculate_score())
df = df.astype({"Score": int})
df.sort_values(by="Score", inplace=True)
rank = 1
for idx, _ in df.iterrows():
    df["Rank"][idx] = str(rank)
    rank += 1
with open(f"{tournament}_superscored.csv", "w") as fil:
    df.to_csv(fil, index=False)
