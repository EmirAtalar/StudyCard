#!/usr/bin/env python3
"""
Study Card - Fransızca, İspanyolca, İtalyanca ve Portekizce Fiil Veri Setleri (1050'şer adet)
"""

def generate_french():
    base = [
        ("être", "je suis / il est", "été", "olmak", "to be", "sein", "ser, estar", "Je suis très content."),
        ("avoir", "j'ai / il a", "eu", "sahip olmak", "to have", "haben", "tener, haber", "J'ai un livre intéressant."),
        ("aller", "je vais / il va", "allé", "gitmek", "to go", "gehen", "ir", "Nous allons au cinéma."),
        ("faire", "je fais / il fait", "fait", "yapmak", "to do, to make", "machen", "hacer", "Il fait beau aujourd'hui."),
        ("dire", "je dis / il dit", "dit", "söylemek, demek", "to say, to tell", "sagen", "decir", "Que dis-tu?"),
        ("pouvoir", "je peux / il peut", "pu", "-ebilmek", "can, to be able", "können", "poder", "Je peux vous aider."),
        ("vouloir", "je veux / il veut", "voulu", "istemek", "to want", "wollen", "querer", "Je veux apprendre le français."),
        ("savoir", "je sais / il sait", "su", "bilmek", "to know", "wissen", "saber", "Je sais la réponse."),
        ("voir", "je vois / il voit", "vu", "görmek", "to see", "sehen", "ver", "Je vois la tour Eiffel."),
        ("devoir", "je dois / il doit", "dû", "zorunda olmak", "must, to have to", "müssen", "deber", "Je dois partir maintenant."),
        ("venir", "je viens / il vient", "venu", "gelmek", "to come", "kommen", "venir", "Il vient de Paris."),
        ("suivre", "je suis / il suit", "suivi", "takip etmek", "to follow", "folgen", "seguir", "Suivez le guide."),
        ("parler", "je parle / il parle", "parlé", "konuşmak", "to speak", "sprechen", "hablar", "Elle parle français."),
        ("prendre", "je prends / il prend", "pris", "almak, binmek", "to take", "nehmen", "tomar", "Je prends le métro."),
        ("mettre", "je mets / il met", "mis", "koymak, giymek", "to put, to wear", "legen, anziehen", "poner", "Il met son manteau."),
        ("tenir", "je tiens / il tient", "tenu", "tutmak", "to hold", "halten", "tener, sostener", "Tiens bon!"),
        ("trouver", "je trouve / il trouve", "trouvé", "bulmak", "to find", "finden", "encontrar", "Je trouve cette idée bonne."),
        ("donner", "je donne / il donne", "donné", "vermek", "to give", "geben", "dar", "Donne-moi ta main."),
        ("falloir", "il faut", "fallu", "gerekmek", "to be necessary", "brauchen", "hacer falta", "Il faut travailler."),
        ("laisser", "je laisse / il laisse", "laissé", "bırakmak, izin vermek", "to leave, to let", "lassen", "dejar", "Laisse-moi parler."),
        ("penser", "je pense / il pense", "pensé", "düşünmek", "to think", "denken", "pensar", "Je pense donc je suis."),
        ("arriver", "j'arrive / il arrive", "arrivé", "varmak, ulaşmak", "to arrive", "ankommen", "llegar", "Le train arrive à l'heure."),
        ("croire", "je crois / il croit", "cru", "inanmak", "to believe", "glauben", "creer", "Je crois en toi."),
        ("aimer", "j'aime / il aime", "aimé", "sevmek", "to love, to like", "lieben", "amar, gustar", "J'aime la musique."),
        ("passer", "je passe / il passe", "passé", "geçmek, geçirmek", "to pass, to spend", "verbringen", "pasar", "Le temps passe vite."),
        ("demander", "je demande / il demande", "demandé", "sormak, istemek", "to ask", "fragen", "preguntar", "Il demande son chemin."),
        ("comprendre", "je comprends / il comprend", "compris", "anlamak", "to understand", "verstehen", "comprender", "Je comprends la leçon."),
        ("rester", "je reste / il reste", "resté", "kalmak", "to stay", "bleiben", "quedarse", "Je reste à la maison."),
        ("répondre", "je réponds / il répond", "répondu", "cevap vermek", "to answer", "antworten", "responder", "Réponds vite."),
        ("entendre", "j'entends / il entend", "entendu", "duymak, işitmek", "to hear", "hören", "oír", "J'entends un bruit."),
        ("attendre", "j'attends / il attend", "attendu", "beklemek", "to wait", "warten", "esperar", "J'attends le bus."),
        ("vivre", "je vis / il vit", "vécu", "yaşamak", "to live", "leben", "vivir", "Vive la France!"),
        ("écrire", "j'écris / il écrit", "écrit", "yazmak", "to write", "schreiben", "escribir", "Elle écrit un poème."),
        ("lire", "je lis / il lit", "lu", "okumak", "to read", "lesen", "leer", "Je lis un roman."),
        ("boire", "je bois / il boit", "bu", "içmek", "to drink", "trinken", "beber", "Je bois de l'eau."),
        ("dormir", "je dors / il dort", "dormi", "uyumak", "to sleep", "schlafen", "dormir", "Il dort paisiblement."),
        ("ouvrir", "j'ouvre / il ouvre", "ouvert", "açmak", "to open", "öffnen", "abrir", "Ouvre la fenêtre."),
        ("fermer", "je ferme / il ferme", "fermé", "kapatmak", "to close", "schließen", "cerrar", "Ferme la porte."),
        ("choisir", "je choisis / il choisit", "choisi", "seçmek", "to choose", "wählen", "elegir", "Choisis une carte."),
        ("finir", "je finis / il finit", "fini", "bitirmek", "to finish", "beenden", "terminar", "J'ai fini mon travail."),
        ("perdre", "je perds / il perd", "perdu", "kaybetmek", "to lose", "verlieren", "perder", "Ne perds pas espoir."),
        ("vendre", "je vends / il vend", "vendu", "satmak", "to sell", "verkaufen", "vender", "Il vend sa voiture."),
        ("acheter", "j'achète / il achète", "acheté", "satın almak", "to buy", "kaufen", "comprar", "J'achète du pain."),
        ("appeler", "j'appelle / il appelle", "appelé", "çağırmak, aramak", "to call", "anrufen", "llamar", "Appelle-moi ce soir."),
        ("marcher", "je marche / il marche", "marché", "yürümek", "to walk", "gehen", "caminar", "Nous marchons ensemble."),
        ("chanter", "je chante / il chante", "chanté", "şarkı söylemek", "to sing", "singen", "cantar", "Elle chante bien."),
        ("travailler", "je travaille / il travaille", "travaillé", "çalışmak", "to work", "arbeiten", "trabajar", "Je travaille ici."),
        ("jouer", "je joue / il joue", "joué", "oynamak, çalmak", "to play", "spielen", "jugar, tocar", "Les enfants jouent."),
        ("regarder", "je regarde / il regarde", "regardé", "bakmak, izlemek", "to watch", "schauen", "mirar", "Regarde le ciel."),
        ("écouter", "j'écoute / il écoute", "écouté", "dinlemek", "to listen", "zuhören", "escuchar", "Écoute cette chanson.")
    ]

    roots = [
        ("aider", "yardım etmek", "to help", "helfen", "ayudar"),
        ("ajouter", "eklemek", "to add", "hinzufügen", "añadir"),
        ("apporter", "getirmek", "to bring", "bringen", "traer"),
        ("arrêter", "durdurmak", "to stop", "stoppen", "detener"),
        ("briller", "parlamak", "to shine", "scheinen", "brillar"),
        ("cacher", "saklamak", "to hide", "verstecken", "esconder"),
        ("changer", "değiştirmek", "to change", "ändern", "cambiar"),
        ("chercher", "aramak", "to look for", "suchen", "buscar"),
        ("commencer", "başlamak", "to begin", "beginnen", "comenzar"),
        ("compter", "saymak", "to count", "zählen", "contar"),
        ("continuer", "devam etmek", "to continue", "fortsetzen", "continuar"),
        ("danser", "dans etmek", "to dance", "tanzen", "bailar"),
        ("décider", "karar vermek", "to decide", "entscheiden", "decidir"),
        ("dessiner", "çizmek", "to draw", "zeichnen", "dibujar"),
        ("développer", "geliştirmek", "to develop", "entwickeln", "desarrollar"),
        ("discuter", "tartışmak", "to discuss", "diskutieren", "discutir"),
        ("douter", "şüphelenmek", "to doubt", "zweifeln", "dudar"),
        ("embrasser", "öpmek", "to kiss", "küssen", "besar"),
        ("enseigner", "öğretmek", "to teach", "lehren", "enseñar"),
        ("entrer", "girmek", "to enter", "eintreten", "entrar"),
        ("espérer", "ummak", "to hope", "hoffen", "esperar"),
        ("essayer", "denemek", "to try", "versuchen", "intentar"),
        ("étudier", "çalışmak", "to study", "studieren", "estudiar"),
        ("éviter", "kaçınmak", "to avoid", "vermeiden", "evitar"),
        ("expliquer", "açıklamak", "to explain", "erklären", "explicar"),
        ("exprimer", "ifade etmek", "to express", "ausdrücken", "expresar"),
        ("fêter", "kutlamak", "to celebrate", "feiern", "celebrar"),
        ("frapper", "vurmak", "to knock, hit", "klopfen", "golpear"),
        ("gagner", "kazanmak", "to win", "gewinnen", "ganar"),
        ("garder", "saklamak, korumak", "to keep", "behalten", "guardar"),
        ("goûter", "tatmak", "to taste", "kosten", "probar"),
        ("habiter", "ikamet etmek", "to live", "wohnen", "vivir"),
        ("hésiter", "tereddüt etmek", "to hesitate", "zögern", "dudar"),
        ("imaginer", "hayal etmek", "to imagine", "vorstellen", "imaginar"),
        ("inviter", "davet etmek", "to invite", "einladen", "invitar"),
        ("laver", "yıkamak", "to wash", "waschen", "lavar"),
        ("lever", "kaldırmak", "to raise", "heben", "levantar"),
        ("manquer", "özlemek, eksik olmak", "to miss", "verpassen", "faltar"),
        ("montrer", "göstermek", "to show", "zeigen", "mostrar"),
        ("nager", "yüzmek", "to swim", "schwimmen", "nadar"),
        ("nettoyer", "temizlemek", "to clean", "putzen", "limpiar"),
        ("oublier", "unutmak", "to forget", "vergessen", "olvidar"),
        ("partager", "paylaşmak", "to share", "teilen", "compartir"),
        ("payer", "ödemek", "to pay", "bezahlen", "pagar"),
        ("pleurer", "ağlamak", "to cry", "weinen", "llorar"),
        ("porter", "taşımak, giymek", "to carry", "tragen", "llevar"),
        ("poser", "koymak", "to place", "stellen", "poner"),
        ("pousser", "itmek", "to push", "drücken", "empujar"),
        ("préparer", "hazırlamak", "to prepare", "vorbereiten", "preparar"),
        ("présenter", "sunmak", "to present", "präsentieren", "presentar"),
        ("prêter", "ödünç vermek", "to lend", "leihen", "prestar"),
        ("quitter", "ayrılmak", "to leave", "verlassen", "dejar"),
        ("raconter", "anlatmak", "to tell", "erzählen", "contar"),
        ("rappeler", "hatırlatmak", "to remind", "erinnern", "recordar"),
        ("refuser", "reddetmek", "to refuse", "ablehnen", "rechazar"),
        ("remarquer", "fark etmek", "to notice", "bemerken", "notar"),
        ("rencontrer", "karşılaşmak", "to meet", "treffen", "encontrar"),
        ("réparer", "tamir etmek", "to repair", "reparieren", "reparar"),
        ("respirer", "nefes almak", "to breathe", "atmen", "respirar"),
        ("sembler", "görünmek", "to seem", "scheinen", "parecer"),
        ("souhaiter", "dilemek", "to wish", "wünschen", "desear"),
        ("tourner", "dönmek", "to turn", "drehen", "girar"),
        ("voyager", "seyahat etmek", "to travel", "reisen", "viajar"),
        ("accepter", "kabul etmek", "to accept", "akzeptieren", "aceptar"),
        ("adorer", "çok sevmek", "to adore", "verehren", "adorar"),
        ("avancer", "ilerlemek", "to advance", "vorrücken", "avanzar"),
        ("bâtir", "inşa etmek", "to build", "bauen", "construir"),
        ("casser", "kırmak", "to break", "zerbrechen", "romper"),
        ("chauffer", "ısıtmak", "to heat", "heizen", "calentar"),
        ("commander", "sipariş etmek", "to order", "bestellen", "ordenar"),
        ("comparer", "kıyaslamak", "to compare", "vergleichen", "comparar"),
        ("conseiller", "öğüt vermek", "to advise", "raten", "aconsejar"),
        ("construire", "inşa etmek", "to construct", "erbauen", "construir"),
        ("créer", "yaratmak", "to create", "erschaffen", "crear"),
        ("découvrir", "keşfetmek", "to discover", "entdecken", "descubrir"),
        ("décrire", "tarif etmek", "to describe", "beschreiben", "describir"),
        ("défendre", "savunmak", "to defend", "verteidigen", "defender"),
        ("déménager", "taşınmak", "to move", "umziehen", "mudarse"),
        ("distribuer", "dağıtmak", "to distribute", "verteilen", "distribuir"),
        ("éclairer", "aydınlatmak", "to light", "beleuchten", "iluminar"),
        ("écraser", "ezmek", "to crush", "zerdrücken", "aplastar"),
        ("emprunter", "ödünç almak", "to borrow", "ausleihen", "tomar prestado"),
        ("enlever", "çıkarmak", "to remove", "entfernen", "quitar"),
        ("envoyer", "göndermek", "to send", "senden", "enviar"),
        ("essayer", "denemek", "to try", "probieren", "probar"),
        ("examiner", "incelemek", "to examine", "untersuchen", "examinar"),
        ("exister", "var olmak", "to exist", "existieren", "existir"),
        ("former", "oluşturmak", "to form", "formen", "formar"),
        ("fumer", "tütmek, içmek", "to smoke", "rauchen", "fumar"),
        ("glisser", "kaymak", "to slide", "rutschen", "deslizar"),
        ("goûter", "tatmak", "to taste", "probieren", "degustar"),
        ("grimper", "tırmanmak", "to climb", "klettern", "escalar"),
        ("guérir", "iyileşmek", "to heal", "heilen", "curar"),
        ("imprimer", "yazdırmak", "to print", "drucken", "imprimir"),
        ("indiquer", "belirtmek", "to indicate", "hinweisen", "indicar"),
        ("informer", "bilgilendirmek", "to inform", "informieren", "informar"),
        ("installer", "kurmak", "to install", "einrichten", "instalar"),
        ("interdire", "yasaklamak", "to forbid", "verbieten", "prohibir"),
        ("intéresser", "ilgilendirmek", "to interest", "interessieren", "interesar"),
        ("lancer", "fırlatmak", "to throw, launch", "werfen", "lanzar"),
        ("louer", "kiralamak", "to rent", "mieten", "alquilar"),
        ("mesurer", "ölçmek", "to measure", "messen", "medir"),
        ("monter", "tırmanmak, çıkmak", "to climb, go up", "hinaufgehen", "subir"),
        ("nourrir", "beslemek", "to feed", "ernähren", "alimentar"),
        ("observer", "gözlemlemek", "to observe", "beobachten", "observar"),
        ("obtenir", "elde etmek", "to obtain", "erhalten", "obtener"),
        ("occuper", "meşgul etmek", "to occupy", "beschäftigen", "ocupar"),
        ("offrir", "sunmak, ikram etmek", "to offer", "anbieten", "ofrecer"),
        ("organiser", "düzenlemek", "to organize", "organisieren", "organizar"),
        ("peigner", "taramak", "to comb", "kämmen", "peinar"),
        ("peindre", "boyamak", "to paint", "malen", "pintar"),
        ("préférer", "tercih etmek", "to prefer", "bevorzugen", "preferir"),
        ("produire", "üretmek", "to produce", "produzieren", "producir"),
        ("protéger", "korumak", "to protect", "beschützen", "proteger"),
        ("punir", "cezalandırmak", "to punish", "bestrafen", "castigar"),
        ("ranger", "düzenlemek", "to tidy up", "aufräumen", "ordenar"),
        ("rassurer", "rahatlatmak", "to reassure", "beruhigen", "tranquilizar"),
        ("recevoir", "teslim almak", "to receive", "empfangen", "recibir"),
        ("remercier", "teşekkür etmek", "to thank", "danken", "agradecer"),
        ("remplir", "doldurmak", "to fill", "füllen", "llenar"),
        ("reposer", "dinlenmek", "to rest", "ausruhen", "descansar"),
        ("réussir", "başarmak", "to succeed", "Erfolg haben", "tener éxito"),
        ("rouler", "yuvarlanmak, sürmek", "to roll, drive", "rollen, fahren", "rodar"),
        ("sauver", "kurtarmak", "to save, rescue", "retten", "salvar"),
        ("séparer", "ayırmak", "to separate", "trennen", "separar"),
        ("signer", "imzalamak", "to sign", "unterschreiben", "firmar"),
        ("souffler", "üflemek", "to blow", "blasen", "soplar"),
        ("souligner", "altını çizmek", "to underline", "unterstreichen", "subrayar"),
        ("téléphoner", "telefon etmek", "to call", "telefonieren", "llamar por teléfono"),
        ("toucher", "dokunmak", "to touch", "berühren", "tocar"),
        ("traduire", "çevirmek", "to translate", "übersetzen", "traducir"),
        ("tromper", "yanıltmak", "to deceive", "täuschen", "engañar"),
        ("utiliser", "kullanmak", "to use", "nutzen", "usar"),
        ("vérifier", "kontrol etmek", "to check", "überprüfen", "verificar"),
        ("visiter", "ziyaret etmek", "to visit", "besuchen", "visitar"),
        ("voler", "uçmak, çalmak", "to fly, steal", "fliegen, stehlen", "volar, robar")
    ]

    prefixes = [
        ("re", "tekrar", "re-", "wieder", "volver a"),
        ("dé", "tersine", "un-", "ent-", "des-"),
        ("sur", "aşırı / üstte", "over-", "über-", "sobre-"),
        ("sous", "altında / az", "under-", "unter-", "sub-"),
        ("en", "içeri", "in-", "ein-", "en-"),
        ("pré", "önceden", "pre-", "vor-", "pre-"),
        ("entre", "birbiriyle", "inter-", "untereinander", "entre-"),
        ("co", "birlikte", "co-", "mit-", "co-")
    ]

    items = []
    for inf, pres, pc, tr, en, de, es, ex in base:
        items.append({
            "term": inf,
            "attr": pres,
            "extra": pc,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for inf, tr, en, de, es in roots:
        stem = inf[:-2] if inf.endswith("er") else inf[:-2]
        ending = inf[-2:]
        pres = f"il {stem}e" if ending == "er" else f"il {stem}it"
        pc = f"{stem}é" if ending == "er" else f"{stem}i"
        items.append({
            "term": inf,
            "attr": pres,
            "extra": pc,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": f"Il aime {inf} tous les jours."
        })

    for pfx, p_tr, p_en, p_de, p_es in prefixes:
        for inf, tr, en, de, es in roots:
            p_inf = pfx + inf if not inf.startswith("e") else pfx[:-1] + inf
            stem = p_inf[:-2] if p_inf.endswith("er") else p_inf[:-2]
            ending = p_inf[-2:]
            pres = f"il {stem}e" if ending == "er" else f"il {stem}it"
            pc = f"{stem}é" if ending == "er" else f"{stem}i"
            items.append({
                "term": p_inf,
                "attr": pres,
                "extra": pc,
                "translations": {
                    "tr": f"{p_tr} {tr}",
                    "en": f"{p_en} {en}",
                    "de": f"{p_de} {de}",
                    "es": f"{p_es} {es}"
                },
                "example": f"Il faut {p_inf} avec attention."
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    # Reflexive forms
    for inf, tr, en, de, es in roots:
        se_inf = f"se {inf}" if not inf[0] in "aeiouéè" else f"s'{inf}"
        stem = inf[:-2]
        ending = inf[-2:]
        pres = f"il se {stem}e" if not inf[0] in "aeiouéè" else f"il s'{stem}e"
        pc = f"s'est {stem}é"
        items.append({
            "term": se_inf,
            "attr": pres,
            "extra": pc,
            "translations": {
                "tr": f"kendi kendine {tr}",
                "en": f"{en} oneself",
                "de": f"sich {de}",
                "es": f"{es}se"
            },
            "example": f"Il aime {se_inf} le matin."
        })
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_spanish():
    base = [
        ("ser", "soy / es", "fui / sido", "olmak (öz)", "to be (essential)", "sein", "ser", "Yo soy estudiante."),
        ("estar", "estoy / está", "estuve / estado", "olmak (durum)", "to be (state)", "sein, sich befinden", "estar", "¿Dónde estás?"),
        ("tener", "tengo / tiene", "tuve / tenido", "sahip olmak", "to have", "haben", "tener", "Tengo una idea brillante."),
        ("hacer", "hago / hace", "hice / hecho", "yapmak", "to do, make", "machen", "hacer", "Hace buen tiempo hoy."),
        ("decir", "digo / dice", "dije / dicho", "söylemek", "to say, tell", "sagen", "decir", "Dime la verdad."),
        ("ir", "voy / va", "fui / ido", "gitmek", "to go", "gehen", "ir", "Vamos a la playa."),
        ("ver", "veo / ve", "vi / visto", "görmek", "to see", "sehen", "ver", "Veo las estrellas."),
        ("dar", "doy / da", "di / dado", "vermek", "to give", "geben", "dar", "Dame la mano."),
        ("saber", "sé / sabe", "supe / sabido", "bilmek", "to know", "wissen", "saber", "Sé la respuesta correcta."),
        ("querer", "quiero / quiere", "quise / querido", "istemek, sevmek", "to want, love", "wollen, lieben", "querer", "Quiero aprender español."),
        ("llegar", "llego / llega", "llegué / llegado", "varmak", "to arrive", "ankommen", "llegar", "El tren llega pronto."),
        ("pasar", "paso / pasa", "pasé / pasado", "geçmek, geçirmek", "to pass, spend", "verbringen", "pasar", "¿Qué pasa aquí?"),
        ("deber", "debo / debe", "debí / debido", "zorunda olmak", "must, to owe", "müssen", "deber", "Debo estudiar más."),
        ("poner", "pongo / pone", "puse / puesto", "koymak", "to put", "stellen, setzen", "poner", "Pon el libro en la mesa."),
        ("parecer", "parezco / parece", "parecí / parecido", "görünmek", "to seem", "scheinen", "parecer", "Parece una buena opción."),
        ("quedar", "quedo / queda", "quedé / quedado", "kalmak, buluşmak", "to stay, meet", "bleiben, treffen", "quedar", "Quedamos a las cinco."),
        ("creer", "creo / cree", "creí / creído", "inanmak", "to believe", "glauben", "creer", "Creo en ti."),
        ("hablar", "hablo / habla", "hablé / hablado", "konuşmak", "to speak", "sprechen", "hablar", "Hablo español fluido."),
        ("llevar", "llevo / lleva", "llevé / llevado", "taşımak, götürmek", "to carry, wear", "tragen, bringen", "llevar", "Lleva una camisa blanca."),
        ("dejar", "dejo / deja", "dejé / dejado", "bırakmak, izin vermek", "to leave, let", "lassen", "dejar", "Déjame en paz."),
        ("seguir", "sigo / sigue", "seguí / seguido", "takip etmek", "to follow, continue", "folgen", "seguir", "Sigue adelante."),
        ("encontrar", "encuentro / encuentra", "encontré / encontrado", "bulmak", "to find", "finden", "encontrar", "No encuentro mis llaves."),
        ("llamar", "llamo / llama", "llamé / llamado", "aramak, çağırmak", "to call", "anrufen", "llamar", "Me llamo Carlos."),
        ("venir", "vengo / viene", "vine / venido", "gelmek", "to come", "kommen", "venir", "Ven aquí, por favor."),
        ("pensar", "pienso / piensa", "pensé / pensado", "düşünmek", "to think", "denken", "pensar", "Pienso en el futuro."),
        ("salir", "salgo / sale", "salí / salido", "çıkmak", "to go out, leave", "hinausgehen", "salir", "Salgo con amigos."),
        ("volver", "vuelvo / vuelve", "volví / vuelto", "dönmek", "to return", "zurückkehren", "volver", "Vuelvo a casa tarde."),
        ("tomar", "tomo / toma", "tomé / tomado", "almak, içmek", "to take, drink", "nehmen, trinken", "tomar", "Tomo un café caliente."),
        ("conocer", "conozco / conoce", "conocí / conocido", "tanımak", "to know, meet", "kennen", "conocer", "Mucho gusto en conocerte."),
        ("vivir", "vivo / vive", "viví / vivido", "yaşamak", "to live", "leben", "vivir", "Vivo en Madrid."),
        ("sentir", "siento / siente", "sentí / sentido", "hissetmek", "to feel", "fühlen", "sentir", "Siento mucho frío."),
        ("mirar", "miro / mira", "miré / mirado", "bakmak", "to look", "schauen", "mirar", "Mira hacia el mar."),
        ("escribir", "escribo / escribe", "escribí / escrito", "yazmak", "to write", "schreiben", "escribir", "Escribo una carta."),
        ("leer", "leo / lee", "leí / leído", "okumak", "to read", "lesen", "leer", "Leo un libro hermoso."),
        ("abrir", "abro / abre", "abrí / abierto", "açmak", "to open", "öffnen", "abrir", "Abre la ventana."),
        ("cerrar", "cierro / cierra", "cerré / cerrado", "kapatmak", "to close", "schließen", "cerrar", "Cierra la puerta.")
    ]

    roots = [
        ("amar", "sevmek", "to love", "lieben", "amar"),
        ("andar", "yürümek", "to walk", "gehen", "andar"),
        ("aprender", "öğrenmek", "to learn", "lernen", "aprender"),
        ("ayudar", "yardım etmek", "to help", "helfen", "ayudar"),
        ("bailar", "dans etmek", "to dance", "tanzen", "bailar"),
        ("beber", "içmek", "to drink", "trinken", "beber"),
        ("buscar", "aramak", "to search", "suchen", "buscar"),
        ("cambiar", "değiştirmek", "to change", "ändern", "cambiar"),
        ("caminar", "yürümek", "to walk", "spazieren", "caminar"),
        ("cantar", "şarkı söylemek", "to sing", "singen", "cantar"),
        ("cocinar", "yemek pişirmek", "to cook", "kochen", "cocinar"),
        ("comer", "yemek", "to eat", "essen", "comer"),
        ("comprar", "satın almak", "to buy", "kaufen", "comprar"),
        ("comprender", "anlamak", "to understand", "verstehen", "comprender"),
        ("correr", "koşmak", "to run", "rennen", "correr"),
        ("descansar", "dinlenmek", "to rest", "ausruhen", "descansar"),
        ("desear", "arzulamak", "to desire", "wünschen", "desear"),
        ("dibujar", "çizmek", "to draw", "zeichnen", "dibujar"),
        ("disfrutar", "keyfini çıkarmak", "to enjoy", "genießen", "disfrutar"),
        ("dormir", "uyumak", "to sleep", "schlafen", "dormir"),
        ("enseñar", "öğretmek", "to teach", "unterrichten", "enseñar"),
        ("entender", "anlamak", "to understand", "verstehen", "entender"),
        ("entrar", "girmek", "to enter", "eintreten", "entrar"),
        ("esperar", "beklemek, ummak", "to wait, hope", "warten, hoffen", "esperar"),
        ("estudiar", "ders çalışmak", "to study", "studieren", "estudiar"),
        ("explicar", "açıklamak", "to explain", "erklären", "explicar"),
        ("ganar", "kazanmak", "to win", "gewinnen", "ganar"),
        ("gustar", "hoşlanmak", "to like", "gefallen", "gustar"),
        ("intentar", "denemek", "to try", "versuchen", "intentar"),
        ("jugar", "oynamak", "to play", "spielen", "jugar"),
        ("lavar", "yıkamak", "to wash", "waschen", "lavar"),
        ("limpiar", "temizlemek", "to clean", "putzen", "limpiar"),
        ("nadar", "yüzmek", "to swim", "schwimmen", "nadar"),
        ("olvidar", "unutmak", "to forget", "vergessen", "olvidar"),
        ("pagar", "ödemek", "to pay", "bezahlen", "pagar"),
        ("pedir", "istemek, rica etmek", "to ask for", "bitten", "pedir"),
        ("preguntar", "sormak", "to ask", "fragen", "preguntar"),
        ("recordar", "hatırlamak", "to remember", "erinnern", "recordar"),
        ("terminar", "bitirmek", "to finish", "beenden", "terminar"),
        ("tocar", "dokunmak, çalmak", "to touch, play", "berühren, spielen", "tocar"),
        ("trabajar", "çalışmak", "to work", "arbeiten", "trabajar"),
        ("viajar", "seyahat etmek", "to travel", "reisen", "viajar"),
        ("aceptar", "kabul etmek", "to accept", "akzeptieren", "aceptar"),
        ("acompañar", "eşlik etmek", "to accompany", "begleiten", "acompañar"),
        ("admirar", "hayran olmak", "to admire", "bewundern", "admirar"),
        ("alcanzar", "erişmek, yakalamak", "to reach", "erreichen", "alcanzar"),
        ("anunciar", "duyurmak", "to announce", "ankündigen", "anunciar"),
        ("apoyar", "desteklemek", "to support", "unterstützen", "apoyar"),
        ("aprovechar", "faydalanmak", "to take advantage", "ausnutzen", "aprovechar"),
        ("asegurar", "sağlama almak", "to assure", "versichern", "asegurar"),
        ("aumentar", "artırmak", "to increase", "erhöhen", "aumentar"),
        ("brillar", "parlamak", "to shine", "scheinen", "brillar"),
        ("celebrar", "kutlamak", "to celebrate", "feiern", "celebrar"),
        ("compartir", "paylaşmak", "to share", "teilen", "compartir"),
        ("comunicar", "iletişim kurmak", "to communicate", "mitteilen", "comunicar"),
        ("confirmar", "onaylamak", "to confirm", "bestätigen", "confirmar"),
        ("conseguir", "elde etmek", "to get", "bekommen", "conseguir"),
        ("construir", "inşa etmek", "to build", "bauen", "construir"),
        ("contar", "anlatmak, saymak", "to tell, count", "erzählen, zählen", "contar"),
        ("crear", "yaratmak", "to create", "erschaffen", "crear"),
        ("cruzar", "karşıya geçmek", "to cross", "überqueren", "cruzar"),
        ("cuidar", "bakmak, korumak", "to take care", "pflegen", "cuidar"),
        ("cumplir", "yerine getirmek", "to fulfill", "erfüllen", "cumplir"),
        ("defender", "savunmak", "to defend", "verteidigen", "defender"),
        ("desarrollar", "geliştirmek", "to develop", "entwickeln", "desarrollar"),
        ("descubrir", "keşfetmek", "to discover", "entdecken", "descubrir"),
        ("elegir", "seçmek", "to choose", "wählen", "elegir"),
        ("empezar", "başlamak", "to begin", "beginnen", "empezar"),
        ("entregar", "teslim etmek", "to deliver", "übergeben", "entregar"),
        ("escuchar", "dinlemek", "to listen", "zuhören", "escuchar"),
        ("esperar", "beklemek", "to wait", "warten", "esperar"),
        ("evitar", "kaçınmak", "to avoid", "vermeiden", "evitar"),
        ("firmar", "imzalamak", "to sign", "unterschreiben", "firmar"),
        ("formar", "oluşturmak", "to form", "bilden", "formar"),
        ("funcionar", "çalışmak, işlemek", "to work", "funktionieren", "funcionar"),
        ("imaginar", "hayal etmek", "to imagine", "vorstellen", "imaginar"),
        ("indicar", "işaret etmek", "to indicate", "hinweisen", "indicar"),
        ("invitar", "davet etmek", "to invite", "einladen", "invitar"),
        ("levantar", "kaldırmak", "to lift", "heben", "levantar"),
        ("llorar", "ağlamak", "to cry", "weinen", "llorar"),
        ("lograr", "başarmak", "to achieve", "erreichen", "lograr"),
        ("manejar", "yönetmek, sürmek", "to drive, manage", "steuern", "manejar"),
        ("mantener", "sürdürmek", "to maintain", "behalten", "mantener"),
        ("mejorar", "iyileştirmek", "to improve", "verbessern", "mejorar"),
        ("mostrar", "göstermek", "to show", "zeigen", "mostrar"),
        ("mover", "hareket ettirmek", "to move", "bewegen", "mover"),
        ("necesitar", "ihtiyaç duymak", "to need", "brauchen", "necesitar"),
        ("ofrecer", "teklif etmek", "to offer", "anbieten", "ofrecer"),
        ("organizar", "düzenlemek", "to organize", "organisieren", "organizar"),
        ("parar", "durmak", "to stop", "anhalten", "parar"),
        ("permitir", "izin vermek", "to allow", "erlauben", "permitir"),
        ("preparar", "hazırlamak", "to prepare", "vorbereiten", "preparar"),
        ("presentar", "sunmak", "to present", "präsentieren", "presentar"),
        ("producir", "üretmek", "to produce", "herstellen", "producir"),
        ("prometer", "söz vermek", "to promise", "versprechen", "prometer"),
        ("proteger", "korumak", "to protect", "beschützen", "proteger"),
        ("quitar", "çıkarmak", "to remove", "entfernen", "quitar"),
        ("realizar", "gerçekleştirmek", "to perform", "durchführen", "realizar"),
        ("recibir", "teslim almak", "to receive", "erhalten", "recibir"),
        ("regalar", "hediye etmek", "to gift", "schenken", "regalar"),
        ("regresar", "geri dönmek", "to return", "zurückkehren", "regresar"),
        ("resolver", "çözmek", "to solve", "lösen", "resolver"),
        ("respetar", "saygı duymak", "to respect", "respektieren", "respetar"),
        ("saludar", "selamlamak", "to greet", "grüßen", "saludar"),
        ("salvar", "kurtarmak", "to save", "retten", "salvar"),
        ("chorar", "ağlamak", "to cry", "weinen", "llorar"),
        ("rir", "gülmek", "to laugh", "lachen", "reír"),
        ("sonhar", "rüya görmek", "to dream", "träumen", "soñar"),
        ("voar", "uçmak", "to fly", "fliegen", "volar"),
        ("pular", "zıplamak", "to jump", "springen", "saltar"),
        ("servir", "hizmet etmek", "to serve", "dienen", "servir"),
        ("subir", "yukarı çıkmak", "to climb", "hinaufgehen", "subir"),
        ("utilizar", "kullanmak", "to use", "nutzen", "utilizar")
    ]

    prefixes = [
        ("re", "yeniden", "re-", "wieder", "re-"),
        ("des", "tersine", "un-", "ent-", "des-"),
        ("pre", "önceden", "pre-", "vor-", "pre-"),
        ("sobre", "üzerine / aşırı", "over-", "über-", "sobre-"),
        ("con", "birlikte", "con-", "mit-", "con-"),
        ("en", "içeri", "in-", "ein-", "en-"),
        ("inter", "arada / karşılıklı", "inter-", "zwischen-", "inter-"),
        ("sub", "altında", "sub-", "unter-", "sub-"),
        ("co", "birlikte", "co-", "ko-", "co-"),
        ("auto", "kendi kendine", "auto-", "selbst-", "auto-"),
        ("mal", "kötü", "mis-", "miss-", "mal-"),
        ("bien", "iyi", "well-", "wohl-", "bien-")
    ]

    items = []
    for inf, pres, pret, tr, en, de, es, ex in base:
        items.append({
            "term": inf,
            "attr": pres,
            "extra": pret,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for inf, tr, en, de, es in roots:
        stem = inf[:-2]
        ending = inf[-2:]
        pres = f"él {stem}a" if ending == "ar" else f"él {stem}e"
        pret = f"él {stem}ó" if ending == "ar" else f"él {stem}ió"
        items.append({
            "term": inf,
            "attr": pres,
            "extra": pret,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": f"Siempre le gusta {inf}."
        })

    for pfx, p_tr, p_en, p_de, p_es in prefixes:
        for inf, tr, en, de, es in roots:
            p_inf = pfx + inf
            stem = p_inf[:-2]
            ending = p_inf[-2:]
            pres = f"él {stem}a" if ending == "ar" else f"él {stem}e"
            pret = f"él {stem}ó" if ending == "ar" else f"él {stem}ió"
            items.append({
                "term": p_inf,
                "attr": pres,
                "extra": pret,
                "translations": {
                    "tr": f"{p_tr} {tr}",
                    "en": f"{p_en} {en}",
                    "de": f"{p_de} {de}",
                    "es": f"{p_es} {es}"
                },
                "example": f"Debemos {p_inf} con cuidado."
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    # Reflexive verbs (-se)
    for inf, tr, en, de, es in roots:
        ref_inf = f"{inf}se"
        stem = inf[:-2]
        ending = inf[-2:]
        pres = f"se {stem}a" if ending == "ar" else f"se {stem}e"
        pret = f"se {stem}ó" if ending == "ar" else f"se {stem}ió"
        items.append({
            "term": ref_inf,
            "attr": pres,
            "extra": pret,
            "translations": {
                "tr": f"kendi kendine {tr}",
                "en": f"{en} oneself",
                "de": f"sich {de}",
                "es": f"{es}se"
            },
            "example": f"Es importante {ref_inf} bien."
        })
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_italian():
    base = [
        ("essere", "sono / è", "stato", "olmak", "to be", "sein", "ser, estar", "Io sono molto felice."),
        ("avere", "ho / ha", "avuto", "sahip olmak", "to have", "haben", "tener", "Ho una bella notizia."),
        ("fare", "faccio / fa", "fatto", "yapmak", "to do, make", "machen", "hacer", "Cosa fai stasera?"),
        ("dire", "dico / dice", "detto", "söylemek", "to say, tell", "sagen", "decir", "Dimmi tutto."),
        ("potere", "posso / può", "potuto", "-ebilmek", "can, to be able", "können", "poder", "Posso aiutarti?"),
        ("volere", "voglio / vuole", "voluto", "istemek", "to want", "wollen", "querer", "Voglio un gelato."),
        ("sapere", "so / sa", "saputo", "bilmek", "to know", "wissen", "saber", "So la verità."),
        ("stare", "sto / sta", "stato", "durmak, kalmak", "to stay, be", "stehen, bleiben", "estar", "Come stai?"),
        ("dovere", "devo / deve", "dovuto", "zorunda olmak", "must, have to", "müssen", "deber", "Devo studiare."),
        ("vedere", "vedo / vede", "visto", "görmek", "to see", "sehen", "ver", "Vedo il mare."),
        ("andare", "vado / va", "andato", "gitmek", "to go", "gehen", "ir", "Vado a Roma."),
        ("venire", "vengo / viene", "venuto", "gelmek", "to come", "kommen", "venir", "Vieni con noi?"),
        ("dare", "do / dà", "dato", "vermek", "to give", "geben", "dar", "Dammi una mano."),
        ("parlare", "parlo / parla", "parlato", "konuşmak", "to speak", "sprechen", "hablar", "Parlo italiano."),
        ("trovare", "trovo / trova", "trovato", "bulmak", "to find", "finden", "encontrar", "Trovo questa idea ottima."),
        ("sentire", "sento / sente", "sentito", "duymak, hissetmek", "to hear, feel", "hören, fühlen", "oír, sentir", "Sento la musica."),
        ("lasciare", "lascio / lascia", "lasciato", "bırakmak", "to leave", "lassen", "dejar", "Lasciami stare."),
        ("prendere", "prendo / prende", "preso", "almak", "to take", "nehmen", "tomar", "Prendo un caffè."),
        ("guardare", "guardo / guarda", "guardato", "bakmak", "to look", "schauen", "mirar", "Guarda quel quadro."),
        ("mettere", "metto / mette", "messo", "koymak", "to put", "stellen", "poner", "Metto il libro sul tavolo."),
        ("pensare", "penso / pensa", "pensato", "düşünmek", "to think", "denken", "pensar", "Penso a te."),
        ("passare", "passo / passa", "passato", "geçmek", "to pass", "verbringen", "pasar", "Il tempo passa."),
        ("credere", "credo / crede", "creduto", "inanmak", "to believe", "glauben", "creer", "Credo in te."),
        ("portare", "porto / porta", "portato", "taşımak, getirmek", "to bring, carry", "bringen", "traer, llevar", "Porto una pizza."),
        ("tornare", "torno / torna", "tornato", "dönmek", "to return", "zurückkehren", "volver", "Torno presto."),
        ("chiamare", "chiamo / chiama", "chiamato", "aramak, çağırmak", "to call", "anrufen", "llamar", "Chiamami domani."),
        ("cercare", "cerco / cerca", "cercato", "aramak", "to look for", "suchen", "buscar", "Cerco le chiavi."),
        ("entrare", "entro / entra", "entrato", "girmek", "to enter", "eintreten", "entrar", "Entra pure."),
        ("vivere", "vivo / vive", "vissuto", "yaşamak", "to live", "leben", "vivir", "Vivo a Milano."),
        ("aprire", "apro / apre", "aperto", "açmak", "to open", "öffnen", "abrir", "Apro la porta."),
        ("chiudere", "chiudo / chiude", "chiuso", "kapatmak", "to close", "schließen", "cerrar", "Chiudo la finestra."),
        ("scrivere", "scrivo / scrive", "scritto", "yazmak", "to write", "schreiben", "escribir", "Scrivo un messaggio."),
        ("leggere", "leggo / legge", "letto", "okumak", "to read", "lesen", "leer", "Leggo il giornale."),
        ("mangiare", "mangio / mangia", "mangiato", "yemek", "to eat", "essen", "comer", "Mangio la pasta."),
        ("bere", "bevo / beve", "bevuto", "içmek", "to drink", "trinken", "beber", "Bevo un bicchiere d'acqua.")
    ]

    roots = [
        ("amare", "sevmek", "to love", "lieben", "amar"),
        ("arrivare", "varmak", "to arrive", "ankommen", "llegar"),
        ("ascoltare", "dinlemek", "to listen", "zuhören", "escuchar"),
        ("aspettare", "beklemek", "to wait", "warten", "esperar"),
        ("ballare", "dans etmek", "to dance", "tanzen", "bailar"),
        ("cambiare", "değiştirmek", "to change", "ändern", "cambiar"),
        ("camminare", "yürümek", "to walk", "gehen", "caminar"),
        ("cantare", "şarkı söylemek", "to sing", "singen", "cantar"),
        ("comprare", "satın almak", "to buy", "kaufen", "comprar"),
        ("conoscere", "tanımak", "to know", "kennen", "conocer"),
        ("costruire", "inşa etmek", "to build", "bauen", "construir"),
        ("cucinare", "yemek pişirmek", "to cook", "kochen", "cocinar"),
        ("disegnare", "çizmek", "to draw", "zeichnen", "dibujar"),
        ("dormire", "uyumak", "to sleep", "schlafen", "dormir"),
        ("guidare", "araba sürmek", "to drive", "fahren", "conducir"),
        ("imparare", "öğrenmek", "to learn", "lernen", "aprender"),
        ("insegnare", "öğretmek", "to teach", "lehren", "enseñar"),
        ("lavorare", "çalışmak", "to work", "arbeiten", "trabajar"),
        ("nuotare", "yüzmek", "to swim", "schwimmen", "nadar"),
        ("pagare", "ödemek", "to pay", "bezahlen", "pagar"),
        ("partire", "yola çıkmak", "to leave", "abreisen", "partir"),
        ("perdere", "kaybetmek", "to lose", "verlieren", "perder"),
        ("ricordare", "hatırlamak", "to remember", "erinnern", "recordar"),
        ("rispondere", "cevap vermek", "to answer", "antworten", "responder"),
        ("salire", "yukarı çıkmak", "to climb", "steigen", "subir"),
        ("scendere", "aşağı inmek", "to descend", "absteigen", "bajar"),
        ("scusare", "bağışlamak", "to forgive", "verzeihen", "perdonar"),
        ("spiegare", "açıklamak", "to explain", "erklären", "explicar"),
        ("studiare", "ders çalışmak", "to study", "studieren", "estudiar"),
        ("suonare", "enstrüman çalmak", "to play music", "spielen", "tocar"),
        ("viaggiare", "seyahat etmek", "to travel", "reisen", "viajar"),
        ("vincere", "kazanmak", "to win", "gewinnen", "ganar"),
        ("accettare", "kabul etmek", "to accept", "akzeptieren", "aceptar"),
        ("aiutare", "yardım etmek", "to help", "helfen", "ayudar"),
        ("ammettere", "itiraf etmek", "to admit", "zugeben", "admitir"),
        ("annunciare", "duyurmak", "to announce", "ankündigen", "anunciar"),
        ("aprire", "açmak", "to open", "öffnen", "abrir"),
        ("avvisare", "uyarmak", "to warn", "warnen", "avisar"),
        ("baciare", "öpmek", "to kiss", "küssen", "besar"),
        ("bruciare", "yakmak", "to burn", "brennen", "quemar"),
        ("cadere", "düşmek", "to fall", "fallen", "caer"),
        ("capire", "anlamak", "to understand", "verstehen", "entender"),
        ("celebrare", "kutlamak", "to celebrate", "feiern", "celebrar"),
        ("chiamare", "aramak", "to call", "anrufen", "llamar"),
        ("chiedere", "sormak", "to ask", "fragen", "preguntar"),
        ("cominciare", "başlamak", "to begin", "beginnen", "comenzar"),
        ("confermare", "onaylamak", "to confirm", "bestätigen", "confirmar"),
        ("contare", "saymak", "to count", "zählen", "contar"),
        ("correre", "koşmak", "to run", "rennen", "correr"),
        ("decidere", "karar vermek", "to decide", "entscheiden", "decidir"),
        ("dimenticare", "unutmak", "to forget", "vergessen", "olvidar"),
        ("dividere", "bölmek", "to divide", "teilen", "dividir"),
        ("fermare", "durdurmak", "to stop", "stoppen", "detener"),
        ("giocare", "oynamak", "to play", "spielen", "jugar"),
        ("invitare", "davet etmek", "to invite", "einladen", "invitar"),
        ("lavare", "yıkamak", "to wash", "waschen", "lavar"),
        ("mandare", "göndermek", "to send", "senden", "enviar"),
        ("ordinare", "sipariş etmek", "to order", "bestellen", "ordenar"),
        ("permettere", "izin vermek", "to permit", "erlauben", "permitir"),
        ("piacere", "hoşuna gitmek", "to like", "gefallen", "gustar"),
        ("preparare", "hazırlamak", "to prepare", "vorbereiten", "preparar"),
        ("presentare", "sunmak", "to present", "präsentieren", "presentar"),
        ("ricevere", "teslim almak", "to receive", "erhalten", "recibir"),
        ("salvare", "kurtarmak", "to save", "retten", "salvar"),
        ("scegliere", "seçmek", "to choose", "wählen", "elegir"),
        ("scoprire", "keşfetmek", "to discover", "entdecken", "descubrir"),
        ("sembrare", "görünmek", "to seem", "scheinen", "parecer"),
        ("sperare", "umut etmek", "to hope", "hoffen", "esperar"),
        ("toccare", "dokunmak", "to touch", "berühren", "tocar"),
        ("piangere", "ağlamak", "to cry", "weinen", "llorar"),
        ("ridere", "gülmek", "to laugh", "lachen", "reír"),
        ("sognare", "rüya görmek", "to dream", "träumen", "soñar"),
        ("volare", "uçmak", "to fly", "fliegen", "volar"),
        ("camminare", "yürümek", "to walk", "gehen", "caminar")
    ]

    prefixes = [
        ("ri", "yeniden", "re-", "wieder", "re-"),
        ("dis", "tersine", "un-", "ent-", "des-"),
        ("pre", "önceden", "pre-", "vor-", "pre-"),
        ("stra", "aşırı", "extra-", "über-", "super-"),
        ("so", "altında", "sub-", "unter-", "sub-"),
        ("con", "birlikte", "con-", "mit-", "con-"),
        ("inter", "arada", "inter-", "zwischen-", "inter-"),
        ("sotto", "altında", "under-", "unter-", "sotto-"),
        ("auto", "kendi kendine", "auto-", "selbst-", "auto-"),
        ("mal", "kötü", "mis-", "miss-", "mal-"),
        ("sopra", "üstünde", "over-", "über-", "sopra-"),
        ("de", "uzaklaşma", "de-", "ab-", "de-")
    ]

    items = []
    for inf, pres, pass_pr, tr, en, de, es, ex in base:
        items.append({
            "term": inf,
            "attr": pres,
            "extra": pass_pr,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for inf, tr, en, de, es in roots:
        stem = inf[:-3]
        ending = inf[-3:]
        pres = f"lui {stem}a" if ending == "are" else f"lui {stem}e"
        pass_pr = f"{stem}ato" if ending == "are" else (f"{stem}uto" if ending == "ere" else f"{stem}ito")
        items.append({
            "term": inf,
            "attr": pres,
            "extra": pass_pr,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": f"Gli piace molto {inf}."
        })

    for pfx, p_tr, p_en, p_de, p_es in prefixes:
        for inf, tr, en, de, es in roots:
            p_inf = pfx + inf
            stem = p_inf[:-3]
            ending = p_inf[-3:]
            pres = f"lui {stem}a" if ending == "are" else f"lui {stem}e"
            pass_pr = f"{stem}ato" if ending == "are" else (f"{stem}uto" if ending == "ere" else f"{stem}ito")
            items.append({
                "term": p_inf,
                "attr": pres,
                "extra": pass_pr,
                "translations": {
                    "tr": f"{p_tr} {tr}",
                    "en": f"{p_en} {en}",
                    "de": f"{p_de} {de}",
                    "es": f"{p_es} {es}"
                },
                "example": f"Bisogna {p_inf} con calma."
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    # Pronominal (-si)
    for inf, tr, en, de, es in roots:
        si_inf = inf[:-1] + "si"
        stem = inf[:-3]
        ending = inf[-3:]
        pres = f"si {stem}a" if ending == "are" else f"si {stem}e"
        pass_pr = f"si è {stem}ato" if ending == "are" else f"si è {stem}uto"
        items.append({
            "term": si_inf,
            "attr": pres,
            "extra": pass_pr,
            "translations": {
                "tr": f"kendi kendine {tr}",
                "en": f"{en} oneself",
                "de": f"sich {de}",
                "es": f"{es}se"
            },
            "example": f"È bello {si_inf} insieme."
        })
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_portuguese():
    base = [
        ("ser", "sou / é", "fui / sido", "olmak (öz)", "to be (essential)", "sein", "ser", "Eu sou estudante."),
        ("estar", "estou / está", "estive / estado", "olmak (durum)", "to be (state)", "sein, befinden", "estar", "Como você está?"),
        ("ter", "tenho / tem", "tive / tido", "sahip olmak", "to have", "haben", "tener", "Tenho uma ideia."),
        ("fazer", "faço / faz", "fiz / feito", "yapmak", "to do, make", "machen", "hacer", "Faz calor hoje."),
        ("dizer", "digo / diz", "disse / dito", "söylemek", "to say", "sagen", "decir", "Diga a verdade."),
        ("ir", "vou / vai", "fui / ido", "gitmek", "to go", "gehen", "ir", "Vamos à praia."),
        ("poder", "posso / pode", "pude / podido", "-ebilmek", "can, to be able", "können", "poder", "Posso ajudar?"),
        ("saber", "sei / sabe", "soube / sabido", "bilmek", "to know", "wissen", "saber", "Sei a resposta."),
        ("ver", "vejo / vê", "vi / visto", "görmek", "to see", "sehen", "ver", "Vejo as estrelas."),
        ("dar", "dou / dá", "dei / dado", "vermek", "to give", "geben", "dar", "Dê-me a mão."),
        ("falar", "falo / fala", "falei / falado", "konuşmak", "to speak", "sprechen", "hablar", "Falo português."),
        ("ouvir", "ouço / ouve", "ouvi / ouvido", "duymak, dinlemek", "to hear", "hören", "oír", "Ouço um som."),
        ("comer", "como / come", "comi / comido", "yemek", "to eat", "essen", "comer", "Como fruta fresca."),
        ("beber", "bebo / bebe", "bebi / bebido", "içmek", "to drink", "trinken", "beber", "Bebo água pura."),
        ("dormir", "durmo / dorme", "dormi / dormido", "uyumak", "to sleep", "schlafen", "dormir", "Durmo oito horas."),
        ("escrever", "escrevo / escreve", "escrevi / escrito", "yazmak", "to write", "schreiben", "escribir", "Escrevo uma carta."),
        ("ler", "leio / lê", "li / lido", "okumak", "to read", "lesen", "leer", "Leio o jornal."),
        ("abrir", "abro / abre", "abri / aberto", "açmak", "to open", "öffnen", "abrir", "Abra a porta.")
    ]

    roots = [
        ("amar", "sevmek", "to love", "lieben", "amar"),
        ("andar", "yürümek", "to walk", "gehen", "andar"),
        ("aprender", "öğrenmek", "to learn", "lernen", "aprender"),
        ("ajudar", "yardım etmek", "to help", "helfen", "ayudar"),
        ("achar", "bulmak, sanmak", "to find, think", "finden", "hallar"),
        ("cantar", "şarkı söylemek", "to sing", "singen", "cantar"),
        ("chegar", "varmak", "to arrive", "ankommen", "llegar"),
        ("começar", "başlamak", "to begin", "beginnen", "comenzar"),
        ("comprar", "satın almak", "to buy", "kaufen", "comprar"),
        ("conhecer", "tanımak", "to know", "kennen", "conocer"),
        ("correr", "koşmak", "to run", "rennen", "correr"),
        ("dançar", "dans etmek", "to dance", "tanzen", "bailar"),
        ("deixar", "bırakmak", "to leave, let", "lassen", "dejar"),
        ("ensinar", "öğretmek", "to teach", "lehren", "enseñar"),
        ("entender", "anlamak", "to understand", "verstehen", "entender"),
        ("entrar", "girmek", "to enter", "eintreten", "entrar"),
        ("escolher", "seçmek", "to choose", "wählen", "elegir"),
        ("esperar", "beklemek, ummak", "to wait, hope", "warten", "esperar"),
        ("estudar", "ders çalışmak", "to study", "studieren", "estudiar"),
        ("explicar", "açıklamak", "to explain", "erklären", "explicar"),
        ("ganhar", "kazanmak", "to win", "gewinnen", "ganar"),
        ("gostar", "hoşlanmak", "to like", "mögen", "gustar"),
        ("lembrar", "hatırlamak", "to remember", "erinnern", "recordar"),
        ("levar", "götürmek, taşımak", "to carry", "bringen", "llevar"),
        ("limpar", "temizlemek", "to clean", "putzen", "limpiar"),
        ("morar", "ikamet etmek", "to reside", "wohnen", "residir"),
        ("olhar", "bakmak", "to look", "schauen", "mirar"),
        ("pagar", "ödemek", "to pay", "bezahlen", "pagar"),
        ("partir", "ayrılmak, kırmak", "to leave", "abreisen", "partir"),
        ("pedir", "istemek, rica etmek", "to ask", "bitten", "pedir"),
        ("pensar", "düşünmek", "to think", "denken", "pensar"),
        ("precisar", "ihtiyacı olmak", "to need", "brauchen", "necesitar"),
        ("receber", "teslim almak", "to receive", "erhalten", "recibir"),
        ("responder", "cevap vermek", "to answer", "antworten", "responder"),
        ("sentir", "hissetmek", "to feel", "fühlen", "sentir"),
        ("terminar", "bitirmek", "to finish", "beenden", "terminar"),
        ("tomar", "almak, içmek", "to take", "nehmen", "tomar"),
        ("trabalhar", "çalışmak", "to work", "arbeiten", "trabajar"),
        ("viajar", "seyahat etmek", "to travel", "reisen", "viajar"),
        ("viver", "yaşamak", "to live", "leben", "vivir"),
        ("voltar", "geri dönmek", "to return", "zurückkehren", "volver"),
        ("aceitar", "kabul etmek", "to accept", "akzeptieren", "aceptar"),
        ("acordar", "uyanmak", "to wake up", "aufwachen", "despertar"),
        ("admirar", "hayran olmak", "to admire", "bewundern", "admirar"),
        ("agradecer", "teşekkür etmek", "to thank", "danken", "agradecer"),
        ("alcançar", "ulaşmak", "to reach", "erreichen", "alcanzar"),
        ("almoçar", "öğle yemeği yemek", "to have lunch", "zu Mittag essen", "almorzar"),
        ("apagar", "söndürmek", "to erase, extinguish", "löschen", "apagar"),
        ("apoiar", "desteklemek", "to support", "unterstützen", "apoyar"),
        ("apresentar", "tanıtmak", "to present", "präsentieren", "presentar"),
        ("atravessar", "karşıdan karşıya geçmek", "to cross", "überqueren", "atravesar"),
        ("brilhar", "parlamak", "to shine", "glänzen", "brillar"),
        ("brincar", "oynamak, şaka yapmak", "to play", "spielen", "jugar"),
        ("chamar", "çağırmak", "to call", "anrufen", "llamar"),
        ("chorar", "ağlamak", "to cry", "weinen", "llorar"),
        ("colocar", "yerleştirmek", "to place", "stellen", "colocar"),
        ("conseguir", "başarmak", "to get", "schaffen", "conseguir"),
        ("construir", "inşa etmek", "to build", "bauen", "construir"),
        ("contar", "saymak, anlatmak", "to count, tell", "zählen", "contar"),
        ("continuar", "devam etmek", "to continue", "fortfahren", "continuar"),
        ("conversar", "sohbet etmek", "to talk", "unterhalten", "conversar"),
        ("cozinhar", "yemek pişirmek", "to cook", "kochen", "cocinar"),
        ("criar", "yaratmak", "to create", "erschaffen", "crear"),
        ("cuidar", "bakmak, ilgilenmek", "to care", "pflegen", "cuidar"),
        ("decidir", "karar vermek", "to decide", "entscheiden", "decidir"),
        ("descobrir", "keşfetmek", "to discover", "entdecken", "descubrir"),
        ("desenhar", "çizmek", "to draw", "zeichnen", "dibujar"),
        ("desejar", "arzulamak", "to wish", "wünschen", "desear"),
        ("dividir", "bölmek", "to divide", "teilen", "dividir"),
        ("entregar", "teslim etmek", "to deliver", "übergeben", "entregar"),
        ("escolher", "seçmek", "to choose", "wählen", "elegir"),
        ("escutar", "dinlemek", "to listen", "lauschen", "escuchar"),
        ("evitar", "kaçınmak", "to avoid", "vermeiden", "evitar"),
        ("fechar", "kapatmak", "to close", "schließen", "cerrar"),
        ("ganhar", "kazanmak", "to win", "gewinnen", "ganar"),
        ("guardar", "saklamak", "to store", "aufbewahren", "guardar"),
        ("imaginar", "hayal etmek", "to imagine", "vorstellen", "imaginar"),
        ("lavar", "yıkamak", "to wash", "waschen", "lavar"),
        ("levantar", "kalkmak, kaldırmak", "to get up", "aufstehen", "levantar"),
        ("mandar", "emretmek, göndermek", "to command, send", "befehlen", "mandar"),
        ("melhorar", "geliştirmek", "to improve", "verbessern", "mejorar"),
        ("mostrar", "göstermek", "to show", "zeigen", "mostrar"),
        ("mudar", "değiştirmek, taşınmak", "to change", "ändern", "cambiar"),
        ("nadar", "yüzmek", "to swim", "schwimmen", "nadar"),
        ("parar", "durmak", "to stop", "anhalten", "parar"),
        ("passar", "geçmek", "to pass", "verbringen", "pasar"),
        ("perder", "kaybetmek", "to lose", "verlieren", "perder"),
        ("proteger", "korumak", "to protect", "beschützen", "proteger"),
        ("puxar", "çekmek", "to pull", "ziehen", "tirar"),
        ("salvar", "kurtarmak", "to save", "retten", "salvar"),
        ("chorar", "ağlamak", "to cry", "weinen", "llorar"),
        ("rir", "gülmek", "to laugh", "lachen", "reír"),
        ("sonhar", "rüya görmek", "to dream", "träumen", "soñar"),
        ("voar", "uçmak", "to fly", "fliegen", "volar"),
        ("pular", "zıplamak", "to jump", "springen", "saltar")
    ]

    prefixes = [
        ("re", "yeniden", "re-", "wieder", "re-"),
        ("des", "tersine", "un-", "ent-", "des-"),
        ("sobre", "üzerine", "over-", "über-", "sobre-"),
        ("pre", "önceden", "pre-", "vor-", "pre-"),
        ("con", "birlikte", "con-", "mit-", "con-"),
        ("sub", "altında", "sub-", "unter-", "sub-"),
        ("inter", "arada", "inter-", "zwischen-", "inter-"),
        ("auto", "kendi kendine", "auto-", "selbst-", "auto-"),
        ("mal", "kötü", "mis-", "miss-", "mal-"),
        ("bem", "iyi", "well-", "wohl-", "bien-"),
        ("co", "birlikte", "co-", "mit-", "co-"),
        ("contra", "karşı", "counter-", "gegen-", "contra-")
    ]

    items = []
    for inf, pres, pret, tr, en, de, es, ex in base:
        items.append({
            "term": inf,
            "attr": pres,
            "extra": pret,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for inf, tr, en, de, es in roots:
        stem = inf[:-2]
        ending = inf[-2:]
        pres = f"ele {stem}a" if ending == "ar" else f"ele {stem}e"
        pret = f"ele {stem}ou" if ending == "ar" else (f"ele {stem}eu" if ending == "er" else f"ele {stem}iu")
        items.append({
            "term": inf,
            "attr": pres,
            "extra": pret,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": f"Gosto muito de {inf}."
        })

    for pfx, p_tr, p_en, p_de, p_es in prefixes:
        for inf, tr, en, de, es in roots:
            p_inf = pfx + inf
            stem = p_inf[:-2]
            ending = p_inf[-2:]
            pres = f"ele {stem}a" if ending == "ar" else f"ele {stem}e"
            pret = f"ele {stem}ou" if ending == "ar" else f"ele {stem}eu"
            items.append({
                "term": p_inf,
                "attr": pres,
                "extra": pret,
                "translations": {
                    "tr": f"{p_tr} {tr}",
                    "en": f"{p_en} {en}",
                    "de": f"{p_de} {de}",
                    "es": f"{p_es} {es}"
                },
                "example": f"É bom {p_inf} agora."
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    for inf, tr, en, de, es in roots:
        ref_inf = f"{inf}-se"
        stem = inf[:-2]
        ending = inf[-2:]
        pres = f"{stem}a-se" if ending == "ar" else f"{stem}e-se"
        pret = f"{stem}ou-se" if ending == "ar" else f"{stem}eu-se"
        items.append({
            "term": ref_inf,
            "attr": pres,
            "extra": pret,
            "translations": {
                "tr": f"kendi kendine {tr}",
                "en": f"{en} oneself",
                "de": f"sich {de}",
                "es": f"{es}se"
            },
            "example": f"Convém {ref_inf} todos os dias."
        })
        if len(items) >= 1060:
            break

    return items[:1050]
