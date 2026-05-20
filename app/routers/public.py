from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DeliverySetting, Location, Order, OrderItem, Product


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def is_valid_delivery_date(selected: date, setting: DeliverySetting) -> bool:
    if setting.mode == "any":
        return True
    js_weekday = (selected.weekday() + 1) % 7
    allowed = {int(day) for day in setting.allowed_weekdays.split(",") if day != ""}
    return js_weekday in allowed


@router.get("/", response_class=HTMLResponse)
def order_page(request: Request, db: Session = Depends(get_db), success: bool = False, error: str = ""):
    products = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.name).all()
    locations = db.query(Location).filter(Location.is_active.is_(True)).order_by(Location.name).all()
    setting = db.query(DeliverySetting).first()
    return templates.TemplateResponse(
        "public_order.html",
        {
            "request": request,
            "products": products,
            "locations": locations,
            "setting": setting,
            "success": success,
            "error": error,
            "today": date.today().isoformat(),
        },
    )


@router.post("/orders")
async def create_order(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    full_name = str(form.get("full_name", "")).strip()
    phone = str(form.get("phone", "")).strip()
    location_id = str(form.get("location_id", "")).strip()
    delivery_date_raw = str(form.get("delivery_date", "")).strip()

    if not full_name or not phone or not location_id or not delivery_date_raw:
        return RedirectResponse("/?error=missing", status_code=303)

    try:
        delivery_date = datetime.strptime(delivery_date_raw, "%Y-%m-%d").date()
        location = db.query(Location).filter(Location.id == int(location_id), Location.is_active.is_(True)).first()
    except ValueError:
        return RedirectResponse("/?error=invalid", status_code=303)

    setting = db.query(DeliverySetting).first()
    if not location or not setting or not is_valid_delivery_date(delivery_date, setting):
        return RedirectResponse("/?error=date", status_code=303)

    product_ids = [int(key.split("_", 1)[1]) for key in form.keys() if str(key).startswith("quantity_")]
    products = db.query(Product).filter(Product.id.in_(product_ids), Product.is_active.is_(True)).all() if product_ids else []
    product_by_id = {product.id: product for product in products}

    order_items = []
    for product_id in product_ids:
        product = product_by_id.get(product_id)
        if not product:
            continue
        try:
            quantity = int(str(form.get(f"quantity_{product_id}", "0")))
        except ValueError:
            quantity = 0
        if quantity > 0:
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=Decimal(product.price),
                    product_name=product.name,
                    product_weight=product.weight,
                )
            )

    if not order_items:
        return RedirectResponse("/?error=products", status_code=303)

    order = Order(full_name=full_name, phone=phone, location_id=location.id, delivery_date=delivery_date, items=order_items)
    db.add(order)
    db.commit()
    return RedirectResponse("/?success=true", status_code=303)

