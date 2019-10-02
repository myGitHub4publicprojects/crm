# -*- coding: utf-8 -*-
import traceback

from .models import Hearing_Aid_Stock, Hearing_Aid, Other_Item, Other_Item_Stock, SZOI_Errors

def lines_over_8(f):
    # enables to iterate over lines in a field starting from the 8th line, yields one line
        for ii, line in enumerate(f):
            if ii >= 8:
                yield line

def process_HA(line):
    '''accepts a line of a csv file, returns a dict with make, family, model, price 
    and pkwiu_code'''
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
        price = line[8].split('.')
        price = int(price[0])

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
        price = line[8].split('.')
        price = int(price[0])

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
        price = line[8].split('.')
        price = int(price[0])

    # Oticon
    if 'OTICON' in line[1]:
        make = 'Oticon'
        family_model = line[2].split()  # HIT PRO BTE POWER
        family = family_model[0]
        model = ' '.join(family_model[1:])
        price = line[8].split('.')
        price = int(price[0])

    # Audioservice
    if 'AUDIO SERVICE' in line[1]:
        make = 'Audioservice'
        family_model = line[2].split()  # SINA HYPE 12 G4
        family = family_model[0]
        model = ' '.join(family_model[1:])
        price = line[8].split('.')
        price = int(price[0])

    # Interton
    if 'INTERTON' in line[1]:
        make = 'Interton'
        family_model = line[2].split()
        family = family_model[0]
        model = ' '.join(family_model[1:]) + ' ' + line[5]
        price = line[8].split('.')
        price = int(price[0])

    # Siemens
    if 'SIEMENS' in line[1]:
        make = 'Siemens'
        family_model = line[2].split()
        family = family_model[0]
        model = ' '.join(family_model[1:])
        price = line[8].split('.')
        price = int(price[0])

    # BHM
    if 'BHM TECH' in line[1]:
        make = 'BHM TECH'
        family_model = line[2].split()
        family = family_model[0]
        model = ' '.join(family_model[1:])
        if not 'WYŁĄCZENIEM APARATÓW' in line[8]:
            price = line[8].split('.')
        else:
            price = line[9].split('.')
        price = int(price[0])
    
    res['make'] = make
    res['family'] = family
    res['model'] = model
    res['price'] = price
    res['pkwiu_code'] = '26.60.14.0'
    return res

def process_Other(line):
    '''accepts a line of a csv file, returns a dict with make, family, model, price 
    and pkwiu_code of an Other_Item_Stock device'''
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
    price = line[8].split('.')
    price = int(price[0])

    if 'SYSTEMY WSPOMAGAJĄCE SŁYSZENIE' in line[7]:
        family = line[5]
        pkwiu_code = '26.60.14.0'

    if 'WKŁADKA USZNA' in line[7]:
        family = 'WKŁADKA USZNA'
        pkwiu_code = '32.50.23.0'
    
    res['make'] = make
    res['family'] = family
    res['model'] = model
    res['price'] = price
    res['pkwiu_code'] = pkwiu_code
    return res

def update_or_create(items_class, item):
    '''accepts a dict with make, family, model, price and pkwiu_code,
    updates existing instance of create a new one,
    returns a dict with created and updated instances'''
    res = {'new': None, 'update': None}
    # check for existing instance with same make, family and model
    existing = items_class.objects.filter(
        make=item['make'],
        family=item['family'],
        model=item['model'],
    )

    # update price if needed
    if existing.exists():
        for i in existing:
            if i.price_gross != item['price']:
                i.price_gross = item['price']
                i.save()
                # update res
                res['update'] = i

    else:
        # create instance
        i = items_class.objects.create(
            make=item['make'],
            family=item['family'],
            model=item['model'],
            price_gross=item['price'],
            vat_rate=8,
            pkwiu_code=item['pkwiu_code']
        )

        # update res
        res['new'] = i

    return res


def stock_update(szoi_file, szoi_file_usage):
    '''accepts SZOI_File and SZOI_File_Usage instance:
    create new Hearing_Aid_Stock and Other_Item_Stock instances,
    upadates price for devices that are already in stock,
    if errors occure create SZOI_Error instance,
    returns a dict with created and updated HA and Other:
    {'ha_new': [<instance1>, <instance2], 'other_new': [<instance1>, <instance2>],
    'ha_update': [<instance1>, <instance2], 'other_update': [<instance1>, <instance2>]}'''
    res = {'ha_new': [], 'other_new': [], 'ha_update': [], 'other_update': []}
    file_path = szoi_file.file.path
    f = open(file_path)

    for i in lines_over_8(f):
        line = i.split(';')
        try:
            # assume price for adults and children are the same, avoid duplicates
            if 'PACJENCI DO UKOŃCZENIA 26 RŻ.' in line[7]:
                continue

            # Hearing_Aid_Stock
            elif 'APARAT SŁUCHOWY' in line[7]:
                # create a dict from a line
                HA = process_HA(line)
                # update exisitng or create new HA instance
                u = update_or_create(Hearing_Aid_Stock, HA)

                if u['new'] != None:
                    res['ha_new'].append(u['new'])
                if u['update'] != None:
                    res['ha_update'].append(u['update'])

            # Other_Item_Stock
            elif 'SYSTEMY WSPOMAGAJĄCE SŁYSZENIE' in line[7] or 'WKŁADKA USZNA' in line[7]:
                # create a dict from a line
                other = process_Other(line)
                # update existing or create new device instance
                u = update_or_create(Other_Item_Stock, other)

                if u['new'] != None:
                    res['other_new'].append(u['new'])
                if u['update'] != None:
                    res['other_update'].append(u['update'])
            
            else:
                SZOI_Errors.objects.create(
                    szoi_file_usage=szoi_file_usage,
                    error_log='Eight item in a line as other than expected text',
                    line=i
                )
        
        except:
            SZOI_Errors.objects.create(
                szoi_file_usage=szoi_file_usage,
                error_log=traceback.format_exc(),
                line = i
            )
    f.close()
    return res
