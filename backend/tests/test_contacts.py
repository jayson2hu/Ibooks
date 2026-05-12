"""
Tests for contact information APIs.
"""
import pytest
from httpx import AsyncClient

from app.database import AsyncSessionLocal
from app.main import app
from app.models.contact import Contact, ContactType
from app.models.user import User, UserRole
from app.utils.security import create_access_token, get_password_hash


async def create_user(email: str, role: UserRole = UserRole.USER) -> tuple[User, str]:
    """Create a user and return it with an auth token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            username=email.split("@")[0],
            role=role,
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        return user, token


async def create_contact(
    label: str,
    *,
    contact_type: ContactType = ContactType.EMAIL,
    value: str = "support@example.com",
    is_active: bool = True,
    display_order: int = 0,
) -> Contact:
    """Create a contact record for API tests."""
    async with AsyncSessionLocal() as session:
        contact = Contact(
            type=contact_type,
            label=label,
            value=value,
            is_active=is_active,
            display_order=display_order,
        )
        session.add(contact)
        await session.commit()
        await session.refresh(contact)
        return contact


@pytest.mark.asyncio
async def test_list_contacts_filters_active_and_orders_by_display_order():
    """Public contact list returns active contacts ordered by display_order."""
    await create_contact("Later Email", display_order=20)
    await create_contact("First QQ", contact_type=ContactType.QQ, value="12345", display_order=10)
    await create_contact("Hidden Phone", contact_type=ContactType.PHONE, value="10086", is_active=False)

    async with AsyncClient(app=app, base_url="http://test") as client:
        active_response = await client.get("/api/v1/contacts")
        all_response = await client.get("/api/v1/contacts", params={"active_only": False})

    assert active_response.status_code == 200
    assert [item["label"] for item in active_response.json()] == ["First QQ", "Later Email"]

    assert all_response.status_code == 200
    assert {item["label"] for item in all_response.json()} == {
        "First QQ",
        "Later Email",
        "Hidden Phone",
    }


@pytest.mark.asyncio
async def test_get_contact_by_id_and_missing_contact():
    """Public contact detail returns a contact or 404."""
    contact = await create_contact("Support Email")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/contacts/{contact.id}")
        missing_response = await client.get("/api/v1/contacts/99999")

    assert response.status_code == 200
    assert response.json()["label"] == "Support Email"
    assert response.json()["type"] == "email"
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_regular_user_cannot_manage_contacts():
    """Contact mutations are admin-only."""
    _, token = await create_user("contact-user@example.com")
    contact = await create_contact("Protected Email")

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/contacts",
            json={"type": "email", "label": "Blocked", "value": "blocked@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        update_response = await client.patch(
            f"/api/v1/contacts/{contact.id}",
            json={"label": "Blocked Update"},
            headers={"Authorization": f"Bearer {token}"},
        )
        delete_response = await client.delete(
            f"/api/v1/contacts/{contact.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert delete_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_update_and_delete_contacts():
    """Admins can manage contact records."""
    _, token = await create_user("contact-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/contacts",
            json={
                "type": "telegram",
                "label": "Telegram",
                "value": "@ibooks",
                "is_clickable": True,
                "link_url": "https://t.me/ibooks",
                "display_order": 5,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        contact_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/api/v1/contacts/{contact_id}",
            json={"label": "Telegram Support", "is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        delete_response = await client.delete(
            f"/api/v1/contacts/{contact_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        get_deleted_response = await client.get(f"/api/v1/contacts/{contact_id}")

    assert create_response.status_code == 201
    assert create_response.json()["type"] == "telegram"
    assert create_response.json()["link_url"] == "https://t.me/ibooks"

    assert update_response.status_code == 200
    assert update_response.json()["label"] == "Telegram Support"
    assert update_response.json()["is_active"] is False

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Contact deleted successfully"
    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_and_delete_missing_contact_return_404():
    """Managing a missing contact returns 404."""
    _, token = await create_user("contact-missing-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        update_response = await client.patch(
            "/api/v1/contacts/99999",
            json={"label": "Missing"},
            headers={"Authorization": f"Bearer {token}"},
        )
        delete_response = await client.delete(
            "/api/v1/contacts/99999",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert update_response.status_code == 404
    assert delete_response.status_code == 404
