from sqlalchemy import func, select, update, delete, insert, exists, desc, text, not_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta

from Application.models.users import User
from Application.models.score import TotalScore, StudySession
from Application.core.config import STUDY_TIME_THRESHOLD

from Application.api.dashboard.schemas import UserRankingItem, UserRecentReport

# Users 테이블
class UsersDB:
    # "status" 컬럼이 "active"인 유저 수 집계
    @staticmethod
    async def get_active_cnt(db: AsyncSession) -> int:
        query = select(func.count()).where(User.status == "active")
        result = await db.execute(query)
        return result.scalar_one()
    
    @staticmethod
    async def exists_user_name(db: AsyncSession, user_name: str) -> bool:
        query = select(exists().where(User.user_name == user_name))
        result = await db.execute(query)
        return result.scalar()


class ScoreDB:
    @staticmethod
    async def sort_total_score(db: AsyncSession) -> List[UserRankingItem]:
        query = (select(TotalScore.user_name,
                        TotalScore.total_score,
                        TotalScore.avg_focus,
                        TotalScore.total_cnt,
                        TotalScore.prev_rank).order_by(desc(TotalScore.total_score)))
        result = await db.execute(query)
        rows = result.all()  # List[Tuple[str, int, float, int, int]
        rank_list: List[UserRankingItem] = []
        for rank, (name, total_score, avg_focus, total_cnt, prev_rank) in enumerate(rows, start=1):
            trend_flag = (prev_rank == 0) or ((prev_rank != -1) and (rank <= prev_rank))
            rank_list.append(UserRankingItem(rank=rank,
                                             score=total_score,
                                             user_name=name,
                                             total_cnt=total_cnt,
                                             avg_focus= avg_focus,
                                             trend= trend_flag))
        for rank, item in enumerate(rank_list, start=1):
            query = (update(TotalScore).where(TotalScore.user_name == item.user_name)
                                            .values(prev_rank=rank))
            await db.execute(query)
        return rank_list
    
    @staticmethod
    async def get_TotalScore_record(db: AsyncSession, name: str) -> TotalScore | None:
        query = select(TotalScore).where(TotalScore.user_name==name)
        result = await db.execute(query)
        return result.scalars().one_or_none()

    @staticmethod
    async def get_user_rank(db: AsyncSession, name: str) -> int | None:
        # 먼저 해당 유저의 total_score를 구함
        score_query = select(TotalScore.total_score).where(TotalScore.user_name == name)
        user_score_result = await db.execute(score_query)
        user_score = user_score_result.scalar_one_or_none()
        if user_score is None or user_score == 0.0:
            return None
        # user_score보다 큰 점수 가진 사람의 수 + 1 = 랭킹
        rank_query = select(func.count()).where(TotalScore.total_score > user_score)
        rank_result = await db.execute(rank_query)
        higher_cnt = rank_result.scalar_one()
        return higher_cnt + 1

    @staticmethod
    async def renew_table(db: AsyncSession, ranking: dict) -> None:
        # UPSERT 대상 행
        rows = []
        for user_name, vals in ranking.items():
            ts = int(vals.get("total_score") or 0)
            tt = int(vals.get("total_time") or 0)
            avg = float(ts / tt) if tt > 0 else 0.0
            # INSERT 시 prev_rank 는 0으로 초기화 (DB server default가 없다면 명시적으로 보장)
            rows.append({"user_name" : user_name,
                                "total_score" : ts,
                                "avg_focus" : avg})
        # ranking 유저는 UPSERT
        if rows:
            ins = mysql_insert(TotalScore).values(rows)
            query = ins.on_duplicate_key_update(total_score=ins.inserted.total_score,
                                                avg_focus=ins.inserted.avg_focus)
            await db.execute(query)
            # ranking 에 '없는' 유저는 기본값 초기화, 단 prev_rank = -1 로 초기화 하여 trend 값 False 로 유도 (reset)
            names = [r["user_name"] for r in rows]
            await db.execute(update(TotalScore)
                             .where(not_(TotalScore.user_name.in_(names)))
                             .values(total_score=0,
                                     avg_focus=0.0,
                                     prev_rank=-1))

class StudyDB:
    @staticmethod
    async def get_prev_records(db: AsyncSession, name: str, cnt: int) -> List[StudySession | None]:
        query = (select(StudySession).where(StudySession.user_name == name)
                                            .order_by(desc(StudySession.started_at))
                                            .limit(cnt))
        result = await db.execute(query)
        records = result.scalars().all()
        if len(records) < cnt:
            records += [None] * (cnt - len(records))
        return records
    
    @staticmethod
    async def get_recent_record(db: AsyncSession, name: str) -> StudySession | None:
        # study_time이 5분(300초) 이하인 경우는 제외 (웹소켓 서버에서도 동일하게 300초 이하 인 경우 학습으로 간주하지 않음 (DB 접근 overhead 최소화))
        # 현재 시연 준비로 0 으로 설정...
        query = (select(StudySession)
                    .where(StudySession.user_name == name, StudySession.study_time > 0)
                    .order_by(desc(StudySession.started_at))
                    .limit(1))
        rows = await db.execute(query)
        return rows.scalars().first()
        
    @staticmethod
    async def renew_records(db: AsyncSession) -> dict:
        # 1. StudySession 테이블에서 현재 시각 기준 StudySession.started_at 이 일주일 이내 인 record 제외 전부 delete
        deletion = (delete(StudySession)
                .where(StudySession.started_at < func.date_sub(func.now(), text("INTERVAL 7 DAY"))))
        await db.execute(deletion)
        await db.flush()
        # 2. StudySession.user_name 이 key, value 는 total_score (StudySession.score 의 누적 합), total_time (StudySession.study_time / 10 의 누적합)
        agg_query = (select(StudySession.user_name.label("user_name"),
                            func.coalesce(func.sum(StudySession.score), 0).label("total_score"),
                            func.coalesce(func.sum(func.floor(func.coalesce(StudySession.study_time, 0) / 10)), 0)
                                        .label("total_time"))
                            .group_by(StudySession.user_name))
        result = await db.execute(agg_query)
        rows = result.all()
        ranking = dict()
        for user_name, total_score, total_time in rows:
            ranking[user_name] = { "total_score": int(total_score or 0), "total_time": int(total_time or 0) }
        return ranking