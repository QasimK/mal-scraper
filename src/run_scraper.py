# -*- coding: utf-8 -*-

import csv
import time

from .mal_scraper import anime


def get_values(dictionary, key_arr):
    w = []
    for key in key_arr:
        w.append(dictionary[key])
    return w


results = 'results/remaining/'
debug = 'debug/'

num = '1'

anime_file = results + 'csv_anime_' + num + '.csv'
character_file = results + 'csv_characters_' + num + '.csv'
staff_file = results + 'csv_staff_' + num + '.csv'

progress = debug + 'progress_' + num + '.txt'

an = open(anime_file, 'w', newline="\n", encoding='utf-8')
ch = open(character_file, 'w', newline="\n", encoding='utf-8')
stf = open(staff_file, 'w', newline="\n", encoding='utf-8')

p = open(progress, 'w')

r = csv.writer(an)
t = csv.writer(ch)
y = csv.writer(stf)

keys = ['id', 'name', 'name_japanese', 'name_english', 'format', 'episodes', 'airing_status',
        'airing_started', 'airing_finished', 'airing_premiere', 'producers', 'licensors',
        'studios', 'source', 'genres', 'duration', 'mal_age_rating', 'mal_score', 'mal_scored_by',
        'mal_rank', 'mal_popularity', 'mal_members', 'mal_favourites']
r.writerow(keys)
t.writerow(['id', 'character', 'voice'])
y.writerow(['id', 'staff'])

count = 0

f = open('to_parse/remaining_' + num + '.txt', 'r')
for line in f:
    sline = line.strip()
    data = {}

    if count >= 100:
        time.sleep(15)
        count = 0

    if sline:
        time.sleep(1)
        print(sline)
        smth = anime.get_anime(sline)
        data = smth[1]

        if data:
            # write in anime
            r.writerow(get_values(data, keys))

            # write in characters
            ani_id = data['id']
            k = data['char_voice']
            for v in k:
                character = v[0]
                actors = v[1:]
                for actor in actors:
                    t.writerow([ani_id, character, actor])

            # write in staff
            staffs = data['anime_staff']
            for staff in staffs:
                y.writerow([ani_id, staff])

    if data:
        p.write(sline + '\n')
        print("done", sline)

    count += 1

print('end')

an.close()
ch.close()
stf.close()

p.close()
