<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>Feest Reservering</title>
</head>
<body>
<h2>🎉 Feest Reservering</h2>
<form id="form">
<label>Stad:</label><select id="stad"><option>Amsterdam</option><option>Rotterdam</option><option>Utrecht</option><option>Maastricht</option></select>
<label>Datum:</label><input type="date" id="datum">
<label>Feest naam:</label><input type="text" id="feest_naam">
<label>Aantal personen:</label><input type="number" id="aantal">
<label>Namen:</label><input type="text" id="namen">
<label>Email:</label><input type="email" id="customer_email">
<button type="button" onclick="verstuur()">Naar Betaling</button>
</form>
<div id="resultaat"></div>

<script>
function verstuur(){
    const data = {
        stad: document.getElementById('stad').value,
        datum: document.getElementById('datum').value,
        feest_naam: document.getElementById('feest_naam').value,
        aantal_personen: parseInt(document.getElementById('aantal').value)||0,
        namen: document.getElementById('namen').value,
        customer_email: document.getElementById('customer_email').value
    };

    fetch("https://yourusername.pythonanywhere.com/reserveer", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(async r => {
        const text = await r.text();
        try {
            const res = JSON.parse(text);
            if(res.url){
                // تحويل المستخدم إلى PayPal
                window.location.href = res.url;
            } else {
                document.getElementById('resultaat').style.display = 'block';
                document.getElementById('resultaat').innerText = res.melding || 'Er is een fout.';
            }
        } catch(e){
            document.getElementById('resultaat').style.display = 'block';
            document.getElementById('resultaat').innerText = 'Server gaf geen geldig JSON terug: ' + text;
        }
    })
    .catch(e => {
        document.getElementById('resultaat').style.display = 'block';
        document.getElementById('resultaat').innerText = 'Fout bij verbinding met server: ' + e;
    });
}
</script>

</body>
</html>
