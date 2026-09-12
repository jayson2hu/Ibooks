"""
Tests for order APIs.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.main import app
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.models.wallet import CoinLedger, CoinLedgerType, Wallet
from app.services.wallet import credit_wallet, get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


async def create_user(email: str, username: str, role: UserRole = UserRole.USER) -> tuple[User, str]:
    """Create a user and return it with a JWT token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            username=username,
            role=role,
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.flush()
        await get_or_create_wallet(session, user.id)
        await session.commit()
        await session.refresh(user)

        token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        return user, token


async def create_resource(slug: str, is_free: bool, coin_price: int | None = None) -> Resource:
    """Create a published resource for order tests."""
    async with AsyncSessionLocal() as session:
        resource = Resource(
            title=f"Resource {slug}",
            slug=slug,
            description="Test resource",
            tags=[],
            price=Decimal("0.00") if is_free else Decimal("99.00"),
            coin_price=0 if is_free else (coin_price if coin_price is not None else 99),
            is_free=is_free,
            cloud_link=f"https://pan.example.com/{slug}",
            backup_links=[],
            access_code="abcd",
            preview_images=[],
            is_published=True,
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource


async def create_paid_order(user_id: int, resource_id: int) -> Order:
    """Create a paid order directly."""
    async with AsyncSessionLocal() as session:
        order = Order(
            order_no="ORDTESTPAID",
            user_id=user_id,
            resource_id=resource_id,
            amount=Decimal("99.00"),
            coin_amount=99,
            payment_method=PaymentMethod.ALIPAY,
            status=OrderStatus.PAID,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order


@pytest.mark.asyncio
async def test_create_free_resource_order_is_paid_and_grants_access():
    """Free resource orders are paid immediately and grant access."""
    user, token = await create_user("free-order@example.com", "freeorder")
    resource = await create_resource("free-order-resource", is_free=True)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        access_response = await client.get(
            "/api/v1/resources/free-order-resource/access",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "paid"
    assert data["payment_method"] == "free"
    assert data["user_id"] == user.id
    assert access_response.status_code == 200
    assert access_response.json() == {"has_access": True}


@pytest.mark.asyncio
async def test_create_paid_resource_order_uses_coin_balance():
    """Paid resources are purchased immediately with coin balance."""
    user, token = await create_user("paid-order@example.com", "paidorder")
    resource = await create_resource("paid-order-resource", is_free=False, coin_price=30)

    async with AsyncSessionLocal() as session:
        await credit_wallet(session, user.id, 50, CoinLedgerType.RECHARGE, related_order_no="RCHORDER")
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        access_response = await client.get(
            "/api/v1/resources/paid-order-resource/access",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "paid"
    assert data["payment_method"] == "coin"
    assert data["amount"] == "99.00"
    assert data["coin_amount"] == 30
    assert access_response.status_code == 200
    assert access_response.json() == {"has_access": True}

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledger = (await session.execute(
            select(CoinLedger).where(
                CoinLedger.user_id == user.id,
                CoinLedger.related_order_no == data["order_no"],
            )
        )).scalar_one()
        assert wallet.balance == 20
        assert wallet.total_spent == 30
        assert ledger.amount == -30
        assert ledger.balance_after == 20
        assert ledger.type == CoinLedgerType.PURCHASE


@pytest.mark.asyncio
async def test_create_paid_resource_order_rejects_insufficient_coin_balance():
    """Paid resource purchase fails without enough coin balance."""
    user, token = await create_user("coin-short@example.com", "coinshort")
    resource = await create_resource("coin-short-resource", is_free=False, coin_price=30)

    async with AsyncSessionLocal() as session:
        await credit_wallet(session, user.id, 10, CoinLedgerType.RECHARGE, related_order_no="RCHSHORT")
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 402
    detail = response.json()["detail"]
    assert detail["required_coins"] == 30
    assert detail["balance"] == 10

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        orders = (await session.execute(
            select(Order).where(
                Order.user_id == user.id,
                Order.resource_id == resource.id,
            )
        )).scalars().all()
        ledgers = (await session.execute(
            select(CoinLedger).where(
                CoinLedger.user_id == user.id,
                CoinLedger.type == CoinLedgerType.PURCHASE,
            )
        )).scalars().all()
        assert wallet.balance == 10
        assert orders == []
        assert ledgers == []


@pytest.mark.asyncio
async def test_paid_legacy_resource_requires_coin_price_configuration():
    """A monetary-priced legacy row cannot be purchased as a free resource."""
    _, token = await create_user("legacy-price@example.com", "legacyprice")
    resource = await create_resource("legacy-price-resource", is_free=False, coin_price=0)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "该资源尚未配置有效的书币价格"


@pytest.mark.asyncio
async def test_duplicate_paid_purchase_returns_409():
    """Users cannot buy a resource again after a paid order exists."""
    user, token = await create_user("duplicate@example.com", "duplicate")
    resource = await create_resource("duplicate-resource", is_free=True)

    async with AsyncClient(app=app, base_url="http://test") as client:
        first = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        second = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_paid_order_user_resource_pair_is_unique():
    """The database rejects duplicate paid orders for one user and resource."""
    user, _ = await create_user("unique-order@example.com", "uniqueorder")
    resource = await create_resource("unique-order-resource", is_free=True)

    async with AsyncSessionLocal() as session:
        session.add_all([
            Order(
                order_no="ORDUNIQUE001",
                user_id=user.id,
                resource_id=resource.id,
                amount=Decimal("0.00"),
                coin_amount=0,
                payment_method=PaymentMethod.FREE,
                status=OrderStatus.PAID,
            ),
            Order(
                order_no="ORDUNIQUE002",
                user_id=user.id,
                resource_id=resource.id,
                amount=Decimal("0.00"),
                coin_amount=0,
                payment_method=PaymentMethod.FREE,
                status=OrderStatus.PAID,
            ),
        ])

        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


@pytest.mark.asyncio
async def test_non_paid_orders_do_not_block_a_later_purchase():
    """Cancelled and pending history does not permanently block a purchase."""
    user, token = await create_user("retry-order@example.com", "retryorder")
    resource = await create_resource("retry-order-resource", is_free=True)
    pending = await create_pending_order(user.id, resource.id, order_no="ORDRETRYPENDING")

    async with AsyncClient(app=app, base_url="http://test") as client:
        cancel_response = await client.patch(
            f"/api/v1/orders/{pending.order_no}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )
        purchase_response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert cancel_response.status_code == 200
    assert purchase_response.status_code == 201


@pytest.mark.asyncio
async def test_order_unique_conflict_returns_409_without_debiting_wallet(monkeypatch):
    """A uniqueness race is mapped to 409 before coins are debited."""
    user, token = await create_user("race-order@example.com", "raceorder")
    resource = await create_resource("race-order-resource", is_free=False, coin_price=30)

    async with AsyncSessionLocal() as session:
        await credit_wallet(
            session,
            user.id,
            50,
            CoinLedgerType.RECHARGE,
            related_order_no="RCHRACE",
        )
        await session.commit()

    async def raise_unique_conflict(self, *args, **kwargs):
        raise IntegrityError("INSERT INTO orders", {}, Exception("unique conflict"))

    monkeypatch.setattr(AsyncSession, "flush", raise_unique_conflict)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Resource already purchased"

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        orders = (await session.execute(
            select(Order).where(
                Order.user_id == user.id,
                Order.resource_id == resource.id,
            )
        )).scalars().all()
        purchase_ledgers = (await session.execute(
            select(CoinLedger).where(
                CoinLedger.user_id == user.id,
                CoinLedger.type == CoinLedgerType.PURCHASE,
            )
        )).scalars().all()

        assert wallet.balance == 50
        assert wallet.total_spent == 0
        assert orders == []
        assert purchase_ledgers == []


@pytest.mark.asyncio
async def test_non_owner_cannot_view_order():
    """Users cannot view another user's order."""
    owner, owner_token = await create_user("owner@example.com", "owner")
    _, other_token = await create_user("other@example.com", "other")
    resource = await create_resource("private-order-resource", is_free=False, coin_price=10)

    async with AsyncSessionLocal() as session:
        await credit_wallet(session, owner.id, 10, CoinLedgerType.RECHARGE)
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        order_no = create_response.json()["order_no"]
        view_response = await client.get(
            f"/api/v1/orders/{order_no}",
            headers={"Authorization": f"Bearer {other_token}"},
        )

    assert view_response.status_code == 403


@pytest.mark.asyncio
async def test_cancel_pending_order_success():
    """Pending orders can be cancelled."""
    user, token = await create_user("cancel@example.com", "cancel")
    resource = await create_resource("cancel-resource", is_free=False)
    pending_order = await create_pending_order(user.id, resource.id)

    async with AsyncClient(app=app, base_url="http://test") as client:
        cancel_response = await client.patch(
            f"/api/v1/orders/{pending_order.order_no}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_paid_order_returns_400():
    """Paid orders cannot be cancelled."""
    _, token = await create_user("paid-cancel@example.com", "paidcancel")
    resource = await create_resource("paid-cancel-resource", is_free=True)

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        order_no = create_response.json()["order_no"]
        cancel_response = await client.patch(
            f"/api/v1/orders/{order_no}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert cancel_response.status_code == 400


@pytest.mark.asyncio
async def test_admin_can_list_all_orders():
    """Admins can list all orders."""
    user, user_token = await create_user("order-user@example.com", "orderuser")
    _, admin_token = await create_user("order-admin@example.com", "orderadmin", UserRole.ADMIN)
    resource = await create_resource("admin-list-resource", is_free=False, coin_price=10)

    async with AsyncSessionLocal() as session:
        await credit_wallet(session, user.id, 10, CoinLedgerType.RECHARGE)
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        response = await client.get(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_paid_order_grants_paid_resource_access():
    """Paid resources are accessible when a paid order exists."""
    user, token = await create_user("paid-access@example.com", "paidaccess")
    resource = await create_resource("paid-access-resource", is_free=False)
    await create_paid_order(user.id, resource.id)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/resources/paid-access-resource/access",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"has_access": True}


async def create_pending_order(
    user_id: int,
    resource_id: int,
    order_no: str = "ORDTESTPENDING",
) -> Order:
    """Create a legacy pending order directly."""
    async with AsyncSessionLocal() as session:
        order = Order(
            order_no=order_no,
            user_id=user_id,
            resource_id=resource_id,
            amount=Decimal("99.00"),
            coin_amount=99,
            status=OrderStatus.PENDING,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order
