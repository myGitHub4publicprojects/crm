# -*- coding: utf-8 -*-
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

        # if ha_list[make].get(family):
        #     ha_list[make][family].update({model: price})
        # else:
        #     ha_list[make][family] = {model:price}

        if items[make].get(family):
            items[make][family].update({
                model: {'price': price, 'pkwiu': pkwiu, 'vat': vat}})
        else:
            items[make][family] = {
                model: {'price': price, 'pkwiu': pkwiu, 'vat': vat}}

    return items


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
