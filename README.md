# Laadplanner thuisbatterij

Webapp die de goedkoopste kwartieren kiest om een thuisbatterij te laden bij een dynamisch tarief.

Deze repo bevat **alleen de app-code**. Er staan geen gegevens, wachtwoorden of sleutels in.
De app leest haar gegevens uit een aparte privé-repo, met een sleutel die alleen in de browser
van de gebruiker bewaard wordt. Zonder die sleutel toont de app geen gegevens en kan ze niets doen.

`index.html` wordt gemaakt met `app/build.py` in de privé-repo; pas het bestand hier niet met de hand aan.
