from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta, date
from config import Config
import pyotp
import os
import qrcode
import io
import secrets
import random
import string
from flask_mail import Mail, Message
from functools import wraps
import base64
import json
import requests
from sqlalchemy import LargeBinary
from twilio.rest import Client

# WebAuthn imports
from webauthn import generate_registration_options, verify_registration_response
from webauthn import generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import AuthenticatorSelectionCriteria, AuthenticatorAttachment, \
    UserVerificationRequirement

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)


# =========================
# LOCATION TRACKING FUNCTION
# =========================

def get_location_from_ip(ip_address):
    """Get location from IP address using free ipapi.co API"""
    try:
        print(f"📍 Looking up location for IP: {ip_address}")

        if ip_address in ['127.0.0.1', 'localhost', '::1', '0.0.0.0']:
            print(f"📍 Localhost detected - using Local Development")
            return {
                'city': 'Localhost',
                'country': 'Local Development',
                'lat': 0,
                'lon': 0
            }

        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        data = response.json()

        if 'error' not in data:
            city = data.get('city', 'Unknown')
            country = data.get('country_name', 'Unknown')
            lat = data.get('latitude', 0)
            lon = data.get('longitude', 0)

            print(f"📍 Found location: {city}, {country} (lat: {lat}, lon: {lon})")
            return {
                'city': city,
                'country': country,
                'lat': lat,
                'lon': lon
            }
        else:
            print(f"📍 Location lookup failed: {data.get('error')}")
            return {
                'city': 'Unknown',
                'country': 'Unknown',
                'lat': 0,
                'lon': 0
            }

    except requests.exceptions.Timeout:
        print(f"📍 Location lookup timeout for {ip_address}")
        return {
            'city': 'Unknown',
            'country': 'Unknown',
            'lat': 0,
            'lon': 0
        }
    except Exception as e:
        print(f"📍 Location lookup error: {e}")
        return {
            'city': 'Unknown',
            'country': 'Unknown',
            'lat': 0,
            'lon': 0
        }


# =========================
# SECURITY LOG FUNCTION
# =========================

def log_security_event(user_id, username, action, details, request, status="success"):
    """Log security events to database"""
    try:
        log = SecurityLog(
            user_id=user_id,
            username=username,
            action=action,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', 'Unknown')[:200],
            status=status
        )
        db.session.add(log)
        db.session.commit()
        print(f"📝 Security log: {username} - {action} - {status}")
    except Exception as e:
        print(f"❌ Logging error: {e}")


# =========================
# TWILIO VERIFY FUNCTIONS
# =========================

def send_otp_verify(phone_number):
    """Send OTP via Twilio Verify Service"""
    try:
        client = Client(
            app.config.get('TWILIO_ACCOUNT_SID'),
            app.config.get('TWILIO_AUTH_TOKEN')
        )
        client.verify.v2.services(
            app.config.get('TWILIO_VERIFY_SID')
        ).verifications.create(to=phone_number, channel="sms")
        print(f"✅ OTP sent to {phone_number}")
        return True
    except Exception as e:
        print(f"❌ Error sending OTP: {e}")
        return False


def check_otp_verify(phone_number, otp_code):
    """Verify OTP using Twilio Verify Service"""
    try:
        client = Client(
            app.config.get('TWILIO_ACCOUNT_SID'),
            app.config.get('TWILIO_AUTH_TOKEN')
        )
        result = client.verify.v2.services(
            app.config.get('TWILIO_VERIFY_SID')
        ).verification_checks.create(to=phone_number, code=otp_code)
        print(f"✅ Verification result: {result.status}")
        return result.status == "approved"
    except Exception as e:
        print(f"❌ Error verifying OTP: {e}")
        return False


# =========================
# ENHANCED EMAIL RECEIPT FUNCTIONS
# =========================

def send_transaction_confirmation(user, transaction_type, amount, reference_id):
    """Send quick confirmation email that transaction was processed"""
    try:
        subject = f"✅ Transaction Confirmed - {transaction_type.title()} - Zero Trust Bank"

        if transaction_type == 'deposit':
            icon = "💰"
            color = "#28a745"
        elif transaction_type == 'withdraw':
            icon = "💸"
            color = "#dc3545"
        else:
            icon = "🔄"
            color = "#ffc107"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
            <div style="max-width: 550px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, {color} 0%, {color}80 100%); padding: 25px; text-align: center;">
                    <div style="font-size: 48px;">{icon}</div>
                    <h1 style="color: white; margin: 10px 0 0; font-size: 24px;">Transaction Confirmed</h1>
                </div>
                <div style="padding: 25px;">
                    <p style="font-size: 18px; color: #333; margin-bottom: 20px;">Hello <strong>{user.username}</strong>,</p>
                    <p style="color: #666; margin-bottom: 20px;">Your transaction has been successfully processed.</p>
                    <div style="background-color: {color}10; border-left: 4px solid {color}; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="margin: 0 0 8px 0;"><strong>💰 Transaction Type:</strong> {transaction_type.title()}</p>
                        <p style="margin: 0 0 8px 0;"><strong>💷 Amount:</strong> £{amount:,.2f}</p>
                        <p style="margin: 0;"><strong>🔖 Reference:</strong> {reference_id}</p>
                    </div>
                    <p style="color: #666; margin-bottom: 20px;">
                        A detailed receipt has been sent to your email. Please keep it for your records.
                    </p>
                    <p style="color: #999; font-size: 12px; text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #e0e0e0;">
                        Zero Trust Bank - Never Trust, Always Verify<br>
                        {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[user.email])
        msg.html = html_content
        msg.body = f"""Transaction Confirmed - {transaction_type.title()}

Reference: {reference_id}
Amount: £{amount:,.2f}
Type: {transaction_type.title()}

A detailed receipt has been sent separately.
"""
        mail.send(msg)
        print(f"✅ Confirmation email sent to {user.email}")
        return True
    except Exception as e:
        print(f"❌ Confirmation email failed: {e}")
        return False


def send_detailed_receipt(user, transaction_type, amount, reference_id, new_balance,
                          daily_limit_remaining, monthly_limit_remaining,
                          description="", recipient_name=None, recipient_email=None,
                          location=None, ip_address=None, risk_score=None):
    """Send detailed transaction receipt with all information"""
    try:
        if transaction_type == 'deposit':
            icon = "💰"
            color = "#28a745"
            bg_color = "#e8f5e9"
            amount_display = f"+ £{amount:,.2f}"
            type_display = "DEPOSIT"
        elif transaction_type == 'withdraw':
            icon = "💸"
            color = "#dc3545"
            bg_color = "#ffebee"
            amount_display = f"- £{amount:,.2f}"
            type_display = "WITHDRAWAL"
        elif transaction_type in ['transfer_out', 'transfer']:
            icon = "📤"
            color = "#ffc107"
            bg_color = "#fff3e0"
            amount_display = f"- £{amount:,.2f}"
            type_display = "TRANSFER SENT"
        elif transaction_type == 'transfer_in':
            icon = "📥"
            color = "#17a2b8"
            bg_color = "#e1f5fe"
            amount_display = f"+ £{amount:,.2f}"
            type_display = "TRANSFER RECEIVED"
        else:
            icon = "💳"
            color = "#667eea"
            bg_color = "#f3e5f5"
            amount_display = f"£{amount:,.2f}"
            type_display = transaction_type.upper()

        location_info = location if location else "Unknown"
        ip_info = ip_address if ip_address else "Unknown"

        risk_display = ""
        if risk_score is not None:
            if risk_score < 30:
                risk_badge = "🟢 Low Risk"
                risk_color = "#28a745"
            elif risk_score < 70:
                risk_badge = "🟡 Medium Risk"
                risk_color = "#ffc107"
            else:
                risk_badge = "🔴 High Risk"
                risk_color = "#dc3545"
            risk_display = f"""
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                <span style="font-weight: 600; color: #555;">🎲 Risk Score:</span>
                <span style="color: {risk_color}; font-weight: 600;">{risk_score}/100 ({risk_badge})</span>
            </div>
            """

        recipient_info = ""
        if recipient_name:
            recipient_info = f"""
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                <span style="font-weight: 600; color: #555;">👤 Recipient:</span>
                <span style="color: #333;">{recipient_name} {f'({recipient_email})' if recipient_email else ''}</span>
            </div>
            """

        desc_info = ""
        if description:
            desc_info = f"""
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                <span style="font-weight: 600; color: #555;">📝 Description:</span>
                <span style="color: #333;">{description}</span>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #1a3e60 0%, #2c5a7a 100%); padding: 30px; text-align: center;">
                    <div style="font-size: 48px;">{icon}</div>
                    <h1 style="color: white; margin: 10px 0 5px; font-size: 24px;">Zero Trust Bank</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 0;">Official Transaction Receipt</p>
                </div>
                <div style="padding: 30px;">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <span style="background: {color}; color: white; padding: 8px 20px; border-radius: 50px; font-size: 14px; font-weight: 600;">
                            {type_display}
                        </span>
                        <p style="color: {color}; font-size: 36px; font-weight: bold; margin: 15px 0 0;">
                            {amount_display}
                        </p>
                    </div>
                    <div style="background-color: {bg_color}; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin: 0 0 15px; font-size: 16px;">📋 Transaction Details</h3>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.1);">
                            <span style="font-weight: 600; color: #555;">🔖 Reference Number:</span>
                            <span style="color: #333; font-family: monospace;">{reference_id}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.1);">
                            <span style="font-weight: 600; color: #555;">📅 Date & Time:</span>
                            <span style="color: #333;">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} UTC</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.1);">
                            <span style="font-weight: 600; color: #555;">🏦 Transaction Type:</span>
                            <span style="color: #333;">{transaction_type.replace('_', ' ').title()}</span>
                        </div>
                        {recipient_info}
                        {desc_info}
                        {risk_display}
                    </div>
                    <div style="background-color: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin: 0 0 15px; font-size: 16px;">💰 Balance Information</h3>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="font-weight: 600; color: #555;">New Balance:</span>
                            <span style="color: #28a745; font-weight: bold; font-size: 18px;">£{new_balance:,.2f}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="font-weight: 600; color: #555;">📊 Daily Limit Remaining:</span>
                            <span style="color: #666;">£{daily_limit_remaining:,.2f} / £500.00</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                            <span style="font-weight: 600; color: #555;">📅 Monthly Limit Remaining:</span>
                            <span style="color: #666;">£{monthly_limit_remaining:,.2f} / £5,000.00</span>
                        </div>
                    </div>
                    <div style="background-color: #e3f2fd; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin: 0 0 15px; font-size: 16px;">📍 Security Information</h3>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.1);">
                            <span style="font-weight: 600; color: #555;">Location:</span>
                            <span style="color: #333;">{location_info}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                            <span style="font-weight: 600; color: #555;">IP Address:</span>
                            <span style="color: #333; font-family: monospace;">{ip_info}</span>
                        </div>
                    </div>
                    <div style="background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="margin: 0; font-size: 13px; color: #e65100;">
                            ⚠️ <strong>Security Notice:</strong> If you did NOT authorize this transaction, please contact Zero Trust Bank support immediately at support@zerotrustbank.com
                        </p>
                    </div>
                    <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">
                    <div style="text-align: center;">
                        <p style="color: #666; font-size: 12px; margin: 0;">
                            This is an official transaction receipt from Zero Trust Bank.<br>
                            Please retain this receipt for your records.
                        </p>
                        <p style="color: #999; font-size: 11px; margin: 10px 0 0;">
                            Zero Trust Bank - Secure Banking Platform | Never Trust, Always Verify
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        msg = Message(f"📧 Detailed Receipt - {type_display} - {reference_id}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[user.email])
        msg.html = html_content

        msg.body = f"""
