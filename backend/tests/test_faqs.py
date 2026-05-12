"""
Tests for FAQ APIs.
"""
import pytest
from httpx import AsyncClient

from app.database import AsyncSessionLocal
from app.main import app
from app.models.faq import FAQ
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


async def create_faq(
    question: str,
    *,
    category: str = "general",
    display_order: int = 0,
    is_active: bool = True,
) -> FAQ:
    """Create an FAQ record for API tests."""
    async with AsyncSessionLocal() as session:
        faq = FAQ(
            category=category,
            question=question,
            answer=f"Answer for {question}",
            display_order=display_order,
            is_active=is_active,
        )
        session.add(faq)
        await session.commit()
        await session.refresh(faq)
        return faq


@pytest.mark.asyncio
async def test_list_faqs_filters_active_category_and_orders_results():
    """Public FAQ list filters active/category and orders by category then display_order."""
    await create_faq("Payment second", category="payment", display_order=20)
    await create_faq("General first", category="general", display_order=10)
    await create_faq("Payment first", category="payment", display_order=5)
    await create_faq("Hidden payment", category="payment", is_active=False)

    async with AsyncClient(app=app, base_url="http://test") as client:
        active_response = await client.get("/api/v1/faqs")
        payment_response = await client.get("/api/v1/faqs", params={"category": "payment"})
        all_payment_response = await client.get(
            "/api/v1/faqs",
            params={"category": "payment", "active_only": False},
        )

    assert active_response.status_code == 200
    assert [item["question"] for item in active_response.json()] == [
        "General first",
        "Payment first",
        "Payment second",
    ]

    assert payment_response.status_code == 200
    assert [item["question"] for item in payment_response.json()] == [
        "Payment first",
        "Payment second",
    ]

    assert all_payment_response.status_code == 200
    assert {item["question"] for item in all_payment_response.json()} == {
        "Payment first",
        "Payment second",
        "Hidden payment",
    }


@pytest.mark.asyncio
async def test_get_faq_by_id_and_missing_faq():
    """Public FAQ detail returns a record or 404."""
    faq = await create_faq("How do I download?")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/faqs/{faq.id}")
        missing_response = await client.get("/api/v1/faqs/99999")

    assert response.status_code == 200
    assert response.json()["question"] == "How do I download?"
    assert response.json()["answer"] == "Answer for How do I download?"
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_regular_user_cannot_manage_faqs():
    """FAQ mutations are admin-only."""
    _, token = await create_user("faq-user@example.com")
    faq = await create_faq("Protected FAQ")

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/faqs",
            json={"category": "general", "question": "Blocked", "answer": "No"},
            headers={"Authorization": f"Bearer {token}"},
        )
        update_response = await client.patch(
            f"/api/v1/faqs/{faq.id}",
            json={"question": "Blocked update"},
            headers={"Authorization": f"Bearer {token}"},
        )
        delete_response = await client.delete(
            f"/api/v1/faqs/{faq.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert delete_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_update_and_delete_faqs():
    """Admins can manage FAQ records."""
    _, token = await create_user("faq-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/faqs",
            json={
                "category": "billing",
                "question": "Can I recharge?",
                "answer": "Yes.",
                "display_order": 3,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        faq_id = create_response.json()["id"]

        update_response = await client.patch(
            f"/api/v1/faqs/{faq_id}",
            json={"answer": "Use coin recharge.", "is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        delete_response = await client.delete(
            f"/api/v1/faqs/{faq_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        get_deleted_response = await client.get(f"/api/v1/faqs/{faq_id}")

    assert create_response.status_code == 201
    assert create_response.json()["category"] == "billing"
    assert create_response.json()["question"] == "Can I recharge?"

    assert update_response.status_code == 200
    assert update_response.json()["answer"] == "Use coin recharge."
    assert update_response.json()["is_active"] is False

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "FAQ deleted successfully"
    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_and_delete_missing_faq_return_404():
    """Managing a missing FAQ returns 404."""
    _, token = await create_user("faq-missing-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        update_response = await client.patch(
            "/api/v1/faqs/99999",
            json={"answer": "Missing"},
            headers={"Authorization": f"Bearer {token}"},
        )
        delete_response = await client.delete(
            "/api/v1/faqs/99999",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert update_response.status_code == 404
    assert delete_response.status_code == 404
