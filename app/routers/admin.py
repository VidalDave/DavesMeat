from datetime import datetime
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import re
import shutil
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import authenticate_user, hash_password, require_admin_user, require_role
from app.database import get_db
from app.models import DeliverySetting, Location, Order, OrderItem, Product, User


ADMIN_PREFIX = "/ddavedata"
UPLOAD_DIR = Path("storage/static/uploads/products")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

router = APIRouter(prefix=ADMIN_PREFIX)
templates = Jinja2Templates(directory="app/templates")

ORDER_STATUSES = {
    "new": "חדש",
    "confirmed": "מאושר",
    "delivered": "נמסר",
    "paid": "שולם",
    "cancelled": "בוטל",
}
ROLES = {"admin": "Admin", "order_manager": "Order Manager"}
WEEKDAYS = [(0, "ראשון"), (1, "שני"), (2, "שלישי"), (3, "רביעי"), (4, "חמישי"), (5, "שישי"), (6, "שבת")]


def admin_context(request: Request, db: Session) -> dict:
    user = require_admin_user(request, db)
    return {"request": request, "user": user, "statuses": ORDER_STATUSES, "roles": ROLES, "admin_prefix": ADMIN_PREFIX}


def save_uploaded_product_image(upload: UploadFile | None) -> str | None:
    if not upload or not upload.filename:
        return None

    original_name = Path(upload.filename).name
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="סוג קובץ תמונה לא נתמך")

    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", Path(original_name).stem).strip("-") or "product"
    filename = f"{safe_stem}-{uuid4().hex}.{extension}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIR / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return f"/storage/static/uploads/products/{filename}"


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": ""})


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username.strip(), password)
    if not user:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "שם משתמש או סיסמה שגויים"}, status_code=401)
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse(ADMIN_PREFIX, status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(f"{ADMIN_PREFIX}/login", status_code=303)


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    context = admin_context(request, db)
    context.update(
        {
            "orders_count": db.query(Order).count(),
            "new_orders": db.query(Order).filter(Order.status == "new").count(),
            "products_count": db.query(Product).count(),
            "locations_count": db.query(Location).count(),
        }
    )
    return templates.TemplateResponse("admin_dashboard.html", context)


@router.get("/orders", response_class=HTMLResponse)
def orders(
    request: Request,
    status: str = "",
    delivery_date: str = "",
    product_id: str = "",
    location_id: str = "",
    phone: str = "",
    db: Session = Depends(get_db),
):
    context = admin_context(request, db)
    query = db.query(Order).options(joinedload(Order.location), joinedload(Order.items)).order_by(Order.created_at.desc())
    if status:
        query = query.filter(Order.status == status)
    if delivery_date:
        query = query.filter(Order.delivery_date == datetime.strptime(delivery_date, "%Y-%m-%d").date())
    if location_id:
        query = query.filter(Order.location_id == int(location_id))
    if phone:
        query = query.filter(Order.phone.contains(phone.strip()))
    if product_id:
        query = query.join(OrderItem).filter(OrderItem.product_id == int(product_id))
    context.update(
        {
            "orders": query.all(),
            "products": db.query(Product).order_by(Product.name).all(),
            "locations": db.query(Location).order_by(Location.name).all(),
            "filters": {"status": status, "delivery_date": delivery_date, "product_id": product_id, "location_id": location_id, "phone": phone},
        }
    )
    return templates.TemplateResponse("admin_orders.html", context)


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def order_detail(order_id: int, request: Request, db: Session = Depends(get_db)):
    context = admin_context(request, db)
    order = db.query(Order).options(joinedload(Order.location), joinedload(Order.items)).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    context["order"] = order
    return templates.TemplateResponse("admin_order_detail.html", context)


@router.post("/orders/{order_id}")
def update_order(order_id: int, request: Request, status: str = Form(...), admin_note: str = Form(""), db: Session = Depends(get_db)):
    admin_context(request, db)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    if status not in ORDER_STATUSES:
        raise HTTPException(status_code=400)
    order.status = status
    order.admin_note = admin_note.strip()
    db.commit()
    return RedirectResponse(f"{ADMIN_PREFIX}/orders/{order.id}", status_code=303)


@router.get("/products", response_class=HTMLResponse)
def products(request: Request, db: Session = Depends(get_db)):
    context = admin_context(request, db)
    require_role(context["user"], {"admin"})
    context["products"] = db.query(Product).order_by(Product.name).all()
    return templates.TemplateResponse("admin_products.html", context)


@router.post("/products")
def save_product(
    request: Request,
    product_id: str = Form(""),
    name: str = Form(...),
    image_url: str = Form(""),
    image_file: UploadFile | None = File(None),
    weight: str = Form(...),
    price: str = Form(...),
    features: str = Form(""),
    is_active: str = Form("off"),
    db: Session = Depends(get_db),
):
    context = admin_context(request, db)
    require_role(context["user"], {"admin"})
    try:
        parsed_price = Decimal(price)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="מחיר לא תקין")
    if parsed_price <= 0:
        raise HTTPException(status_code=400, detail="מחיר חייב להיות גדול מאפס")
    product = db.query(Product).filter(Product.id == int(product_id)).first() if product_id else Product()
    if not product:
        raise HTTPException(status_code=404)
    image_path = save_uploaded_product_image(image_file)
    if not image_url.strip() and not image_path and not getattr(product, "image_path", None):
        raise HTTPException(status_code=400, detail="נדרשת תמונת מוצר או כתובת תמונה")
    product.name = name.strip()
    product.image_url = image_url.strip()
    if image_path:
        product.image_path = image_path
    product.weight = weight.strip()
    product.price = parsed_price
    product.features = features.strip()
    product.is_active = is_active == "on"
    db.add(product)
    db.commit()
    return RedirectResponse(f"{ADMIN_PREFIX}/products", status_code=303)


