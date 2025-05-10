import mido
import math
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import pyperclip
import os
import random
import string

def midi_note_to_freq(note):
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def midi_note_to_name(note):
    note_names = ['C', 'CS', 'D', 'DS', 'E', 'F', 'FS', 'G', 'GS', 'A', 'AS', 'B']
    octave = note // 12 - 1
    note_index = note % 12
    return f"NOTE_{note_names[note_index]}{octave}"

def duration_to_divider(duration_ticks, ticks_per_beat):
    possible_dividers = [4, 8, 16, 32]
    for divider in possible_dividers:
        expected_ticks = ticks_per_beat * 4 / divider
        if abs(duration_ticks - expected_ticks) < expected_ticks * 0.05:
            return divider
        dotted_ticks = expected_ticks * 1.5
        if abs(duration_ticks - dotted_ticks) < dotted_ticks * 0.05:
            return -divider
    return 8

def generate_arduino_code(midi_file_path, output_dir, output_file_name, max_code_length=69000,
                          inter_note_delay=50, max_notes=200, fixed_tempo_bpm=130,
                          polyphonic_mode=False):
    try:
        midi = mido.MidiFile(midi_file_path)
    except Exception as e:
        raise Exception(f"Error reading MIDI file: {e}")

    piezo_pins = {'small_passive': 9, 'large_passive': 10, 'large_active': 11}
    notes = []
    tempos = []
    ticks_per_beat = midi.ticks_per_beat
    default_tempo = 500000
    velocity_range = {'min': 127, 'max': 0}
    pin_usage = {9: 0, 10: 0, 11: 0}
    simultaneous_notes_count = 0

    for track in midi.tracks:
        current_time_ticks = 0
        for msg in track:
            current_time_ticks += msg.time
            if msg.type == 'set_tempo':
                tempos.append({'time_ticks': current_time_ticks, 'tempo': msg.tempo})
            elif msg.type == 'note_on' and msg.velocity > 0:
                note_duration_ticks = 0
                temp_time = current_time_ticks
                note_number = msg.note
                for next_msg in track:
                    temp_time += next_msg.time
                    if next_msg.type == 'note_off' and next_msg.note == note_number:
                        note_duration_ticks = temp_time - current_time_ticks
                        break

                velocity_range['min'] = min(velocity_range['min'], msg.velocity)
                velocity_range['max'] = max(velocity_range['max'], msg.velocity)

                if velocity_range['max'] - velocity_range['min'] < 10:
                    pin = piezo_pins['small_passive'] if note_number % 3 == 0 else piezo_pins['large_passive'] if note_number % 3 == 1 else piezo_pins['large_active']
                else:
                    pin = piezo_pins['small_passive'] if msg.velocity < 50 else piezo_pins['large_passive'] if msg.velocity < 90 else piezo_pins['large_active']

                if polyphonic_mode:
                    pin = piezo_pins['large_passive']

                freq = midi_note_to_freq(msg.note)
                notes.append({
                    'start_time_ticks': current_time_ticks,
                    'duration_ticks': note_duration_ticks,
                    'frequency': freq,
                    'pin': pin,
                    'velocity': msg.velocity,
                    'note_number': msg.note
                })
                pin_usage[pin] += 1

    if not tempos:
        tempos.append({'time_ticks': 0, 'tempo': default_tempo})

    print("Tempo events (BPM):", [60000000 / t['tempo'] for t in tempos])

    tempo_bpm = fixed_tempo_bpm if fixed_tempo_bpm else 60000000 / tempos[0]['tempo']
    for note in notes:
        start_time_ms = 0
        current_ticks = 0
        current_tempo = tempos[0]['tempo']
        for tempo_event in tempos:
            if tempo_event['time_ticks'] <= note['start_time_ticks']:
                ticks_in_segment = min(note['start_time_ticks'], tempo_event['time_ticks']) - current_ticks
                seconds_per_tick = current_tempo / 1000000.0 / ticks_per_beat
                start_time_ms += ticks_in_segment * seconds_per_tick * 1000
                current_ticks = tempo_event['time_ticks']
                current_tempo = tempo_event['tempo']
            else:
                break
        ticks_remaining = note['start_time_ticks'] - current_ticks
        seconds_per_tick = current_tempo / 1000000.0 / ticks_per_beat
        start_time_ms += ticks_remaining * seconds_per_tick * 1000
        note['start_time_ms'] = start_time_ms

    notes.sort(key=lambda x: x['start_time_ms'])

    final_notes = []
    i = 0
    while i < len(notes):
        current_time = notes[i]['start_time_ms']
        overlapping_notes = [notes[i]]
        j = i + 1
        while j < len(notes) and abs(notes[j]['start_time_ms'] - current_time) < 5:
            overlapping_notes.append(notes[j])
            j += 1

        if len(overlapping_notes) > 1:
            simultaneous_notes_count += 1

        if polyphonic_mode:
            selected_notes = [overlapping_notes[0]]
            selected_notes[0]['pin'] = piezo_pins['large_passive'] 
        else:
            overlapping_notes.sort(key=lambda x: x['velocity'], reverse=True)
            selected_notes = overlapping_notes[:2]
            available_pins = [9, 10, 11]
            for idx, note in enumerate(selected_notes):
                if idx == 0:
                    note['pin'] = note['pin'] if note['pin'] in available_pins else available_pins[0]
                    available_pins.remove(note['pin'])
                else:
                    note['pin'] = available_pins[0] if available_pins else note['pin']

        final_notes.extend(selected_notes)

        i = j

    final_notes = final_notes[:max_notes]

    note_definitions = [
        "#define NOTE_B0  31", "#define NOTE_C1  33", "#define NOTE_CS1 35", "#define NOTE_D1  37",
        "#define NOTE_DS1 39", "#define NOTE_E1  41", "#define NOTE_F1  44", "#define NOTE_FS1 46",
        "#define NOTE_G1  49", "#define NOTE_GS1 52", "#define NOTE_A1  55", "#define NOTE_AS1 58",
        "#define NOTE_B1  62", "#define NOTE_C2  65", "#define NOTE_CS2 69", "#define NOTE_D2  73",
        "#define NOTE_DS2 78", "#define NOTE_E2  82", "#define NOTE_F2  87", "#define NOTE_FS2 93",
        "#define NOTE_G2  98", "#define NOTE_GS2 104", "#define NOTE_A2  110", "#define NOTE_AS2 117",
        "#define NOTE_B2  123", "#define NOTE_C3  131", "#define NOTE_CS3 139", "#define NOTE_D3  147",
        "#define NOTE_DS3 156", "#define NOTE_E3  165", "#define NOTE_F3  175", "#define NOTE_FS3 185",
        "#define NOTE_G3  196", "#define NOTE_GS3 208", "#define NOTE_A3  220", "#define NOTE_AS3 233",
        "#define NOTE_B3  247", "#define NOTE_C4  262", "#define NOTE_CS4 277", "#define NOTE_D4  294",
        "#define NOTE_DS4 311", "#define NOTE_E4  330", "#define NOTE_F4  349", "#define NOTE_FS4 370",
        "#define NOTE_G4  392", "#define NOTE_GS4 415", "#define NOTE_A4  440", "#define NOTE_AS4 466",
        "#define NOTE_B4  494", "#define NOTE_C5  523", "#define NOTE_CS5 554", "#define NOTE_D5  587",
        "#define NOTE_DS5 622", "#define NOTE_E5  659", "#define NOTE_F5  698", "#define NOTE_FS5 740",
        "#define NOTE_G5  784", "#define NOTE_GS5 831", "#define NOTE_A5  880", "#define NOTE_AS5 932",
        "#define NOTE_B5  988", "#define NOTE_C6  1047", "#define NOTE_CS6 1109", "#define NOTE_D6  1175",
        "#define NOTE_DS6 1245", "#define NOTE_E6  1319", "#define NOTE_F6  1397", "#define NOTE_FS6 1480",
        "#define NOTE_G6  1568", "#define NOTE_GS6 1661", "#define NOTE_A6  1760", "#define NOTE_AS6 1865",
        "#define NOTE_B6  1976", "#define NOTE_C7  2093", "#define NOTE_CS7 2217", "#define NOTE_D7  2349",
        "#define NOTE_DS7 2489", "#define NOTE_E7  2637", "#define NOTE_F7  2794", "#define NOTE_FS7 2960",
        "#define NOTE_G7  3136", "#define NOTE_GS7 3322", "#define NOTE_A7  3520", "#define NOTE_AS7 3729",
        "#define NOTE_B7  3951", "#define NOTE_C8  4186", "#define NOTE_CS8 4435", "#define NOTE_D8  4699",
        "#define NOTE_DS8 4978", "#define REST 0"
    ]

    arduino_code = [
        "// Arduino code generated from MIDI file",
        f"// Generated by midi_to_arduino.py on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    arduino_code.extend(note_definitions)
    arduino_code.extend([
        "",
        f"int tempo = {int(tempo_bpm)};",
        "",
        "const int pinSmallPassive = 9;",
        "const int pinLargePassive = 10;",
        "const int pinLargeActive = 11;",
        "",
        "int melody[] = {"
    ])

    pins_array = ["int pins[] = {"]
    current_code_length = len("\n".join(arduino_code))
    max_code_length -= 1000
    notes_truncated = False

    melody_entries = []
    pin_entries = []
    note_count = 0
    i = 0
    while i < len(final_notes):
        note = final_notes[i]
        duration_ticks = note['duration_ticks']
        freq = note['frequency']
        pin = note['pin']
        note_number = note['note_number']

        divider = duration_to_divider(duration_ticks, ticks_per_beat)

        if not (31 <= freq <= 4978):
            i += 1
            continue

        note_name = midi_note_to_name(note_number)
        melody_entries.append(f"  {note_name},{divider}, // {note_count + 1}")
        pin_entries.append(f"  {pin},")
        note_count += 1

        temp_code = "\n".join(arduino_code + melody_entries + ["};"] + pins_array + pin_entries + ["};"])
        if len(temp_code) > max_code_length or note_count >= max_notes:
            notes_truncated = True
            break

        i += 1

    arduino_code.extend(melody_entries)
    arduino_code.append("};")
    pins_array.extend(pin_entries)
    pins_array.append("};")

    arduino_code.extend([
        "",
    ])
    arduino_code.extend(pins_array)
    arduino_code.extend([
        "",
        f"int notes = sizeof(melody) / sizeof(melody[0]) / 2;",
        "",
        f"int wholenote = (60000 * 4) / tempo;",
        "",
        "void setup() {",
        "  pinMode(pinSmallPassive, OUTPUT);",
        "  pinMode(pinLargePassive, OUTPUT);",
        "  pinMode(pinLargeActive, OUTPUT);",
        "",
        "  for (int i = 0; i < notes * 2; i += 2) {",
        "    int divider1 = melody[i + 1];",
        "    int noteDuration1;",
        "    if (divider1 > 0) {",
        "      noteDuration1 = wholenote / divider1;",
        "    } else {",
        "      noteDuration1 = wholenote / abs(divider1);",
        "      noteDuration1 *= 1.5;",
        "    }",
        "    int note1 = melody[i];",
        "    int pin1 = pins[i / 2];",
        "",
        "    int note2 = REST;",
        "    int noteDuration2 = 0;",
        "    int pin2 = 0;",
        "    if (i + 2 < notes * 2) {",
        "      int nextStartTime = i + 2 < notes * 2 ? melody[i + 2] : 0;",
        "      if (i + 2 < notes * 2 && abs(melody[i + 2] - melody[i]) < 5) {",
        "        int divider2 = melody[i + 3];",
        "        if (divider2 > 0) {",
        "          noteDuration2 = wholenote / divider2;",
        "        } else {",
        "          noteDuration2 = wholenote / abs(divider2);",
        "          noteDuration2 *= 1.5;",
        "        }",
        "        note2 = melody[i + 2];",
        "        pin2 = pins[(i + 2) / 2];",
        "        if (pin2 == pin1) {",
        "          pin2 = (pin1 == 9 ? 10 : pin1 == 10 ? 11 : 9);",
        "        }",
        "        i += 2;",
        "      }",
        "    }",
        "",
        "    if (note1 != REST) {",
        "      tone(pin1, note1, noteDuration1 * 0.9);",
        "    }",
        "    if (note2 != REST) {",
        "      tone(pin2, note2, noteDuration2 * 0.9);",
        "    }",
        "",
        "    int minDuration = noteDuration2 > 0 ? min(noteDuration1, noteDuration2) : noteDuration1;",
        f"    delay(minDuration + {inter_note_delay});",
        "    noTone(pin1);",
        "    if (note2 != REST) noTone(pin2);",
        "  }",
        "}",
        "",
        "void loop() {",
        "  // No repeat",
        "}"
    ])

    if notes_truncated:
        arduino_code.insert(-4, "  // Note: Melody truncated due to memory or code size limit")
        print("Warning: Melody was truncated to fit within memory or 69000 character limit.")

    print("Velocity range:", velocity_range)
    print("Pin usage statistics:")
    print(f"Pin 9 (small passive): {pin_usage[9]} notes")
    print(f"Pin 10 (large passive): {pin_usage[10]} notes")
    print(f"Pin 11 (large active): {pin_usage[11]} notes")
    print(f"Total notes in melody: {note_count}")
    print(f"Tempo (BPM): {tempo_bpm}")
    print(f"Simultaneous note groups: {simultaneous_notes_count}")

    arduino_code_str = "\n".join(arduino_code)
    return arduino_code_str

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    midi_file_path = filedialog.askopenfilename(title="Select MIDI File", filetypes=[("MIDI Files", "*.mid")])
    if not midi_file_path:
        messagebox.showerror("Error", "No MIDI file selected. Exiting.")
        exit()

    polyphonic_mode = messagebox.askyesno("Polyphonic Mode", "Enable polyphonic mode (10 pin only)?")

    fixed_tempo_bpm = 130

    try:
        random_sketch_name = 'sketch_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        output_dir = os.path.join(os.getcwd(), random_sketch_name)
        os.makedirs(output_dir, exist_ok=True)
        output_file_name = os.path.join(output_dir, f"{random_sketch_name}.ino")

        arduino_code = generate_arduino_code(midi_file_path, output_dir, output_file_name, fixed_tempo_bpm=fixed_tempo_bpm,
                                              polyphonic_mode=polyphonic_mode)
        print("Arduino code generated successfully!")
        print(f"Code length: {len(arduino_code)} characters")

        copy_to_clipboard = messagebox.askyesno("Copy to Clipboard", "Copy code to clipboard?")
        if copy_to_clipboard:
            pyperclip.copy(arduino_code)
            messagebox.showinfo("Copied!", "Code copied to clipboard!")
        open_file = messagebox.askyesno("Open File", "Open the generated file?")
        if open_file:
            if os.name == 'nt':
                os.system(f"start {output_file_name}")
            else:
                os.system(f"open {output_file_name}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

    root.destroy()
