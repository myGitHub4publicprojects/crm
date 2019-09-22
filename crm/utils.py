# -*- coding: utf-8 -*-
import decimal
from .models import Hearing_Aid_Stock, Hearing_Aid, Other_Item, Other_Item_Stock

def get_devices(model):
    """ returns a dict of devices in the following form:
    {make1_name:{family1_name:{model1_name:price}}} """
    items = {}
    for i in model.objects.all():
        make = i.make
        family = i.family
        model = i.model
        price = i.price_gross
        pkwiu = i.pkwiu_code
        vat = i.vat_rate

        if make not in items:
            items[make] = {}

        if items[make].get(family):
            items[make][family].update({
                model: {'price': price, 'pkwiu': pkwiu, 'vat': vat}})
        else:
            items[make][family] = {
                model: {'price': price, 'pkwiu': pkwiu, 'vat': vat}}

    return items

def process_device_formset_pcpr(formset, patient, pcpr, today):
    for form in formset:
        # if hearing aid
        if form.cleaned_data['device_type'] == 'ha':
            print('creating aparat')
            # print(form)
            quantity = int(form.cleaned_data['quantity'])
            ear = form.cleaned_data['ear']
            if quantity==1:
                print('jeden')
                Hearing_Aid.objects.create(
                    patient=patient,
                    make=form.cleaned_data['make'],
                    family=form.cleaned_data['family'],
                    model=form.cleaned_data['model'],
                    purchase_date=today,
                    price_gross=form.cleaned_data['price_gross'],
                    vat_rate=form.cleaned_data['vat_rate'],
                    pkwiu_code = form.cleaned_data['pkwiu_code'],
                    ear = ear,
                    estimate=pcpr,
                    current=False
                )
            elif quantity==2 and ear=='both':
                    for i in ['left', 'right']:
                        Hearing_Aid.objects.create(
                            patient=patient,
                            make=form.cleaned_data['make'],
                            family=form.cleaned_data['family'],
                            model=form.cleaned_data['model'],
                            purchase_date=today,
                            price_gross=form.cleaned_data['price_gross'],
                            vat_rate=form.cleaned_data['vat_rate'],
                            pkwiu_code = form.cleaned_data['pkwiu_code'],
                            ear = i,
                            estimate=pcpr,
                            current=False
                        )

            elif quantity > 1:
                    for i in range(quantity):
                        Hearing_Aid.objects.create(
                            patient=patient,
                            make=form.cleaned_data['make'],
                            family=form.cleaned_data['family'],
                            model=form.cleaned_data['model'],
                            purchase_date=today,
                            price_gross=form.cleaned_data['price_gross'],
                            vat_rate=form.cleaned_data['vat_rate'],
                            pkwiu_code = form.cleaned_data['pkwiu_code'],
                            ear = ear,
                            estimate=pcpr,
                            current=False
                        )
        
        # if other device
        if form.cleaned_data['device_type'] == 'other':
            print('creating other item')
            print('Quant: ', form.cleaned_data['quantity'],)
            # how many to create: 'quantity'
            quantity = int(form.cleaned_data['quantity'])
            for i in range(quantity):
                Other_Item.objects.create(
                    patient=patient,
                    make=form.cleaned_data['make'],
                    family=form.cleaned_data['family'],
                    model=form.cleaned_data['model'],
                    price_gross=form.cleaned_data['price_gross'],
                    vat_rate=form.cleaned_data['vat_rate'],
                    pkwiu_code=form.cleaned_data['pkwiu_code'],
                    estimate=pcpr
                )