@router.get("/locations", response_class=HTMLResponse)
def locations(request: Request, db: Session = Depends(get_db)):
    context = admin_context(request, db)
    require_role(context["user"], {"admin"})
    context["locations"] = db.query(Location).order_by(Location.name).all()
    return templates.TemplateResponse("admin_locations.html", context)


@router.post("/locations")
def save_location(request: Request, location_id: str = Form(""), name: str = Form(...), is_active: str = Form("off"), db: Session = Depends(get_db)):
    context = admin_context(request, db)
    require_role(context["user"], {"admin"})
    location = db.query(Location).filter(Location.id == int(location_id)).first() if location_id else Location()
    location.name = name.strip()
    location.is_active = is_active == "on"
    db.add(location)
    db.commit()
    return RedirectResponse(f"{ADMIN_PREFIX}/locations", status_code=303)


@router.get("/users", response_class=HTMLResponse)
def users(request: Request, db: Session = Depends(get_db)):
    context = admin_context(request, db)
    require_role(context["user"], {"admin"})
    context["users"] = db.query(User).order_by(User.username).all()
    return templates.TemplateResponse("admin_users.html", context)


@router.post("/users")
def save_user(
    request: Request,
    user_id: str = Form(""),
    username: str = Form(...),
    role: str = Form(...),
    password: str = Form(""),
    is_active: str = Form("off"),
    db: Session = Depends(get_db),
):
    context = admin_context(request, db)
    require_role(context["user"], {"admin"})
    if role not in ROLES:
        raise HTTPException(status_code=400)
    user = db.query(User).filter(User.id == int(user_id)).first() if user_id else User()
    user.username = username.strip()
    user.role = role
    user.is_active = is_active == "on"
    if password:
        user.password_hash = hash_password(password)
    elif not user_id:
        raise HTTPException(status_code=400, detail="נדרשת סיסמה")
    db.add(user)
    db.commit()
    return RedirectResponse(f"{ADMIN_PREFIX}/users", status_code=303)


@router.get("/delivery-settings", response_class=HTMLResponse)
def delivery_settings(request: Request, db: Session = Depends(get_db)):
    context = admin_context(request, db)
    require_role(context["user"], {"admin"})
    setting = db.query(DeliverySetting).first()
    context.update(
        {
            "setting": setting,
            "weekdays": WEEKDAYS,
            "selected_days": setting.allowed_weekdays.split(",") if setting else [],
            "notification_email_fallback": os.getenv("ORDER_NOTIFICATION_EMAIL", ""),
        }
    )
    return templates.TemplateResponse("admin_delivery_settings.html", context)


@router.post("/delivery-settings")
async def save_delivery_settings(request: Request, db: Session = Depends(get_db)):
    context = admin_context(request, db)
    require_role(context["user"], {"admin"})
    form = await request.form()
    setting = db.query(DeliverySetting).first() or DeliverySetting()
    mode = str(form.get("mode", "any"))
    days = [str(day) for day in form.getlist("allowed_weekdays") if str(day).isdigit()]
    setting.mode = "weekdays" if mode == "weekdays" and days else "any"
    setting.allowed_weekdays = ",".join(days)
    setting.notification_email = str(form.get("notification_email", "")).strip() or None
    db.add(setting)
    db.commit()
    return RedirectResponse(f"{ADMIN_PREFIX}/delivery-settings", status_code=303)


@router.get("/delivery-summary", response_class=HTMLResponse)
def delivery_summary(request: Request, delivery_date: str = "", db: Session = Depends(get_db)):
    context = admin_context(request, db)
    selected_date = datetime.strptime(delivery_date, "%Y-%m-%d").date() if delivery_date else None
    rows = []
    if selected_date:
        rows = (
            db.query(
                OrderItem.product_name,
                OrderItem.product_weight,
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_price"),
                func.count(func.distinct(OrderItem.order_id)).label("orders_count"),
            )
            .join(Order)
            .filter(Order.delivery_date == selected_date, Order.status != "cancelled")
            .group_by(OrderItem.product_name, OrderItem.product_weight)
            .order_by(OrderItem.product_name)
            .all()
        )
    context.update(
        {
            "delivery_date": delivery_date,
            "rows": rows,
            "total_items": sum(row.total_quantity or 0 for row in rows),
            "total_amount": sum(row.total_price or 0 for row in rows),
        }
    )
    return templates.TemplateResponse("admin_delivery_summary.html", context)
