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
    var head = style + date + sonovox + documentTitle;

    var patientName = document.getElementById('patientName');
    var name = '<p>Imię i Nazwisko: ' + patientName.innerText + '</p><hr>';

    var address1 = document.getElementById('address1').innerText;
    var address2 = document.getElementById('address2').innerText;
    var address = "<p>Adres zamieszkania: " + address1 + ', ' + address2 + "</p><hr>";

    var table = document.getElementsByClassName('table')[0];
    var patient = name + address;

    var nfz = document.getElementById('nfz_refund').outerHTML;
    var accNo = '<p>Przelew na konto: 40 1160 2202 0000 0002 5500 6585</p><hr>';
    var currentYear = new Date().getFullYear();
    var dopisek = '<p style="position: fixed; bottom: 150px; left: 100px;"><small>Do realizacji do 31.12.' + currentYear + '</small></p>';
    var divClose = '</div>';
    var printContents = head + patient + table.outerHTML +  nfz + accNo + dopisek + divClose;
    var originalContents = document.body.innerHTML;

    document.body.innerHTML = printContents;

    window.print();

    document.body.innerHTML = originalContents;
}