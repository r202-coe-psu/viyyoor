import io

import cairocffi
from cairosvg.parser import Tree
from cairosvg.surface import PDFSurface

from viyyoor import models


class RecordingPDFSurface(PDFSurface):
    surface_class = cairocffi.RecordingSurface

    def _create_surface(self, width, height):
        cairo_surface = cairocffi.RecordingSurface(
            cairocffi.CONTENT_COLOR_ALPHA, (0, 0, width, height)
        )
        return cairo_surface, width, height


def export_certificates(class_, dpi=72):

    output = io.BytesIO()
    surface = cairocffi.PDFSurface(output, 1, 1)
    context = cairocffi.Context(surface)

    for participant in class_.participants:
        certificate = models.Certificate.objects(
            class_=class_, participant_id=participant.participant_id
        ).first()

        if not certificate:
            continue

        bytestring = class_.render_certificate(participant.participant_id, "svg")

        image_surface = RecordingPDFSurface(
            Tree(bytestring=bytestring.read()), None, dpi
        )
        surface.set_size(image_surface.width, image_surface.height)
        context.set_source_surface(image_surface.cairo, 0, 0)
        context.paint()
        surface.show_page()
    surface.finish()

    output.seek(0)
    return output
