from typing import Optional

from nicegui import app, ui

from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
import asyncio
# import aiosqlite
import hashlib
import datetime


# 配置数据库
database_url = "sqlite+aiosqlite:///./data/users.db"
engine = create_async_engine(database_url, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    created_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now())

# 创建数据库表


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 注册用户


async def register_user(username: str, password: str) -> bool:
    async with SessionLocal() as session:
        existing_user = await session.scalar(User.__table__.select().where(User.username == username))
        if existing_user:
            return False
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        new_user = User(username=username, password_hash=hashed_password)
        session.add(new_user)
        await session.commit()
        return True

# 用户登录


async def login_user(username: str, password: str) -> bool:
    async with SessionLocal() as session:
        user = (await session.execute(User.__table__.select().where(User.username == username))).first()
        if not user or user.password_hash != hashlib.sha256(password.encode()).hexdigest():
            return False
        return True

# 获取当前登录用户


async def get_current_user() -> User | None:
    username = app.storage.user.get('username', None)
    async with SessionLocal() as session:
        user = (await session.execute(User.__table__.select().where(User.username == username))).first()
        return user


# 配置登录中间件
unrestricted_page_routes = ['/login', '/']


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if not request.url.path.startswith('/_nicegui') and request.url.path not in unrestricted_page_routes:
                return RedirectResponse(f'/login?redirect_to={request.url.path}')
        return await call_next(request)


app.add_middleware(AuthMiddleware)

# 构建 UI


def length_validator(value: str, min: int, max: int) -> str:
    if len(value) < min or len(value) > max:
        return False
    return True


@ui.page("/login")
async def login(redirect_to: str = '/') -> Optional[RedirectResponse]:
    async def try_login() -> None:
        if await login_user(username.value, password.value):
            app.storage.user.update(
                {'username': username.value, 'authenticated': True})
            ui.navigate.to(redirect_to)
        else:
            ui.notify('无效用户名或密码', color='negative')

    async def try_register() -> None:
        if not length_validator(username.value, 3, 20) or not length_validator(password.value, 6, 20):
            ui.notify('用户名或密码长度不符合要求', color='negative')
            return
        if await register_user(username.value, password.value):
            app.storage.user.update(
                {'username': username.value, 'authenticated': True})
            ui.notify('注册成功', color='positive')
            ui.navigate.to(redirect_to)
        else:
            ui.notify('用户名已存在', color='negative')

    # 如果已经登录，跳转到首页
    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')

    with ui.card().classes('absolute-center'):
        username = ui.input(
            'Username', validation=lambda value: "用户名应为3-20字符" if not length_validator(username.value, 3, 20) else None)
        password = ui.input('Password', password=True,
                            password_toggle_button=True, validation=lambda value: "密码应为6-20字符" if not length_validator(password.value, 3, 20) else None)
        with ui.row():
            ui.button('登录', on_click=try_login)
            ui.button("注册", on_click=try_register)


@ui.page("/")
async def home():
    def logout():
        app.storage.user.update({'authenticated': False})
        ui.navigate.reload()
    with ui.card().classes('absolute-center'):
        if app.storage.user.get('authenticated', False):
            ui.label('欢迎, ' + app.storage.user['username'])
            ui.link('个人信息接口', '/info')
            ui.button('退出', on_click=logout)
        else:
            ui.label('欢迎，陌生人！')
            ui.link('登录/注册', '/login').classes('button')

# 创建接口


@app.get("/info")
async def info():
    user = await get_current_user()
    return JSONResponse({'id': user.id, 'username': user.username, 'create_at': user.created_date.strftime("%Y-%m-%d %H:%M:%S")})

if __name__ in {"__main__", "__mp_main__"}:
    asyncio.run(init_db())
    ui.run(storage_secret="JUST_A_PLACEHOLDER")
