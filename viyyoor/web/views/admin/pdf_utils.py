import io

import cairocffi
from cairosvg.parser import Tree
from cairosvg.surface import PDFSurface

from viyyoor import models

from . import certificate_utils


class RecordingPDFSurface(PDFSurface):
    surface_class = cairocffi.RecordingSurface

    def _create_surface(self, width, height):
        cairo_surface = cairocffi.RecordingSurface(
            cairocffi.CONTENT_COLOR_ALPHA, (0, 0, width, height)
        )
        return cairo_surface, width, height


def generate_certificates(
    class_,
    required_signature=True,
    dpi=300,
    validated_url_template="http://localhost/certificates/{certificate_id}",
):

    output = io.BytesIO()
    surface = cairocffi.PDFSurface(output, 1, 1)
    context = cairocffi.Context(surface)

    for key, participant in class_.participants.items():
        certificate = models.Certificate.objects(
            class_=class_, participant_id=participant.id
        ).first()

        if not certificate:
            continue

        bytestring = certificate_utils.render_certificate(
            class_, participant.id, "svg", required_signature, validated_url_template
        )

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


def export_certificates(
    class_,
    required_signature=True,
    dpi=300,
    filename="",
    validated_url_template="http://localhost/certificates/{certificate_id}",
):
    output = generate_certificates(
        class_, required_signature, dpi, validated_url_template
    )

    if not filename:
        return output

    with open(filename, "wb") as f:
        f.write(output.read())
