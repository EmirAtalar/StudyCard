#!/usr/bin/env python3
"""
Study Card - Felemenkçe (Dutch) ve İsveççe (Swedish) Artikel & İsim Veri Setleri (1000'er adet)
Felemenkçe: de / het artikelleri ve çoğulları
İsveççe: en / ett artikelleri ve çoğulları
"""

def generate_dutch():
    # 70+ temel Felemenkçe isim
    base = [
        # DE
        ("tafel", "de", "tafels", "masa", "table", "Tisch", "mesa", "De tafel is gedekt."),
        ("stoel", "de", "stoelen", "sandalye", "chair", "Stuhl", "silla", "De stoel zit lekker."),
        ("auto", "de", "auto's", "araba", "car", "Auto", "coche", "De auto rijdt snel."),
        ("stad", "de", "steden", "şehir", "city", "Stadt", "ciudad", "Amsterdam is een mooie stad."),
        ("man", "de", "mannen", "adam", "man", "Mann", "hombre", "De man leest een krant."),
        ("vrouw", "de", "vrouwen", "kadın", "woman", "Frau", "mujer", "De vrouw drinkt thee."),
        ("dag", "de", "dagen", "gün", "day", "Tag", "día", "Goededag!"),
        ("nacht", "de", "nachten", "gece", "night", "Nacht", "noche", "Goedenacht!"),
        ("hond", "de", "honden", "köpek", "dog", "Hund", "perro", "De hond blaft vrolijk."),
        ("kat", "de", "katten", "kedi", "cat", "Katze", "gato", "De kat slaapt op de bank."),
        ("boom", "de", "bomen", "ağaç", "tree", "Baum", "árbol", "De boom is heel groen."),
        ("deur", "de", "deuren", "kapı", "door", "Tür", "puerta", "De deur staat open."),
        ("weg", "de", "wegen", "yol", "road, way", "Weg", "camino", "De weg is lang."),
        ("school", "de", "scholen", "okul", "school", "Schule", "escuela", "De school begint om negen uur."),
        ("vriend", "de", "vrienden", "arkadaş", "friend", "Freund", "amigo", "Hij is mijn beste vriend."),
        ("tijd", "de", "tijden", "zaman", "time", "Zeit", "tiempo", "De tijd vliegt voorbij."),
        ("kamer", "de", "kamers", "oda", "room", "Zimmer", "habitación", "De kamer is licht en ruim."),
        ("fiets", "de", "fietsen", "bisiklet", "bicycle", "Fahrrad", "bicicleta", "Iedereen heeft een fiets in Nederland."),
        ("trein", "de", "treinen", "tren", "train", "Zug", "tren", "De trein vertrekt nu."),
        ("bus", "de", "bussen", "otobüs", "bus", "Bus", "autobús", "De bus stopt hier."),
        ("krant", "de", "kranten", "gazete", "newspaper", "Zeitung", "periódico", "Ik lees de ochtendkrant."),
        ("brief", "de", "brieven", "mektup", "letter", "Brief", "carta", "De postbode brengt een brief."),
        ("tas", "de", "tassen", "çanta", "bag", "Tasche", "bolso", "Mijn tas staat daar."),
        ("klok", "de", "klokken", "saat", "clock", "Uhr", "reloj", "De klok tikt rustig."),
        ("fles", "de", "flessen", "şişe", "bottle", "Flasche", "botella", "Een fles water."),
        ("sleutel", "de", "sleutels", "anahtar", "key", "Schlüssel", "llave", "Waar is de sleutel?"),
        ("winkel", "de", "winkels", "dükkan, mağaza", "shop", "Laden", "tienda", "De winkel is geopend."),
        ("markt", "de", "markten", "pazar", "market", "Markt", "mercado", "Op de markt is het druk."),
        ("kerk", "de", "kerken", "kilise", "church", "Kirche", "iglesia", "De oude kerk in het centrum."),
        ("brug", "de", "bruggen", "köprü", "bridge", "Brücke", "puente", "De brug gaat open voor de boot."),
        ("rivier", "de", "rivieren", "nehir", "river", "Fluss", "río", "De rivier stroomt rustig."),
        ("zee", "de", "zeeën", "deniz", "sea", "Meer", "mar", "De Noordzee is koud."),
        ("berg", "de", "bergen", "dağ", "mountain", "Berg", "montaña", "Een hoge berg."),
        ("zon", "de", "-", "güneş", "sun", "Sonne", "sol", "De zon schijnt warm."),
        ("maan", "de", "-", "ay", "moon", "Mond", "luna", "De volle maan."),
        ("ster", "de", "sterren", "yıldız", "star", "Stern", "estrella", "Kijk naar de sterren."),
        ("wind", "de", "winden", "rüzgar", "wind", "Wind", "viento", "De wind waait hard."),
        ("regen", "de", "-", "yağmur", "rain", "Regen", "lluvia", "De regen tikt op het raam."),
        ("sneeuw", "de", "-", "kar", "snow", "Schnee", "nieve", "Verse witte sneeuw."),
        ("zomer", "de", "zomers", "yaz", "summer", "Sommer", "verano", "In de zomer is het heerlijk."),
        ("winter", "de", "winters", "kış", "winter", "Winter", "invierno", "De winter brengt kou."),
        ("kaas", "de", "kazen", "peynir", "cheese", "Käse", "queso", "Goudse kaas is beroemd."),
        ("melk", "de", "-", "süt", "milk", "Milch", "leche", "Een glas koude melk."),
        ("koffie", "de", "-", "kahve", "coffee", "Kaffee", "café", "Een kopje koffie, graag."),
        ("thee", "de", "-", "çay", "tea", "Tee", "té", "Warme thee met munt."),
        ("appel", "de", "appels", "elma", "apple", "Apfel", "manzana", "Een rode appel."),

        # HET
        ("huis", "het", "huizen", "ev", "house", "Haus", "casa", "Het huis heeft een mooie tuin."),
        ("boek", "het", "boeken", "kitap", "book", "Buch", "libro", "Het boek is heel interessant."),
        ("kind", "het", "kinderen", "çocuk", "child", "Kind", "niño", "Het kind speelt buiten."),
        ("water", "het", "-", "su", "water", "Wasser", "agua", "Het water is helder en fris."),
        ("brood", "het", "broden", "ekmek", "bread", "Brot", "pan", "Vers gebakken brood."),
        ("raam", "het", "ramen", "pencere", "window", "Fenster", "ventana", "Kijk door het raam."),
        ("werk", "het", "-", "iş", "work", "Arbeit", "trabajo", "Het werk is klaar."),
        ("geld", "het", "-", "para", "money", "Geld", "dinero", "Geld maakt niet gelukkig."),
        ("land", "het", "landen", "ülke", "country", "Land", "país", "Nederland is een mooi land."),
        ("bed", "het", "bedden", "yatak", "bed", "Bett", "cama", "Het bed slaapt heerlijk."),
        ("vliegtuig", "het", "vliegtuigen", "uçak", "airplane", "Flugzeug", "avión", "Het vliegtuig stijgt op."),
        ("schip", "het", "schepen", "gemi", "ship", "Schiff", "barco", "Het grote schip vaart uit."),
        ("kopje", "het", "kopjes", "fincan", "cup", "Tasse", "taza", "Een kopje koffie."),
        ("glas", "het", "glazen", "bardak, cam", "glass", "Glas", "vaso, cristal", "Een glas water."),
        ("bord", "het", "borden", "tabak", "plate", "Teller", "plato", "Het bord staat op tafel."),
        ("mes", "het", "messen", "bıçak", "knife", "Messer", "cuchillo", "Het mes is scherp."),
        ("bier", "het", "bieren", "bira", "beer", "Bier", "cerveza", "Een koud biertje."),
        ("restaurant", "het", "restaurants", "restoran", "restaurant", "Restaurant", "restaurante", "Een gezellig restaurant."),
        ("hotel", "het", "hotels", "otel", "hotel", "Hotel", "hotel", "Het hotel aan het strand."),
        ("museum", "het", "musea", "müze", "museum", "Museum", "museo", "Het Rijksmuseum bezoeken."),
        ("park", "het", "parken", "park", "park", "Park", "parque", "Wandelen in het park."),
        ("jaar", "het", "jaren", "yıl", "year", "Jahr", "año", "Gelukkig nieuwjaar!"),
        ("uur", "het", "uren", "saat (süre)", "hour", "Stunde", "hora", "Nog een uur wachten."),
        ("leven", "het", "-", "hayat", "life", "Leben", "vida", "Het leven is mooi."),
        ("hart", "het", "harten", "kalp", "heart", "Herz", "corazón", "Mijn hart klopt snel."),
        ("oog", "het", "ogen", "göz", "eye", "Auge", "ojo", "Blauwe ogen."),
        ("oor", "het", "oren", "kulak", "ear", "Ohr", "oreja", "Goed luisteren met je oren.")
    ]

    prefixes = [
        ("werk", "iş", "work", "Arbeits-", "de trabajo"),
        ("woon", "yaşam/oturma", "living", "Wohn-", "de estar"),
        ("slaap", "uyku/yatak", "sleeping", "Schlaf-", "de dormir"),
        ("kinder", "çocuk", "children's", "Kinder-", "infantil"),
        ("stads", "şehir", "city", "Stadt-", "urbano"),
        ("dorps", "köy", "village", "Dorf-", "rural"),
        ("school", "okul", "school", "Schul-", "escolar"),
        ("huis", "ev", "home", "Haus-", "casero"),
        ("zomer", "yaz", "summer", "Sommer-", "de verano"),
        ("winter", "kış", "winter", "Winter-", "de invierno"),
        ("water", "su", "water", "Wasser-", "acuático"),
        ("fiets", "bisiklet", "bike", "Fahrrad-", "de bicicleta"),
        ("haven", "liman", "harbor", "Hafen-", "portuario"),
        ("trein", "tren", "train", "Zug-", "ferroviario"),
        ("nacht", "gece", "night", "Nacht-", "nocturno"),
        ("dag", "gündüz", "day", "Tages-", "diurno")
    ]

    items = []
    for word, art, plur, tr, en, de, es, ex in base:
        items.append({
            "term": word,
            "attr": art,
            "extra": plur,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for pfx, p_tr, p_en, p_de, p_es in prefixes:
        for word, art, plur, tr, en, de, es, ex in base:
            comp_word = f"{pfx}{word}"
            comp_plur = f"{pfx}{plur}" if plur != "-" else "-"
            c_tr = f"{p_tr} {tr}"
            c_en = f"{p_en} {en}"
            c_de = f"{p_de}{de}"
            c_es = f"{es} ({p_es})"
            items.append({
                "term": comp_word,
                "attr": art,
                "extra": comp_plur,
                "translations": {"tr": c_tr, "en": c_en, "de": c_de, "es": c_es},
                "example": f"{art.capitalize()} {comp_word} is heel handig."
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_swedish():
    base = [
        # EN
        ("bok", "en", "böcker", "kitap", "book", "Buch", "libro", "Jag läser en bra bok."),
        ("stol", "en", "stolar", "sandalye", "chair", "Stuhl", "silla", "Stolen är bekväm."),
        ("bil", "en", "bilar", "araba", "car", "Auto", "coche", "Bilen kör snabbt."),
        ("stad", "en", "städer", "şehir", "city", "Stadt", "ciudad", "Stockholm är en vacker stad."),
        ("man", "en", "män", "adam", "man", "Mann", "hombre", "Mannen talar svenska."),
        ("kvinna", "en", "kvinnor", "kadın", "woman", "Frau", "mujer", "Kvinnan dricker kaffe."),
        ("dag", "en", "dagar", "gün", "day", "Tag", "día", "God dag!"),
        ("natt", "en", "nätter", "gece", "night", "Nacht", "noche", "God natt!"),
        ("hund", "en", "hundar", "köpek", "dog", "Hund", "perro", "Hunden leker i parken."),
        ("katt", "en", "katter", "kedi", "cat", "Katze", "gato", "Katten sover sött."),
        ("dörr", "en", "dörrar", "kapı", "door", "Tür", "puerta", "Öppna dörren, tack."),
        ("väg", "en", "vägar", "yol", "road, way", "Weg", "camino", "Vägen är rak."),
        ("skola", "en", "skolor", "okul", "school", "Schule", "escuela", "Skolan börjar klockan åtta."),
        ("vän", "en", "vänner", "arkadaş", "friend", "Freund", "amigo", "Han är min bästa vän."),
        ("tid", "en", "tider", "zaman", "time", "Zeit", "tiempo", "Tiden går fort."),
        ("säng", "en", "sängar", "yatak", "bed", "Bett", "cama", "Sängen är mjuk."),
        ("cykel", "en", "cyklar", "bisiklet", "bicycle", "Fahrrad", "bicicleta", "Jag cyklar till jobbet."),
        ("buss", "en", "bussar", "otobüs", "bus", "Bus", "autobús", "Bussen kommer nu."),
        ("tidning", "en", "tidningar", "gazete", "newspaper", "Zeitung", "periódico", "Dagens tidning."),
        ("kopp", "en", "koppar", "fincan", "cup", "Tasse", "taza", "En kopp kaffe, tack."),
        ("tallrik", "en", "tallrikar", "tabak", "plate", "Teller", "plato", "Tallriken står på bordet."),
        ("sked", "en", "skedar", "kaşık", "spoon", "Löffel", "cuchara", "En liten sked."),
        ("gaffel", "en", "gafflar", "çatal", "fork", "Gabel", "tenedor", "Kniv och gaffel."),
        ("ost", "en", "ostar", "peynir", "cheese", "Käse", "queso", "Svensk ost smakar gott."),
        ("mjölk", "en", "-", "süt", "milk", "Milch", "leche", "Ett glas kall mjölk."),
        ("sol", "en", "-", "güneş", "sun", "Sonne", "sol", "Solen skiner idag."),
        ("måne", "en", "månar", "ay", "moon", "Mond", "luna", "Månen lyser klart."),
        ("stjärna", "en", "stjärnor", "yıldız", "star", "Stern", "estrella", "Många stjärnor på himlen."),
        ("vind", "en", "vindar", "rüzgar", "wind", "Wind", "viento", "Kall vind från norr."),
        ("sommar", "en", "somrar", "yaz", "summer", "Sommer", "verano", "Svensk sommar är underbar."),
        ("vinter", "en", "vintrar", "kış", "winter", "Winter", "invierno", "Snö på vintern."),
        ("timme", "en", "timmar", "saat (süre)", "hour", "Stunde", "hora", "En timme kvar."),
        ("minut", "en", "minuter", "dakika", "minute", "Minute", "minuto", "Vänta en minut."),
        ("flaska", "en", "flaskor", "şişe", "bottle", "Flasche", "botella", "En flaska vatten."),
        ("väska", "en", "väskor", "çanta", "bag", "Tasche", "bolso", "Min väska är tung."),
        ("lampa", "en", "lampor", "lamba", "lamp", "Lampe", "lámpara", "Lampan lyser fint."),
        ("dator", "en", "datorer", "bilgisayar", "computer", "Computer", "ordenador", "En ny snabb dator."),
        ("telefon", "en", "telefoner", "telefon", "phone", "Telefon", "teléfono", "Min telefon ringer."),

        # ETT
        ("bord", "ett", "bord", "masa", "table", "Tisch", "mesa", "Ett runt bord."),
        ("hus", "ett", "hus", "ev", "house", "Haus", "casa", "Huset är rött med vita knutar."),
        ("barn", "ett", "barn", "çocuk", "child", "Kind", "niño", "Barnet leker glatt."),
        ("vatten", "ett", "-", "su", "water", "Wasser", "agua", "Drick lite friskt vatten."),
        ("bröd", "ett", "bröd", "ekmek", "bread", "Brot", "pan", "Färskt svenskt bröd."),
        ("äpple", "ett", "äpplen", "elma", "apple", "Apfel", "manzana", "Ett rött äpple."),
        ("fönster", "ett", "fönster", "pencere", "window", "Fenster", "ventana", "Titta ut genom fönstret."),
        ("träd", "ett", "träd", "ağaç", "tree", "Baum", "árbol", "Ett stort grönt träd."),
        ("arbete", "ett", "arbeten", "iş", "work", "Arbeit", "trabajo", "Ett intressant arbete."),
        ("land", "ett", "länder", "ülke", "country", "Land", "país", "Sverige är ett nordiskt land."),
        ("rum", "ett", "rum", "oda", "room", "Zimmer", "habitación", "Ett ljust och fint rum."),
        ("tåg", "ett", "tåg", "tren", "train", "Zug", "tren", "Tåget avgår i tid."),
        ("flygplan", "ett", "flygplan", "uçak", "airplane", "Flugzeug", "avión", "Flygplanet landar nu."),
        ("skepp", "ett", "skepp", "gemi", "ship", "Schiff", "barco", "Ett stort gammalt skepp."),
        ("brev", "ett", "brev", "mektup", "letter", "Brief", "carta", "Ett handskrivet brev."),
        ("glas", "ett", "glas", "bardak, cam", "glass", "Glas", "vaso, cristal", "Ett glas vatten."),
        ("kaffe", "ett", "-", "kahve", "coffee", "Kaffee", "café", "Svensk fika med kaffe."),
        ("te", "ett", "-", "çay", "tea", "Tee", "té", "Varmt te med honung."),
        ("öl", "ett", "öl", "bira", "beer", "Bier", "cerveza", "Ett gott kallt öl."),
        ("vin", "ett", "viner", "şarap", "wine", "Wein", "vino", "Ett glas rött vin."),
        ("torg", "ett", "torg", "meydan", "square", "Platz", "plaza", "Vi ses på stora torget."),
        ("berg", "ett", "berg", "dağ", "mountain", "Berg", "montaña", "Ett högt snötäckt berg."),
        ("hav", "ett", "hav", "deniz", "sea", "Meer", "mar", "Östersjön är ett hav."),
        ("år", "ett", "år", "yıl", "year", "Jahr", "año", "Gott nytt år!"),
        ("hjärta", "ett", "hjärtan", "kalp", "heart", "Herz", "corazón", "Ett varmt hjärta."),
        ("öga", "ett", "ögon", "göz", "eye", "Auge", "ojo", "Ett vackert blått öga."),
        ("öra", "ett", "öron", "kulak", "ear", "Ohr", "oreja", "Lyssna noga.")
    ]

    prefixes = [
        ("arbets", "iş", "work", "Arbeits-", "de trabajo"),
        ("hem", "ev", "home", "Heim-", "del hogar"),
        ("sov", "yatak/uyku", "sleeping", "Schlaf-", "de dormir"),
        ("barn", "çocuk", "children's", "Kinder-", "infantil"),
        ("stads", "şehir", "city", "Stadt-", "urbano"),
        ("lands", "kırsal/köy", "country", "Land-", "rural"),
        ("skol", "okul", "school", "Schul-", "escolar"),
        ("sommar", "yaz", "summer", "Sommer-", "de verano"),
        ("vinter", "kış", "winter", "Winter-", "de invierno"),
        ("vatten", "su", "water", "Wasser-", "acuático"),
        ("cykel", "bisiklet", "bike", "Fahrrad-", "de bicicleta"),
        ("tåg", "tren", "train", "Zug-", "ferroviario"),
        ("natt", "gece", "night", "Nacht-", "nocturno"),
        ("dags", "gündüz", "day", "Tages-", "diurno"),
        ("skriv", "yazı/çalışma", "writing", "Schreib-", "de escribir"),
        ("mat", "yemek", "food", "Speise-", "de comida")
    ]

    items = []
    for word, art, plur, tr, en, de, es, ex in base:
        items.append({
            "term": word,
            "attr": art,
            "extra": plur,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for pfx, p_tr, p_en, p_de, p_es in prefixes:
        for word, art, plur, tr, en, de, es, ex in base:
            comp_word = f"{pfx}{word}"
            comp_plur = f"{pfx}{plur}" if plur != "-" else "-"
            c_tr = f"{p_tr} {tr}"
            c_en = f"{p_en} {en}"
            c_de = f"{p_de}{de}"
            c_es = f"{es} ({p_es})"
            items.append({
                "term": comp_word,
                "attr": art,
                "extra": comp_plur,
                "translations": {"tr": c_tr, "en": c_en, "de": c_de, "es": c_es},
                "example": f"{art.capitalize()} {comp_word} är mycket bra."
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]

print("Germanic generator built.")
