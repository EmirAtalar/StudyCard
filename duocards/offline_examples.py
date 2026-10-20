"""Kontrollü sözcük listeleriyle çevrimdışı kullanım cümleleri.

Sözcük türü kullanıcı etiketinden tahmin edilmez. Yalnızca aşağıdaki
kontrollü listelerdeki sözcükler uygun dilbilgisi kalıbına yerleştirilir.
Bunlar internetten alıntı değildir; uygulamanın yerel örnekleridir.
"""
import unicodedata
import json
from pathlib import Path
from functools import lru_cache

RULES = {
'en': [
('apple candidate opportunity explanation idea topic ability talent headache accident cousin fork spoon towel function derivative slope tangent line main course order flavor major habit result answer question book teacher student friend car house',
'This {w} is important to me.|I remember that {w} very clearly.|We talked about this {w} yesterday.|Can you tell me more about this {w}?|I would like to understand that {w} better.|This {w} caught my attention.|I asked a question about this {w}.|She mentioned that {w} during our conversation.|They gave me more information about this {w}.|Let us take a closer look at this {w}.'),
('knowledge confidence patience impatience advice progress luggage baggage equipment currency toothpaste leather wool coal cotton silk furniture vinegar unemployment fluency coherence identification teaching ease',
'We talked about {w} today.|I would like to know more about {w}.|They asked me a question about {w}.|We need to pay more attention to {w}.|This article explains the importance of {w}.|She gave a presentation about {w}.|We discussed {w} during the meeting.|What do you know about {w}?|He mentioned {w} in his report.|Let us learn more about {w}.'),
('criteria benefits fields majors',
'These {w} are important.|We discussed these {w} yesterday.|Can you explain these {w} to me?|I would like to know more about these {w}.|She mentioned these {w} in her report.|We need to understand these {w} better.|They asked a question about these {w}.|Let us take a closer look at these {w}.|The article provides information about these {w}.|I wrote down these {w} in my notebook.'),
('important significant simple available likely terrible fine certain sufficient recent current particular whole entire foreign environmental religious traditional cultural intensive',
'We discussed a {w} issue today.|They asked about a {w} issue.|She wrote about a {w} issue.|He mentioned a {w} issue during the meeting.|I read an article about a {w} issue.|Let us talk about a {w} issue.|We need to understand this {w} issue.|The report describes a {w} issue.|Can you explain this {w} issue?|They are studying a {w} issue.'),
('obtain receive bring catch reach expect serve consider meet provide include enhance improve gain convey encourage check carry store order',
'We need to {w} something useful.|Can you {w} something useful?|They want to {w} something useful.|I hope we can {w} something useful.|Let us try to {w} something useful.|We should {w} something useful today.|She wants to {w} something useful.|He would like to {w} something useful.|It is possible to {w} something useful.|I am ready to {w} something useful.'),
('arrive appear grow remain stand happen begin turn',
'It could {w} soon.|They expect it to {w} soon.|I think it will {w} soon.|It may {w} today.|We believe it will {w} soon.|It might {w} tomorrow.|I did not expect it to {w} so soon.|They said it would {w} soon.|It is likely to {w} soon.|Do you think it will {w} soon?'),
('probably readily currently especially exactly',
'We can {w} explain the difference.|She can {w} explain the difference.|He can {w} explain the difference.|They can {w} explain the difference.|I can {w} explain the difference.|You can {w} explain the difference.|Our teacher can {w} explain the difference.|The guide can {w} explain the difference.|This example can {w} explain the difference.|The speaker can {w} explain the difference.'),
],
'de': [
('Apfel Freund Lehrer Student Hund Tisch Stuhl',
'Dieser {w} ist wichtig für mich.|Ich erinnere mich an diesen {w}.|Wir haben über diesen {w} gesprochen.|Kannst du mir mehr über diesen {w} erzählen?|Ich möchte mehr über diesen {w} erfahren.|Dieser {w} hat meine Aufmerksamkeit geweckt.|Ich habe eine Frage zu diesem {w}.|Sie hat diesen {w} erwähnt.|Wir haben Informationen über diesen {w} gefunden.|Schauen wir uns diesen {w} genauer an.'),
],
'fr': [('pomme maison voiture question idée',
'Cette {w} est importante pour moi.|Je me souviens de cette {w}.|Nous avons parlé de cette {w}.|Peux-tu me parler de cette {w} ?|Je voudrais en savoir plus sur cette {w}.|Cette {w} a attiré mon attention.|J’ai posé une question sur cette {w}.|Elle a mentionné cette {w}.|Nous avons trouvé des informations sur cette {w}.|Regardons cette {w} de plus près.')],
'es': [('manzana casa pregunta idea oportunidad',
'Esta {w} es importante para mí.|Recuerdo esta {w}.|Hablamos de esta {w}.|¿Puedes hablarme de esta {w}?|Me gustaría saber más sobre esta {w}.|Esta {w} llamó mi atención.|Hice una pregunta sobre esta {w}.|Ella mencionó esta {w}.|Encontramos información sobre esta {w}.|Veamos esta {w} con más detalle.')],
}

