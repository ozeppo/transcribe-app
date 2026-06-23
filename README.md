# WhisperAI - Generator napisów SRT

WhisperAI to aplikacja na system MacOS (Nie testowałem z Windowsem) do konwersji plików audio i wideo na napisy `.srt` przy użyciu modelu [OpenAI Whisper](https://github.com/openai/whisper). Aplikacja ma prosty interfejs graficzny, obsługuje wiele formatów plików i pozwala wygodnie ustawić sposób dzielenia napisów.

Powstała właściwie z bardzo praktycznej potrzeby: funkcja transkrypcji w Adobe Premiere Pro naprawdę ułatwia życie przy montażu, ale brak obsługi języka polskiego bywa niesamowicie problematyczny.

## Świetna obsługa języka polskiego

WhisperAI bardzo dobrze sprawdza się z nagraniami w języku polskim. Możesz ustawić język na `pl`, aby wymusić transkrypcję po polsku, albo zostawić tryb `auto`, jeśli aplikacja ma sama wykryć język nagrania. To szczególnie przydatne przy podcastach, wywiadach, materiałach YouTube, kursach, spotkaniach i nagraniach z polską mową.

## Funkcje

- **Audio i wideo**: obsługa MP3, WAV, M4A, MP4, AVI, MOV, MKV, FLAC, OGG i innych formatów.
- **Modele Whisper**: wybór modeli `tiny`, `base`, `small`, `medium` albo `large`.
- **Wiele języków**: automatyczne wykrywanie języka albo ręczny wybór, w tym `pl`.
- **Formatowanie napisów SRT**:
  - maksymalna liczba linii w jednym napisie,
  - maksymalna szerokość linii w znakach,
  - maksymalna liczba słów w jednym napisie.
- **Znaczniki czasu dla słów**: precyzyjne dzielenie napisów na podstawie czasów pojedynczych słów.
- **Wygodny zapis**: wybór katalogu, w którym zostanie zapisany plik `.srt`.

## Wymagania

### System

- **macOS** 10.13+
- **Python** 3.9 lub nowszy
- **ffmpeg**, wymagany do przetwarzania audio i wideo

### Instalacja ffmpeg

#### macOS przez Homebrew

```bash
brew install ffmpeg
```

#### Linux, Ubuntu/Debian

```bash
sudo apt-get install ffmpeg
```

#### Windows

Pobierz ffmpeg z [ffmpeg.org](https://ffmpeg.org/download.html)

## Instalacja

1. Sklonuj repozytorium:

```bash
git clone https://github.com/filipchmielecki/WhisperAI.git
cd WhisperAI
```

2. Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

3. Uruchom aplikację:

```bash
python3 main.py
```

Na macOS możesz też użyć gotowej aplikacji, dostępnej w zakładce releases

## Jak używać

1. Kliknij **Wybierz plik** i wybierz plik audio albo wideo.
2. Kliknij **Wybierz folder** i wybierz katalog zapisu napisów.
3. Ustaw model Whispera, urządzenie oraz język.
4. Dla polskich nagrań wybierz `pl` albo zostaw `auto`.
5. Opcjonalnie dostosuj format napisów:
   - liczbę linii w jednym napisie,
   - szerokość linii,
   - liczbę słów w jednym napisie.
6. Kliknij **Generuj SRT**.
7. Gotowy plik `.srt` znajdziesz w wybranym katalogu.

## Domyślna konfiguracja

- **Model**: `medium`
- **Urządzenie**: `cpu`
- **Język**: `auto`
- **Maksymalna liczba linii**: 1
- **Maksymalna szerokość linii**: 25 znaków
- **Maksymalna liczba słów na napis**: 3

Model `medium` jest dobrym kompromisem między jakością a czasem przetwarzania. Dla języka polskiego zwykle daje bardzo dobre wyniki.

## Budowanie aplikacji `.app` na macOS

Aby utworzyć paczkę aplikacji:

```bash
bash build_macos.sh
```

Gotowa aplikacja pojawi się w katalogu:

```text
dist/WhisperAI.app
```

Możesz uruchomić ją lokalnie albo skopiować do katalogu `Applications`.

## Obsługiwane formaty

### Audio

- MP3, WAV, M4A, FLAC, OGG, WMA, AAC

### Wideo

- MP4, MKV, AVI, MOV, WMV, FLV, WebM

## Wskazówki wydajności

- `tiny`: najszybszy, ale najmniej dokładny.
- `base`: szybki i lekki.
- `small`: lepsza dokładność.
- `medium`: zalecany kompromis jakości i szybkości.
- `large`: najwyższa jakość, ale najwolniejsze przetwarzanie.

Pierwsze uruchomienie wybranego modelu może potrwać dłużej, bo aplikacja musi pobrać pliki modelu. Rozmiar zależy od wybranego wariantu.

## Rozwiązywanie problemów

### Brak `ffmpeg`

Zainstaluj `ffmpeg` zgodnie z instrukcją dla swojego systemu.

### Aplikacja długo przetwarza plik

To normalne przy dłuższych nagraniach albo większych modelach. Modele `tiny`, `base` i `small` działają szybciej, a `medium` i `large` dają zwykle lepszą dokładność.

### Model nie chce się pobrać

Sprawdź połączenie z internetem. Modele Whispera są pobierane przy pierwszym użyciu.

### GUI nie pojawia się na macOS

Spróbuj uruchomić aplikację z terminala:

```bash
python3 main.py
```

## Licencja

Projekt jest udostępniany na licencji GNU.

Model Whisper jest udostępniany przez OpenAI również na licencji MIT.

## Podziękowania

- [OpenAI Whisper](https://github.com/openai/whisper) - model rozpoznawania mowy.
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - framework GUI.
- [ffmpeg](https://ffmpeg.org/) - przetwarzanie audio i wideo.
