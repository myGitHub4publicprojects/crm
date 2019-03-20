function printDiv() {
    var style = '<div style="padding: 50px;">';
    var ldate = document.querySelector('[name="left_PCPR_date"]');
    if (ldate) {
        ldate = ldate.value;
    }
    var rdate = document.querySelector('[name="right_PCPR_date"]');
    if (rdate) {
        rdate = rdate.value;
    }
    var date = ldate || rdate
    date = '<p style="text-align:right;">Data: ' + date + '</p>';
    var sVox = '<p><small>SONOVOX<br>Aparaty Słuchowe<br>';
    var sVox1 = 'Barbara Golon-Szczepaniak<br>';
    var sVox2 = 'ul. Wagi 6 m 1, 61-244 Poznań<br>';
    var sVox3 = 'NIP 782-137-75-19, Regon 302634863<br>';
    var sVox4 = 'tel. 721 210 180</small></p>';
    var sonovox = sVox+sVox1+sVox2+sVox3+sVox4;

    var head = style + date + sonovox + '<h1 style="text-align:center;">Kosztorys</h1>';
    var fname = document.querySelector('[name="fname"]').value;
    var lname = document.querySelector('[name="lname"]').value;
    var name = '<p>Imię i Nazwisko: ' + fname + ' ' + lname + '</p><hr>';
    var address = "<p>Adres zamieszkania:</p><hr>";
    var ha = '<p>Aparat słuchowy: ';
    var left_ha = document.getElementById('left_PCPR_ha');
    if (left_ha) {
        left_ha = left_ha.innerHTML;
        ha += left_ha;
    }
    var right_ha = document.getElementById('right_PCPR_ha');
    if (right_ha) {
        right_ha = right_ha.innerHTML;
        ha += ' ' + right_ha
    }
    if (left_ha==right_ha) {
        ha = '<p>Aparat słuchowy: 2x ' + left_ha;
    }

    var wkladka = '</p><hr><p>Wkładka uszna: </p><hr>';
    var koszty = '<p>Koszt aparatu słuchowego: </p><hr><p>Koszt wkładki usznej: </p><hr>';
    var patient = name + address + ha + wkladka + koszty;

    var h2 = '<h2 style="text-align:center;">Dofinansowanie z NFZ</h2>';
    var fin = '<p>Do aparatu słuchowego: </p><hr><p>Do wkładki usznej: </p><hr>';
    var nfz = h2 + fin + '<p>Kwota wnioskowanej dopłaty: </p><hr>';
    var accNo = '<p>Przelew na konto: 40 1160 2202 0000 0002 5500 6585</p><hr>';
    var currentYear = new Date().getFullYear();
    var dopisek = '<p style="position: fixed; bottom: 150px; left: 100px;"><small>Do realizacji do 31.12.' + currentYear + '</small></p>';
    var divClose = '</div>';
    var printContents = head + patient + nfz + accNo + dopisek + divClose;
    var originalContents = document.body.innerHTML;

    document.body.innerHTML = printContents;

    window.print();

    document.body.innerHTML = originalContents;
}