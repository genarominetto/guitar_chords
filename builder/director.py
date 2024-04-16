from creating_chord_collection.collection.resources.scales import scales
from PIL import Image

class Director:
    def __init__(self, builder):
        self._builder = builder
        self._current_image = None
        self._composite_image = None
        self._current_row_images = []
        self._all_rows = []

    def _build_diagram(self, root, starting_fret, finger_ascending=None, scale=None, name=None):
        self._builder.draw_boundaries()
        self._builder.root = root
        self._builder.starting_fret = starting_fret
        self._builder.finger_ascending = finger_ascending
        self._builder.scale = scale
        self._builder.write_starting_fret()
        self._builder.draw_frets()
        self._builder.draw_strings()
        self._builder.draw_notes()
        self._builder.write_name(name)

    def build_chord(self, chord):
        chord_name = f"{chord.root}{chord.chord_type}"
        self._build_diagram(chord.root, chord.starting_fret, finger_ascending=chord.finger_ascending, name=chord_name)
        self._save_image()  # Changed from _save_current_image to _save_image

    def build_scale(self, root, scale, starting_fret=1):
        self._builder.name_coordenate = (self._builder.name_coordenate[0] - 45, self._builder.name_coordenate[1])
        scale_name = None
        for key, value in scales.items():
            if value == scale:
                scale_name = f'{root} {key}'
                break
        if not scale_name:
            scale_name = root
        self._build_diagram(root, starting_fret, scale=scale, name=scale_name)
        self._save_image()

    def _save_image(self):
        self._current_image = self._builder.get_result()
        self._current_row_images.append(self._current_image)

    def _concatenate_images(self, images, direction='horizontal'):
        """
        Concatenate a list of images in the specified direction.
        """
        widths, heights = zip(*(i.size for i in images))

        if direction == 'horizontal':
            total_width = sum(widths)
            max_height = max(heights)
            combined_image = Image.new('RGB', (total_width, max_height), 'white')  # white background
            x_offset = 0
            for im in images:
                combined_image.paste(im, (x_offset, 0))
                x_offset += im.width
        else:  # vertical concatenation
            total_height = sum(heights)
            max_width = max(widths)
            combined_image = Image.new('RGB', (max_width, total_height), 'white')  # white background
            y_offset = 0
            for im in images:
                combined_image.paste(im, (0, y_offset))
                y_offset += im.height
        return combined_image

    def build_multiple_chords(self, chords, columns=4):
        """
        Build and concatenate multiple chord images.
        """
        self._current_row_images = []  # Resetting the current row images
        self._all_rows = []            # Resetting all rows

        for chord in chords:
            self.build_chord(chord)
            if len(self._current_row_images) == columns:
                self._all_rows.append(self._concatenate_images(self._current_row_images, 'horizontal'))
                self._current_row_images = []

        # Handle remaining chords
        if self._current_row_images:
            self._all_rows.append(self._concatenate_images(self._current_row_images, 'horizontal'))

        if self._all_rows:
            self._composite_image = self._concatenate_images(self._all_rows, 'vertical')
        else:
            print("No chords were processed to create an image.")

    def save_image(self, file_path):
        image_to_save = self._composite_image if self._composite_image else self._current_image
        if image_to_save:
            image_to_save.save(file_path)
        else:
            print("No image to save.")

    def display_image(self):
        image_to_display = self._composite_image if self._composite_image else self._current_image
        if image_to_display:
            display(image_to_display)
        else:
            print("No image to display.")

