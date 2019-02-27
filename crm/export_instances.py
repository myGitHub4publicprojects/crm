from .models import (Patient, Audiogram, NewInfo, Hearing_Aid, NFZ_Confirmed,
                     NFZ_New, PCPR_Estimate, HA_Invoice, Audiogram, Reminder,
                     Invoice, Other_Item)

def get_hearing_aids():
    hearing_aid = {}
    for i in Hearing_Aid.objects.all():
        hearing_aid[i.id] = {'patient_id':i.patient.id,
                            'purchase_date': i.purchase_date,
                            'our': i.our,
                            'price_gross': i.price_gross,
                            'vat_rate': i.vat_rate,
                            'pkwiu_code': i.pkwiu_code,
                             'make': i.ha_make,
                             'family': i.ha_family,
                             'model': i.ha_model,
                             'ear': i.ear,
                             'current': i.current
                            }
        if i.invoice:
            hearing_aid[i.id]['invoice_id'] =  i.invoice.id
    print(len(hearing_aid))
    return hearing_aid


def get_invoice():
    inv = {}
    for i in Invoice.objects.all():
        inv[i.id] = {'patient_id': i.patient.id,
                    'timestamp': i.timestamp,
                    'updated': i.updated,
                    'type': i.type,
                    }
    print(len(inv))
    return inv

def get_pcpr_estimates():
    pcpr = {}
    for i in PCPR_Estimate.objects.all():
        pcpr[i.id] = {'patient_id': i.patient.id,
                    'date': i.date,
                    'in_progress': i.in_progress}

    print(len(pcpr))
    return pcpr

def get_other_item():
    items = {}
    for i in Other_Item.objects.all():
        items[i.id] = {'patient_id': i.patient.id,
                       'price_gross': i.price_gross,
                       'vat_rate': i.vat_rate,
                       'pkwiu_code': i.pkwiu_code,
                       'make': i.make,
                       'family': i.family,
                       'model': i.model,
                       }
        if i.invoice:
            items[i.id]['invoice_id'] = i.invoice.id
    print(len(items))
    return items

def get_ha_invoice():
    inv = {}
    for i in HA_Invoice.objects.all():
        inv[i.id] = {'patient_id': i.patient.id,
                  'date': i.date,
                  'in_progress': i.in_progress }
    print(len(inv))
    return inv


def get_reminder():
    rem = {}
    for i in Reminder.objects.all():
        rem[i.id] = {'active': i.active,
                     'timestamp': i.timestamp,
                     'activation_date': i.activation_date,
                     }
        if i.nfz_new:
            rem[i.id]['nfz_new_id'] = i.nfz_new.id

        if i.nfz_confirmed:
            rem[i.id]['nfz_confirmed_id'] = i.nfz_confirmed.id

        if i.pcpr:
            rem[i.id]['pcpr_id'] = i.pcpr.id

        if i.invoice:
            rem[i.id]['invoice_id'] = i.invoice.id

        if i.ha:
            rem[i.id]['ha_id'] = i.ha.id

    print(len(rem))
    return rem


