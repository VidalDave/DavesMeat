import logging
import os
import smtplib
from decimal import Decimal
from email.message import EmailMessage

from app.models import Order


logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        logger.warning("%s is invalid; using %s", name, default)
        return default


def notification_recipient(setting_email: str | None = None) -> str:
    return (setting_email or os.getenv("ORDER_NOTIFICATION_EMAIL") or "").strip()


def send_new_order_email(order: Order, setting_email: str | None = None) -> bool:
    recipient = notification_recipient(setting_email)
    if not recipient:
        logger.info("Order notification email skipped: ORDER_NOTIFICATION_EMAIL is not configured")
        return False

    host = os.getenv("SMTP_HOST", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    if not host or not from_email:
        logger.warning("Order notification email skipped: SMTP_HOST or SMTP_FROM_EMAIL is missing")
        return False

    port = _env_int("SMTP_PORT", 587)
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    use_tls = _env_bool("SMTP_USE_TLS", True)

    message = EmailMessage()
    message["Subject"] = "New order received"
    message["From"] = from_email
    message["To"] = recipient
    message.set_content(_order_email_body(order))

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if use_tls:
                smtp.starttls()
            if username:
                smtp.login(username, password)
            smtp.send_message(message)
        logger.info("Order notification email sent for order_id=%s to %s", order.id, recipient)
        return True
    except Exception:
        logger.exception("Failed to send order notification email for order_id=%s", order.id)
        return False


def _order_email_body(order: Order) -> str:
    lines = [
        f"Order ID: {order.id}",
        f"Customer full name: {order.full_name}",
        f"Phone: {order.phone}",
        f"Location: {order.location.name if order.location else order.location_id}",
        f"Supply/delivery date: {order.delivery_date}",
        "",
        "Products:",
    ]

    total = Decimal("0")
    for item in order.items:
        line_total = Decimal(item.unit_price) * item.quantity
        total += line_total
        lines.append(f"- {item.product_name}: quantity {item.quantity}, unit price {item.unit_price}, total {line_total}")

    lines.extend(["", f"Total price: {total}", f"Order created date/time: {order.created_at}"])
    return "\n".join(lines)
