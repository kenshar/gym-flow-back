from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import MemberRequest, Member, User
from app.middleware.auth import admin_required
from datetime import datetime

member_requests_bp = Blueprint('member_requests', __name__)


@member_requests_bp.route('', methods=['POST'])
def submit_member_request():
    """
    Submit a new member signup request
    Public endpoint - no authentication required
    """
    data = request.get_json()

    # Validate required fields
    if not data.get('name') or not data.get('email') or not data.get('phone') or not data.get('plan'):
        return jsonify({'message': 'Missing required fields: name, email, phone, plan'}), 400

    # Check if email already exists in members or pending requests
    existing_member = Member.query.filter_by(email=data['email']).first()
    if existing_member:
        return jsonify({'message': 'Email already registered as a member'}), 409

    existing_request = MemberRequest.query.filter_by(email=data['email'], status='pending').first()
    if existing_request:
        return jsonify({'message': 'A signup request already exists for this email'}), 409

    # Validate plan
    valid_plans = ['basic', 'premium', 'vip']
    if data['plan'] not in valid_plans:
        return jsonify({'message': f'Invalid plan. Must be one of: {", ".join(valid_plans)}'}), 400

    # Create new request
    member_request = MemberRequest(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        plan=data['plan']
    )

    db.session.add(member_request)
    db.session.commit()

    return jsonify(member_request.to_dict()), 201


@member_requests_bp.route('', methods=['GET'])
@admin_required
def get_member_requests():
    """
    Get all member signup requests (admin only)
    Can filter by status: pending, approved, rejected
    """
    status = request.args.get('status', 'pending')
    
    if status == 'all':
        requests = MemberRequest.query.order_by(MemberRequest.created_at.desc()).all()
    else:
        requests = MemberRequest.query.filter_by(status=status).order_by(MemberRequest.created_at.desc()).all()

    return jsonify([r.to_dict() for r in requests]), 200


@member_requests_bp.route('/<request_id>', methods=['GET'])
@admin_required
def get_member_request(request_id):
    """
    Get a specific member signup request (admin only)
    """
    member_request = MemberRequest.query.get(request_id)
    if not member_request:
        return jsonify({'message': 'Request not found'}), 404

    return jsonify(member_request.to_dict()), 200


@member_requests_bp.route('/<request_id>/approve', methods=['PUT'])
@admin_required
def approve_member_request(request_id):
    """
    Approve a member signup request and create a new member (admin only)
    """
    member_request = MemberRequest.query.get(request_id)
    if not member_request:
        return jsonify({'message': 'Request not found'}), 404

    if member_request.status != 'pending':
        return jsonify({'message': f'Cannot approve a {member_request.status} request'}), 400

    # Check if email already exists
    existing_member = Member.query.filter_by(email=member_request.email).first()
    if existing_member:
        return jsonify({'message': 'A member with this email already exists'}), 409

    admin_id = get_jwt_identity()

    # Create new member
    new_member = Member(
        name=member_request.name,
        email=member_request.email,
        phone=member_request.phone,
        membership_type=member_request.plan,
        membership_status='active'
    )

    # Update the request
    member_request.status = 'approved'
    member_request.approved_by = admin_id
    member_request.updated_at = datetime.utcnow()

    db.session.add(new_member)
    db.session.commit()

    return jsonify({
        'message': 'Member request approved and member created successfully',
        'request': member_request.to_dict(),
        'member': new_member.to_dict()
    }), 200


@member_requests_bp.route('/<request_id>/reject', methods=['PUT'])
@admin_required
def reject_member_request(request_id):
    """
    Reject a member signup request (admin only)
    """
    member_request = MemberRequest.query.get(request_id)
    if not member_request:
        return jsonify({'message': 'Request not found'}), 404

    if member_request.status != 'pending':
        return jsonify({'message': f'Cannot reject a {member_request.status} request'}), 400

    admin_id = get_jwt_identity()

    member_request.status = 'rejected'
    member_request.approved_by = admin_id
    member_request.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'message': 'Member request rejected',
        'request': member_request.to_dict()
    }), 200


@member_requests_bp.route('/<request_id>', methods=['DELETE'])
@admin_required
def delete_member_request(request_id):
    """
    Delete a member signup request (admin only)
    """
    member_request = MemberRequest.query.get(request_id)
    if not member_request:
        return jsonify({'message': 'Request not found'}), 404

    db.session.delete(member_request)
    db.session.commit()

    return jsonify({'message': 'Member request deleted'}), 200