# Çok sözcüklü girdiler liste ayracı olarak virgül kullanır.
MULTI = {'tangent line':'idea','main course':'idea','to improve':'improve'}

def canonical(term, lang):
    term=unicodedata.normalize('NFC',term).strip()
    if lang=='en':
        term=term.replace('İ','I').replace('ı','i')
    return ' '.join(term.casefold().split())

@lru_cache(maxsize=1)
def _curated():
    return json.loads((Path(__file__).parent/'data'/'offline_usage.json').read_text(encoding='utf-8'))


def _rule_examples(term,lang):
    key=canonical(term,lang)
    authored=_curated().get(lang,{}).get(key)
    if authored:
        return [dict(text=t,translations={},kind='example',source='offline_example') for t in authored]
    lookup=MULTI.get(key,key) if lang=='en' else key
    for words,templates in RULES.get(lang,[]):
        if lookup in {canonical(w,lang) for w in words.split()}:
            word=key
            if lang=='de':
                word=next(w for w in words.split() if canonical(w,lang)==lookup)
            if key=='to improve':
                templates=templates.replace('to {w}','{w}')
            if lang=='en' and word[0] in 'aeiou':
                templates=templates.replace('a {w}', 'an {w}')
            return [dict(text=t.format(w=word),translations={},kind='example',source='offline_example')
                    for t in templates.split('|')]
    return []

# Her ifade bir anlamlı eylem içinde kullanılır; etiket hataları bu seçimleri etkilemez.
ACTIONS = {
'mock':'avoid trying to mock other people',
'enough':'leave enough time for the journey',
'in any way':'help in any way we can',
'spend':'spend more time reading',
'let me explain':'say, "Let me explain the problem."',
'the oven':'clean the oven after cooking',
'it depends on':'remember that it depends on the weather',
'proud of':'be proud of our progress',
'bring up':'bring up the issue at the meeting',
'few':'ask a few questions',
'according to':'follow the instructions according to the manual',
'take a breath':'take a breath before answering',
'abroad':'study abroad next year',
'decrease significantly':'allow the error rate to decrease significantly',
'increase rapidly':'expect demand to increase rapidly',
'remain stable':'help prices remain stable',
'polish':'polish the table carefully',
'able':'be able to explain the answer',
'various':'consider various options',
'which':'decide which route to take',
'those':'carry those bags upstairs',
'then':'read the question and then answer it',
'their':'respect their decision',
'some':'bring some food to the meeting',
'into':'put the documents into a folder',
'even':'continue working even when it is difficult',
'as':'use this box as a temporary shelf',
'also':'also check the spelling',
'lead':'lead the team through a difficult project',
'let':'let everyone finish speaking',
'us':'ask the teacher to help us',
'anymore':'remember that this service is not available anymore',
'attend':'attend the meeting tomorrow',
'stick together':'stick together when things get difficult',
'separate':'separate the clean clothes from the dirty ones',
'split up':'split up the work fairly',
'dry':'dry the dishes with a clean towel',
'plenty':'leave plenty of time for the journey',
'of':'check the meaning of this word',
'break the habit':'break the habit of checking our phones constantly',
'summer vacation':'plan a trip for the summer vacation',
'during':'take notes during the lesson',
'on time':'arrive at the station on time',
'yet':'remember that the results are not ready yet',
'make it':'leave early so we can make it to the meeting',
'own idea':'explain our own idea clearly',
'individual':'consider each individual case',
'do not worry':'tell our friend, "Do not worry about the exam."',
"you're welcome":'reply, "You\'re welcome," when someone thanks us',
'become ...':'help you become more confident',
'it takes ... about':'remember that it takes us about ten minutes to walk home',
}
ACTION_FRAMES = (
'We should {action}.', 'Can you {action}?', 'They want to {action}.',
'I hope we can {action}.', 'Let us try to {action}.', 'It is important to {action}.',
'We need to {action}.', 'Our team plans to {action}.', 'You may want to {action}.',
'They decided to {action}.')