ZERO TRUST BANK - DETAILED TRANSACTION RECEIPT
================================================

Reference: {reference_id}
Type: {transaction_type.upper()}
Amount: £{amount:,.2f}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Description: {description if description else 'N/A'}
{f'Recipient: {recipient_name} ({recipient_email})' if recipient_name else ''}

New Balance: £{new_balance:,.2f}
Daily Limit Remaining: £{daily_limit_remaining:,.2f}
Monthly Limit Remaining: £{monthly_limit_remaining:,.2f}

Location: {location_info}
IP Address: {ip_info}
{f'Risk Score: {risk_score}/100' if risk_score is not None else ''}

Thank you for banking with Zero Trust Bank.
"""

        mail.send(msg)
        print(f"✅ Detailed receipt email sent to {user.email} for {reference_id}")
        return True
    except Exception as e:
        print(f"❌ Detailed receipt email failed: {e}")
        return False


# =========================
# ORIGINAL send_transaction_receipt (kept for compatibility)
# =========================

def send_transaction_receipt_original(user, transaction, transaction_type, other_party=None):
    """Send transaction receipt email to user (original function - kept for compatibility)"""
    try:
        if transaction_type == "deposit":
            subject = f"💰 Deposit Receipt - ${transaction.amount:.2f}"
        elif transaction_type == "withdraw":
            subject = f"💸 Withdrawal Receipt - ${transaction.amount:.2f}"
        elif transaction_type == "transfer":
            subject = f"🔄 Transfer Sent - ${transaction.amount:.2f}"
        elif transaction_type == "received":
            subject = f"📥 Money Received - ${transaction.amount:.2f}"
        else:
            subject = f"Transaction Receipt - ${transaction.amount:.2f}"

        msg = Message(
            subject=f"Zero Trust Bank - {subject}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[user.email]
        )

        is_suspicious = transaction.risk_score and transaction.risk_score > 50

        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 5px 20px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">🏦 Zero Trust Bank</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0;">Transaction Receipt</p>
                </div>
                <div style="padding: 30px;">
                    <h2 style="text-align: center; margin-bottom: 20px;">Transaction {'Completed' if transaction.status == 'completed' else 'Pending'}</h2>
                    <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 20px 0;">
                        <div style="font-size: 14px; color: #666;">Amount</div>
                        <div style="font-size: 36px; font-weight: bold; color: {'#dc3545' if transaction_type in ['withdraw', 'transfer'] else '#28a745'};">${transaction.amount:.2f}</div>
                        <div style="font-size: 12px; color: #666;">{transaction.timestamp.strftime('%B %d, %Y at %H:%M:%S')}</div>
                    </div>
                    <div style="margin: 20px 0;">
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="color: #666;">Transaction ID:</span>
                            <span style="font-weight: 500;">{transaction.reference_id}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="color: #666;">Type:</span>
                            <span style="font-weight: 500;">{transaction_type | title}</span>
                        </div>
                        {f'''
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="color: #666;">To:</span>
                            <span style="font-weight: 500;">{transaction.to_user.username if transaction.to_user else 'System'}</span>
                        </div>
                        ''' if transaction_type == 'transfer' else ''}
                        {f'''
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="color: #666;">From:</span>
                            <span style="font-weight: 500;">{transaction.from_user.username if transaction.from_user else 'System'}</span>
                        </div>
                        ''' if transaction_type == 'received' else ''}
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="color: #666;">Description:</span>
                            <span style="font-weight: 500;">{transaction.description or 'N/A'}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="color: #666;">Status:</span>
                            <span style="font-weight: 500;">{'✅ Completed' if transaction.status == 'completed' else '⏳ Pending'}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e0e0e0;">
                            <span style="color: #666;">Location:</span>
                            <span style="font-weight: 500;">{transaction.location_city or 'Unknown'}, {transaction.location_country or 'Unknown'}</span>
                        </div>
                    </div>
                    {f'''
                    <div style="background: #fff3cd; padding: 15px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <strong>⚠️ Security Notice</strong><br>
                        This transaction was flagged for additional review due to unusual activity.
                    </div>
                    ''' if is_suspicious else ''}
                    <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 2px dashed #e0e0e0;">
                        <span style="font-size: 16px;">Your New Balance: </span>
                        <span style="font-size: 24px; font-weight: bold;">${user.balance:.2f}</span>
                    </div>
                    <div style="text-align: center; margin-top: 20px;">
                        <a href="http://localhost:5000/dashboard" style="display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px;">View Dashboard</a>
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #999;">
                    <p>Zero Trust Bank - Your security is our priority</p>
                    <p>If you did not authorize this transaction, please contact support immediately.</p>
                </div>
            </div>
        </body>
        </html>
        """

        mail.send(msg)
        print(f"📧 Transaction receipt sent to {user.email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send receipt: {e}")
        return False


# =========================
# TRANSACTION HELPER FUNCTIONS
# =========================

def generate_transaction_reference():
    """Generate unique transaction reference"""
    prefix = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"TX{prefix}{random_part}"


def calculate_risk_score(user, amount, transaction_type, recipient=None, request=None):
    """Calculate risk score for transaction (0-100)"""
    risk_score = 0

    if amount > 1000:
        risk_score += 20
    elif amount > 500:
        risk_score += 10
    elif amount > 100:
        risk_score += 5

    if user.last_login_city and user.last_login_city != 'Localhost':
        risk_score += 15

    current_hour = datetime.now().hour
    if current_hour < 5 or current_hour > 23:
        risk_score += 20

    if transaction_type == 'transfer' and recipient:
        existing_transfers = Transaction.query.filter(
            Transaction.from_user_id == user.id,
            Transaction.to_user_id == recipient.id,
            Transaction.status == 'completed'
        ).count()
        if existing_transfers == 0:
            risk_score += 25

    today = date.today()
    today_transactions = Transaction.query.filter(
        Transaction.from_user_id == user.id,
        db.func.date(Transaction.timestamp) == today,
        Transaction.status == 'completed'
    ).count()
    if today_transactions > 5:
        risk_score += 15
    elif today_transactions > 3:
        risk_score += 10

    if user.failed_attempts > 0:
        risk_score += user.failed_attempts * 5

    return min(risk_score, 100)


def check_limits(user, amount, transaction_type='withdraw'):
    """Check if transaction is within user limits"""
    today = date.today()

    if user.daily_transaction_date is None:
        user.daily_transaction_date = today
    if user.monthly_transaction_date is None:
        user.monthly_transaction_date = today
    if user.daily_transaction_total is None:
        user.daily_transaction_total = 0
    if user.monthly_transaction_total is None:
        user.monthly_transaction_total = 0
    if user.daily_limit is None:
        user.daily_limit = 500.00
    if user.monthly_limit is None:
        user.monthly_limit = 5000.00

    if user.daily_transaction_date != today:
        user.daily_transaction_total = 0
        user.daily_transaction_date = today
        db.session.commit()

    if user.monthly_transaction_date.month != today.month:
        user.monthly_transaction_total = 0
        user.monthly_transaction_date = today
        db.session.commit()

    if transaction_type in ['withdraw', 'transfer']:
        if user.daily_transaction_total + amount > user.daily_limit:
            remaining = user.daily_limit - user.daily_transaction_total
            return False, f"Daily limit exceeded! Maximum ${user.daily_limit:.2f} per day. You have ${remaining:.2f} left today."

        if user.monthly_transaction_total + amount > user.monthly_limit:
            return False, f"Monthly limit exceeded! Maximum ${user.monthly_limit:.2f} per month."

        if user.balance < amount:
            return False, f"Insufficient balance! You have ${user.balance:.2f}. Need ${amount:.2f}."

    return True, "OK"


