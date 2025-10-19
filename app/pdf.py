from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pikepdf
from PIL import Image
from pyhanko.sign import fields as sig_fields
from pyhanko.sign.general import Signer
from pyhanko.sign.signers import SimpleSigner
from reportlab.pdfgen import canvas

from .models import Field, Signature


@dataclass
class SignatureLayer:
    signature: Signature
    image: Image.Image | None
    stamp_path: Path | None


def _render_signature_layer(layer: SignatureLayer) -> bytes:
    packet = io.BytesIO()
    c = canvas.Canvas(packet)
    field = layer.signature.field
    if field:
        c.translate(field.x, field.y)
        c.scale(field.width / 200, field.height / 50)
    if layer.image:
        c.drawInlineImage(layer.image, 0, 0)
    if layer.stamp_path and Path(layer.stamp_path).exists():
        c.drawImage(str(layer.stamp_path), 0, -60, width=200, height=50)
    c.save()
    packet.seek(0)
    return packet.read()


def merge_signature_layers(pdf_path: Path, layers: Iterable[SignatureLayer]) -> Path:
    pdf = pikepdf.open(pdf_path)
    for layer in layers:
        overlay_data = _render_signature_layer(layer)
        pdf.pages[0].add_overlay(pikepdf.Pdf.open(io.BytesIO(overlay_data)))
    output = pdf_path.with_name(pdf_path.stem + '_signed.pdf')
    pdf.save(output)
    return output


def apply_pades_signature(pdf_path: Path, signature: Signature, signer: SimpleSigner) -> Path:
    output = pdf_path.with_name(pdf_path.stem + '_pades.pdf')
    with open(pdf_path, 'rb') as inf, open(output, 'wb') as outf:
        sig_fields.signdoc_approval(
            inf,
            output=outf,
            signer=Signer(signer=signer),
            signature_meta=sig_fields.PdfSignatureMetadata(field_name=signature.field.field_type if signature.field else None),
        )
    return output
