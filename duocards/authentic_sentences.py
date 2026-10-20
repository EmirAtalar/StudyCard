"""
Study Card - Doğal ve Özgün Örnek Cümle Veri Tabanı (Authentic Sentences Engine)
Yapay/şablon cümleler yerine, kelimenin gerçekten kullanıldığı doğal, akıcı ve
dilbilgisel olarak kusursuz cümleler ve Türkçe çevirilerini sağlar.
"""

from typing import Optional, Tuple, Dict

# Gerçek hayatta, matematikte, akademik ve günlük dilde kullanılan zengin örnek cümleler
AUTHENTIC_SENTENCES_MAP: Dict[str, Tuple[str, str]] = {
    # Matematik & Kalkülüs & Akademik Terimler
    "tangent line": ("The tangent line touches the curve at exactly one point without crossing it.", "Teğet doğrusu eğriye kesmeden tam olarak bir noktada değer."),
    "tangent": ("The slope of the tangent represents the instantaneous rate of change.", "Teğetin eğimi anlık değişim oranını temsil eder."),
    "derivative": ("The derivative of a function measures how fast its value changes.", "Bir fonksiyonun türevi, değerinin ne kadar hızlı değiştiğini ölçer."),
    "slope": ("Calculate the slope of the line passing through these two coordinates.", "Bu iki koordinattan geçen doğrunun eğimini hesaplayın."),
    "equals": ("In this equation, x plus five equals twelve.", "Bu denklemde x artı beş on ikiye eşittir."),
    "equal": ("All sides of an equilateral triangle are equal in length.", "Bir eşkenar üçgenin tüm kenarları eşit uzunluktadır."),
    "function": ("A continuous function has no sudden jumps or breaks in its graph.", "Sürekli bir fonksiyonun grafiğinde ani sıçramalar veya kopmalar yoktur."),
    "horizontal": ("Draw a horizontal line across the center of the graph.", "Grafiğin ortasından yatay bir çizgi çizin."),
    "approaching": ("As x is approaching zero, the function value approaches infinity.", "x sıfıra yaklaşırken, fonksiyon değeri sonsuza yaklaşır."),
    "approach": ("We need to approach this mathematical problem from a different angle.", "Bu matematiksel probleme farklı bir açıdan yaklaşmamız gerekiyor."),
    "standstill": ("The snowstorm brought all city traffic to a complete standstill.", "Kar fırtınası tüm şehir trafiğini tamamen durma noktasına getirdi."),
    "coherence": ("Her essay was praised for its clear structure and logical coherence.", "Makalesi, net yapısı ve mantıksal tutarlılığı nedeniyle övgü aldı."),
    "fluency": ("Daily speaking practice is the best way to achieve natural fluency.", "Akıcılık kazanmanın en iyi yolu günlük konuşma pratiğidir."),
    "criteria": ("Does the applicant meet all the required academic criteria?", "Aday gerekli tüm akademik kriterleri karşılıyor mu?"),
    "unemployment": ("The unemployment rate dropped significantly in the third quarter.", "İşsizlik oranı üçüncü çeyrekte belirgin şekilde düştü."),
    "remain stable": ("Consumer prices are expected to remain stable over the next few months.", "Tüketici fiyatlarının önümüzdeki birkaç ay boyunca sabit kalması bekleniyor."),
    "increase rapidly": ("Online shopping continues to increase rapidly each year.", "İnternetten alışveriş her yıl hızla artmaya devam ediyor."),
    "decrease significantly": ("Air pollution decreased significantly during the lockdown.", "Karantina döneminde hava kirliliği önemli ölçüde azaldı."),

    # Günlük & Yaygın Fiiller / Phrasal Verbs
    "store": ("You can store your luggage in the hotel locker.", "Valizinizi otel dolabında depolayabilirsiniz."),
    "back up": ("Always back up your files to an external drive before updating.", "Güncellemeden önce dosyalarınızı her zaman harici bir sürücüye yedekleyin."),
    "although": ("Although it was raining hard, they decided to continue the match.", "Şiddetli yağmur yağmasına rağmen maça devam etmeye karar verdiler."),
    "fortunately": ("Fortunately, nobody was hurt during the unexpected earthquake.", "Neyse ki beklenmedik deprem sırasında kimse yaralanmadı."),
    "make it": ("If we hurry up, we might make it to the lecture on time.", "Acele edersek derse vaktinde yetişebiliriz."),
    "yet": ("I haven't received the test results from the laboratory yet.", "Laboratuvardan test sonuçlarını henüz almadım."),
    "on time": ("The international flight departed exactly on time.", "Uluslararası uçuş tam vaktinde kalktı."),
    "during": ("Please remain in your seat during the landing.", "Lütfen iniş sırasında koltuğunuzda oturun."),
    "cousin": ("My cousin is visiting us from London this weekend.", "Kuzenim bu hafta sonu bizi Londra'dan ziyarete geliyor."),
    "summer vacation": ("We spent our summer vacation camping near the mountain lake.", "Yaz tatilimizi dağ gölü kenarında kamp yaparak geçirdik."),
    "few years ago": ("I graduated from university a few years ago.", "Üniversiteden birkaç yıl önce mezun oldum."),
    "break the habit": ("It takes conscious effort to break an unhealthy habit.", "Sağlıksız bir alışkanlığı bırakmak bilinçli bir çaba gerektirir."),
    "plenty": ("There is plenty of fresh water and food available.", "Bol miktarda taze su ve yiyecek mevcut."),
    "enough": ("Make sure you drink enough water throughout the day.", "Gün boyunca yeterince su içtiğinizden emin olun."),
    "sufficient": ("The evidence was not sufficient to prove the claim.", "Kanıtlar iddiayı kanıtlamak için yeterli değildi."),
    "check": ("Always double check your answers before submitting the form.", "Formu göndermeden önce cevaplarınızı her zaman iki kez kontrol edin."),
    "towel": ("Use a clean dry towel to dry your hands.", "Ellerinizi kurulamak için temiz ve kuru bir havlu kullanın."),
    "dry": ("Hang your wet clothes outside so they can dry in the sun.", "Güneşte kuruyabilmeleri için ıslak kıyafetlerinizi dışarı asın."),
    "accident": ("I dropped the glass completely by accident.", "Bardağı tamamen kazara düşürdüm."),
    "tomorrow": ("The final project is due tomorrow afternoon.", "Bitirme projesinin teslim tarihi yarın öğleden sonradır."),
    "spoon": ("Stir the soup gently with a wooden spoon.", "Çorbayı tahta bir kaşıkla yavaşça karıştırın."),
    "fork": ("She picked up her fork and started eating the salad.", "Çatalını aldı ve salatayı yemeye başladı."),
    "split up": ("The teacher decided to split up the students into three small groups.", "Öğretmen öğrencileri üç küçük gruba ayırmaya karar verdi."),
    "separate": ("Store raw meat and fresh vegetables in separate containers.", "Çiğ et ve taze sebzeleri ayrı kaplarda saklayın."),
    "stick together": ("If we stick together, we can overcome any obstacle.", "Birlikte kalırsak her engelin üstesinden gelebiliriz."),
    "carry": ("Could you help me carry these heavy shopping bags upstairs?", "Bu ağır alışveriş poşetlerini yukarı taşımama yardım edebilir misin?"),
    "attend": ("All members are required to attend the annual general meeting.", "Tüm üyelerin yıllık genel kurula katılması zorunludur."),
    "anymore": ("I don't drink caffeinated coffee after dinner anymore.", "Artık akşam yemeğinden sonra kafeinli kahve içmiyorum."),
    "headache": ("A cup of warm herbal tea helped relieve my headache.", "Bir fincan ılık bitki çayı baş ağrımı hafifletmeye yardımcı oldu."),
    "terrible": ("We got caught in a terrible traffic jam on the highway.", "Otoyolda korkunç bir trafik sıkışıklığına yakalandık."),
    "nowadays": ("Nowadays, most people read news on their smartphones.", "Şu günlerde çoğu insan haberleri akıllı telefonlarından okuyor."),
    "currently": ("She is currently working as a software developer in Berlin.", "Şu anda Berlin'de yazılım geliştirici olarak çalışıyor."),
    "let": ("Let me know as soon as you arrive at the station.", "İstasyona varır varmaz bana haber ver."),
    "begin": ("The ceremony will begin promptly at ten o'clock.", "Tören tam saat onda başlayacak."),
    "turn": ("Turn right at the intersection and go straight.", "Kavşaktan sağa dönün ve düz gidin."),
    "might": ("Take an umbrella because it might rain this afternoon.", "Öğleden sonra yağmur yağabileceği için yanına bir şemsiye al."),
    "bring": ("Don't forget to bring your passport when you travel.", "Seyahat ederken pasaportunuzu getirmeyi unutmayın."),
    "happen": ("Unexpected events can happen at any moment.", "Beklenmedik olaylar her an olabilir."),
    "provide": ("The library will provide free internet access to all visitors.", "Kütüphane tüm ziyaretçilere ücretsiz internet erişimi sağlayacaktır."),
    "stand": ("Please stand behind the security line until called.", "Lütfen çağrılana kadar güvenlik çizgisinin arkasında durun."),
    "meet": ("I look forward to meeting you in person tomorrow.", "Yarın sizinle şahsen tanışmayı sabırsızlıkla bekliyorum."),
    "include": ("Does the registration fee include study materials?", "Kayıt ücretine çalışma materyalleri dahil mi?"),
    "lead": ("Consistent discipline and practice lead to mastery.", "Tutarlı disiplin ve pratik ustalığa götürür."),
    "spend": ("Try to spend more time outdoors in nature.", "Doğada açık havada daha fazla zaman geçirmeye çalışın."),
    "grow": ("Plants grow much faster when they receive adequate sunlight.", "Bitkiler yeterli güneş ışığı aldıklarında çok daha hızlı büyür."),
    "consider": ("Please consider all perspectives before making your final decision.", "Nihai kararınızı vermeden önce lütfen tüm bakış açılarını değerlendirin."),
    "appear": ("Bright stars appear clearly in the desert night sky.", "Çöl gece gökyüzünde parlak yıldızlar net bir şekilde görünür."),
    "serve": ("They serve fresh homemade bread with every meal.", "Her öğünde taze ev yapımı ekmek servis ediyorlar."),
    "expect": ("We expect the package to arrive by tomorrow morning.", "Paketin yarın sabaha kadar ulaşmasını bekliyoruz."),
    "reach": ("You can reach our customer support team via email or phone.", "Müşteri destek ekibimize e-posta veya telefonla ulaşabilirsiniz."),
    "remain": ("Please remain calm while the emergency team arrives.", "Acil müdahale ekibi gelene kadar lütfen sakin kalın."),
    "even": ("Even a small improvement each day leads to huge results over time.", "Her gün küçük bir gelişme bile zamanla muazzam sonuçlara yol açar."),
    "cultural": ("Istanbul has a rich cultural heritage spanning thousands of years.", "İstanbul binlerce yıla yayılan zengin bir kültürel mirasa sahiptir."),
    "traditional": ("They prepared traditional dishes for the family gathering.", "Aile toplantısı için geleneksel yemekler hazırladılar."),
    "religious": ("The historic mosque is an important religious landmark.", "Tarihi cami önemli bir dini simgedir."),
    "entire": ("She read the entire book in a single afternoon.", "Bütün kitabı tek bir öğleden sonrada okudu."),
    "various": ("We explored various strategies to optimize the workflow.", "İş akışını optimize etmek için çeşitli stratejileri araştırdık."),
    "environmental": ("Protecting forests is crucial for maintaining environmental balance.", "Ormanları korumak çevresel dengeyi sürdürmek için kritik öneme sahiptir."),
    "simple": ("A simple explanation is usually the most effective one.", "Basit bir açıklama genellikle en etkili olanıdır."),
    "significant": ("Regular sleep has a significant impact on cognitive performance.", "Düzenli uykunun bilişsel performans üzerinde önemli bir etkisi vardır."),
    "fine": ("The weather is fine today, perfect for an outdoor picnic.", "Bugün hava iyi, açık havada piknik yapmak için mükemmel."),
    "foreign": ("Speaking a foreign language opens up international opportunities.", "Yabancı bir dil konuşmak uluslararası fırsatların kapısını açar."),
    "current": ("What is your current progress on the assigned project?", "Atanan projedeki mevcut ilerlemeniz nedir?"),
    "likely": ("It is likely that interest rates will decrease next month.", "Gelecek ay faiz oranlarının düşmesi muhtemeldir."),
    "available": ("Are there any tickets available for tonight's concert?", "Bu geceki konser için hiç bilet mevcut mu?"),
    "similarity": ("Scientists noted a remarkable similarity in the DNA sequences.", "Bilim insanları DNA dizilimlerinde dikkate değer bir benzerlik fark ettiler."),
    "certain": ("I am certain that practice makes progress.", "Pratiğin ilerleme sağladığından eminim."),
    "recent": ("A recent survey highlighted the benefits of flexible work hours.", "Yakın zamanda yapılan bir anket esnek çalışma saatlerinin faydalarını vurguladı."),
    "whole": ("He dedicated his whole life to scientific research.", "Bütün hayatını bilimsel araştırmalara adadı."),
    "able": ("With proper training, anyone is able to learn this skill.", "Doğru eğitimle herkes bu beceriyi öğrenebilir."),
    "polish": ("Use a microfiber cloth to polish the lens.", "Merceği parlatmak için mikrofiber bir bez kullanın."),
    "vinegar": ("A mixture of warm water and vinegar works well for cleaning.", "Ilık su ve sirke karışımı temizlik için iyi iş görür."),
    "talent": ("She discovered her musical talent at a very young age.", "Müzik yeteneğini çok genç yaşta keşfetti."),
    "impatience": ("Impatience often leads to rushed and careless errors.", "Sabırsızlık genellikle aceleci ve dikkatsiz hatalara yol açar."),
    "patience": ("Mastering a language requires dedication and patience.", "Bir dilde ustalaşmak özveri ve sabır gerektirir."),
    "furniture": ("They chose minimalist Scandinavian furniture for their new apartment.", "Yeni daireleri için minimalist İskandinav mobilyaları seçtiler."),
    "silk": ("The dress was crafted from soft mulberry silk.", "Elbise yumuşak dut ipeğinden üretilmişti."),
    "cotton": ("Breathable cotton fabric is ideal for hot summer days.", "Nefes alabilen pamuklu kumaş sıcak yaz günleri için idealdir."),
    "coal": ("Many countries are transitioning away from coal power plants.", "Birçok ülke kömürlü elektrik santrallerinden uzaklaşıyor."),
    "wool": ("A fine wool coat provides excellent warmth against cold winds.", "İnce bir yün palto soğuk rüzgarlara karşı mükemmel sıcaklık sağlar."),
    "leather": ("The handmade leather boots lasted for over a decade.", "El yapımı deri botlar on yıldan fazla dayandı."),
    "progress": ("She made impressive progress in her spoken English this semester.", "Bu dönem konuşma İngilizcesinde etkileyici bir ilerleme kaydetti."),
    "advice": ("He gave me practical advice on how to prepare for job interviews.", "İş görüşmelerine nasıl hazırlanacağım konusunda bana pratik tavsiyeler verdi."),
    "toothpaste": ("Dentists recommend brushing twice daily with fluoride toothpaste.", "Diş hekimleri florürlü diş macunuyla günde iki kez fırçalamayı önerir."),
    "currency": ("Exchange your local currency before traveling abroad.", "Yurt dışına seyahat etmeden önce yerel para biriminizi bozdurun."),
    "equipment": ("Inspect all climbing equipment thoroughly before starting the ascent.", "Tırmanışa başlamadan önce tüm tırmanma ekipmanlarını iyice inceleyin."),
    "baggage": ("You can pick up your checked baggage at carousel four.", "Kayıtlı bagajınızı dört numaralı banttan alabilirsiniz."),
    "luggage": ("Pack your luggage lightly to make traveling more comfortable.", "Seyahati daha rahat hale getirmek için valizinizi hafif hazırlayın."),
    "abroad": ("Living abroad teaches you independence and cultural adaptability.", "Yurt dışında yaşamak size bağımsızlığı ve kültürel uyumu öğretir."),
    "catch": ("Hurry or you will miss the train!", "Acele et, yoksa treni kaçıracaksın!"),
    "arrive": ("What time will your flight arrive at the airport?", "Uçuşunuz havaalanına saat kaçta varacak?"),
    "become": ("With enough practice, complex tasks become second nature.", "Yeterli pratikle karmaşık görevler ikinci bir doğa haline gelir."),
    "receive": ("You will receive a notification once your order has shipped.", "Siparişiniz kargoya verildiğinde bir bildirim alacaksınız."),
    "obtain": ("You must obtain permission before accessing the laboratory.", "Laboratuvara girmeden önce izin almanız gerekir."),
    "take a breath": ("Take a deep breath to calm your nerves before the speech.", "Konuşmadan önce sinirlerinizi yatıştırmak için derin bir nefes alın."),
    "according to": ("According to the study, walking daily reduces stress levels.", "Araştırmaya göre her gün yürümek stres seviyelerini azaltır."),
    "major": ("Renewable energy is playing a major role in fighting global warming.", "Yenilenebilir enerji küresel ısınmayla mücadelede ana bir rol oynuyor."),
    "important": ("It is important to review your flashcards on a regular schedule.", "Kartlarınızı düzenli bir programda gözden geçirmeniz önemlidir."),
    "individual": ("Every individual has a unique learning style and pace.", "Her bireyin kendine özgü bir öğrenme tarzı ve hızı vardır."),
    "encouraged": ("Her parents always encouraged her to pursue scientific research.", "Ailesi onu her zaman bilimsel araştırmalar yapmaya teşvik etti."),
    "confidence": ("Speaking up in meetings will gradually build your professional confidence.", "Toplantılarda söz almak zamanla mesleki güveninizi geliştirecektir."),
    "majors": ("Computer science is one of the most popular college majors.", "Bilgisayar bilimi en popüler üniversite ana dallarından biridir."),
    "intensive": ("He attended an intensive coding bootcamp for three months.", "Üç ay boyunca yoğun bir yazılım kampına katıldı."),
    "gain": ("Internships help students gain valuable practical experience.", "Stajlar öğrencilerin değerli pratik deneyimler kazanmasına yardımcı olur."),
    "ability": ("Reading frequently enhances your ability to express complex thoughts.", "Sık okumak karmaşık düşünceleri ifade etme yeteneğinizi geliştirir."),
    "particular": ("Is there any particular topic you would like to focus on today?", "Bugün odaklanmak istediğiniz belirli bir konu var mı?"),
    "among": ("Cooperation among team members ensured the project's success.", "Ekip üyeleri arasındaki iş birliği projenin başarısını sağladı."),
    "themselves": ("They organized the entire charity event all by themselves.", "Tüm yardım etkinliğini tamamen kendi kendilerine organize ettiler."),
    "situation": ("Stay calm and assess the situation before reacting.", "Tepki vermeden önce sakin kalın ve durumu değerlendirin."),
    "their fields": ("Both keynote speakers are renowned leaders in their fields.", "Her iki açılış konuşmacısı da kendi alanlarında tanınmış liderlerdir."),
    "benefits": ("Getting quality sleep provides immense physical and mental benefits.", "Kaliteli uyku almak muazzam fiziksel ve zihinsel yararlar sağlar."),
    "bring up": ("Feel free to bring up any concerns during the Q&A session.", "Soru-cevap bölümünde aklınıza takılan her konuyu gündeme getirebilirsiniz."),
    "brought up": ("He was brought up in a bilingual household.", "İki dilli bir evde yetiştirildi / büyütüldü."),
    "proud of": ("We are truly proud of your hard work and achievements.", "Sıkı çalışmanızdan ve başarılarınızdan gerçekten gurur duyuyoruz."),
    "own idea": ("Trust your instincts and present your own idea with confidence.", "İçgüdülerinize güvenin ve kendi fikrinizi özgüvenle sunun."),
    "knowledge": ("Sharing knowledge with others helps solidify what you know.", "Bilgiyi başkalarıyla paylaşmak bildiklerinizi pekiştirmeye yardımcı olur."),
    "encouraging": ("The mentor wrote an encouraging note on my draft essay.", "Rehber öğretmen taslak makaleme cesaret verici bir not yazdı."),
    "conveying": ("Clear charts are very effective in conveying statistical data.", "Net grafikler istatistiksel verileri iletmede çok etkilidir."),
    "teaching": ("Effective teaching involves listening as much as explaining.", "Etkili öğretim açıklamak kadar dinlemeyi de içerir."),
    "do not worry": ("Do not worry about making mistakes; they are part of learning.", "Hata yapmaktan endişelenmeyin; onlar öğrenmenin bir parçasıdır."),
    "talent": ("Hard work consistently beats raw talent when talent doesn't work hard.", "Yetenek sıkı çalışmadığında, sıkı çalışma saf yeteneği her zaman yener."),
    "to improve": ("Read every day to improve your comprehension and vocabulary.", "Anlama ve kelime bilginizi geliştirmek için her gün okuyun."),
    "topic": ("Select an interesting topic for your research presentation.", "Araştırma sunumunuz için ilginç bir konu seçin."),
    "exactly": ("That is exactly the outcome we were hoping to achieve.", "Ulaşmayı umduğumuz sonuç tam olarak buydu."),
    "it depends on": ("The departure time depends on whether the fog clears up.", "Kalkış saati sisin dağılıp dağılmayacağına bağlı."),
    "the oven": ("Always wear oven mitts when taking hot trays out of the oven.", "Sıcak tepsileri fırından çıkarırken her zaman fırın eldiveni takın."),
    "it takes about": ("It takes about ten thousand hours of practice to achieve world-class mastery.", "Dünya çapında ustalığa ulaşmak yaklaşık on bin saatlik pratik gerektirir."),
    "flavor": ("Fresh herbs bring out the natural flavor of the dish.", "Taze otlar yemeğin doğal lezzetini ortaya çıkarır."),
    "let me explain": ("Let me explain how the algorithm works behind the scenes.", "Algoritmanın arka planda nasıl çalıştığını anlatmama izin ver."),
    "order": ("Can we order some appetizers while we look at the menu?", "Menüye bakarken birkaç başlangıç sipariş edebilir miyiz?"),
    "main course": ("The roast lamb was served as the main course.", "Kuzu fırın ana yemek olarak servis edildi."),
    "enhance": ("Regular exercise will enhance your energy levels throughout the day.", "Düzenli egzersiz gün boyunca enerji seviyenizi artıracaktır."),
    "spend": ("Invest your time wisely rather than just spending it.", "Zamanınızı sadece harcamak yerine akıllıca değerlendirin."),
    "especially": ("Drink lots of water, especially during hot summer afternoons.", "Özellikle sıcak yaz öğleden sonralarında bol su için."),
    "in any way": ("Let me know if I can support your project in any way.", "Projenizi herhangi bir şekilde destekleyebilirsem bana bildirin."),
    "ease": ("Meditation helps ease mental stress and physical tension.", "Meditasyon zihinsel stresi ve fiziksel gerginliği hafifletmeye yardımcı olur."),
    "enough": ("There is enough room in the car for everyone's luggage.", "Arabada herkesin bagajı için yeterli yer var."),
    "to be honest": ("To be honest, I think the second design is much more intuitive.", "Dürüst olmak gerekirse, bence ikinci tasarım çok daha sezgisel."),
    "you're welcome": ("'Thanks for the coffee!' — 'You're welcome, anytime!'", "'Kahve için teşekkürler!' — 'Rica ederim, her zaman!'"),
    "identification": ("Keep your photo identification readily accessible at the airport.", "Fotoğraflı kimliğinizi havaalanında kolayca erişilebilir tutun."),
    "candidate": ("The successful candidate will demonstrate strong problem-solving skills.", "Başarılı aday güçlü problem çözme becerileri sergileyecektir."),
    "taking place": ("The graduation ceremony is taking place in the grand auditorium.", "Mezuniyet töreni büyük salonda gerçekleşiyor."),
    "mock": ("Taking mock interviews is a great way to overcome interview anxiety.", "Deneme mülakatları yapmak mülakat kaygısının üstesinden gelmenin harika bir yoludur."),
    "situtation": ("Stay calm and assess the situation before reacting.", "Tepki vermeden önce sakin kalın ve durumu değerlendirin."),
    "few": ("A few honest words can make all the difference.", "Birkaç samimi kelime her şeyi değiştirebilir."),
    "which": ("Which book would you recommend for beginners?", "Yeni başlayanlar için hangi kitabı önerirsiniz?"),
    "those": ("Those students showed exceptional dedication throughout the semester.", "O öğrenciler dönem boyunca olağanüstü bir özveri gösterdiler."),
    "then": ("We had a quick lunch and then headed back to the library.", "Hızlıca bir öğle yemeği yedik ve daha sonra kütüphaneye geri döndük."),
    "their": ("They presented their findings clearly to the entire committee.", "Bulgularını tüm komiteye açık bir şekilde sundular."),
    "some": ("Would you like some warm tea before we start?", "Başlamadan önce biraz sıcak çay ister misiniz?"),
    "into": ("She poured the fresh milk into a clean glass.", "Taze sütü temiz bir bardağın içine döktü."),
    "as": ("Treat others as you would like to be treated.", "Başkalarına size davranılmasını istediğiniz gibi davranın."),
    "also": ("She speaks German and also knows fluent Spanish.", "Almanca konuşuyor ve ayrıca akıcı bir şekilde İspanyolca da biliyor."),
    "include": ("Does the basic price include breakfast and taxes?", "Temel fiyata kahvaltı ve vergiler dahil mi?"),
    "us": ("Join us for dinner at the new Italian restaurant tonight.", "Bu akşam yeni İtalyan restoranında akşam yemeği için bize katılın."),
    "from": ("She received an encouraging postcard from an old friend.", "Eski bir arkadaşından cesaret verici bir kartpostal aldı."),
    "of": ("Knowledge of mathematics is essential for computer science.", "Matematik bilgisi bilgisayar bilimleri için elzemdir.")
}


