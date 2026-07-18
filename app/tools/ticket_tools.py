from sqlalchemy.orm import Session

from app.db.models import SupportTicket


def create_ticket(session: Session, customer_email: str, ticket_details: dict) -> SupportTicket:
    ticket = SupportTicket(
        customer_name=ticket_details["customer_name"],
        email=customer_email,
        issue=ticket_details["issue"],
        ticket_number="PENDING",
        status="open",
    )
    session.add(ticket)
    session.flush()
    ticket.ticket_number = f"APX-{ticket.id:05d}"
    session.commit()
    session.refresh(ticket)
    return ticket


def find_tickets_by_email(session: Session, customer_email: str) -> list[SupportTicket]:
    return (
        session.query(SupportTicket)
        .filter(SupportTicket.email == customer_email)
        .order_by(SupportTicket.created_at.desc())
        .all()
    )
