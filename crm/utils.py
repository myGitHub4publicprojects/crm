# -*- coding: utf-8 -*-
from .models import Hearing_Aid_Stock, Hearing_Aid, Other_Item

def get_ha_list():
    """ returns a dict of a hearing aid in the following form:
    {make1_name:{family1_name:{model1_name:price}}} """
    ha_list = {}
    for ha in Hearing_Aid_Stock.objects.all():
        make = ha.make
        family = ha.family
        model = ha.model
        price = ha.price_gross
        pkwiu = ha.pkwiu_code
        vat = ha.vat_rate

        if make not in ha_list:
            ha_list[make] = {}

        # if ha_list[make].get(family):
        #     ha_list[make][family].update({model: price})
        # else:
        #     ha_list[make][family] = {model:price}

        if ha_list[make].get(family):
            ha_list[make][family].update({
                model: {'price': price, 'pkwiu': pkwiu, 'vat': vat}})
        else:
            ha_list[make][family] = {
                model: {'price': price, 'pkwiu': pkwiu, 'vat': vat}}

    return ha_list


def process_device_formset(formset, patient, invoice, today):
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
                    invoice=invoice
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
                            pkwiu_code = form.cleaned_data['pkwiu_code'],
                            ear = ear,
                            invoice=invoice
                        )
        
        # if other device
        if form.cleaned_data['device_type'] == 'other':
            print('creating other item')
            print('Quant: ', form.cleaned_data['quantity'],)
            # how many to create: 'quantity'

            Other_Item.objects.create(
                patient=patient,
                make=form.cleaned_data['make'],
                family=form.cleaned_data['family'],
                model=form.cleaned_data['model'],
                price_gross=form.cleaned_data['price_gross'],
                vat_rate=form.cleaned_data['vat_rate'],
                pkwiu_code = form.cleaned_data['pkwiu_code'],
                invoice=invoice
            )
