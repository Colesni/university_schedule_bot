# AI APP SPECIFICATION

## Telegram Bot pentru orarul universitar

## 1. Scop

Construiește un bot Telegram simplu care permite unui student să-și
aleagă grupa și să afle rapid: - ce curs are acum sau care este
următorul; - programul complet pentru ziua curentă; - să își schimbe
grupa.

Fișierul Excel/Google Sheet cu orarul este sursa de adevăr pentru
program. Utilizatorul nu trebuie să deschidă manual Excelul.

## 2. MVP

### Inclus

1.  `/start`
2.  Selectarea grupei prin butoane Telegram
3.  Salvarea grupei selectate
4.  `🕐 Acum`
5.  `📅 Program azi`
6.  `⚙️ Schimbă grupa`
7.  Descărcarea și parsarea orarului
8.  Cache local al ultimului orar valid
9.  Refresh periodic al sursei

### Exclus din MVP

Nu implementa: - notificări sau remindere; - program săptămânal; -
examene/sesiuni separate; - Google Calendar; - abonamente/plăți; -
statistici; - admin panel; - conturi complexe sau autentificare
externă; - multi-universitate; - n8n; - Google Sheets API; - aplicație
web/mobile; - sisteme separate pentru profesori/săli; - administrare
manuală a orarului.

## 3. Stack

-   Python 3.11+
-   `python-telegram-bot`
-   SQLite
-   `pandas`
-   `openpyxl`
-   `python-dotenv`

Aplicația trebuie să poată rula local. Nu introduce PostgreSQL, Redis,
Docker sau alte servicii dacă nu sunt necesare pentru MVP.

## 4. Configurare

Valorile configurabile se păstrează în `.env`.

Exemplu:

``` env
TELEGRAM_BOT_TOKEN=
SCHEDULE_SOURCE_URL=
TIMEZONE=Europe/Chisinau
SCHEDULE_REFRESH_HOURS=72
```

URL-ul sursei NU trebuie hardcodat.

Tokenul Telegram nu trebuie inclus în cod, loguri sau repository. `.env`
trebuie inclus în `.gitignore`.

## 5. Sursa orarului

Sursa de producție este un Google Sheet public, accesat printr-un export
CSV/XLSX configurat în `SCHEDULE_SOURCE_URL`.

Pentru dezvoltare și teste se poate folosi fișierul Excel furnizat:
`2026-2027 Orar2_instruire_an.2,4_web (1)(1).xlsx`

Arhitectura sursei:

``` text
ScheduleSource
└── PublicExportScheduleSource
```

Trebuie să fie posibilă adăugarea ulterioară a altei implementări, de
exemplu `GoogleSheetsApiScheduleSource`, fără rescrierea parserului sau
a botului.

## 6. Structura REALĂ verificată a Excelului

Fișierul analizat conține: - o singură foaie relevantă: `orar`; - 130
rânduri; - 12 coloane; - 71 zone de celule îmbinate; - titlul indică
perioada `21.09.2026 - 18.10.2026`.

### Antet

Rândul 2 conține anul de studiu. Rândul 3 conține grupele. Rândul 4
conține informații despre numărul de studenți/subgrupe. Datele efective
ale orarului încep de la rândul 5.

### Grupe identificate

-   `MFR2501`
-   `IAFR2501`
-   `IAFR2502`
-   `IȘEFR2501`
-   `IAFR2503 R`
-   `IAFR2301`
-   `IAFR2302 R`

Grupele NU trebuie hardcodate în aplicație. Parserul trebuie să le
descopere din antet.

### Layout relevant

În structura observată: - coloana B conține ziua/data; - coloana C
conține intervalul orar; - coloanele D--J corespund grupelor; -
coloanele K--L repetă informații de timp/zi în partea dreaptă și nu
reprezintă grupe.

Nu presupune însă că literele coloanelor vor rămâne mereu identice.
Identifică dinamic coloanele grupelor folosind antetul.

### Date

Exemple: - `Luni, 21.09.2026` - `Marți, 22.09.2026` -
`Miercuri, 23.09.2026`

Ziua/data apare adesea doar pe primul rând al zilei din cauza celulelor
îmbinate. Parserul trebuie să propage data curentă către rândurile
următoare până la următoarea dată.

### Intervalele orare

Exemple reale: - `I\n15:00-16:30` - `II\n16:45-18:15` -
`III\n18:30-20:00` - `13:15-14:45` - pot exista spații suplimentare.

Prefixele `I`, `II`, `III` sunt indicatoare de pereche și nu fac parte
din oră.

