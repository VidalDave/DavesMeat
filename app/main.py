import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth import hash_password, session_cookie_secure
from app.database import SessionLocal
from app.models import DeliverySetting, Location, Product, User
from app.routers import admin, public


def create_app() -> FastAPI:
    app = FastAPI(title="חנות הזמנות מוצרים")
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "change-me-in-production"),
        https_only=session_cookie_secure(),
        same_site="lax",
        max_age=60 * 60 * 8,
    )
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    Path("storage/static/uploads/products").mkdir(parents=True, exist_ok=True)
    app.mount("/storage/static", StaticFiles(directory="storage/static"), name="storage_static")
    app.include_router(public.router)
    app.include_router(admin.router)

    @app.on_event("startup")
    def startup() -> None:
        seed_data()

    return app


def seed_data() -> None:
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(username="admin", password_hash=hash_password("admin123!"), role="admin", is_active=True))

        if db.query(Product).count() == 0:
            db.add_all(
                [
                    Product(
                        name="מארז ירקות טריים",
                        image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=900&q=80",
                        weight="כ-5 קג",
                        price=89,
                        features="עונתי, טרי, מתאים למשפחה",
                    ),
                    Product(
                        name="מארז פירות מובחרים",
                        image_url="https://images.unsplash.com/photo-1619566636858-adf3ef4640b1?auto=format&fit=crop&w=900&q=80",
                        weight="כ-4 קג",
                        price=99,
                        features="מתוק, צבעוני, בחירה יומית",
                    ),
                    Product(
                        name="סל ירוקים",
                        image_url="https://images.unsplash.com/photo-1519996529931-28324d5a630e?auto=format&fit=crop&w=900&q=80",
                        weight="כ-2 קג",
                        price=49,
                        features="עשבי תיבול, עלים, שטוף ומוכן",
                    ),
                ]
            )

        if db.query(Location).count() == 0:
            db.add_all([Location(name="תל אביב"), Location(name="רמת גן"), Location(name="גבעתיים"), Location(name="חולון")])

        if db.query(DeliverySetting).count() == 0:
            db.add(DeliverySetting(mode="any", allowed_weekdays="0"))

        db.commit()
    finally:
        db.close()


app = create_app()
