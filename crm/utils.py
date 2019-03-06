# -*- coding: utf-8 -*-
from .models import Hearing_Aid_Stock

def get_ha_list():
    """ returns a dict of a hearing aid in the following form:
    {make1_name:{family1_name:{model1_name:price}}} """
    ha_list = {}
    for ha in Hearing_Aid_Stock.objects.all():
        make = ha.make
        family = ha.family
        model = ha.model
        price = ha.price_gross

        if make not in ha_list:
            ha_list[make] = {}

        if ha_list[make].get(family):
            ha_list[make][family].update({model: price})
        else:
            ha_list[make][family] = {model:price}

    return ha_list
