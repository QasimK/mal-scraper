# -*- coding: utf-8 -*-

import csv
import ast


def blend_files(somh, output='default.txt'):
    o = open(output, 'w', encoding='utf-8')
    for ff in somh:
        f = open(ff, 'r', encoding='utf-8')
        for line in f:
            o.write(line)  # or is it line+\n?
        f.close()
    o.close()


def file_complement(universe, file, output='default.txt'):
    un = open(universe, 'r', encoding='utf-8')
    f = open(file, 'r', encoding='utf-8')
    o = open(output, 'w', encoding='utf-8')

    a_list = []
    for line in f:
        a_list.append(int(line))
    for line in un:
        an_int = int(line)
        if not (an_int in a_list):
            o.write(str(an_int)+'\n')

    un.close()
    f.close()
    o.close()


def replace_by_id(file, output='default.txt'):
    f = open(file, 'r', encoding='utf-8')
    o = open(output, 'w', encoding='utf-8')

    for line in f:
        if line.strip():
            id_ = line.split('/')[4]
            o.write(id_+'\n')

    f.close()
    o.close()


def get_ids(file, output='default.txt'):
    f = open(file, 'r', encoding='utf-8')
    o = open(output, 'w', encoding='utf-8')
    cont = 0
    for line in f:
        if cont == 0:
            pass
        elif line.strip():
            a = int(line.split(',')[0].strip())
            o.write(str(a)+'\n')
        cont += 1
    f.close()
    o.close()


def list_add(a_list, args):
    for a in args:
        a_list.append(a)


def correct_anime(file, out_general, out_date, out_p, out_li, out_st, out_gen):
    f = open(file, 'r', newline="\n", encoding='utf-8')
    o0 = open(out_general, 'w', newline="\n", encoding='utf-8')
    o1 = open(out_date, 'w', newline="\n", encoding='utf-8')
    o2 = open(out_p, 'w', newline="\n", encoding='utf-8')
    o3 = open(out_li, 'w', newline="\n", encoding='utf-8')
    o4 = open(out_st, 'w', newline="\n", encoding='utf-8')
    o5 = open(out_gen, 'w', newline="\n", encoding='utf-8')

    oo0 = csv.writer(o0)
    oo1 = csv.writer(o1)
    oo2 = csv.writer(o2)
    oo3 = csv.writer(o3)
    oo4 = csv.writer(o4)
    oo5 = csv.writer(o5)
    count = 0
    for line in csv.reader(f):
        if count == 0:
            oo0.writerow(['anime_id', 'name', 'name_jap', 'name_en', 'format', 'episodes',
                          'airing_status', 'premiere_year', 'premiere_season', 'source', 'duration',
                          'rating', 'score', 'scored_by', 'rank', 'popularity', 'members', 'favourites'])
            oo1.writerow(['anime_id', 'start_year', 'start_month',
                          'start_day', 'finish_year', 'finish_month', 'finish_day'])
            oo2.writerow(['anime_id', 'producer'])
            oo3.writerow(['anime_id', 'licensor'])
            oo4.writerow(['anime_id', 'studio'])
            oo5.writerow(['anime_id', 'genre'])

        else:
            line_parts = []
            for l in line:
                # print(l)
                line_parts.append(l.strip())

            # Parts of the data line
            ani_id = line_parts[0]
            name = line_parts[1]
            name_jap = line_parts[2]
            name_en = line_parts[3]
            ani_format = line_parts[4]  # Unknown
            episodes = line_parts[5]
            airing = line_parts[6]
            started = line_parts[7]  # [y,m,d] can be None y NULL
            finished = line_parts[8]  # [y,m,d] can be None y NULL
            premiere = line_parts[9]  # [y,s] can be NULL
            producers = ast.literal_eval(line_parts[10])  # None found, add some
            licensors = ast.literal_eval(line_parts[11])  # None found, add some
            studios = ast.literal_eval(line_parts[12])  # None found, add some
            source = line_parts[13]  # Unknown
            genres = ast.literal_eval(line_parts[14])  # No genres have been added yet.
            duration = line_parts[15]  # Unknown
            age = line_parts[16]  # None
            score = line_parts[17]
            score_by = line_parts[18]
            rank = line_parts[19]
            popu = line_parts[20]
            members = line_parts[21]
            fav = line_parts[22]

            # to be writen
            table_general = []
            table_date = []

            # check for inconsistencies in GENERAL table
            if ani_format == 'Unknown':
                ani_format = ''
            if source == 'Unknown':
                source = ''
            if duration == 'Unknown':
                duration = ''
            if age == 'None':
                age = ''
            premiere_year = ''
            premiere_season = ''
            if premiere:  # if premiere is not NULL
                n_premiere = ast.literal_eval(line_parts[9])
                premiere_year = n_premiere[0]
                premiere_season = n_premiere[1]

            list_add(table_general, [ani_id, name, name_jap, name_en, ani_format, episodes, airing,
                                     premiere_year, premiere_season, source, duration, age, score, score_by, rank,
                                     popu, members, fav])
            oo0.writerow(table_general)

            # check for DATE table
            started_year = 0
            started_month = 0
            started_day = 0
            if started:  # if not NULL
                n_started = ast.literal_eval(started)
                started_year = n_started[0]
                if str(n_started[1]) != 'None':
                    started_month = n_started[1]
                if str(n_started[2]) != 'None':
                    started_day = n_started[2]
            finished_year = 0
            finished_month = 0
            finished_day = 0
            if finished:   # if not NULL
                n_finished = ast.literal_eval(finished)
                finished_year = n_finished[0]
                if str(n_finished[1]) != 'None':
                    finished_month = n_finished[1]
                if str(n_finished[2]) != 'None':
                    finished_day = n_finished[2]

            list_add(table_date, [ani_id, started_year, started_month, started_day,
                                  finished_year, finished_month, finished_day])
            oo1.writerow(table_date)

            # check for PRODUCER table
            for p in producers:
                if str(p) == 'None found':
                    oo2.writerow([ani_id, ''])
                    break
                else:
                    oo2.writerow([ani_id, p])

            # check for LICENSOR table
            for l in licensors:
                if str(l) == 'None found':
                    oo3.writerow([ani_id, ''])
                    break
                else:
                    oo3.writerow([ani_id, l])

            # check for LICENSOR table
            for s in studios:
                if str(s) == 'None found':
                    oo4.writerow([ani_id, ''])
                    break
                else:
                    oo4.writerow([ani_id, s])

            # check for LICENSOR table
            for g in genres:
                if str(g) == 'No genres have been added yet.':
                    oo5.writerow([ani_id, ''])
                    break
                else:
                    oo5.writerow([ani_id, g])

        count += 1

    o0.close()
    o1.close()
    o2.close()
    o3.close()
    o4.close()
    o5.close()


