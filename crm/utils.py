# -*- coding: utf-8 -*-
import decimal
from .models import Hearing_Aid_Stock, Hearing_Aid, Other_Item

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


def get_ha_from_qs(queryset):
    """ returns a dict of devices in the following form:
    {make1_name:{family1_name:{model1_name:
    {'price': price, 'pkwiu': pkwiu, 'vat': vat, 'ear': ear}}}} """
    items = {}
    for i in queryset:
        make = i.make
        family = i.family
        model = i.model
        price = i.price_gross
        pkwiu = i.pkwiu_code
        vat = i.vat_rate
        ear = i.ear

        if make not in items:
            items[make] = {}

        if items[make].get(family):
            items[make][family].update({
                model: {'price': price, 'pkwiu': pkwiu, 'vat': vat}})
        else:
            items[make][family] = {
                model: {'price': price, 'pkwiu': pkwiu, 'vat': vat, 'ear': ear}}

    return items

def get_other_from_qs(queryset):
    """ returns a dict of devices in the following form:
    {make1_name:{family1_name:{model1_name:
    {'price': price, 'pkwiu': pkwiu, 'vat': vat, 'ear': ear}}}} """
    items = {}
    for i in queryset:
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
                    estimate=pcpr
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
                            estimate=pcpr
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
                            estimate=pcpr
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
                    invoice=invoice
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
                            invoice=invoice
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
                            invoice=invoice
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


def process_device_formset_proforma(formset, patient, proforma, today):
    for form in formset:
        # if hearing aid
        if form.cleaned_data['device_type'] == 'ha':
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
                    pro_forma=proforma
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
                            pro_forma=proforma
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
                            pro_forma=proforma
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
                    pro_forma=proforma
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
            net_price = round(((i.price_gross*100)/(100 + i.vat_rate)), 2)
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
        net_price = round(((i.price_gross*100)/(100 + i.vat_rate)), 2)
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
