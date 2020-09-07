# -*- coding: utf-8 -*-
from .models import Hearing_Aid_Stock, Hearing_Aid, Other_Item, Other_Item_Stock

def get_devices(model):
    """ returns a dict of devices in the following form:
    {make1_name:{family1_name:[model1_name,]}} """
    items = {}
    for i in model.objects.all():
        make = i.make
        family = i.family
        model = i.model

        if make not in items:
            items[make] = {family:[model]}
        else:
            if not items[make].get(family):
                items[make][family]=[model]
            else:
                if model not in items[make][family]:
                    items[make][family].append(model)

    return items