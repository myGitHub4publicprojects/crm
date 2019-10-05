function printDiv() {
    var style = '<div style="padding: 50px;">';
    var date = document.getElementById('date').innerText;
    
    var sVox = '<p style="padding-left: 20%;"><small>SONOVOX<br>Aparaty Słuchowe<br>';
    var sVox1 = 'Barbara Golon-Szczepaniak<br>';
    var sVox2 = 'ul. Wagi 6 m 1, 61-244 Poznań<br>';
    var sVox3 = 'NIP 782-137-75-19, Regon 302634863<br>';
    var sVox4 = 'tel. 721 210 180</small></p>';
    var headDivLeft = '<div style="width: 50%; float: left;">'
    var sonovox = headDivLeft + sVox + sVox1 + sVox2 + sVox3 + sVox4 + '</div>';
    var documentType = document.getElementById('documentType').innerText;
    var documentTitle = '<h1 style="text-align:center; clear:both;">' + documentType + '</h1>';
    var originalDoc = document.getElementById('originalDoc').innerText;
    originalDoc = '<p>' + originalDoc + '</p>';
    var h3Seller = '<h3 style="text-align:center;">Sprzedawca</h3>'
    var seller = headDivLeft + h3Seller + '<hr>' + sVox + sVox1 + sVox2 + sVox3 + '</div>';

    var h3Buyer = '<h3 style="text-align:center;">Nabywca</h3>'
    var patientName = document.getElementById('patientName');
    var name = '<p style="padding-left: 20%;">Nazwa: ' + patientName.innerText + '<br>';

    var address1 = document.getElementById('address1').innerText;
    var address2 = document.getElementById('address2').innerText;
    var address = "Adres: " + address1 + ', ' + address2;
    if (nip) {
        address += '<br>NIP: ' + nip;
    }

    var buyer = headDivLeft + h3Buyer + '<hr>' + name + address + '</p></div>';

    var tables = document.getElementById('tables');


    var headDivRight = '<div style="width: 50%; float: right;">'
    var invoiceDetailsDiv = headDivRight + '<p style="padding-left: 20%;">' + date + '</p></div>';

    var head = style + sonovox + invoiceDetailsDiv + documentTitle + originalDoc + seller + buyer;
    var items = '<h2 style="text-align:center; clear:both;">Pozycje</h2>' + tables.outerHTML;

    var printContents =  head + items;

    var invoiceNote = document.getElementById('note');
    if (invoiceNote) {
        invoiceNote = invoiceNote.innerHTML;
        printContents += invoiceNote;
    }
    var footer = '<br><p style="float: right;">Osoba upoważniona do wystawienia dokumentu:</p></div>';
    printContents += footer;

    var originalContents = document.body.innerHTML;

    document.body.innerHTML = printContents;

    window.print();

    document.body.innerHTML = originalContents;
}