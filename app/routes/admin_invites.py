from datetime import datetime
import secrets
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import AdminInvite, User
from app.middleware.auth import admin_required

admin_invites_bp = Blueprint('admin_invites', __name__)


@admin_invites_bp.route('', methods=['GET'])
@admin_required
def list_invites():
    invites = AdminInvite.query.order_by(AdminInvite.created_at.desc()).all()
    return jsonify([i.to_dict() for i in invites])


@admin_invites_bp.route('', methods=['POST'])
@admin_required
def create_invite():
    # generate a secure random code
    code = secrets.token_urlsafe(16)
    user_id = get_jwt_identity()

    invite = AdminInvite(code=code, created_by=user_id)
    db.session.add(invite)
    db.session.commit()

    return jsonify(invite.to_dict()), 201


@admin_invites_bp.route('/<invite_id>', methods=['DELETE'])
@admin_required
def revoke_invite(invite_id):
    invite = AdminInvite.query.get(invite_id)
    if not invite:
        return jsonify({'message': 'Invite not found'}), 404
    invite.active = False
    db.session.commit()
    return jsonify({'message': 'Invite revoked'})
