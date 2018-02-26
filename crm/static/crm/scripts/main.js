function printDiv() {
    var style = '<div style="padding: 50px;">';
    var head = '<h1 style="text-align:center;">Kosztorys</h1>'
    var fname = document.querySelector('[name="fname"]').value;
    var lname = document.querySelector('[name="lname"]').value;
    var name = '<p>Imię i Nazwisko: ' + fname + ' ' + lname + '</p><hr>';
    var address = "<p>Adres: .............................................</p><hr>"
    var ha = '<p>Aparat: '
    var left_ha = document.getElementById('left_PCPR_ha');
    if (left_ha) {
        ha += left_ha.innerHTML;
    }
    var right_ha = document.getElementById('right_PCPR_ha');
    if (right_ha) {
        ha += ' ' + right_ha.innerHTML;
        if (left_ha == right_ha) {
            ha = '2x: ' + left_ha.innerHTML;
        }
    }

    var wkladka = '</p><hr><p>Wkładka uszna: </p><hr>';
    var rest = '<p>Koszt aparatu: </p><hr><p>Koszt wkładki: </p><hr><p>Dofinansowanie NFZ: </p><hr><p>Udział własny: </p><hr>';
    var accNo = '<p>Numer konta: </p><hr>';
    var dopisek = '<p style="position: fixed; bottom: 20px; left: 100px;"><small>Do realizacji do 31.12.2018</small></p>';
    var divClose = '</div>'
    var printContents = style + head + name + address + ha + wkladka + rest + accNo + dopisek + divClose;

    var originalContents = document.body.innerHTML;

    document.body.innerHTML = printContents;

    window.print();

    document.body.innerHTML = originalContents;
}