Parserul trebuie să normalizeze whitespace-ul și să extragă orele cu o
expresie tolerantă, nu prin comparație exactă de string.

## 7. Celulele de activitate

Exemplu simplu:

``` text
Mat. discr graf. (prel),
A. Niculiță, 122/4
```

Exemplu cu două activități:

``` text
Analiza funct. (sem),
V. Popa, 419/4
Teoria prob. (sem),
V. Popa, 419/4
```

O singură celulă poate produce mai multe obiecte `ScheduleEntry`.

Tipurile observate includ: - `(prel)` - `(sem)` - `(lab)`

Nu presupune că fiecare câmp este mereu prezent. Dacă profesorul, sala
sau tipul nu pot fi determinate sigur, valoarea trebuie să fie `None`.
Nu inventa date.

## 8. Subgrupe

Unele grupe au una sau două subgrupe, iar unele celule pot conține
activități distincte marcate `I:` și `II:`.

Modelul trebuie să poată păstra această informație fără a pierde date.

Model recomandat:

``` python
@dataclass
class ScheduleEntry:
    group: str
    date: date
    start_time: time
    end_time: time
    subject: str
    activity_type: str | None = None
    teacher: str | None = None
    room: str | None = None
    subgroup: str | None = None
```

`subgroup` poate fi `None`, `"I"` sau `"II"` când această informație
este prezentă explicit.

În MVP utilizatorul selectează grupa, nu este obligatoriu să configureze
permanent subgrupa. Dacă în aceeași oră există activități diferite pe
subgrupe, botul trebuie să le afișeze clar pe ambele, etichetate.

## 9. Reguli parser

Parserul trebuie: 1. să inspecteze antetul și să descopere grupele; 2.
să ignore coloanele auxiliare care nu sunt grupe; 3. să gestioneze
celulele îmbinate și valorile goale; 4. să propage data pentru rândurile
aceleiași zile; 5. să normalizeze spațiile și newline-urile; 6. să
extragă `start_time` și `end_time`; 7. să separe mai multe activități
din aceeași celulă; 8. să recunoască marcajele de subgrupă; 9. să
extragă materia, tipul, profesorul și sala când sunt identificabile; 10.
să păstreze diacriticele românești; 11. să nu inventeze informații
lipsă; 12. să continue parsarea dacă o celulă este invalidă, logând
problema.

Nu construi parserul doar pentru exemplele de mai sus. El trebuie să fie
tolerant la variații rezonabile ale aceluiași format de orar.

## 10. Validare

Un `ScheduleEntry` valid trebuie să aibă cel puțin: - `group`; -
`date`; - `start_time`; - `end_time`; - `subject`.

Trebuie verificat:

``` text
start_time < end_time
```

O intrare invalidă nu trebuie să oprească întreg botul.

## 11. Arhitectură

Flux:

``` text
Google Sheet / XLSX
        ↓
ScheduleSource
        ↓
Downloader
        ↓
Parser
        ↓
list[ScheduleEntry]
        ↓
ScheduleService
        ↓
Telegram handlers
```

SQLite:

``` text
Telegram user → selected_group
```

Orarul nu trebuie copiat integral în SQLite. El rămâne în memorie/cache.

Responsabilitățile downloaderului, parserului, serviciului, bazei de
date și handlerelor Telegram trebuie separate.

## 12. Structură recomandată

``` text
university_schedule_bot/
├── AI_APP_SPECIFICATION.md
├── MASTER_PROMPT.md
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── bot/
│   ├── __init__.py
│   ├── handlers.py
│   ├── keyboards.py
│   └── messages.py
├── schedule/
│   ├── __init__.py
│   ├── models.py
│   ├── source.py
│   ├── parser.py
│   ├── service.py
│   └── cache.py
├── database/
│   ├── __init__.py
│   └── repository.py
├── utils/
│   ├── __init__.py
│   └── logging_config.py
├── tests/
│   ├── test_parser.py
│   ├── test_schedule_service.py
│   └── test_repository.py
└── main.py
```

Structura poate fi ajustată ușor dacă există un motiv tehnic clar, dar
păstrează separarea responsabilităților.

## 13. UX Telegram

### `/start`

Utilizator nou: 1. mesaj scurt de bun venit; 2. lista grupelor
detectate; 3. utilizatorul selectează grupa; 4. grupa este salvată în
SQLite; 5. apare meniul principal.

Utilizator existent: - nu cere din nou grupa; - afișează direct meniul
principal.

Meniu:

``` text
🕐 Acum
📅 Program azi
⚙️ Schimbă grupa
```