def process_transaction(from_user, to_user, amount, transaction_type, description, request, recipient=None):
    """Process transaction with risk assessment and send emails"""

    reference = generate_transaction_reference()
    location = get_location_from_ip(request.remote_addr)
    risk_score = calculate_risk_score(from_user, amount, transaction_type, recipient, request)
    needs_approval = risk_score > 50

    if not needs_approval:
        if transaction_type == 'withdraw':
            from_user.balance -= amount
            from_user.daily_transaction_total += amount
            from_user.monthly_transaction_total += amount
        elif transaction_type == 'transfer':
            from_user.balance -= amount
            to_user.balance += amount
            from_user.daily_transaction_total += amount
            from_user.monthly_transaction_total += amount
        elif transaction_type == 'deposit':
            from_user.balance += amount

        status = 'completed'
        message = f"✅ Transaction processed successfully"
        db.session.commit()
    else:
        status = 'pending'
        message = f"⚠️ Transaction flagged for review (Risk Score: {risk_score}). Admin approval required."

    transaction = Transaction(
        from_user_id=from_user.id if from_user else None,
        to_user_id=to_user.id if to_user else None,
        amount=amount,
        type=transaction_type,
        description=description,
        status=status,
        reference_id=reference,
        ip_address=request.remote_addr,
        location_city=location['city'],
        location_country=location['country'],
        risk_score=risk_score
    )
    db.session.add(transaction)
    db.session.commit()

    log_security_event(
        from_user.id, from_user.username, f"{transaction_type}_initiated",
        f"{transaction_type.capitalize()} of ${amount:.2f} - Risk Score: {risk_score} - Ref: {reference}",
        request, "warning" if needs_approval else "success"
    )

    daily_remaining = from_user.daily_limit - from_user.daily_transaction_total
    monthly_remaining = from_user.monthly_limit - from_user.monthly_transaction_total
    location_str = f"{location['city']}, {location['country']}"
    ip_address = request.remote_addr

    send_transaction_confirmation(from_user, transaction_type, amount, reference)

    send_detailed_receipt(
        user=from_user,
        transaction_type=transaction_type,
        amount=amount,
        reference_id=reference,
        new_balance=from_user.balance,
        daily_limit_remaining=daily_remaining,
        monthly_limit_remaining=monthly_remaining,
        description=description,
        recipient_name=to_user.username if to_user else None,
        recipient_email=to_user.email if to_user else None,
        location=location_str,
        ip_address=ip_address,
        risk_score=risk_score
    )

    if transaction_type == 'transfer' and to_user and not needs_approval:
        recipient_daily_remaining = to_user.daily_limit - to_user.daily_transaction_total
        recipient_monthly_remaining = to_user.monthly_limit - to_user.monthly_transaction_total

        send_transaction_confirmation(to_user, 'received', amount, reference + "-R")

        send_detailed_receipt(
            user=to_user,
            transaction_type='transfer_in',
            amount=amount,
            reference_id=reference + "-R",
            new_balance=to_user.balance,
            daily_limit_remaining=recipient_daily_remaining,
            monthly_limit_remaining=recipient_monthly_remaining,
            description=f"Money received from {from_user.username}: {description}",
            recipient_name=from_user.username,
            recipient_email=from_user.email,
            location=location_str,
            ip_address=ip_address,
            risk_score=0
        )

    return transaction, message, needs_approval


def process_transaction_with_data(user, transaction_data, request):
    """Process transaction after biometric verification"""
    transaction_type = transaction_data.get('type')
    amount = float(transaction_data.get('amount'))
    description = transaction_data.get('description', '')

    if transaction_type == 'deposit':
        if amount <= 0:
            return {"success": False, "message": "Amount must be positive!"}
        if amount > 10000:
            return {"success": False, "message": "Maximum deposit is $10,000!"}

        transaction, message, needs_approval = process_transaction(
            from_user=user,
            to_user=None,
            amount=amount,
            transaction_type="deposit",
            description=f"Deposit of ${amount:.2f}",
            request=request
        )

        return {"success": True, "message": message}

    elif transaction_type == 'withdraw':
        if amount <= 0:
            return {"success": False, "message": "Amount must be positive!"}

        allowed, message = check_limits(user, amount, 'withdraw')
        if not allowed:
            return {"success": False, "message": message}

        transaction, message, needs_approval = process_transaction(
            from_user=user,
            to_user=None,
            amount=amount,
            transaction_type="withdraw",
            description=f"Withdrawal of ${amount:.2f}",
            request=request
        )

        return {"success": True, "message": message}

    elif transaction_type == 'transfer':
        recipient_id = int(transaction_data.get('recipient_id'))
        recipient = User.query.get(recipient_id)

        if not recipient:
            return {"success": False, "message": "Recipient not found!"}
        if amount <= 0:
            return {"success": False, "message": "Amount must be positive!"}
        if recipient.id == user.id:
            return {"success": False, "message": "Cannot transfer to yourself!"}

        allowed, message = check_limits(user, amount, 'transfer')
        if not allowed:
            return {"success": False, "message": message}

        transaction, message, needs_approval = process_transaction(
            from_user=user,
            to_user=recipient,
            amount=amount,
            transaction_type="transfer",
            description=f"Transfer to {recipient.username}: {description}" if description else f"Transfer to {recipient.username}",
            request=request,
            recipient=recipient
        )

        return {"success": True, "message": message}

    return {"success": False, "message": "Invalid transaction type"}


# =========================
# WEBAUTHN HELPER FUNCTIONS
# =========================

def base64url_to_bytes(data):
    if data is None:
        return None
    padding = '=' * (4 - len(data) % 4) if len(data) % 4 != 0 else ''
    return base64.urlsafe_b64decode(data + padding)


def bytes_to_base64url(data):
    if data is None:
        return None
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


# =========================
# ROLE-BASED ACCESS DECORATORS
# =========================

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please login first!", "error")
                return redirect(url_for("login"))
            user = User.query.get(session["user_id"])
            if not user:
                session.clear()
                flash("User not found!", "error")
                return redirect(url_for("login"))
            if user.role not in roles:
                flash(f"Access denied! {user.role} role cannot access this page.", "error")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def customer_required(f):
    return role_required("customer", "employee", "admin")(f)


def employee_required(f):
    return role_required("employee", "admin")(f)


def admin_required(f):
    return role_required("admin")(f)


# =========================
# EMAIL FUNCTIONS
# =========================

def send_registration_email(user_email, username):
    try:
        msg = Message(
            subject="🎉 Welcome to Zero Trust Bank!",
            sender=app.config['MAIL_USERNAME'],
            recipients=[user_email]
        )
        msg.body = f"""
        Dear {username},

        Thank you for registering with Zero Trust Bank!

        Your account has been successfully created with $1000 starting balance.

        Security Reminders:
        • Never share your password
        • Enable 2FA for extra security
        • Verify your email address
        • Monitor your account regularly

        Best regards,
        Zero Trust Bank Security Team
        """
        mail.send(msg)
        print(f"✅ Welcome email sent to {user_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")


def send_verification_email(user):
    try:
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        user.email_verification_expiry = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()

        verification_link = url_for('verify_email', token=token, _external=True)
        print(f"📧 Verification link: {verification_link}")

        msg = Message(
            subject="✅ Verify Your Email - Zero Trust Bank",
            sender=app.config['MAIL_USERNAME'],
            recipients=[user.email]
        )
        msg.html = f"""
        <html><body><h2>Email Verification</h2>
        <p>Hello {user.username},</p>
        <p>Click the link below to verify your email:</p>
        <p><a href="{verification_link}">{verification_link}</a></p>
        <p>This link expires in 24 hours.</p>
        </body></html>
        """
        msg.body = f"Verify your email: {verification_link}"
        mail.send(msg)

        print("✅ Verification email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False


def send_new_location_alert(user, location, ip_address):
    """Send alert when user logs in from new location"""
    try:
        msg = Message(
            subject="⚠️ New Login Location Detected - Zero Trust Bank",
            sender=app.config['MAIL_USERNAME'],
            recipients=[user.email]
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background: #fff3cd; border: 1px solid #ffc107; border-radius: 10px; padding: 20px;">
                <h2 style="color: #856404;">⚠️ New Login Location Alert</h2>
                <p>Hello {user.username},</p>
                <p>We detected a login to your account from a new location:</p>
                <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>📍 Location:</strong> {location}</p>
                    <p><strong>🌐 IP Address:</strong> {ip_address}</p>
                    <p><strong>🕐 Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                </div>
                <p>If this was you, you can ignore this email.</p>
                <p><strong>If this wasn't you, please contact support immediately!</strong></p>
                <hr>
                <p style="font-size: 12px; color: #666;">Zero Trust Bank - Security Alert</p>
            </div>
        </body>
        </html>
        """

        msg.html = html_content
        msg.body = f"""New Login Location Alert

Location: {location}
IP Address: {ip_address}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

If this wasn't you, please contact support immediately!"""

        mail.send(msg)
        print(f"📧 Location alert sent to {user.email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send location alert: {e}")
        return False


# =========================
# USER MODEL
# =========================

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="customer")
    failed_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    otp_secret = db.Column(db.String(32), default=lambda: pyotp.random_base32())
    is_otp_enabled = db.Column(db.Boolean, default=False)

    mobile = db.Column(db.String(20), nullable=True)
    is_mobile_verified = db.Column(db.Boolean, default=False)
    mobile_otp = db.Column(db.String(6), nullable=True)
    mobile_otp_expiry = db.Column(db.DateTime, nullable=True)

    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), nullable=True)
    email_verification_expiry = db.Column(db.DateTime, nullable=True)

    webauthn_credential_id = db.Column(LargeBinary, nullable=True)
    webauthn_public_key = db.Column(LargeBinary, nullable=True)
    webauthn_sign_count = db.Column(db.Integer, default=0)

    registration_ip = db.Column(db.String(45), nullable=True)
    registration_city = db.Column(db.String(100), nullable=True)
    registration_country = db.Column(db.String(100), nullable=True)
    registration_lat = db.Column(db.Float, nullable=True)
    registration_lon = db.Column(db.Float, nullable=True)

    last_login_ip = db.Column(db.String(45), nullable=True)
    last_login_city = db.Column(db.String(100), nullable=True)
    last_login_country = db.Column(db.String(100), nullable=True)
    last_login_lat = db.Column(db.Float, nullable=True)
    last_login_lon = db.Column(db.Float, nullable=True)

    known_ips = db.Column(db.Text, nullable=True)

    balance = db.Column(db.Float, default=1000.00)
    daily_transaction_total = db.Column(db.Float, default=0)
    daily_transaction_date = db.Column(db.Date, default=date.today)
    monthly_transaction_total = db.Column(db.Float, default=0)
    monthly_transaction_date = db.Column(db.Date, default=date.today)
    daily_limit = db.Column(db.Float, default=500.00)
    monthly_limit = db.Column(db.Float, default=5000.00)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_otp_uri(self):
        if not self.otp_secret:
            return None
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(
            name=self.email,
            issuer_name=app.config.get('MFA_ISSUER_NAME', 'ZeroTrustBank')
        )

    def verify_otp(self, otp_code):
        if not self.otp_secret:
            return False
        return pyotp.TOTP(self.otp_secret).verify(otp_code)


