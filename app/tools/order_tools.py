from sqlalchemy.orm import Session

from app.db.models import Order


def create_order(session: Session, customer_email: str, order_details: dict) -> Order:
    order = Order(
        customer_name=order_details["customer_name"],
        email=customer_email,
        phone_number=order_details["phone_number"],
        home_address=order_details["home_address"],
        product=order_details["product"],
        status="pending",
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def find_orders_by_email(session: Session, customer_email: str) -> list[Order]:
    return (
        session.query(Order)
        .filter(Order.email == customer_email)
        .order_by(Order.created_at.desc())
        .all()
    )
