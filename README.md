This code converts the selected midi file into a fully working code for arduino at once, unfortunately I did not test it on boards other than Uno, so you can do it.
# MIDI to Arduino Piezo Sound Converter

## English

### Overview
This tool converts MIDI files into Arduino code for playing melodies on piezo buzzers. It allows you to transform your favorite music into code that can be directly uploaded to an Arduino board to play through piezo speakers.

### Features
- Converts MIDI files to Arduino-compatible code
- Supports multiple piezo speakers (up to 3 pins)
- Optional polyphonic mode
- Automatic tempo detection and adjustment
- Note duration calculation

### Requirements
- Python 3.x
- Required libraries: mido, tkinter, pyperclip
- Arduino board with piezo buzzers connected to pins 9, 10, and 11

### Installation
1. Clone this repository
2. Install required dependencies:
   ```
   pip install mido pyperclip
   ```

### Usage
1. Run the script:
   ```
   python midi_to_arduino.py
   ```
2. Select a MIDI file through the file dialog
3. Choose whether to enable polyphonic mode
4. The script will generate Arduino code and offer to:
   - Copy the code to clipboard
   - Open the generated file

### Hardware Setup
Connect piezo buzzers to your Arduino:
- Small passive buzzer: Pin 9
- Large passive buzzer: Pin 10
- Large active buzzer: Pin 11

### Code Customization
You can modify these parameters in the script:
- `max_code_length`: Maximum character count for Arduino code (default: 69000)
- `inter_note_delay`: Delay between notes in milliseconds (default: 50)
- `max_notes`: Maximum number of notes to process (default: 200)
- `fixed_tempo_bpm`: Override MIDI tempo with fixed BPM (default: 130)

---

## Русский

### Обзор
Этот инструмент преобразует MIDI-файлы в код Arduino для воспроизведения мелодий на пьезоизлучателях. Он позволяет превратить вашу любимую музыку в код, который можно загрузить на плату Arduino для воспроизведения через пьезодинамики.

### Возможности
- Преобразование MIDI-файлов в код, совместимый с Arduino
- Поддержка нескольких пьезоизлучателей (до 3 пинов)
- Опциональный полифонический режим
- Автоматическое определение и регулировка темпа
- Расчет длительности нот

### Требования
- Python 3.x
- Необходимые библиотеки: mido, tkinter, pyperclip
- Плата Arduino с пьезоизлучателями, подключенными к пинам 9, 10 и 11

### Установка
1. Клонируйте этот репозиторий
2. Установите необходимые зависимости:
   ```
   pip install mido pyperclip
   ```

### Использование
1. Запустите скрипт:
   ```
   python midi_to_arduino.py
   ```
2. Выберите MIDI-файл через диалоговое окно
3. Выберите, включать ли полифонический режим
4. Скрипт сгенерирует код Arduino и предложит:
   - Скопировать код в буфер обмена
   - Открыть сгенерированный файл

### Настройка оборудования
Подключите пьезоизлучатели к Arduino:
- Малый пассивный излучатель: Пин 9
- Большой пассивный излучатель: Пин 10
- Большой активный излучатель: Пин 11

### Настройка кода
Вы можете изменить следующие параметры в скрипте:
- `max_code_length`: Максимальное количество символов для кода Arduino (по умолчанию: 69000)
- `inter_note_delay`: Задержка между нотами в миллисекундах (по умолчанию: 50)
- `max_notes`: Максимальное количество обрабатываемых нот (по умолчанию: 200)
- `fixed_tempo_bpm`: Переопределение темпа MIDI фиксированным значением BPM (по умолчанию: 130)
