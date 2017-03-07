from app.countries import countries

with open('../static/countries.css','w') as f:
    for c in countries:
        f.write('select#country option[value="'+c+'"] { background-image:url('+c+'.png); }\n')
    f.close()