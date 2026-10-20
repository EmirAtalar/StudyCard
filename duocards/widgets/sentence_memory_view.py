"""Kaynak ve çevirileriyle 10 örnek cümleyi inceleme ve dinleme ekranı."""
import logging
import sqlite3
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QColor
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QListWidget,QTableWidget,
    QTableWidgetItem,QPushButton,QSplitter,QAbstractItemView,QHeaderView,QLineEdit,QMessageBox)
from duocards.settings import settings
from duocards.ui_localization import ui_text
from duocards.audio import audio_player
from duocards.practice_menus import title
from duocards.sentence_memory import (request_examples, read_examples, fetch_status, add_example, card_language, fetch_error)
from duocards.languages import get_language_code
from duocards.widgets.practice_view import CardFilters
from duocards.widgets.practice_styles import PRACTICE_STYLES
from duocards.ui_localization import ui_text, localize_tree , QLabel, QPushButton, QLineEdit

logger=logging.getLogger(__name__)
SOURCE_NAMES={'tatoeba':'Tatoeba','wikipedia':'Wikipedia'}

MESSAGES={
'fetch':['İnternetten Örnek Ara','Find Online Examples','Online-Beispiele Suchen','Buscar Ejemplos en Línea'],
'listen':['Dinle','Listen','Anhören','Escuchar'],
'empty':['Bu seçimde kart yok. Önce bir kelime ekle.','No cards match. Add a word first.','Keine passenden Karten. Füge ein Wort hinzu.','No hay tarjetas. Añade una palabra.'],
'practice':['Kelime alıştırması','Word exercise','Wortübung','Ejercicio de palabra'],
'user':['Senin örneğin','Your example','Dein Beispiel','Tu ejemplo'],
'local':['Yerel örnek','Local example','Lokales Beispiel','Ejemplo local'],
'loading':['Gerçek kullanım örnekleri aranıyor…','Searching for usage examples…','Beispiele werden gesucht…','Buscando ejemplos…'],
'offline':['İnternete erişilemedi. Kayıtlı cümleler kullanılabilir; sonra yeniden deneyebilirsin.','No internet connection. Saved sentences remain available; try again later.','Keine Internetverbindung. Gespeicherte Sätze bleiben verfügbar.','Sin conexión. Las frases guardadas siguen disponibles.'],
'partial':['Kaynakta yeterli örnek bulunamadı; yalnızca bulunan gerçek cümleler gösteriliyor.','Not enough usage examples were found; only genuine sentences are shown.','Zu wenige Beispiele gefunden; nur echte Beispiele werden angezeigt.','Faltan ejemplos; solo se muestran ejemplos reales.'],
'ready':['10 kullanım örneği hazır ve hafızaya kaydedildi.','10 usage examples are saved.','10 Beispiele sind gespeichert.','10 ejemplos guardados.'],
'local_status':['Yerel cümleler hazır. İnternet araması gerçek kullanım örnekleriyle hafızayı zenginleştirir.','Local sentences are ready. Online search adds usage examples.','Lokale Sätze sind verfügbar. Die Online-Suche ergänzt Beispiele.','Frases locales disponibles. La búsqueda añade ejemplos de uso.'],
'add':['Örnek Kaydet','Save Example','Beispiel Speichern','Guardar Ejemplo'],
'sentence':['Kelimenin geçtiği bir cümle yaz…','Write a sentence containing the word…','Satz mit dem Wort eingeben…','Escribe una frase con la palabra…'],
'translation':['İsteğe bağlı cümle çevirisi…','Optional sentence translation…','Optionale Übersetzung…','Traducción opcional…'],
'saved':['Örnek hafızaya kaydedildi.','Example saved.','Beispiel gespeichert.','Ejemplo guardado.'],
'headers':[['Cümle','Çeviri','Kaynak'],['Sentence','Translation','Source'],['Satz','Übersetzung','Quelle'],['Frase','Traducción','Fuente']],
}

