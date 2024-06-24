import csv, argparse
from pathlib import Path

CLASSES = ["Artífice", "Bardo", "Brujo", "Clérigo", "Druida", "Explorador", "Hechicero", "Mago", "Paladín",]
# layout
# [name, subclass, optional]
CLASS2SPELL = {}
for c in CLASSES:
    CLASS2SPELL[c] = []
CLASS2CASTER = {"Artífice":1, "Bardo":0, "Brujo":0, "Clérigo":0, "Druida":0, "Explorador":1, "Hechicero":0, "Mago":0, "Paladín":1}

MAX_SPELL_LVL = [
    lambda lvl: min((lvl+1)//2, 9),
    lambda lvl: min((lvl-1)//4 +1, 5)
]
# layout
# [lvl, name, school, cast_time, reach, components, duration, description, src]
ALL_SPELLS = {}

def process_file(fname:Path):
    class_name = fname.stem
    with fname.open(encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in reader:
            CLASS2SPELL[class_name].append(row)

def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def correct(spell):
    if spell in ALL_SPELLS:
        return spell
    closest = min(ALL_SPELLS.keys(),
                  key=lambda s:min(levenshteinDistance(spell+" (RITUAL)", s), levenshteinDistance(spell, s)))
    print(f"{spell} unknown. Do you mean {closest}?")
    return closest

def get_spells(classes=None, spell_list=None, full=False):
    if not classes and not spell_list:
        raise RuntimeError("Must specify eithre classes or spell_list")
    # layout [class, subclass, lvl]
    classes = classes or []
    result = {}
    for c, sc, lvl in classes:
        max_sp_lvl = MAX_SPELL_LVL[CLASS2CASTER[c]](int(lvl))
        entries = filter(lambda e: (e[1] == "" or e[1] == sc)
                         and (int(ALL_SPELLS[e[0]][0]) <= max_sp_lvl)
                         and (full or (e[2] =="False")), CLASS2SPELL[c])
        for entry in entries:
            class_disp = f"{c}({entry[1][:3]})" if entry[1] else c
            if entry[0] in result:
                if entry[2] == "False":
                    if result[entry[0]][1][-1] == '*':
                        result[entry[0]][1] += f", {class_disp}*"
                    else:
                        result[entry[0]] = [entry[0], f"{class_disp}*"]
                else:
                    if result[entry[0]][1][-1] != '*':
                        result[entry[0]][1] += f", {class_disp}" #
            else:
                if entry[2] == "False":
                    result[entry[0]] = [entry[0], f"{class_disp}*"]
                else:
                    result[entry[0]] = [entry[0], class_disp] #
    
    for sp in filter(lambda sp:sp[0] not in result, spell_list):
        result[sp[0]] = [correct(sp[0].upper()), sp[1]]
    
    spells = sorted([
        [ALL_SPELLS[e[0]][0], f"Lv.{ALL_SPELLS[e[0]][0]} {ALL_SPELLS[e[0]][1]}", *ALL_SPELLS[e[0]][2:-1], e[1]+" "+ALL_SPELLS[e[0]][-1]]
        for e in result.values()
    ])
    return spells


if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--classes','-c', action='append')
    parser.add_argument('--full', '-f', action='store_true')
    parser.add_argument('--list', '-l', type=Path)
    parser.add_argument('-o', '--output', type=Path)
    args = parser.parse_args(sys.argv[1:])

    with open("all_spells.csv", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in reader:
            ALL_SPELLS[row[1]] = row
    
                
    INPUT_DIR = Path("class_spells")
    for f in INPUT_DIR.iterdir():
        process_file(f)
    
    classes = [c.split(',') for c in args.classes]
    if args.list is not None:
        with args.list.open('r', encoding="utf-8") as f:
            sp_list = [sp[:-1].split(";") for sp in f]
    else:
        sp_list = []

    spells = get_spells(classes, sp_list, args.full)
    with args.output.open('w', encoding="utf-8") as csvfile:
        writter = csv.writer(csvfile, delimiter=';', quotechar='"', lineterminator="\n", quoting= csv.QUOTE_ALL)
        csvfile.write("\n")
        writter.writerows(spells)
    
    