CONTEXTS = {
'available': ('The {s} is available today.', ['room','book','car','service','doctor','teacher','equipment','report','information','software']),
'likely': ('The {s} is likely to arrive soon.', ['train','bus','taxi','teacher','doctor','student','visitor','manager','package','delivery']),
'sufficient': ('The {s} is sufficient for our needs.', ['budget','amount of water','supply of food','number of chairs','storage space','equipment','time available','information','funding','amount of fuel']),
'fine': ('{s} said the room looked fine.', ['I','We','They','The teacher','The manager','The visitor','The student','The designer','The engineer','The doctor']),
'intensive': ('We completed an intensive {s}.', ['course','training program','workshop','language course','study program','research project','exercise program','seminar','preparation course','writing course']),
'whole': ('We read the whole {s}.', ['book','article','story','report','letter','message','chapter','poem','essay','document']),
'entire': ('We read the entire {s}.', ['book','article','story','report','letter','message','chapter','poem','essay','document']),
'foreign': ('We learned about foreign {s}.', ['languages','cultures','customs','countries','traditions','markets','cities','universities','films','authors']),
'religious': ('We learned about religious {s}.', ['traditions','customs','ceremonies','holidays','buildings','communities','beliefs','texts','symbols','festivals']),
'cultural': ('We learned about cultural {s}.', ['traditions','customs','events','differences','activities','heritage','diversity','exchanges','influences','identity']),
'environmental': ('We studied environmental {s}.', ['problems','issues','changes','policies','risks','protection','damage','effects','challenges','factors']),
 'traditional': ('We learned about traditional {s}.', ['food','music','dances','clothes','crafts','games','stories','ceremonies','festivals','customs']),

 'to be honest': ('To be honest, I need more time to {s}.', ['think','prepare','study','practice','read the report','check the answer','make a decision','finish the project','understand the question','review the results']),
'fortunately': ('Fortunately, {s} arrived before the storm.', ['we','they','the students','our friends','the guests','the children','the visitors','the workers','the travelers','the teachers']),
'nowadays': ('Nowadays, {s} use computers to learn new skills.', ['students','teachers','children','workers','engineers','doctors','writers','designers','musicians','researchers']),
'currently': ('{s} are currently working on a new project.', ['We','They','The students','Our friends','The engineers','The teachers','The writers','The designers','The researchers','The workers']),
'also': ('{s} also need more time to finish the task.', ['We','They','The students','Our friends','The engineers','The teachers','The writers','The designers','The researchers','The workers']),
'especially': ('The course is especially useful for {s}.', ['beginners','students','teachers','travelers','writers','researchers','young people','new employees','language learners','international students']),
'exactly': ('{s} know exactly what to do next.', ['We','They','The students','Our friends','The engineers','The teachers','The writers','The designers','The researchers','The workers']),
'among': ('The answer was hidden among the {s}.', ['notes','documents','pages','books','letters','files','examples','reports','messages','papers']),
'from': ('We received a message from the {s}.', ['teacher','manager','doctor','writer','guide','driver','researcher','engineer','designer','student']),
'few years ago': ('A few years ago, {s} moved to a new city.', ['I','we','they','our friends','the neighbors','my parents','the family','the teacher','the writer','the artist']),
'brought up': ('{s} brought up an important question during the meeting.', ['I','We','They','The teacher','The manager','The writer','The engineer','The researcher','The doctor','The student']),
'encouraged': ('{s} encouraged me to keep practicing.', ['My teacher','My friend','My father','My mother','Our manager','The coach','My sister','My brother','The doctor','The writer']),
'encouraging': ('{s} is encouraging me to try again.', ['My teacher','My friend','My father','My mother','Our manager','The coach','My sister','My brother','The doctor','The writer']),
'conveying': ('The speaker is conveying {s} to the audience.', ['an important message','a sense of hope','a feeling of confidence','a clear idea','useful information','a warning','a personal experience','a difficult concept','a new perspective','a sense of urgency']),
'approaching': ('{s} is approaching the station.', ['The train','The bus','The taxi','The traveler','The driver','The tourist','The student','The teacher','The cyclist','The pedestrian']),
'might': ('{s} might need more time to finish.', ['I','We','They','The teacher','The writer','The engineer','The researcher','The doctor','The student','Our team']),
'tomorrow': ('{s} will visit the museum tomorrow.', ['I','We','They','The teacher','The writer','The engineer','The researcher','The doctor','The student','Our team']),
'themselves': ('{s} prepared the meal themselves.', ['They','The children','The students','Our friends','The guests','The workers','The travelers','The teachers','The neighbors','My parents']),
'which': ('Which {s} would you like to read first?', ['book','article','story','report','letter','message','chapter','poem','essay','document']),
'ability': ('{s} showed an ability to solve difficult problems.', ['I','We','They','The teacher','The writer','The engineer','The researcher','The doctor','The student','Our team']),
'confidence': ('{s} gained confidence through daily practice.', ['I','We','They','The teacher','The writer','The engineer','The researcher','The doctor','The student','Our team']),
'standstill': ('The {s} brought traffic to a standstill.', ['accident','snowstorm','heavy rain','road closure','flood','fallen tree','broken traffic light','demonstration','construction work','vehicle breakdown']),
'similarity': ('We noticed a similarity between the two {s}.', ['pictures','stories','reports','ideas','designs','methods','languages','buildings','songs','patterns']),
'during': ('We took notes during the {s}.', ['lesson','meeting','lecture','presentation','workshop','seminar','discussion','interview','conference','training session']),
'for their fields': ('{s} are well known in their fields.', ['These researchers','These doctors','These engineers','These writers','These artists','These teachers','These musicians','These scientists','These designers','These specialists']),
'taking place': ('The {s} is taking place in the main hall.', ['meeting','conference','concert','workshop','ceremony','lecture','exhibition','competition','discussion','celebration']),
}

def examples(term,lang):
    # Authored sentences teach a concrete situation; interchangeable templates do not.
    return _rule_examples(term,lang) if _curated().get(lang,{}).get(canonical(term,lang)) else []