def correct_character(file, out):
    f = open(file, 'r', newline="\n", encoding='utf-8')
    o = open(out, 'w', newline="\n", encoding='utf-8')

    oo = csv.writer(o)
    count = 0
    for line in csv.reader(f):
        if count == 0:
            oo.writerow(['anime_id', 'character_id', 'character_name', 'character_type',
                        'voice_actor_id', 'voice_actor_name', 'voice_actor_language'])

        else:
            line_parts = []
            for l in line:
                line_parts.append(l.strip())

            # Parts of the data line
            ani_id = line_parts[0]
            character = ast.literal_eval(line_parts[1])
            voice_actor = ast.literal_eval(line_parts[2])

            oo.writerow([ani_id, character[0], character[1], character[2],
                         voice_actor[0], voice_actor[1], voice_actor[2]])

        count += 1

    o.close()


def correct_staff(file, out):
    f = open(file, 'r', newline="\n", encoding='utf-8')
    o = open(out, 'w', newline="\n", encoding='utf-8')

    oo = csv.writer(o)
    count = 0
    for line in csv.reader(f):
        if count == 0:
            oo.writerow(['anime_id', 'people_id', 'staff_name', 'staff_position'])

        else:
            line_parts = []
            for l in line:
                line_parts.append(l.strip())

            # Parts of the data line
            ani_id = line_parts[0]
            staff = ast.literal_eval(line_parts[1])

            staff_id = staff[0]
            staff_name = staff[1]
            positions = str(staff[2]).split(',')
            for pos in positions:
                oo.writerow([ani_id, staff_id, staff_name, pos])

        count += 1

    o.close()


# asd = []
# txt = ['csv_anime_', '.txt']
# k=1
# while k < 8:
#     qwe = 'testsss/'+txt[0]+str(k)+txt[1]
#     asd.append(qwe)
#     k+=1
#
# blend_files(asd, 'testsss/progress_9_mixed.txt')
# replace_by_id('testsss/progress_9_mixed.txt', 'testsss/asd.txt')
# replace_by_id('testsss/jp.txt', 'testsss/id_total_file.txt')
# blend_files(['testsss/asd.txt','testsss/progress_8.txt'], 'testsss/id_file.txt')
#
# file_complement('testsss/id_total_file.txt', 'testsss/id_file.txt', 'testsss/final.txt')

# a = []
# out = []
# path = ['results/Isidora/csv_anime','.csv']
# k=1
# while k<8:
#     a.append(path[0]+str(k)+path[1])
#     out.append('results/Isidora/'+str(k) + '_out'+ path[1])
#     k+=1
#
# k=1
# while k<8:
#     get_ids(a[k-1], out[k-1])
#     k+=1
#
# blend_files(out, path[0]+'isidora_done.txt')

# r = 'results/final/'
# f_format = ['f_', '.csv']
# a = 'anime'
# c = 'characters'
# s = 'staff'
#
# a_files = []
# c_files = []
# s_files = []
#
# for i in range(1,5):
#     a_files.append(r + f_format[0] + a + str(i) + f_format[1])
#     c_files.append(r + f_format[0] + c + str(i) + f_format[1])
#     s_files.append(r + f_format[0] + s + str(i) + f_format[1])
#
# for i in range(1,4):
#     blend_files(a_files, r + a + f_format[1])
#     blend_files(c_files, r + c + f_format[1])
#     blend_files(s_files, r + s + f_format[1])

r = 'results/'
t = 'tables/'
staff = 'staff.csv'

# correct_anime(r+anime, r+t+'general.csv',r+t+'date.csv',r+t+'producers.csv',r+t+'licensors.csv',
#               r + t + 'studio.csv',r+t+'genre.csv')
correct_staff(r + staff, r + t + 'staff.csv')