# =========================
# TRANSACTION MODEL
# =========================

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50))
    description = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending')
    reference_id = db.Column(db.String(50), unique=True)
    ip_address = db.Column(db.String(45))
    location_city = db.Column(db.String(100))
    location_country = db.Column(db.String(100))
    risk_score = db.Column(db.Integer, default=0)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='sent_transactions')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='received_transactions')
    approver = db.relationship('User', foreign_keys=[approved_by])


# =========================
# SECURITY LOG MODEL
# =========================

class SecurityLog(db.Model):
    __tablename__ = 'security_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(100))
    action = db.Column(db.String(100))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    status = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# MOBILE OTP FOR REGISTRATION (TWILIO VERIFY)
# =========================

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    mobile = data.get('mobile')

    if not mobile:
        return jsonify({"success": False, "message": "Mobile number required"})

    if not mobile.startswith('+'):
        mobile = '+' + mobile

    sms_sent = send_otp_verify(mobile)

    if sms_sent:
        session['reg_pending_mobile'] = mobile
        return jsonify({"success": True, "message": "OTP sent to your phone!"})
    else:
        return jsonify({"success": False, "message": "Failed to send OTP. Check your number."})


@app.route("/verify-otp-registration", methods=["POST"])
def verify_otp_registration():
    data = request.get_json()
    mobile = data.get('mobile')
    otp = data.get('otp')

    if not mobile.startswith('+'):
        mobile = '+' + mobile

    stored_mobile = session.get('reg_pending_mobile')

    if not stored_mobile:
        return jsonify({"success": False,
                        "message": "No OTP request found. Click Send OTP first!"})

    if mobile != stored_mobile:
        return jsonify({"success": False, "message": "Mobile number mismatch!"})

    approved = check_otp_verify(mobile, otp)

    if approved:
        session['mobile_verified'] = True
        session['reg_mobile_otp'] = otp
        session['reg_mobile_otp_expiry'] = (
                datetime.utcnow() + timedelta(minutes=10)
        ).timestamp()
        return jsonify({"success": True, "message": "✅ Mobile verified!"})
    else:
        return jsonify({"success": False,
                        "message": "❌ Wrong code! Check your phone and try again."})


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return redirect(url_for("login"))


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        mobile = request.form.get("mobile", "")
        mobile_otp = request.form.get("mobile_otp", "")

        if User.query.filter_by(email=email).first():
            flash("User already exists!", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "error")
            return redirect(url_for("register"))

        if not mobile:
            flash("Mobile number is required!", "error")
            return redirect(url_for("register"))

        if not mobile.startswith('+'):
            mobile = '+' + mobile

        stored_otp = session.get('reg_mobile_otp')
        stored_expiry = session.get('reg_mobile_otp_expiry')
        stored_mobile = session.get('reg_pending_mobile')
        mobile_verified = session.get('mobile_verified', False)

        if not mobile_verified:
            flash("Please verify your mobile number with the OTP code!", "error")
            return redirect(url_for("register"))

        if not mobile_otp:
            flash("Please enter the verification code!", "error")
            return redirect(url_for("register"))

        if not stored_otp or not stored_expiry:
            flash("Please request an OTP code first!", "error")
            return redirect(url_for("register"))

        if datetime.utcnow().timestamp() > stored_expiry:
            flash("OTP has expired! Please request a new code.", "error")
            return redirect(url_for("register"))

        if mobile_otp != stored_otp:
            flash("Invalid verification code! Please try again.", "error")
            return redirect(url_for("register"))

        if mobile != stored_mobile:
            flash("Mobile number mismatch!", "error")
            return redirect(url_for("register"))

        location = get_location_from_ip(request.remote_addr)
        print(f"📍 New user registration from: {location['city']}, {location['country']}")

        new_user = User(
            username=username,
            email=email,
            mobile=mobile,
            role="customer",
            is_mobile_verified=True,
            registration_ip=request.remote_addr,
            registration_city=location['city'],
            registration_country=location['country'],
            registration_lat=location['lat'],
            registration_lon=location['lon'],
            balance=1000.00,
            daily_transaction_date=date.today(),
            monthly_transaction_date=date.today()
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        session.pop('reg_mobile_otp', None)
        session.pop('reg_mobile_otp_expiry', None)
        session.pop('reg_pending_mobile', None)
        session.pop('mobile_verified', None)

        log_security_event(
            new_user.id, username, "registration",
            f"User registered from {location['city']}, {location['country']} with verified mobile {mobile}",
            request, "success"
        )

        send_registration_email(email, username)
        send_verification_email(new_user)

        flash("Registration successful! Mobile verified. Please check your email to verify your account.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# VERIFY EMAIL
# =========================

@app.route("/verify-email/<token>")
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    if not user:
        flash("Invalid verification link!", "error")
        return redirect(url_for("login"))
    if user.email_verification_expiry < datetime.utcnow():
        flash("Verification link expired!", "error")
        return redirect(url_for("resend_verification"))
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expiry = None
    db.session.commit()
    flash("Email verified successfully!", "success")
    return redirect(url_for("login"))


# =========================
# RESEND VERIFICATION
# =========================

@app.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email not found!", "error")
            return redirect(url_for("resend_verification"))
        if user.email_verified:
            flash("Email already verified!", "success")
            return redirect(url_for("login"))
        if send_verification_email(user):
            flash("Verification email sent!", "success")
        else:
            flash("Error sending email!", "error")
        return redirect(url_for("login"))
    return render_template("resend_verification.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        location = get_location_from_ip(request.remote_addr)
        current_location = f"{location['city']}, {location['country']}"

        if not user:
            log_security_event(None, email, "failed_login",
                               f"Failed login for non-existent user from {current_location}",
                               request, "failure")
            flash("User not found!", "error")
            return redirect(url_for("login"))

        if user.is_locked:
            log_security_event(user.id, user.username, "locked_login",
                               f"Attempted login on locked account from {current_location}",
                               request, "failure")
            flash("Account locked! Contact support.", "error")
            return redirect(url_for("login"))

        if user.check_password(password):
            if not user.email_verified:
                flash("Please verify your email first!", "warning")
                return redirect(url_for("resend_verification"))

            warning = ""
            if user.last_login_city and user.last_login_city != location['city']:
                warning = f"⚠️ Login from new location: {current_location}"
                log_security_event(user.id, user.username, "new_location",
                                   f"Login from new location: {current_location}",
                                   request, "warning")
                print(f"⚠️ New location detected for {user.username}: {current_location}")
                send_new_location_alert(user, current_location, request.remote_addr)

            current_hour = datetime.now().hour
            if current_hour < 5 or current_hour > 23:
                warning += f"\n⏰ Unusual login time: {current_hour}:00"
                log_security_event(user.id, user.username, "unusual_time",
                                   f"Login at unusual time: {current_hour}:00",
                                   request, "warning")

            user.last_login_ip = request.remote_addr
            user.last_login_city = location['city']
            user.last_login_country = location['country']
            user.last_login_lat = location['lat']
            user.last_login_lon = location['lon']

            user.failed_attempts = 0

            log_security_event(user.id, user.username, "login",
                               f"Successful login from {current_location}",
                               request, "success")

            print(f"✅ Login successful for {user.username} from {current_location}")

            if user.is_otp_enabled and user.otp_secret:
                session["temp_user_id"] = user.id
                session["temp_username"] = user.username
                db.session.commit()
                return redirect(url_for("verify_otp"))
            else:
                session["user_id"] = user.id
                session["username"] = user.username
                user.last_login = datetime.utcnow()
                db.session.commit()

                flash(f"Welcome back, {user.username}! {warning}", "success")
                return redirect(url_for("dashboard"))
        else:
            user.failed_attempts += 1
            log_security_event(user.id, user.username, "failed_login",
                               f"Failed login attempt from {current_location}",
                               request, "failure")

            print(f"❌ Failed login for {user.username} from {current_location}")

            if user.failed_attempts >= 5:
                user.is_locked = True
                log_security_event(user.id, user.username, "account_locked",
                                   f"Account locked after {user.failed_attempts} failed attempts",
                                   request, "alert")
                flash("Account locked due to too many failed attempts!", "error")
            else:
                flash(f"Invalid credentials! Attempt {user.failed_attempts}/5", "error")

            db.session.commit()
            return redirect(url_for("login"))

    return render_template("login.html")


# =========================
# FORGOT PASSWORD
# =========================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            reset_link = url_for('reset_password', token=token, _external=True)
            try:
                msg = Message(
                    subject="🔐 Password Reset Request",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[email]
                )
                msg.html = f'<a href="{reset_link}">Reset Password</a>'
                mail.send(msg)
                flash("Password reset link sent!", "success")
            except Exception as e:
                flash("Error sending email!", "error")
        else:
            flash("Email not found!", "error")
    return render_template("forgot_password.html")


# =========================
# RESET PASSWORD
# =========================

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiry < datetime.utcnow():
        flash("Invalid or expired reset link!", "error")
        return redirect(url_for("login"))
    if request.method == "POST":
        password = request.form["password"]
        confirm = request.form["confirm_password"]
        if password != confirm:
            flash("Passwords do not match!", "error")
            return redirect(url_for("reset_password", token=token))
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        flash("Password reset successful!", "success")
        return redirect(url_for("login"))
    return render_template("reset_password.html")


# =========================
# MOBILE VERIFICATION
# =========================

@app.route("/verify-mobile", methods=["GET", "POST"])
def verify_mobile():
    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    reverify = request.args.get('reverify', 'false').lower() == 'true'
    if user.is_mobile_verified and not reverify:
        flash("Mobile already verified. Re-verify if needed.", "info")
        return render_template("verify_mobile.html", user=user, reverify=False)
    if request.method == "POST":
        if "send_otp" in request.form:
            mobile = request.form["mobile"]
            otp = str(random.randint(100000, 999999))
            user.mobile = mobile
            user.mobile_otp = otp
            user.mobile_otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            if reverify:
                user.is_mobile_verified = False
            db.session.commit()
            print(f"📱 OTP for {mobile}: {otp}")
            flash("OTP sent! Check terminal.", "success")
            return redirect(url_for("verify_mobile", reverify=reverify))
        elif "verify_otp" in request.form:
            entered = request.form["otp"]
            if user.mobile_otp == entered and user.mobile_otp_expiry > datetime.utcnow():
                user.is_mobile_verified = True
                user.mobile_otp = None
                db.session.commit()
                flash("Mobile verified successfully!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid or expired OTP!", "error")
                return redirect(url_for("verify_mobile", reverify=reverify))
        elif "resend_otp" in request.form:
            if not user.mobile:
                flash("No mobile number found.", "error")
                return redirect(url_for("verify_mobile"))
            otp = str(random.randint(100000, 999999))
            user.mobile_otp = otp
            user.mobile_otp_expiry = datetime.utcnow() + timedelta(minutes=10)
            db.session.commit()
            print(f"📱 NEW OTP for {user.mobile}: {otp}")
            flash("New OTP sent!", "success")
            return redirect(url_for("verify_mobile", reverify=reverify))
    return render_template("verify_mobile.html", user=user, reverify=reverify)


# =========================
# CHANGE PASSWORD
# =========================

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        current = request.form["current_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]
        if not user.check_password(current):
            flash("Current password is incorrect!", "error")
            return redirect(url_for("change_password"))
        if new != confirm:
            flash("New passwords do not match!", "error")
            return redirect(url_for("change_password"))
        user.set_password(new)
        db.session.commit()
        flash("Password changed successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("change_password.html")


# =========================
# SETUP OTP
# =========================

@app.route("/setup-otp", methods=["GET", "POST"])
def setup_otp():
    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.is_otp_enabled = False
        db.session.commit()
        print(f"🔐 New OTP secret generated for {user.username}")

    if request.method == "POST":
        otp = request.form["otp_code"]

        if not user.otp_secret:
            flash("Error: No OTP secret found. Please try again.", "error")
            return redirect(url_for("setup_otp"))

        try:
            if user.verify_otp(otp):
                user.is_otp_enabled = True
                db.session.commit()
                flash("✅ OTP setup successful! You'll now need OTP to login.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("❌ Invalid OTP code! Please try again.", "error")
        except Exception as e:
            print(f"OTP verification error: {e}")
            flash(f"Error verifying OTP: {e}", "error")

    otp_uri = user.get_otp_uri()

    return render_template("setup_otp.html",
                           otp_secret=user.otp_secret,
                           otp_uri=otp_uri,
                           email=user.email,
                           user=user)


# =========================
# VERIFY OTP
# =========================

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "temp_user_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))

    user = User.query.get(session["temp_user_id"])

    if not user:
        session.clear()
        flash("User not found!", "error")
        return redirect(url_for("login"))

    if not user.is_otp_enabled or not user.otp_secret:
        flash("2FA is not enabled for this account!", "warning")
        session.pop("temp_user_id", None)
        session.pop("temp_username", None)
        return redirect(url_for("login"))

    if request.method == "POST":
        otp = request.form["otp_code"]

        try:
            if user.verify_otp(otp):
                session["user_id"] = user.id
                session["username"] = user.username
                session.pop("temp_user_id", None)
                session.pop("temp_username", None)
                user.last_login = datetime.utcnow()
                db.session.commit()
                flash(f"Welcome back, {user.username}!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid OTP!", "error")
        except Exception as e:
            print(f"OTP verification error: {e}")
            flash(f"2FA error: {e}", "error")

    return render_template("verify_otp.html", email=user.email)


# =========================
# QR CODE GENERATOR
# =========================

@app.route("/qr-code")
def generate_qr():
    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found!", "error")
        return redirect(url_for("login"))

    if not user.otp_secret:
        flash("OTP not configured yet!", "error")
        return redirect(url_for("setup_otp"))

    otp_uri = user.get_otp_uri()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(otp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


# =========================
# DASHBOARDS
# =========================

@app.route("/dashboard")
@customer_required
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))

    transactions = Transaction.query.filter(
        (Transaction.from_user_id == user.id) | (Transaction.to_user_id == user.id)
    ).order_by(Transaction.timestamp.desc()).limit(10).all()

    if user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif user.role == "employee":
        return redirect(url_for("employee_dashboard"))
    else:
        return render_template("customer_dashboard.html", user=user, transactions=transactions)


@app.route("/customer-dashboard")
@customer_required
def customer_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    transactions = Transaction.query.filter(
        (Transaction.from_user_id == user.id) | (Transaction.to_user_id == user.id)
    ).order_by(Transaction.timestamp.desc()).limit(10).all()
    return render_template("customer_dashboard.html", user=user, transactions=transactions)


@app.route("/employee-dashboard")
@employee_required
def employee_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    users = User.query.all()
    return render_template("employee_dashboard.html", user=user, users=users)


@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    users = User.query.all()
    return render_template("admin_dashboard.html", user=user, users=users)


# =========================
# TRANSACTION ROUTES
# =========================

@app.route("/deposit", methods=["GET", "POST"])
@customer_required
def deposit():
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            confirm_password = request.form.get("confirm_password")

            if amount <= 0:
                flash("Amount must be positive!", "error")
                return redirect(url_for("deposit"))

            if amount > 10000:
                flash("Maximum deposit is $10,000 per transaction!", "error")
                return redirect(url_for("deposit"))

            if not user.check_password(confirm_password):
                flash("❌ Incorrect password! Transaction cancelled.", "error")
                return redirect(url_for("deposit"))

            transaction, message, needs_approval = process_transaction(
                from_user=user, to_user=None, amount=amount,
                transaction_type="deposit",
                description=f"Deposit of ${amount:.2f}",
                request=request
            )

            if needs_approval:
                flash(f"⚠️ {message}. Transaction ID: {transaction.reference_id}", "warning")
            else:
                flash(f"✅ {message}. New balance: ${user.balance:.2f}", "success")

            return redirect(url_for("dashboard"))

        except ValueError:
            flash("Invalid amount!", "error")
            return redirect(url_for("deposit"))

    return render_template("deposit.html", user=user)


@app.route("/withdraw", methods=["GET", "POST"])
@customer_required
def withdraw():
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            confirm_password = request.form.get("confirm_password")

            if amount <= 0:
                flash("Amount must be positive!", "error")
                return redirect(url_for("withdraw"))

            if not user.check_password(confirm_password):
                flash("❌ Incorrect password! Transaction cancelled.", "error")
                return redirect(url_for("withdraw"))

            allowed, message = check_limits(user, amount, 'withdraw')
            if not allowed:
                flash(message, "error")
                return redirect(url_for("withdraw"))

            transaction, message, needs_approval = process_transaction(
                from_user=user, to_user=None, amount=amount,
                transaction_type="withdraw",
                description=f"Withdrawal of ${amount:.2f}",
                request=request
            )

            if needs_approval:
                flash(f"⚠️ {message}. Transaction ID: {transaction.reference_id}", "warning")
            else:
                flash(f"✅ {message}. New balance: ${user.balance:.2f}", "success")

            return redirect(url_for("dashboard"))

        except ValueError:
            flash("Invalid amount!", "error")
            return redirect(url_for("withdraw"))

    return render_template("withdraw.html", user=user)


@app.route("/transfer", methods=["GET", "POST"])
@customer_required
def transfer():
    user = User.query.get(session["user_id"])
    users = User.query.filter(User.id != user.id).all()

    if request.method == "POST":
        try:
            recipient_id = int(request.form["recipient_id"])
            amount = float(request.form["amount"])
            description = request.form.get("description", "")
            confirm_password = request.form.get("confirm_password")

            recipient = User.query.get(recipient_id)
            if not recipient:
                flash("Recipient not found!", "error")
                return redirect(url_for("transfer"))

            if amount <= 0:
                flash("Amount must be positive!", "error")
                return redirect(url_for("transfer"))

            if recipient.id == user.id:
                flash("Cannot transfer to yourself!", "error")
                return redirect(url_for("transfer"))

            if not user.check_password(confirm_password):
                flash("❌ Incorrect password! Transaction cancelled.", "error")
                return redirect(url_for("transfer"))

            allowed, message = check_limits(user, amount, 'transfer')
            if not allowed:
                flash(message, "error")
                return redirect(url_for("transfer"))

            transaction, message, needs_approval = process_transaction(
                from_user=user, to_user=recipient, amount=amount,
                transaction_type="transfer",
                description=f"Transfer to {recipient.username}: {description}" if description else f"Transfer to {recipient.username}",
                request=request, recipient=recipient
            )

            if needs_approval:
                flash(f"⚠️ {message}. Transaction ID: {transaction.reference_id}", "warning")
            else:
                flash(f"✅ {message} to {recipient.username}! Check your email for receipts.", "success")

            return redirect(url_for("dashboard"))

        except (ValueError, KeyError):
            flash("Invalid input!", "error")
            return redirect(url_for("transfer"))

    return render_template("transfer.html", user=user, users=users)


@app.route("/transactions")
@customer_required
def transactions():
    user = User.query.get(session["user_id"])
    all_transactions = Transaction.query.filter(
        (Transaction.from_user_id == user.id) | (Transaction.to_user_id == user.id)
    ).order_by(Transaction.timestamp.desc()).all()
    return render_template("transactions.html", user=user, transactions=all_transactions)


# =========================
# BIOMETRIC FOR TRANSACTIONS
# =========================

@app.route("/webauthn/transaction/begin", methods=["POST"])
@customer_required
def webauthn_transaction_begin():
    user = User.query.get(session["user_id"])
    current_host = request.host.split(':')[0]

    transaction_data = request.get_json()
    session['pending_transaction'] = transaction_data

    print(f"🔐 Starting biometric verification for transaction: {transaction_data.get('type')} of ${transaction_data.get('amount')}")

    if not user.webauthn_credential_id:
        return jsonify({"success": False, "error": "No biometric registered. Please use password.", "fallback": True})

    options = generate_authentication_options(
        rp_id=current_host,
        user_verification=UserVerificationRequirement.PREFERRED,
        allow_credentials=[{"id": user.webauthn_credential_id, "type": "public-key"}]
    )

    session["webauthn_transaction_challenge"] = options.challenge

    allow_credentials_list = []
    if options.allow_credentials:
        for cred in options.allow_credentials:
            if hasattr(cred, 'id'):
                allow_credentials_list.append({
                    "id": bytes_to_base64url(cred.id),
                    "type": cred.type if hasattr(cred, 'type') else "public-key"
                })

    response = {
        "challenge": bytes_to_base64url(options.challenge),
        "timeout": options.timeout,
        "rpId": options.rp_id,
        "allowCredentials": allow_credentials_list,
        "userVerification": options.user_verification.value
    }
    return jsonify(response)


@app.route("/webauthn/transaction/complete", methods=["POST"])
@customer_required
def webauthn_transaction_complete():
    user = User.query.get(session["user_id"])
    data = request.get_json()

    current_host = request.host.split(':')[0]
    origin = f"https://{current_host}" if current_host != 'localhost' else "http://localhost:5000"

    try:
        original_challenge = session.get("webauthn_transaction_challenge")
        if not original_challenge:
            return jsonify({"success": False, "error": "No verification in progress"}), 400

        if not user.webauthn_credential_id:
            return jsonify({"success": False, "error": "No biometric registered", "fallback": True}), 400

        verification = verify_authentication_response(
            credential=data,
            expected_challenge=original_challenge,
            expected_rp_id=current_host,
            expected_origin=origin,
            credential_public_key=user.webauthn_public_key,
            credential_current_sign_count=user.webauthn_sign_count
        )

        user.webauthn_sign_count = verification.new_sign_count
        db.session.commit()

        session.pop("webauthn_transaction_challenge", None)

        transaction_data = session.get('pending_transaction')
        if transaction_data:
            session.pop('pending_transaction', None)
            result = process_transaction_with_data(user, transaction_data, request)
            if result.get("success"):
                return jsonify({"success": True, "redirect": url_for("dashboard")})
            else:
                return jsonify({"success": False, "error": result.get("message")}), 400

        return jsonify({"success": True, "message": "Biometric verification successful!"})

    except Exception as e:
        print(f"❌ Transaction biometric error: {e}")
        return jsonify({"success": False, "error": str(e), "fallback": True}), 400


# =========================
# ADMIN TRANSACTION MANAGEMENT
# =========================

@app.route("/admin/transactions")
@admin_required
def admin_transactions():
    pending = Transaction.query.filter_by(status='pending').order_by(Transaction.timestamp.desc()).all()
    completed = Transaction.query.filter_by(status='completed').order_by(Transaction.timestamp.desc()).limit(50).all()
    failed = Transaction.query.filter_by(status='failed').order_by(Transaction.timestamp.desc()).limit(20).all()
    return render_template("admin_transactions.html", pending=pending, completed=completed, failed=failed)


@app.route("/admin/transaction/<int:transaction_id>/approve", methods=["POST"])
@admin_required
def approve_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    admin = User.query.get(session["user_id"])
    if transaction.status != 'pending':
        flash("Transaction is not pending!", "error")
        return redirect(url_for("admin_transactions"))

    if transaction.type == 'withdraw':
        from_user = transaction.from_user
        from_user.balance -= transaction.amount
        from_user.daily_transaction_total += transaction.amount
        from_user.monthly_transaction_total += transaction.amount
    elif transaction.type == 'transfer':
        from_user = transaction.from_user
        to_user = transaction.to_user
        from_user.balance -= transaction.amount
        to_user.balance += transaction.amount
        from_user.daily_transaction_total += transaction.amount
        from_user.monthly_transaction_total += transaction.amount
    elif transaction.type == 'deposit':
        to_user = transaction.to_user
        to_user.balance += transaction.amount

    transaction.status = 'completed'
    transaction.approved_by = admin.id
    transaction.approved_at = datetime.utcnow()
    db.session.commit()

    log_security_event(admin.id, admin.username, "transaction_approved",
                       f"Approved transaction {transaction.reference_id} for ${transaction.amount:.2f}",
                       request, "success")

    if transaction.from_user:
        send_transaction_confirmation(transaction.from_user, transaction.type, transaction.amount,
                                      transaction.reference_id)

    flash(f"✅ Transaction {transaction.reference_id} approved successfully!", "success")
    return redirect(url_for("admin_transactions"))


@app.route("/admin/transaction/<int:transaction_id>/reject", methods=["POST"])
@admin_required
def reject_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    admin = User.query.get(session["user_id"])
    if transaction.status != 'pending':
        flash("Transaction is not pending!", "error")
        return redirect(url_for("admin_transactions"))

    transaction.status = 'failed'
    transaction.approved_by = admin.id
    transaction.approved_at = datetime.utcnow()
    transaction.notes = request.form.get("notes", "")
    db.session.commit()

    log_security_event(admin.id, admin.username, "transaction_rejected",
                       f"Rejected transaction {transaction.reference_id} for ${transaction.amount:.2f}",
                       request, "warning")

    if transaction.from_user:
        try:
            msg = Message(
                subject=f"❌ Transaction Rejected - {transaction.reference_id}",
                sender=app.config['MAIL_USERNAME'],
                recipients=[transaction.from_user.email]
            )
            msg.body = f"""Your transaction has been rejected.

Transaction Reference: {transaction.reference_id}
Amount: ${transaction.amount:.2f}
Type: {transaction.type}
Reason: {transaction.notes or 'Risk threshold exceeded'}

If you believe this is an error, please contact support.
"""
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send rejection email: {e}")

    flash(f"❌ Transaction {transaction.reference_id} rejected!", "warning")
    return redirect(url_for("admin_transactions"))


@app.route("/admin/transaction/<int:transaction_id>/details")
@admin_required
def transaction_details(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    return jsonify({
        'id': transaction.id,
        'reference_id': transaction.reference_id,
        'type': transaction.type,
        'amount': transaction.amount,
        'status': transaction.status,
        'risk_score': transaction.risk_score,
        'from_user': transaction.from_user.username if transaction.from_user else None,
        'to_user': transaction.to_user.username if transaction.to_user else None,
        'location_city': transaction.location_city,
        'location_country': transaction.location_country,
        'ip_address': transaction.ip_address,
        'description': transaction.description,
        'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'approved_by': transaction.approver.username if transaction.approver else None,
        'approved_at': transaction.approved_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.approved_at else None,
        'notes': transaction.notes
    })


# =========================
# ADMIN SECURITY DASHBOARD
# =========================

@app.route("/admin/security-dashboard")
@admin_required
def admin_security_dashboard():
    total_logs = SecurityLog.query.count()
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    failed_logins_today = SecurityLog.query.filter(
        SecurityLog.action == 'failed_login',
        SecurityLog.timestamp >= today
    ).count()
    suspicious_events = SecurityLog.query.filter(
        SecurityLog.status.in_(['warning', 'alert'])
    ).order_by(SecurityLog.timestamp.desc()).limit(20).all()
    recent_logs = SecurityLog.query.order_by(SecurityLog.timestamp.desc()).limit(50).all()
    users = User.query.filter(User.registration_city.isnot(None)).all()
    location_alerts = []
    for u in users:
        if u.last_login_city and u.registration_city != u.last_login_city:
            location_alerts.append({
                'user': u.username,
                'registered': f"{u.registration_city}, {u.registration_country}",
                'last_login': f"{u.last_login_city}, {u.last_login_country}"
            })
    return render_template("admin_security_dashboard.html",
                           total_logs=total_logs,
                           failed_logins_today=failed_logins_today,
                           suspicious_events=suspicious_events,
                           recent_logs=recent_logs,
                           location_alerts=location_alerts)


# =========================
# ADMIN USER MANAGEMENT
# =========================

@app.route("/admin/user/<int:user_id>")
@admin_required
def admin_view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("admin_view_user.html", user=user)


@app.route("/admin/user/<int:user_id>/role", methods=["POST"])
@admin_required
def admin_change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form["role"]
    if new_role in ["customer", "employee", "admin"]:
        user.role = new_role
        db.session.commit()
        flash(f"User {user.username} role changed to {new_role}", "success")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/verify-email", methods=["POST"])
@admin_required
def admin_verify_email(user_id):
    user = User.query.get_or_404(user_id)
    user.email_verified = True
    db.session.commit()
    flash(f"Email for {user.username} has been verified!", "success")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/unverify-email", methods=["POST"])
@admin_required
def admin_unverify_email(user_id):
    user = User.query.get_or_404(user_id)
    user.email_verified = False
    db.session.commit()
    flash(f"Email for {user.username} has been unverified!", "warning")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/verify-mobile", methods=["POST"])
@admin_required
def admin_verify_mobile(user_id):
    user = User.query.get_or_404(user_id)
    user.is_mobile_verified = True
    db.session.commit()
    flash(f"Mobile for {user.username} has been verified!", "success")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/unverify-mobile", methods=["POST"])
@admin_required
def admin_unverify_mobile(user_id):
    user = User.query.get_or_404(user_id)
    user.is_mobile_verified = False
    db.session.commit()
    flash(f"Mobile for {user.username} has been unverified!", "warning")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/enable-2fa", methods=["POST"])
@admin_required
def admin_enable_2fa(user_id):
    user = User.query.get_or_404(user_id)
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.is_otp_enabled = False
        db.session.commit()
        flash(f"2FA setup initiated for {user.username}. Please scan the QR code.", "info")
    session["admin_setup_user_id"] = user.id
    return redirect(url_for("admin_setup_user_otp", user_id=user.id))


@app.route("/admin/user/<int:user_id>/disable-2fa", methods=["POST"])
@admin_required
def admin_disable_2fa(user_id):
    user = User.query.get_or_404(user_id)
    user.is_otp_enabled = False
    db.session.commit()
    flash(f"2FA for {user.username} has been disabled!", "warning")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/setup-otp/<int:user_id>", methods=["GET", "POST"])
@admin_required
def admin_setup_user_otp(user_id):
    user = User.query.get_or_404(user_id)
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.is_otp_enabled = False
        db.session.commit()
    if request.method == "POST":
        otp = request.form["otp_code"]
        try:
            if user.verify_otp(otp):
                user.is_otp_enabled = True
                db.session.commit()
                flash(f"✅ 2FA successfully enabled for {user.username}!", "success")
                return redirect(url_for("admin_view_user", user_id=user.id))
            else:
                flash("❌ Invalid OTP code! Please try again.", "error")
        except Exception as e:
            flash(f"Error: {e}", "error")
    otp_uri = user.get_otp_uri()
    return render_template("admin_setup_otp.html",
                           otp_secret=user.otp_secret,
                           otp_uri=otp_uri,
                           email=user.email,
                           username=user.username,
                           user=user)


@app.route("/admin/user/<int:user_id>/enable-biometric", methods=["POST"])
@admin_required
def admin_enable_biometric(user_id):
    user = User.query.get_or_404(user_id)
    flash(f"Biometric registration must be done by {user.username} from their dashboard.", "info")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/disable-biometric", methods=["POST"])
@admin_required
def admin_disable_biometric(user_id):
    user = User.query.get_or_404(user_id)
    user.webauthn_credential_id = None
    user.webauthn_public_key = None
    user.webauthn_sign_count = 0
    db.session.commit()
    flash(f"Biometric authentication for {user.username} has been disabled!", "warning")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/lock", methods=["POST"])
@admin_required
def admin_lock_account(user_id):
    user = User.query.get_or_404(user_id)
    user.is_locked = True
    db.session.commit()
    flash(f"Account for {user.username} has been locked!", "warning")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/unlock", methods=["POST"])
@admin_required
def admin_unlock_account(user_id):
    user = User.query.get_or_404(user_id)
    user.is_locked = False
    user.failed_attempts = 0
    db.session.commit()
    flash(f"Account for {user.username} has been unlocked!", "success")
    return redirect(url_for("admin_view_user", user_id=user.id))


@app.route("/admin/user/<int:user_id>/reset-failed-attempts", methods=["POST"])
@admin_required
def admin_reset_failed_attempts(user_id):
    user = User.query.get_or_404(user_id)
    user.failed_attempts = 0
    db.session.commit()
    flash(f"Failed attempts for {user.username} have been reset!", "success")
    return redirect(url_for("admin_view_user", user_id=user.id))


# =========================
# WEBAUTHN REGISTRATION & LOGIN
# =========================

@app.route("/webauthn/register/begin", methods=["POST"])
@customer_required
def webauthn_register_begin():
    user = User.query.get(session["user_id"])
    current_host = request.host.split(':')[0]
    print(f"🔐 Starting biometric registration for: {user.username} on {current_host}")

    options = generate_registration_options(
        rp_id=current_host,
        rp_name="Zero Trust Bank",
        user_id=str(user.id).encode('utf-8'),
        user_name=user.username,
        user_display_name=user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            user_verification=UserVerificationRequirement.PREFERRED,
            resident_key="preferred"
        ),
    )
    session["webauthn_registration_challenge"] = options.challenge

    response = {
        "rp": {"id": options.rp.id, "name": options.rp.name},
        "user": {
            "id": bytes_to_base64url(options.user.id),
            "name": options.user.name,
            "displayName": options.user.display_name
        },
        "challenge": bytes_to_base64url(options.challenge),
        "pubKeyCredParams": [
            {"type": p.type, "alg": p.alg} for p in options.pub_key_cred_params
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": options.authenticator_selection.authenticator_attachment.value,
            "userVerification": options.authenticator_selection.user_verification.value,
            "residentKey": options.authenticator_selection.resident_key
        },
        "timeout": options.timeout,
        "attestation": options.attestation,
        "excludeCredentials": [
            {
                "id": bytes_to_base64url(cred.credential_id),
                "type": cred.type
            } for cred in options.exclude_credentials
        ] if options.exclude_credentials else []
    }
    return jsonify(response)


@app.route("/webauthn/register/complete", methods=["POST"])
@customer_required
def webauthn_register_complete():
    user = User.query.get(session["user_id"])
    data = request.get_json()
    current_host = request.host.split(':')[0]
    origin = f"https://{current_host}" if current_host != 'localhost' else "http://localhost:5000"

    try:
        original_challenge = session.get("webauthn_registration_challenge")
        if not original_challenge:
            return jsonify({"success": False, "error": "No registration in progress"}), 400

        verification = verify_registration_response(
            credential=data,
            expected_challenge=original_challenge,
            expected_rp_id=current_host,
            expected_origin=origin
        )
        user.webauthn_credential_id = verification.credential_id
        user.webauthn_public_key = verification.credential_public_key
        user.webauthn_sign_count = verification.sign_count
        db.session.commit()
        session.pop("webauthn_registration_challenge", None)

        print(f"✅ Biometric registration successful for {user.username} on {current_host}")
        return jsonify({"success": True, "message": "Biometric authentication enabled!"})

    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/webauthn/login/begin", methods=["POST"])
def webauthn_login_begin():
    data = request.get_json()
    login_value = data.get("username")
    current_host = request.host.split(':')[0]
    print(f"🔐 Login attempt with: {login_value} on {current_host}")

    user = User.query.filter_by(username=login_value).first()
    if not user:
        user = User.query.filter_by(email=login_value).first()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    if not user.webauthn_credential_id:
        return jsonify({"success": False, "error": "No biometric credentials found"}), 404

    credential_bytes = user.webauthn_credential_id
    options = generate_authentication_options(
        rp_id=current_host,
        user_verification=UserVerificationRequirement.PREFERRED,
        allow_credentials=[{"id": credential_bytes, "type": "public-key"}]
    )
    session["webauthn_login_challenge"] = options.challenge
    session["webauthn_login_user_id"] = user.id

    allow_credentials_list = []
    if options.allow_credentials:
        for cred in options.allow_credentials:
            if hasattr(cred, 'id'):
                allow_credentials_list.append({
                    "id": bytes_to_base64url(cred.id),
                    "type": cred.type if hasattr(cred, 'type') else "public-key"
                })

    response = {
        "challenge": bytes_to_base64url(options.challenge),
        "timeout": options.timeout,
        "rpId": options.rp_id,
        "allowCredentials": allow_credentials_list,
        "userVerification": options.user_verification.value
    }
    return jsonify(response)


@app.route("/webauthn/login/complete", methods=["POST"])
def webauthn_login_complete():
    data = request.get_json()
    current_host = request.host.split(':')[0]
    origin = f"https://{current_host}" if current_host != 'localhost' else "http://localhost:5000"

    try:
        original_challenge = session.get("webauthn_login_challenge")
        user_id = session.get("webauthn_login_user_id")
        if not original_challenge or not user_id:
            return jsonify({"success": False, "error": "No login in progress"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        verification = verify_authentication_response(
            credential=data,
            expected_challenge=original_challenge,
            expected_rp_id=current_host,
            expected_origin=origin,
            credential_public_key=user.webauthn_public_key,
            credential_current_sign_count=user.webauthn_sign_count
        )
        user.webauthn_sign_count = verification.new_sign_count
        db.session.commit()

        session.pop("webauthn_login_challenge", None)
        session.pop("webauthn_login_user_id", None)
        session["user_id"] = user.id
        session["username"] = user.username
        return jsonify({"success": True, "redirect": url_for("dashboard")})

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


# =========================
# LOGOUT, DISABLE OTP, MAKE ADMIN, TEST ROUTES
# =========================

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/disable-otp", methods=["POST"])
def disable_otp():
    if "user_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    user.is_otp_enabled = False
    db.session.commit()
    flash("OTP disabled successfully!", "success")
    return redirect(url_for("dashboard"))


@app.route("/make-me-admin")
def make_me_admin():
    if "user_id" not in session:
        return "Please login first"
    user = User.query.get(session["user_id"])
    user.role = "admin"
    db.session.commit()
    return f"✅ User {user.username} is now an ADMIN! <a href='/dashboard'>Go to Dashboard</a>"


@app.route("/test-email")
def test_email():
    try:
        msg = Message(
            subject="Test Email",
            sender=app.config['MAIL_USERNAME'],
            recipients=[app.config['MAIL_USERNAME']]
        )
        msg.body = "Test email from Flask app."
        mail.send(msg)
        return "<h2>✅ Email Test Successful!</h2>"
    except Exception as e:
        return f"<h2>❌ Email Test Failed: {e}</h2>"


@app.route("/create-test-user")
def create_test_user():
    test_user = User.query.filter_by(email="test@example.com").first()
    if test_user:
        return "Test user already exists! Email: test@example.com, Password: Test123!"
    new_user = User(
        username="testuser",
        email="test@example.com",
        mobile="+1234567890",
        role="customer",
        balance=1000.00
    )
    new_user.set_password("Test123!")
    new_user.email_verified = True
    new_user.is_mobile_verified = True
    db.session.add(new_user)
    db.session.commit()
    return "<h2>✅ Test User Created!</h2><p>Email: test@example.com<br>Password: Test123!</p>"


@app.route("/show-otp")
def show_otp():
    if "user_id" not in session:
        return "Please login first"
    user = User.query.get(session["user_id"])
    if user.mobile_otp:
        return f"Your OTP is: <strong>{user.mobile_otp}</strong>"
    return "No OTP found."


# =========================
# UPDATE DATABASE
# =========================

@app.route("/update-db")
def update_db():
    try:
        import sqlalchemy as sa
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]

        # Add missing columns if needed
        if 'webauthn_credential_id' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN webauthn_credential_id BLOB NULL')
        if 'webauthn_public_key' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN webauthn_public_key BLOB NULL')
        if 'webauthn_sign_count' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN webauthn_sign_count INT DEFAULT 0')
        if 'registration_ip' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN registration_ip VARCHAR(45) NULL')
        if 'registration_city' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN registration_city VARCHAR(100) NULL')
        if 'registration_country' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN registration_country VARCHAR(100) NULL')
        if 'registration_lat' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN registration_lat FLOAT NULL')
        if 'registration_lon' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN registration_lon FLOAT NULL')
        if 'last_login_ip' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN last_login_ip VARCHAR(45) NULL')
        if 'last_login_city' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN last_login_city VARCHAR(100) NULL')
        if 'last_login_country' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN last_login_country VARCHAR(100) NULL')
        if 'last_login_lat' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN last_login_lat FLOAT NULL')
        if 'last_login_lon' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN last_login_lon FLOAT NULL')
        if 'known_ips' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN known_ips TEXT NULL')
        if 'balance' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN balance FLOAT DEFAULT 1000.00')
        if 'daily_transaction_total' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN daily_transaction_total FLOAT DEFAULT 0')
        if 'daily_transaction_date' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN daily_transaction_date DATE')
        if 'monthly_transaction_total' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN monthly_transaction_total FLOAT DEFAULT 0')
        if 'monthly_transaction_date' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN monthly_transaction_date DATE')
        if 'daily_limit' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN daily_limit FLOAT DEFAULT 500.00')
        if 'monthly_limit' not in columns:
            db.session.execute('ALTER TABLE user ADD COLUMN monthly_limit FLOAT DEFAULT 5000.00')

        db.session.execute('UPDATE user SET balance = 1000.00 WHERE balance IS NULL')
        db.session.execute('UPDATE user SET daily_transaction_date = CURDATE() WHERE daily_transaction_date IS NULL')
        db.session.execute('UPDATE user SET monthly_transaction_date = CURDATE() WHERE monthly_transaction_date IS NULL')
        db.session.execute('UPDATE user SET daily_limit = 500.00 WHERE daily_limit IS NULL')
        db.session.execute('UPDATE user SET monthly_limit = 5000.00 WHERE monthly_limit IS NULL')
        db.session.execute('UPDATE user SET daily_transaction_total = 0 WHERE daily_transaction_total IS NULL')
        db.session.execute('UPDATE user SET monthly_transaction_total = 0 WHERE monthly_transaction_total IS NULL')

        if not inspector.has_table('transactions'):
            db.session.execute('''
                               CREATE TABLE IF NOT EXISTS transactions
                               (
                                   id INT AUTO_INCREMENT PRIMARY KEY,
                                   from_user_id INT NULL,
                                   to_user_id INT NULL,
                                   amount FLOAT NOT NULL,
                                   type VARCHAR(50),
                                   description VARCHAR(200),
                                   status VARCHAR(50) DEFAULT 'pending',
                                   reference_id VARCHAR(50) UNIQUE,
                                   ip_address VARCHAR(45),
                                   location_city VARCHAR(100),
                                   location_country VARCHAR(100),
                                   risk_score INT DEFAULT 0,
                                   approved_by INT NULL,
                                   approved_at DATETIME NULL,
                                   notes TEXT NULL,
                                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                   FOREIGN KEY (from_user_id) REFERENCES user(id) ON DELETE SET NULL,
                                   FOREIGN KEY (to_user_id) REFERENCES user(id) ON DELETE SET NULL,
                                   FOREIGN KEY (approved_by) REFERENCES user(id) ON DELETE SET NULL
                               )
                               ''')
            print("✅ Created enhanced transactions table")

        if not inspector.has_table('security_logs'):
            db.session.execute('''
                               CREATE TABLE IF NOT EXISTS security_logs
                               (
                                   id INT AUTO_INCREMENT PRIMARY KEY,
                                   user_id INT,
                                   username VARCHAR(100),
                                   action VARCHAR(100),
                                   details TEXT,
                                   ip_address VARCHAR(45),
                                   user_agent VARCHAR(200),
                                   status VARCHAR(20),
                                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                   FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
                               )
                               ''')
            print("✅ Created security_logs table")

        db.session.commit()
        return "<h2>✅ Database updated! Enhanced transaction system ready.</h2>"
    except Exception as e:
        return f"<h2>❌ Error: {e}</h2>"


# =========================
# CONTEXT PROCESSOR & NEW ROUTES
# =========================

@app.context_processor
def inject_now():
    """Make datetime and now available in all templates"""
    return {
        'now': datetime.now(),
        'datetime': datetime
    }


@app.route("/ping-session")
@customer_required
def ping_session():
    """Keep session alive"""
    return jsonify({"success": True})


@app.route("/freeze-account", methods=["POST"])
@customer_required
def freeze_account():
    """Allow user to freeze their account"""
    user = User.query.get(session["user_id"])
    user.is_frozen = not getattr(user, 'is_frozen', False)
    db.session.commit()

    status = "frozen" if user.is_frozen else "unfrozen"
    flash(f"Your account has been {status}!", "success")
    return redirect(url_for("dashboard"))


def add_frozen_column():
    """Add is_frozen column to user table if not exists"""
    try:
        db.session.execute('ALTER TABLE user ADD COLUMN is_frozen BOOLEAN DEFAULT FALSE')
        db.session.commit()
        print("✅ Added is_frozen column to user table")
    except Exception as e:
        pass


with app.app_context():
    add_frozen_column()


# =========================
# CREATE DATABASE TABLES & RUN APP
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database tables created/verified!")
        print("✅ Database: zero_trust_db")
        print("✅ Table: user")
        print("✅ Table: security_logs")
        print("✅ Table: transactions")
        print("✅ OTP Multi-Factor Authentication ready!")
        print("✅ QR code generator ready!")
        print("✅ Email notifications ready!")
        print("✅ Mobile verification ready!")
        print("✅ Password reset ready!")
        print("✅ Email verification ready!")
        print("✅ Role-Based Access Control (RBAC) ready!")
        print("✅ Separate dashboards for Customer, Employee, Admin!")
        print("✅ Admin full user management ready!")
        print("✅ WebAuthn (Biometric Authentication) ready!")
        print("✅ Location Tracking (IP Geolocation) ready!")
        print("✅ Security Logs (Audit Trail) ready!")
        print("✅ Enhanced Transaction System ready!")
        print("✅ Risk Scoring & Pending Approval ready!")
        print("✅ Twilio Verify Service ready!")
        print("✅ Biometric Transaction Verification ready!")
        print("✅ ENHANCED EMAIL RECEIPTS ready!")
        print("   - Separate Confirmation and Detailed Receipt emails")
        print("   - Full transaction details including limits, location, risk score")
        print("   - Emails for sender AND recipient on transfers")

    app.run(debug=True, host='localhost')