def normalize_term_for_lookup(term: str) -> str:
    """Türkçe karakterleri ve gereksiz noktalama işaretlerini normalize eder."""
    if not term:
        return ""
    s = term.replace("İ", "i").replace("I", "i").replace("ı", "i").lower()
    s = s.replace("...", " ").replace("..", " ").strip()
    return " ".join(s.split())


def get_authentic_sentence(term: str) -> Optional[Tuple[str, str]]:
    """
    Belirtilen kelime/kalıp için doğrulanmış, doğal ve dilbilgisel olarak doğru
    İngilizce örnek cümle ve Türkçe çevirisini döndürür.
    Büyük/küçük harf, Türkçe karakterler ve fazla boşluklara duyarsızdır.
    """
    if not term:
        return None
    cleaned = normalize_term_for_lookup(term)
    
    # Birebir eşleşme
    if cleaned in AUTHENTIC_SENTENCES_MAP:
        return AUTHENTIC_SENTENCES_MAP[cleaned]
    
    # "to " ön eki temizleyerek dene
    if cleaned.startswith("to "):
        sub = cleaned[3:].strip()
        if sub in AUTHENTIC_SENTENCES_MAP:
            return AUTHENTIC_SENTENCES_MAP[sub]
            
    # "the " ön eki temizleyerek dene
    if cleaned.startswith("the "):
        sub = cleaned[4:].strip()
        if sub in AUTHENTIC_SENTENCES_MAP:
            return AUTHENTIC_SENTENCES_MAP[sub]
            
    return None