MESSAGES.update({
'count':['{count} / 10 kullanım örneği','{count} / 10 usage examples','{count} / 10 Beispielsätze','{count} / 10 ejemplos de uso'],
'invalid':['Cümle, hedef kelimeyi aynı yazılışla içermeli.','The sentence must contain the target word with the same spelling.','Der Satz muss das Zielwort in derselben Schreibweise enthalten.','La frase debe contener la palabra con la misma escritura.'],
'no_results':['Bu kelime ve kaynak dil için örnek bulunamadı. Kartın kaynak dilini kontrol et.','No examples for this word and source language. Check the card’s source language.','Keine Beispiele für dieses Wort und diese Sprache. Prüfe die Ausgangssprache der Karte.','No hay ejemplos para esta palabra e idioma. Revisa el idioma de origen.'],
'dns':['Sunucunun adresi çözülemedi. İnternet veya DNS bağlantısını kontrol et.','Could not resolve the server address. Check your internet or DNS connection.','Serveradresse nicht auflösbar. Prüfe Internet oder DNS.','No se pudo resolver el servidor. Revisa internet o DNS.'],
'timeout':['Cümle servisi zamanında yanıt vermedi. Yeniden dene.','The sentence service timed out. Try again.','Der Satzdienst hat nicht rechtzeitig geantwortet. Erneut versuchen.','El servicio no respondió a tiempo. Inténtalo de nuevo.'],
'http':['Cümle servisi HTTP {code} hatası verdi. Yeniden deneyebilirsin.','The sentence service returned HTTP {code}. You can retry.','Der Satzdienst meldet HTTP {code}. Erneut versuchen.','El servicio devolvió HTTP {code}. Puedes reintentar.'],
'unsupported':['Bu kaynak dil cümle servisinde desteklenmiyor.','This source language is not supported by the sentence service.','Diese Ausgangssprache wird vom Satzdienst nicht unterstützt.','El servicio no admite este idioma de origen.'],
'service':['Cümle servisine erişilemedi. Kayıtlı örnekler korunuyor; yeniden dene.','Could not access the sentence service. Saved examples are preserved; retry.','Satzdienst nicht erreichbar. Gespeicherte Beispiele bleiben erhalten.','Servicio no disponible. Se conservan los ejemplos guardados.'],
'offline_example':['Çevrimdışı örnek','Offline example','Offline-Beispiel','Ejemplo sin conexión'],
'dictionary':['Sözlük örneği','Dictionary example','Wörterbuchbeispiel','Ejemplo del diccionario'],
'storage':['Cümle hafızasına şu anda erişilemedi. Biraz sonra yeniden dene.','Sentence memory is temporarily unavailable. Try again shortly.','Der Satzspeicher ist vorübergehend nicht verfügbar. Versuche es gleich erneut.','La memoria de frases no está disponible temporalmente. Inténtalo en un momento.'],
'busy':['Diğer cümle aramaları sürüyor. Biraz sonra yeniden dene.','Other sentence searches are running. Try again shortly.','Andere Satzsuchen laufen. Versuche es gleich erneut.','Hay otras búsquedas en curso. Inténtalo en un momento.'],
})