## 14. `🕐 Acum`

Folosește timezone:

``` text
Europe/Chisinau
```

Un curs este activ dacă:

``` text
current_time >= start_time
AND
current_time < end_time
```

Dacă există curs activ, afișează-l.

Dacă nu există, găsește prima activitate de azi cu:

``` text
start_time > current_time
```

Dacă nu mai există activități azi, afișează un mesaj prietenos.

Dacă sunt două activități simultane pentru subgrupe diferite,
afișează-le pe ambele cu eticheta subgrupei.

## 15. `📅 Program azi`

Afișează toate activitățile grupei pentru data curentă, în ordine
cronologică.

Pauzele se calculează din diferența dintre sfârșitul unei activități și
începutul următoarei. Pauzele nu se salvează ca `ScheduleEntry`.

Dacă există activități simultane pentru subgrupe, acestea trebuie
grupate/afișate lizibil.

## 16. `⚙️ Schimbă grupa`

Afișează din nou grupele detectate din orarul valid curent. La alegere,
actualizează grupa utilizatorului în SQLite.

## 17. SQLite

Stochează minimum:

``` text
telegram_user_id
selected_group
```

Operațiile necesare: - get selected group; - insert/update selected
group.

Nu crea un sistem de conturi.

## 18. Cache și refresh

Interval implicit:

``` text
72 ore
```

Regulă critică: - descarcă noua sursă; - parsează și validează; - numai
dacă rezultatul este valid înlocuiește cache-ul curent.

Dacă sursa este indisponibilă: - folosește ultimul cache valid; -
loghează eroarea.

Dacă nu există nici sursă disponibilă, nici cache valid: - botul nu
trebuie să crape; - afișează utilizatorului un mesaj prietenos.

Nu înlocui niciodată un cache valid cu un rezultat gol sau invalid.

## 19. Logging

Loghează: - pornirea aplicației; - refresh-ul orarului; - succes/eșec
download; - numărul de intrări valide; - erorile de parsare cu suficient
context pentru debugging; - fallback-ul la cache.

Nu loga tokenuri sau alte secrete.

## 20. Teste obligatorii

### Parser

Teste pentru: - detectarea grupelor; - data în celulă îmbinată /
propagarea datei; - normalizarea intervalelor; - activitate simplă; -
două activități în aceeași celulă; - subgrupele `I:` / `II:`; - câmpuri
lipsă; - celulă goală; - input invalid fără oprirea întregului parser.

Include cel puțin un test de integrare pe workbook-ul real sau pe un
fixture reprezentativ extras din el.

### ScheduleService

Teste pentru: - curs activ; - exact la început; - exact la sfârșit; -
următorul curs; - niciun curs rămas; - zi fără cursuri; - activități
simultane de subgrupe; - sortare cronologică; - calculul pauzelor.

### SQLite

Teste pentru: - utilizator nou; - salvare grupă; - actualizare grupă; -
citire grupă.

## 21. Principii de implementare

-   funcții mici și clare;
-   type hints;
-   fără funcții gigantice;
-   fără duplicare inutilă;
-   fără hardcodarea grupelor;
-   fără hardcodarea URL-ului;
-   fără hardcodarea timezone-ului în logica de business;
-   fără overengineering;
-   nu adăuga funcționalități care nu sunt cerute.

## 22. Acceptance Criteria

MVP este acceptat când: 1. proiectul pornește local; 2. tokenul și
URL-ul sunt citite din `.env`; 3. orarul poate fi descărcat/parsat; 4.
grupele sunt detectate automat; 5. utilizatorul poate selecta și schimba
grupa; 6. grupa este păstrată în SQLite; 7. `/start` recunoaște
utilizatorul existent; 8. `🕐 Acum` funcționează corect în
`Europe/Chisinau`; 9. `📅 Program azi` afișează corect programul; 10.
celulele cu mai multe activități nu pierd cursuri; 11. subgrupele nu
pierd informație; 12. indisponibilitatea sursei folosește ultimul cache
valid; 13. un refresh invalid nu distruge cache-ul valid; 14. erorile
sunt logate și nu opresc botul inutil; 15. testele importante trec; 16.
README explică instalarea și rularea.

## 23. Definition of Done

Proiectul este „done" când toate criteriile de acceptare sunt
îndeplinite și o persoană poate: 1. clona proiectul; 2. crea `.env`; 3.
instala dependențele; 4. porni botul; 5. selecta grupa; 6. apăsa un
buton și vedea orarul fără să deschidă Excelul.

Această specificație este sursa principală de adevăr pentru
implementare.
