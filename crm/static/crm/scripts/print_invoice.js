function printDiv() {
    var style = '<div style="padding: 50px;">';
    var date = document.getElementById('date');
    date=date.innerText.substring(12);
    date = '<p style="text-align:right;">Data: ' + date + '</p>';

    var sVox = '<p><small>SONOVOX<br>Aparaty Słuchowe<br>';
    var sVox1 = 'Barbara Golon-Szczepaniak<br>';
    var sVox2 = 'ul. Wagi 6 m 1, 61-244 Poznań<br>';
    var sVox3 = 'NIP 782-137-75-19, Regon 302634863<br>';
    var sVox4 = 'tel. 721 210 180</small></p>';
    var sonovox = sVox+sVox1+sVox2+sVox3+sVox4;
    var documentType = document.getElementById('documentType').innerText;
    if (documentType.startsWith('Faktura')){
        documentType += ' nr: ' + document.getElementById('documentNo').innerText;
    }
    var documentTitle = '<h1 style="text-align:center;">' + documentType + '</h1>';
    var invoiceType = document.getElementById('invoiceType');
    invoiceType = '<p>Płatność: ' + invoiceType.innerText + '</p>';
    var head = style + date + sonovox + documentTitle + invoiceType;

    var patientName = document.getElementById('patientName');
    var name = '<p>Imię i Nazwisko: ' + patientName.innerText + '</p><hr>';

    var address1 = document.getElementById('address1').innerText;
    var address2 = document.getElementById('address2').innerText;
    var address = "<p>Adres zamieszkania: " + address1 + ', ' + address2 + "</p><hr>";

    var table = document.getElementsByClassName('table')[0];
    var patient = name + address;
    var invoiceNote = document.getElementById('invoiceNote');
    if (invoiceNote){
        invoiceNote = invoiceNote.innerText;
    }
    var divClose = '</div>';
    var printContents = head + patient + table.outerHTML + divClose;
    var originalContents = document.body.innerHTML;

    document.body.innerHTML = printContents;

    window.print();

    document.body.innerHTML = originalContents;
}