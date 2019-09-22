# -*- coding: utf-8 -*-
from .models import Hearing_Aid_Stock, Hearing_Aid, Other_Item, Other_Item_Stock

def stock_update(instance):
    '''accepts SZOI_File instance, on the basis of its file field:
    create new Hearing_Aid_Stock and Other_Item_Stock instances,
    upadates price for devices that are already in stock,
    returns a dict with created and updated HA and Other:
    {'ha_new': [<instance1>, <instance2], 'other_new': [<instance1>, <instance2>],
    'ha_update': [<instance1>, <instance2], 'other_update': [<instance1>, <instance2>]}'''
    res = {'ha_new': [], 'other_new': [], 'ha_update': [], 'other_update': []}
    file_path = instance.file.path
    f = open(file_path)

    def lines_over_8(f):
        for ii, line in enumerate(f):
            if ii >= 8:
                yield line

    # f = open("big text file.txt", "r")
    # for line in read_only_lines(f, 17, 34):
    # print line

    for i in lines_over_8(f):
        line = i.split(';')

        # assume price for adults and children are the same, avoid duplicates
        if 'PACJENCI DO UKOŃCZENIA 26 RŻ.' in line[7]:
            continue

        if 'APARAT SŁUCHOWY' in line[7]:
            # Audibel
            # START 1200  RIC 312T; START WIRELESS 1200I RIC 312; START WIRELESS 1200I RIC 312;
            # ARIES; A4 PLATINUM WIRELESS IIC;
            if 'STARKEY' in line[1]:
                make = 'Audibel'
                family_model = line[2].split()
                if len(family_model) > 1:
                    # there is a type in one of the registered names, hence:
                    if 'SILVERTRIC' in family_model:
                        family_model.remove('WRLS')
                        family = 'A4I SILVER'
                        model = 'WRLS ' + ' '.join(family_model[2:])
                        continue

                    if 'WIRELESS' in family_model:
                        family_model.remove('WIRELESS')
                        family = ' '.join(family_model[:2])
                        model = 'WRLS ' + ' '.join(family_model[2:])

                    if 'WRLS' in family_model:
                        family_model.remove('WRLS')
                        family = ' '.join(family_model[:2])
                        model = 'WRLS ' + ' '.join(family_model[2:])

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

            # check for existing Hearing_Aid_Stock instance with same make, family and model
            existing = Hearing_Aid_Stock.objects.filter(
                make=make,
                family=family,
                model=model,
            )

            # update price of the HA if needed
            if existing.exists():
                for ha in existing:
                    if ha.price_gross != price:
                        ha.price_gross = price
                        ha.save()
                        # update res
                        res['ha_update'].append(ha)

            else:
                # create Hearing_Aid_Stock instance
                ha = Hearing_Aid_Stock.objects.create(
                    make=make,
                    family=family,
                    model=model,
                    price_gross=price,
                    vat_rate=8,
                    pkwiu_code='26.60.14.0'
                )

                # update res
                res['ha_new'].append(ha)

        # Other_Item_Stock
        if 'SYSTEMY WSPOMAGAJĄCE SŁYSZENIE' in line[7] or 'WKŁADKA USZNA' in line[7]:
            if 'SYSTEMY WSPOMAGAJĄCE SŁYSZENIE' in line[7]:
                # make
                if 'AUDIO SERVICE' in line[1]:
                    make = 'Audioservice'
                if 'OTICON' in line[1]:
                    make = 'Oticon'
                if 'BERNAFON' in line[1]:
                    make = 'Bernafon'
                if ('PHONAK' in line[1] or 'SONOVA' in line[1]):
                    make = 'Phonak'
                family = line[5]
                model = line[2]
                price = line[8].split('.')
                price = int(price[0])
                pkwiu_code = '26.60.14.0'

            if 'WKŁADKA USZNA' in line[7]:
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
                family = 'WKŁADKA USZNA'
                model = line[2]
                price = line[8].split('.')
                price = int(price[0])
                pkwiu_code = '32.50.23.0'

            # check for existing Other_Item_Stock instance with same make, family and model
            existing = Other_Item_Stock.objects.filter(
                make=make,
                family=family,
                model=model,
            )

            # update price of the OI if needed
            if existing.exists():
                for o in existing:
                    if o.price_gross != price:
                        o.price_gross = price
                        o.save()
                        # update res
                        res['other_update'].append(o)

            else:
                # create Other_Item_Stock instance
                o = Other_Item_Stock.objects.create(
                    make=make,
                    family=family,
                    model=model,
                    price_gross=price,
                    vat_rate=8,
                    pkwiu_code=pkwiu_code
                )

                # update res
                res['other_new'].append(o)

    f.close()
    return res
