# -*- coding: utf-8 -*-
import traceback
import xlrd

from .models import Hearing_Aid_Stock, Hearing_Aid, SZOI_Errors

def get_line_from_8th(f):
    '''accepts a path to an xls file, yields a list (9 elements, 8 strings and 1 float),
    skips the first 7 lines'''
    wb = xlrd.open_workbook(f)
    sheet = wb.sheet_by_index(0)
    for i in range(sheet.nrows):
        if i > 7:
            yield sheet.row_values(i)


def process_HA(line):
    '''accepts a list (line of a xls file), returns a dict with make, family, model'''
    res = {}
    # Audibel
    # START 1200  RIC 312T; START WIRELESS 1200I RIC 312; START WIRELESS 1200I RIC 312;
    # ARIES; A4 PLATINUM WIRELESS IIC;
    # 'A4 IQ', 'model: ', 'WRLS GOLD CIC'
    # 'family: ', 'START IQ', 'model: ', 'WRLS 1000 BTE 13 PWRPLS')
    if 'STARKEY' in line[1]:
        make = 'Audibel'
        family_model = line[2].split()
        if len(family_model) > 1:
            # there is a type in one of the registered names, hence:
            if 'SILVERTRIC' in family_model:
                family_model.remove('WRLS')
                family = 'A4I SILVER'
                model = 'WRLS ' + ' '.join(family_model[2:])
                
            else:
                if 'WIRELESS' in family_model:
                    family_model.remove('WIRELESS')
                    if 'IQ' in family_model:
                        family = ' '.join(family_model[:3])
                        model = 'WRLS ' + ' '.join(family_model[3:])
                    else:
                        family = ' '.join(family_model[:2])
                        model = 'WRLS ' + ' '.join(family_model[2:])

                if 'WRLS' in family_model:
                    family_model.remove('WRLS')
                    if 'IQ' in family_model:
                        family = ' '.join(family_model[:3])
                        model = 'WRLS ' + ' '.join(family_model[3:])
                    else:
                        family = ' '.join(family_model[:2])
                        model = 'WRLS ' + ' '.join(family_model[2:])

                else:
                    if 'IQ' in family_model:
                        family = ' '.join(family_model[:3])
                        model = ' '.join(family_model[3:])
                    else:
                        family = ' '.join(family_model[:2])
                        model = ' '.join(family_model[2:])
        else:
            family = family_model[0]
            model = family_model[0]


    # Bernafon
    # there might be 2 typos in the file: JUNA7 NANO (JUNA 7) and ZERENA5 (ZERENA 5)
    if 'BERNAFON' in line[1]:
        make = 'Bernafon'
        family_model = line[2].split()  # ZERENA 5 B 105; WIN 102
        family = family_model[0]
        if family == 'ZERENA5':
            family = 'ZERENA 5'
        if family == 'JUNA7':
            family = 'JUNA 7'
        if len(family_model) > 2:
            family += ' ' + family_model[1]
            model = ' '.join(family_model[2:])
        else:
            model = family_model[1]


    # Phonak
    # in some Phonak/Sonova products name includes a brand
    # ie: PHONAK NAIDA B50-UP
    # ie: BOLERO B 30 M
    if ('PHONAK' in line[1] or 'SONOVA' in line[1]):
        make = 'Phonak'
        family_model = line[2].split()
        if 'PHONAK' in family_model[0]:
            family = family_model[1]
            model = ' '.join(family_model[2:])
        else:
            family = family_model[0]
            model = ' '.join(family_model[1:])

    # Oticon
    if 'OTICON' in line[1]:
        make = 'Oticon'
        family_model = line[2].split()  # HIT PRO BTE POWER
        family = family_model[0]
        model = ' '.join(family_model[1:])

    # Audioservice
    if 'AUDIO SERVICE' in line[1]:
        make = 'Audioservice'
        family_model = line[2].split()  # SINA HYPE 12 G4
        family = family_model[0]
        model = ' '.join(family_model[1:])

    # Interton
    if 'INTERTON' in line[1]:
        make = 'Interton'
        family_model = line[2].split()
        family = family_model[0]
        model = ' '.join(family_model[1:]) + ' ' + line[5]

    # Siemens
    if 'SIEMENS' in line[1]:
        make = 'Siemens'
        family_model = line[2].split()
        family = family_model[0]
        model = ' '.join(family_model[1:])

    # BHM
    if 'BHM TECH' in line[1]:
        make = 'BHM TECH'
        family_model = line[2].split()
        family = family_model[0]
        model = ' '.join(family_model[1:])
    
    res['make'] = make
    res['family'] = family
    res['model'] = model

    return res