class SentenceMemoryView(QWidget):
    data_changed = pyqtSignal()
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setObjectName("sentenceMemoryPage")
        self.setStyleSheet(PRACTICE_STYLES)
        self.lang=settings.get('ui_language','tr')
        self.cards=[]
        self.current_card=None
        self.rows=[]
        self._fingerprint=None
        layout=QVBoxLayout(self)
        layout.setContentsMargins(24,22,24,22)
        layout.setSpacing(12)
        self.lbl_title=QLabel(title('sentence_memory',self.lang))
        self.lbl_title.setProperty('class','page-title')
        layout.addWidget(self.lbl_title)
        self.filters=CardFilters(self.lang)
        self.filters.changed.connect(self.reload_cards)
        layout.addWidget(self.filters)
        splitter=QSplitter(Qt.Orientation.Horizontal)
        self.list_words=QListWidget()
        self.list_words.setMinimumWidth(140)
        self.list_words.currentRowChanged.connect(self._select_card)
        splitter.addWidget(self.list_words)
        panel=QWidget()
        body=QVBoxLayout(panel)
        body.setContentsMargins(12,0,0,0)
        self.lbl_term=QLabel()
        self.lbl_term.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_term.setWordWrap(True)
        self.lbl_term.setStyleSheet('font-size:20px; font-weight:700;')
        body.addWidget(self.lbl_term)
        self.lbl_count=QLabel()
        body.addWidget(self.lbl_count)
        self.lbl_status=QLabel()
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_status.setStyleSheet('color:#94a3b8;')
        body.addWidget(self.lbl_status)
        self.table=QTableWidget(0,3)
        self.table.setShowGrid(False)
        self.table.setHorizontalHeaderLabels(self.msg('headers'))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1,120)
        self.table.setColumnWidth(2,110)
        self.table.verticalHeader().setDefaultSectionSize(72)
        self.table.cellDoubleClicked.connect(self._open_source)
        body.addWidget(self.table,1)
        buttons=QHBoxLayout()
        self.btn_listen=QPushButton(self.msg('listen'))
        self.btn_listen.clicked.connect(self._listen)
        self.btn_fetch=QPushButton(self.msg('fetch'))
        self.btn_fetch.clicked.connect(self._fetch)
        buttons.addWidget(self.btn_listen)
        buttons.addWidget(self.btn_fetch)
        body.addLayout(buttons)
        self.input_example=QLineEdit()
        self.input_example.setPlaceholderText(self.msg('sentence'))
        self.input_translation=QLineEdit()
        self.input_translation.setPlaceholderText(self.msg('translation'))
        self.btn_add=QPushButton(self.msg('add'))
        self.btn_add.clicked.connect(self._add)
        body.addWidget(self.input_example)
        body.addWidget(self.input_translation)
        body.addWidget(self.btn_add)
        splitter.addWidget(panel)
        splitter.setStretchFactor(1,1)
        splitter.setSizes([160,800])
        layout.addWidget(splitter,1)
        self._timer=QTimer(self)
        self._timer.setInterval(750)
        self._timer.timeout.connect(self._poll)
        self.reload_cards()

    def msg(self,key):
        return MESSAGES[key][('tr','en','de','es').index(self.lang) if self.lang in ('tr','en','de','es') else 1]

    def reload_cards(self):
        current_id=self.current_card['id'] if self.current_card else None
        self.filters.refresh()
        self.cards=self.filters.cards()
        self.list_words.blockSignals(True)
        self.list_words.clear()
        for card in self.cards:
            self.list_words.addItem(card['term'])
        idx=next((i for i,c in enumerate(self.cards) if c['id']==current_id),0)
        self.list_words.setCurrentRow(idx if self.cards else -1)
        self.list_words.blockSignals(False)
        self._select_card(idx if self.cards else -1)

    def _select_card(self,index):
        self.current_card=self.cards[index] if 0<=index<len(self.cards) else None
        self._fingerprint=None
        self.input_example.clear()
        self.input_translation.clear()
        for control in (self.btn_listen,self.btn_fetch,self.btn_add,self.input_example,self.input_translation):
            control.setEnabled(bool(self.current_card))
        if not self.current_card:
            self.table.setRowCount(0)
            self.rows=[]
            self.lbl_term.setText(self.msg('empty'))
            self.lbl_count.clear()
            self.lbl_status.clear()
            return
        self.lbl_term.setText(self.current_card['term']+' · '+self.current_card['definition'])
        if self.isVisible():
            self._request_examples()
        self._poll()

    def _request_examples(self,force=False):
        try:
            request_examples(self.current_card,force=force)
            return True
        except (sqlite3.Error,OSError,RuntimeError) as exc:
            logger.exception('Could not start sentence search')
            self.lbl_status.setText(self.msg('storage' if isinstance(exc,sqlite3.Error) else 'service'))
            self.btn_fetch.setEnabled(True)
            return False

    def _source_label(self,source):
        if source in SOURCE_NAMES:
            return SOURCE_NAMES[source]
        if source in MESSAGES:
            return self.msg(source)
        return str(source or '')

    def _poll(self):
        if not self.current_card:
            return
        try:
            rows=[row for row in read_examples(self.current_card) if row['kind']=='example']
            state=fetch_status(self.current_card)
            error=fetch_error(self.current_card)
        except sqlite3.Error:
            self.lbl_status.setText(self.msg('storage'))
            self.btn_fetch.setEnabled(True)
            self._fingerprint=None
            return
        self.rows=rows
        fingerprint=(error,tuple((r['text'],r['kind'],str(r['translations']),r['source'],r.get('url',''),r.get('author',''),r.get('license','')) for r in self.rows),state,self.lang)
        if fingerprint==self._fingerprint:
            return
        self._fingerprint=fingerprint
        selected=self.table.currentRow()
        self.table.setRowCount(len(self.rows))
        target=get_language_code(self.current_card.get('target_lang','tr'))
        for i,row in enumerate(self.rows):
            source=self._source_label(row['source'])
            for j,value in enumerate((row['text'],row['translations'].get(target,''),source)):
                item=QTableWidgetItem(value)
                item.setForeground(QColor('#ffffff'))
                item.setToolTip(value+('\n'+row.get('author','')+' · '+row.get('license','')+'\n'+row.get('url','') if j==2 else ''))
                self.table.setItem(i,j,item)
        self.table.resizeRowsToContents()
        for row_index in range(self.table.rowCount()):
            self.table.setRowHeight(row_index,max(64,self.table.rowHeight(row_index)))
        if self.rows:
            self.table.selectRow(max(0,min(selected,len(self.rows)-1)))
        genuine=sum(r['kind']=='example' for r in self.rows)
        self.lbl_count.setText(self.msg('count').format(count=genuine))
        self.lbl_status.setText(self.msg(state if state in ('loading','offline','partial','ready') else 'local_status'))
        if state=='offline':
            key=error if error in ('dns','timeout','unsupported','busy') else 'http' if error.startswith('http_') else 'service'
            self.lbl_status.setText(self.msg(key).format(code=error.removeprefix('http_')))
        elif genuine==10 and state!='loading':
            self.lbl_status.setText(self.msg('ready'))
        elif state=='partial' and not self.rows:
            self.lbl_status.setText(self.msg('no_results'))
        self.btn_listen.setEnabled(bool(self.rows))
        self.btn_fetch.setEnabled(state!='loading')

    def _fetch(self):
        if self.current_card and self._request_examples(force=True):
            self._poll()

    def _listen(self):
        idx=self.table.currentRow()
        if self.current_card and 0<=idx<len(self.rows):
            audio_player.play_pronunciation(self.rows[idx]['text'],lang=card_language(self.current_card))

    def _open_source(self,row,col):
        if col==2 and 0<=row<len(self.rows) and self.rows[row].get('url'):
            QDesktopServices.openUrl(QUrl(self.rows[row]['url']))

    def _add(self):
        if not self.current_card:
            return
        try:
            add_example(self.current_card,self.input_example.text(),self.input_translation.text())
        except ValueError as exc:
            self.lbl_status.setText(self.msg('invalid'))
            return
        except sqlite3.Error:
            self.lbl_status.setText(self.msg('storage'))
            return
        self.input_example.clear()
        self.input_translation.clear()
        self._fingerprint=None
        if not self.current_card:
            self.lbl_term.setText(self.msg('empty'))
        self._poll()
        self.lbl_status.setText(self.msg('saved'))
        self.data_changed.emit()

    def showEvent(self,event):
        super().showEvent(event)
        if self.current_card:
            self._request_examples()
        self._timer.start()
        self._poll()

    def hideEvent(self,event):
        self._timer.stop()
        super().hideEvent(event)

    def update_language(self,lang):
        self.lang=lang
        self.filters.lang=lang
        self.filters.refresh()
        self.lbl_title.setText(title('sentence_memory',lang))
        self.table.setHorizontalHeaderLabels(self.msg('headers'))
        for button,key in ((self.btn_fetch,'fetch'),(self.btn_listen,'listen'),(self.btn_add,'add')):
            button.setText(self.msg(key))
        self.input_example.setPlaceholderText(self.msg('sentence'))
        self.input_translation.setPlaceholderText(self.msg('translation'))
        self._fingerprint=None
        if not self.current_card:
            self.lbl_term.setText(self.msg('empty'))
        self._poll()
        localize_tree(self,lang)