def process_device_formset_invoice(formset, patient, invoice, today):
    for form in formset:
        # if hearing aid
        if form.cleaned_data['device_type'] == 'ha':
            print('creating aparat')
            # print(form)
            quantity = int(form.cleaned_data['quantity'])
            ear = form.cleaned_data['ear']
            if quantity == 1:
                print('jeden')
                Hearing_Aid.objects.create(
                    patient=patient,
                    make=form.cleaned_data['make'],
                    family=form.cleaned_data['family'],
                    model=form.cleaned_data['model'],
                    purchase_date=today,
                    price_gross=form.cleaned_data['price_gross'],
                    vat_rate=form.cleaned_data['vat_rate'],
                    pkwiu_code=form.cleaned_data['pkwiu_code'],
                    ear=ear,
                    invoice=invoice,
                    current=False
                )
            elif quantity == 2 and ear == 'both':
                    for i in ['left', 'right']:
                        Hearing_Aid.objects.create(
                            patient=patient,
                            make=form.cleaned_data['make'],
                            family=form.cleaned_data['family'],
                            model=form.cleaned_data['model'],
                            purchase_date=today,
                            price_gross=form.cleaned_data['price_gross'],
                            vat_rate=form.cleaned_data['vat_rate'],
                            pkwiu_code=form.cleaned_data['pkwiu_code'],
                            ear=i,
                            invoice=invoice,
                            current=False
                        )

            elif quantity > 1:
                    for i in range(quantity):
                        Hearing_Aid.objects.create(
                            patient=patient,
                            make=form.cleaned_data['make'],
                            family=form.cleaned_data['family'],
                            model=form.cleaned_data['model'],
                            purchase_date=today,
                            price_gross=form.cleaned_data['price_gross'],
                            vat_rate=form.cleaned_data['vat_rate'],
                            pkwiu_code=form.cleaned_data['pkwiu_code'],
                            ear=ear,
                            invoice=invoice,
                            current=False
                        )

        # if other device
        if form.cleaned_data['device_type'] == 'other':
            print('creating other item')
            print('Quant: ', form.cleaned_data['quantity'],)
            # how many to create: 'quantity'
            quantity = int(form.cleaned_data['quantity'])
            for i in range(quantity):
                Other_Item.objects.create(
                    patient=patient,
                    make=form.cleaned_data['make'],
                    family=form.cleaned_data['family'],
                    model=form.cleaned_data['model'],
                    price_gross=form.cleaned_data['price_gross'],
                    vat_rate=form.cleaned_data['vat_rate'],
                    pkwiu_code=form.cleaned_data['pkwiu_code'],
                    invoice=invoice
                )

def get_finance_context(instance):  			
    total_value = 0
    nfz_ha_refund = 0
    ha = instance.hearing_aid_set.all()
    ha_items = {}
    for i in ha:
        total_value += i.price_gross
        nfz_ha_refund += 700
        if str(i) not in ha_items:
            if i.vat_rate == 'zwolniona':
                vat_rate_value = 0
            else:
                vat_rate_value = int(i.vat_rate)
            net_price = round(((i.price_gross*100)/(100 + vat_rate_value)), 2)
            ha_items[str(i)] = {
                            # 'name': str(i),
                                        'pkwiu_code': i.pkwiu_code,
                                        'quantity': 1,
                                        'price_gross': i.price_gross,
                                        'net_price': net_price,
                                        'net_value': net_price,
                                        'vat_rate': i.vat_rate,
                                        'vat_amount': round(i.price_gross - decimal.Decimal(net_price), 2),
                                        'gross_value': i.price_gross
                        }
        else:
            ha_items[str(i)]['quantity'] += 1
            current_quantity = ha_items[str(i)]['quantity']
            ha_items[str(i)]['net_value'] *= current_quantity
            ha_items[str(i)]['vat_amount'] *= current_quantity
            ha_items[str(i)]['gross_value'] *= current_quantity

    other_devices = instance.other_item_set.all()
    other_items = {}
    nfz_mold_refund = 0
    for i in other_devices:
        if i.vat_rate == 'zwolniona':
            vat_rate_value = 0
        else:
            vat_rate_value = int(i.vat_rate)
        net_price = round(((i.price_gross*100)/(100 + vat_rate_value)), 2)
        vat_amount = round(i.price_gross - decimal.Decimal(net_price), 2)
        total_value += i.price_gross
        if 'WKŁADKA' in str(i):
            nfz_mold_refund += 50
        if str(i) not in other_items:
            other_items[str(i)] = {
                            'pkwiu_code': i.pkwiu_code,
                                        'quantity': 1,
                                        'price_gross': i.price_gross,
                                        'net_price': net_price,
                                        'net_value': net_price,
                                        'vat_rate': i.vat_rate,
                                        'vat_amount': vat_amount,
                                        'gross_value': i.price_gross
                        }
        else:
            other_items[str(i)]['quantity'] += 1
            current_quantity = other_items[str(i)]['quantity']
            other_items[str(i)]['net_value'] += net_price
            other_items[str(i)]['vat_amount'] += vat_amount
            other_items[str(i)]['gross_value'] += i.price_gross

    context = {	'ha_list': ha_items,
				'other_list': other_items,
				'nfz_ha_refund': nfz_ha_refund,
				'nfz_mold_refund': nfz_mold_refund,
				'nfz_total_refund': nfz_ha_refund + nfz_mold_refund,
				'difference': total_value - (nfz_ha_refund + nfz_mold_refund),
                'instance': instance,
				'total_value': total_value}
    return context


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
        for ii,line in enumerate(f):
            if ii>=8:
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
