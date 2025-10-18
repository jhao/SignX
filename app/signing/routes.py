from __future__ import annotations

import base64
import io
from pathlib import Path

from flask import abort, jsonify, render_template, request, send_file, url_for
from PIL import Image
from pyhanko.sign.signers import SimpleSigner

from ..extensions import db
from ..models import CryptoRecord, Document, Envelope, EnvelopeStatus, Signature, Signer
from ..pdf import SignatureLayer, apply_pades_signature, merge_signature_layers
from ..storage import save_upload
from . import bp


@bp.get('/validate/<token>')
def validate_link(token: str):
    signer = Signer.query.filter_by(invite_token=token).first_or_404()
    envelope = signer.envelope
    if envelope.status not in {EnvelopeStatus.SENT, EnvelopeStatus.VIEWED, EnvelopeStatus.SIGNED}:
        abort(400, 'invalid_status')
    envelope.set_status(EnvelopeStatus.VIEWED)
    db.session.commit()
    document = envelope.documents[0] if envelope.documents else None
    pdf_url = None
    if document:
        pdf_url = url_for('signing.download_document', document_id=document.id)
    return render_template('signing.html', signer=signer, pdf_url=pdf_url)


@bp.post('/submit/<token>')
def submit_signature(token: str):
    signer = Signer.query.filter_by(invite_token=token).first_or_404()
    envelope = signer.envelope
    if envelope.status not in {EnvelopeStatus.SENT, EnvelopeStatus.VIEWED}:
        return jsonify({'error': 'invalid_status'}), 400
    data = request.form or request.get_json() or {}
    signature_data = data.get('signature_data') or request.form.get('signature_data')
    stamp = request.files.get('stamp') if request.files else None
    image = None
    image_bytes = None
    if signature_data:
        image_bytes = base64.b64decode(signature_data.split(',')[-1])
        image = Image.open(io.BytesIO(image_bytes))
    stamp_path = None
    if stamp:
        stamp_path = save_upload(stamp, stamp.filename)
    document = envelope.documents[0]
    signature = Signature(
        document=document,
        signer=signer,
        image_data=image_bytes if signature_data else None,
        stamp_path=str(stamp_path) if stamp_path else None,
    )
    db.session.add(signature)
    signer.has_signed = True
    envelope.set_status(EnvelopeStatus.SIGNED)

    layer = SignatureLayer(signature=signature, image=image, stamp_path=Path(stamp_path) if stamp_path else None)
    signed_pdf = merge_signature_layers(Path(document.pdf_path or document.original_path), [layer])
    document.pdf_path = str(signed_pdf)
    try:
        pades_signer = SimpleSigner.load_pkcs12(Path('certs/signer.p12'), password=b'changeit')  # pragma: no cover
        pades_pdf = apply_pades_signature(signed_pdf, signature, pades_signer)
        signature.crypto_record = CryptoRecord(
            algorithm='pades',
            certificate_subject=str(pades_signer.signing_cert.subject.native),
            signature_bytes=pades_pdf.read_bytes(),
        )
        document.pdf_path = str(pades_pdf)
    except Exception:
        pass

    db.session.commit()

    try:
        envelope.set_status(EnvelopeStatus.COMPLETED)
        db.session.commit()
    except ValueError:
        pass

    return jsonify({'status': 'signed'})


@bp.get('/documents/<int:document_id>/download')
def download_document(document_id: int):
    document = Document.query.get_or_404(document_id)
    path = Path(document.pdf_path or document.original_path)
    return send_file(path, as_attachment=True)
