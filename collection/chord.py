
class GuitarChord:
    all_notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    open_string_notes = ["E", "B", "G", "D", "A", "E"]

    def __init__(self, root, chord_type, transposable_figures, *, starting_fret=0, finger_ascending):
        self.root = root
        self.chord_type = chord_type
        self.starting_fret = starting_fret
        self.finger_ascending = finger_ascending
        self.transposable_figures = transposable_figures

    def __str__(self):
        return f"({repr(self.root)}, {repr(self.chord_type)}, finger_ascending={self.finger_ascending}, starting_fret={self.starting_fret})"

    def calculate_frequencies(self):
        frequencies = {}
        base_frequencies = {
            "E": [329.63, 82.41],  # 1st and 6th strings
            "B": [246.94],         # 2nd string
            "G": [196],            # 3rd string
            "D": [146.83],         # 4th string
            "A": [110]             # 5th string
        }

        def calculate_frequency(open_note, string_number, fret_position):
            base_frequency = base_frequencies[open_note][0] if string_number != 6 else base_frequencies[open_note][1]
            return base_frequency * (2 ** (fret_position / 12))

        for string_number, (open_note, finger_position) in enumerate(zip(GuitarChord.open_string_notes, self.finger_ascending), start=1):
            if finger_position is None:
                continue

            fret_position = self.starting_fret + finger_position - 1 if finger_position > 0 else 0
            frequency = calculate_frequency(open_note, string_number, fret_position)
            frequencies[string_number] = frequency

        return frequencies


    def get_notes(self, include_strings=False):
        def calculate_note(string, fret):
            if fret is None:
                return None
            if fret == 0:  # For open strings, return the default open string note
                return string
            # Calculate the note for fretted strings
            note_index = (GuitarChord.all_notes.index(string) + self.starting_fret + fret - 1) % len(GuitarChord.all_notes)
            return GuitarChord.all_notes[note_index]

        if include_strings:
            notes = {}
            for string_number, (string, fret) in enumerate(zip(GuitarChord.open_string_notes, self.finger_ascending), start=1):
                note = calculate_note(string, fret)
                notes[string_number] = note
            return notes
        else:
            frequencies = self.calculate_frequencies()
            notes = [calculate_note(string, fret) for string, fret in zip(GuitarChord.open_string_notes, self.finger_ascending) if fret is not None]
            unique_notes = list(dict.fromkeys(notes))  # Remove duplicates

            # Correctly map notes to string numbers for sorting
            note_to_string = {}
            for idx, (string, fret) in enumerate(zip(GuitarChord.open_string_notes, self.finger_ascending), start=1):
                if fret is not None:
                    note = calculate_note(string, fret)
                    note_to_string[note] = idx

            # Sort notes based on frequencies
            return sorted(unique_notes, key=lambda note: frequencies.get(note_to_string.get(note), float('inf')))



    def is_open(self):
        return 0 in self.finger_ascending

    def transpose(self, distance):
        # Helper function to transpose figure
        def transpose_figure(lst, num):
            return [item + num if item is not None else None for item in lst]

        # Helper function to raise specific errors after reverting changes
        def raise_transpose_error(error_type):
            self.root = original_root
            self.finger_ascending = original_finger_ascending
            self.starting_fret = original_starting_fret

            error_messages = {
                "below_0": "Chord transposition results in a note below the 0th fret.",
                "above_12": "Chord transposition results in a note above the 12th fret.",
                "not_equivalent_transposable_figure": "Chord figure is not equivalent to any figure in transposable_figures."
            }
            raise ValueError(error_messages[error_type])

        # Save original state for possible reversion
        original_root = self.root
        original_finger_ascending = self.finger_ascending.copy()
        original_starting_fret = self.starting_fret

        # Return if distance is zero
        if distance == 0:
            return

        # Update root note
        new_note_index = (GuitarChord.all_notes.index(self.root) + distance) % len(GuitarChord.all_notes)
        self.root = GuitarChord.all_notes[new_note_index]

        # Transpose open chords
        if self.is_open():
            if distance < 0:
                raise_transpose_error("below_0")
            elif distance > 0:
                self.finger_ascending = transpose_figure(self.finger_ascending, 1)
                self.starting_fret = max(0, self.starting_fret + distance - 1)
        else:  # Transpose barre chords
            if distance < 0:
                new_starting_fret = self.starting_fret + distance
                if new_starting_fret < 0:
                    raise_transpose_error("below_0")
                elif new_starting_fret == 0:
                    self.finger_ascending = transpose_figure(self.finger_ascending, -1)
                    self.starting_fret = 1  # Keeping the fret at 1
                else:
                    self.starting_fret = new_starting_fret
            else:  # Transpose barre chord to the right
                self.starting_fret += distance

        # Check for errors in transposition
        if any(fret < 0 for fret in self.finger_ascending if fret is not None):
            raise_transpose_error("below_0")
        if self.starting_fret > 9:
            raise_transpose_error("above_12")

        # Check transposability
        transposed_figure = self.finger_ascending if self.starting_fret == 0 else transpose_figure(self.finger_ascending, 1)
        if transposed_figure not in self.transposable_figures:
            raise_transpose_error("not_equivalent_transposable_figure")

    def validate_against_scale(self, tonic, scale):
        # Reorder the all_notes list starting from the tonic
        tonic_index = GuitarChord.all_notes.index(tonic)
        reordered_notes = GuitarChord.all_notes[tonic_index:] + GuitarChord.all_notes[:tonic_index]

        # Extract the notes of the scale using the provided scale pattern
        scale_notes = [reordered_notes[i] for i in scale]

        # Get the notes of the chord
        chord_notes = self.get_notes()

        # Check if all chord notes are in the scale
        return all(note in scale_notes for note in chord_notes)


