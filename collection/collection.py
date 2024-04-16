import sqlite3
from creating_chord_collection.collection.chord import GuitarChord
from creating_chord_collection.collection.resources.transposable_figures import transposable_figures

class ChordCollection:
    def __init__(self):
        self.chords = []

    def load(self, db_path):
        self.chords.clear()
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        cursor.execute('SELECT ROOT, TYPE, STARTING_FRET, STRING_1, STRING_2, STRING_3, STRING_4, STRING_5, STRING_6 FROM TABLE_CHORDS')
        rows = cursor.fetchall()

        for row in rows:
            root, chord_type, starting_fret, *fingers = row
            chord = GuitarChord(root, chord_type, transposable_figures, finger_ascending=fingers, starting_fret=starting_fret)
            self.chords.append(chord)

        connection.close()

    def save(self, db_name):
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()

        # Create the table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TABLE_CHORDS (
                ID INTEGER PRIMARY KEY,
                ROOT TEXT,
                TYPE TEXT,
                STARTING_FRET INTEGER,
                STRING_1 INTEGER,
                STRING_2 INTEGER,
                STRING_3 INTEGER,
                STRING_4 INTEGER,
                STRING_5 INTEGER,
                STRING_6 INTEGER
            )
        ''')

        # Insert the chords
        for chord in self.chords:
            cursor.execute('''
                INSERT INTO TABLE_CHORDS (ROOT, TYPE, STARTING_FRET, STRING_1, STRING_2, STRING_3, STRING_4, STRING_5, STRING_6)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (chord.root, chord.chord_type, chord.starting_fret, *chord.finger_ascending))

        connection.commit()
        connection.close()

    def chord_exists(self, new_chord):
        for chord in self.chords:
            if chord.root == new_chord.root and chord.chord_type == new_chord.chord_type and chord.starting_fret == new_chord.starting_fret and chord.finger_ascending == new_chord.finger_ascending:
                return True
        return False

    def extend_barre_chords(self):
        original_chords = self.chords.copy()
        for chord in original_chords:
            counter = 1
            while True:
                try:
                    new_chord = GuitarChord(chord.root, chord.chord_type, chord.transposable_figures, finger_ascending=chord.finger_ascending.copy(), starting_fret=chord.starting_fret)
                    new_chord.transpose(counter)
                    if not self.chord_exists(new_chord):
                        self.chords.append(new_chord)
                    counter += 1
                except ValueError:
                    break

    def only(self, whitelist):
        # Define the helper functions for each filter criterion
        def filter_root(chord, values):
            return chord.root in values

        def filter_chord_type(chord, values):
            return chord.chord_type in values

        def filter_open(chord, values):
            return chord.is_open() in values

        def filter_starting_fret(chord, values):
            return chord.starting_fret in values

        def filter_include_string(chord, values):
            # Check if all strings in values are included (i.e., not None in finger_ascending)
            return all(chord.finger_ascending[string - 1] is not None for string in values)

        def filter_inversion(chord, values):
            notes = chord.get_notes(include_strings=False)

            # Determine the inversion based on the position of the root note
            if chord.root in notes:
                root_position = notes.index(chord.root)
                if root_position == 0:  # Root is the first note
                    inversion = 1
                elif root_position == 1:  # Root is the second note
                    inversion = 2
                else:  # Root is in any other position
                    inversion = 3
            else:
                inversion = None

            return inversion in values

        def filter_scale(chord, scales):
            for tonic, scale in scales:
                if chord.validate_against_scale(tonic, scale):
                    return True
            return False

        # Map each whitelist key to its corresponding filter function
        filter_functions = {
            "root": filter_root,
            "chord_type": filter_chord_type,
            "open": filter_open,
            "starting_fret": filter_starting_fret,
            "include_string": filter_include_string,
            "inversion": filter_inversion,
            "scale": filter_scale  # New entry for scale
        }

        # Filter the chords
        filtered_chords = []
        for chord in self.chords:
            if all(filter_functions[key](chord, values) for key, values in whitelist.items()):
                filtered_chords.append(chord)

        return filtered_chords

    def filter_out(self, blacklist):
        # Get chords that match the blacklist criteria
        matching_chords = self.only(blacklist)

        # Subtract matching chords from the original list
        remaining_chords = [chord for chord in self.chords if chord not in matching_chords]

        return remaining_chords


    def get_tonality(self, root, scale, amplitude=4, rank=1):
        # Helper function to calculate harmonic sum
        def harmonic_sum(n):
            return sum(1 / i for i in range(1, n + 1))

        # Modified helper function to find optimal fret segment
        def find_optimal_fret_segment(guitar, amplitude, rank):
            density_list = []
            for start_fret in range(len(guitar) - amplitude + 1):
                fret_segment = guitar[start_fret:start_fret + amplitude]
                note_counts = {}
                for fret in fret_segment:
                    for note, count in fret.items():
                        note_counts[note] = note_counts.get(note, 0) + count
                density = 1
                for count in note_counts.values():
                    density *= harmonic_sum(count)
                density_list.append((density, start_fret))

            # Sort by density and select the segment of the desired rank
            density_list.sort(key=lambda x: x[0], reverse=True)
            if rank <= len(density_list):
                return density_list[rank - 1][1]
            else:
                return -1  # In case the rank is higher than the number of segments

        # Helper function to group chords by starting fret and root, considering only barre chords
        def group_chords_by_starting_fret_and_root(chord_list):
            guitar = [{} for _ in range(12)]  # Assuming a 12-fret guitar
            for chord in chord_list:
                if not chord.is_open():
                    fret = chord.starting_fret
                    if fret > 0 and fret <= 12:
                        guitar[fret - 1][chord.root] = guitar[fret - 1].get(chord.root, 0) + 1
            return guitar

        # Filtering chords based on root and scale
        filtered_chords = self.only({"root": [root], "scale": [(root, scale)]})
        guitar = group_chords_by_starting_fret_and_root(filtered_chords)

        # Finding the optimal fret segment based on the rank
        optimal_start_fret = find_optimal_fret_segment(guitar, amplitude, rank)

        # Determine the frets with the most density of chords
        selected_frets = list(range(optimal_start_fret + 1, optimal_start_fret + amplitude + 1))

        # Get chords of the tonality that are near each other and well distributed
        tonality_chords = self.only({"scale": [(root, scale)], "starting_fret": selected_frets, "open": [False]})
        return tonality_chords



