import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, select
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)
class Base(DeclarativeBase):
    pass

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String, nullable=False)

class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer_text: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserSetting(Base):
    __tablename__ = "settings"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    times_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_questions():
    from questions import questions
    async with Session() as s:
        cnt = (await s.execute(select(func.count(Question.id)))).scalar_one()
        if cnt == 0:
            s.add_all([Question(text=q) for q in questions])
            await s.commit()

async def get_random_question():
    async with Session() as s:
        return (await s.execute(select(Question).order_by(func.random()).limit(1))).scalars().first()

async def save_answer(user_id: int,  question_id: int, answer_text: str, username: str = None):
    async with Session() as s:
        s.add(Answer(user_id=user_id, username=username, question_id=question_id, answer_text=answer_text))
        await s.commit()

async def get_user_history(user_id: int):
    async with Session() as s:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        q = await s.execute(
            select(Answer.timestamp, Question.text, Answer.answer_text)
            .join(Question, Question.id == Answer.question_id)
            .where(Answer.user_id == user_id, Answer.timestamp >= seven_days_ago)
            .order_by(Answer.timestamp.desc())
        )
        return q.all()

async def save_user_setting(user_id: int, times_per_day: int):
    async with Session() as s:
        setting = await s.get(UserSetting, user_id)
        if setting:
            setting.times_per_day = times_per_day
        else:
            s.add(UserSetting(user_id=user_id, times_per_day=times_per_day))
        await s.commit()

async def get_user_setting(user_id: int):
    async with Session() as s:
        setting = await s.get(UserSetting, user_id)
        return setting.times_per_day if setting else 1

async def get_all_users_with_settings():
    async with Session() as s:
        q = await s.execute(select(UserSetting.user_id))
        return [r[0] for r in q.all()]