def process_Other(line):
    '''accepts a line of a csv file, returns a dict with make, family, model of an Other_Item_Stock device'''
    res = {}
        # make
    if 'STARKEY' in line[1]:
        make = 'Audibel'
    if 'AUDIO SERVICE' in line[1]:
        make = 'Audioservice'
    if 'OTICON' in line[1]:
        make = 'Oticon'
    if 'BERNAFON' in line[1]:
        make = 'Bernafon'
    if ('PHONAK' in line[1] or 'SONOVA' in line[1]):
        make = 'Phonak'
    
    model = line[2]

    if 'P.087.' in line[6]:
        family = line[5]

    if 'P.086.' in line[6]:
        family = 'WKŁADKA USZNA'
    
    res['make'] = make
    res['family'] = family
    res['model'] = model
    return res

def create_if_notexists(items_class, item):
    '''accepts a dict with make, family, model,
    create a new one,
    returns a dict with created instance'''
    res = {'new': None}
    # check for existing instance with same make, family and model
    existing = items_class.objects.filter(
        make=item['make'],
        family=item['family'],
        model=item['model'],
    )

    # update price if needed
    if not existing.exists():
        i = items_class.objects.create(
            make=item['make'],
            family=item['family'],
            model=item['model'],
        )

        # update res
        res['new'] = i

    return res


def stock_update(szoi_file, szoi_file_usage):
    '''accepts SZOI_File and SZOI_File_Usage instance:
    create new Hearing_Aid_Stock and Other_Item_Stock instances,
    if errors occure create SZOI_Error instance,
    returns a dict with created and updated HA and Other:
    {'ha_new': [<instance1>, <instance2], 'other_new': [<instance1>, <instance2>]}'''
    res = {'ha_new': [], 'other_new': []}
    file_path = szoi_file.file.path
    counterTotal = 0
    counterHA = 0
    counterOther = 0
    counterKids = 0
    for i in get_line_from_8th(file_path):
        counterTotal +=1
        try:
            # assume price for adults and children are the same, avoid duplicates,
            # allow phonak Rogers (P.087)
            if '.01' in i[6] and not ('P.087.' in i[6]):
                counterKids += 1
                continue

            # Hearing_Aid_Stock
            elif 'P.084.' in i[6] or 'P.085.' in i[6]:
                counterHA += 1
                # create a dict from a line
                HA = process_HA(i)
                # update exisitng or create new HA instance
                u = create_if_notexists(Hearing_Aid_Stock, HA)

                if u['new'] != None:
                    res['ha_new'].append(u['new'])

            # Other_Item_Stock
            elif 'P.086.' in i[6] or 'P.087.' in i[6]:
                counterOther += 1
                # create a dict from a line
                other = process_Other(i)
                # update existing or create new device instance
                u = create_if_notexists(Other_Item_Stock, other)

                if u['new'] != None:
                    res['other_new'].append(u['new'])
            
            else:
                SZOI_Errors.objects.create(
                    szoi_file_usage=szoi_file_usage,
                    error_log='"Kod środka" not recognized"',
                    line=i
                )
        
        except:
            SZOI_Errors.objects.create(
                szoi_file_usage=szoi_file_usage,
                error_log=traceback.format_exc(),
                line = i
            )
    return res
