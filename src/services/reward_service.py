# src/services/reward_service.py
from typing import Dict, Any
from sqlalchemy import select
from datetime import datetime, timedelta, date

from src.services.base_service import BaseService, ServiceResult
from src.database.models.player import Player
from src.utils.database_service import DatabaseService
from src.utils.transaction_logger import transaction_logger, TransactionType
from src.utils.config_manager import ConfigManager

class RewardService(BaseService):
    """Daily and periodic reward systems"""
    
    @classmethod
    async def claim_daily_reward(cls, player_id: int) -> ServiceResult[Dict[str, Any]]:
        async def _operation():
            async with DatabaseService.get_transaction() as session:
                stmt = select(Player).where(Player.id == player_id).with_for_update() # type: ignore
                player = (await session.execute(stmt)).scalar_one()
                
                today = date.today()
                if (isinstance(player.last_daily_reward, datetime) and 
                    player.last_daily_reward.date() == today):
                    raise ValueError("Daily reward already claimed today")
                
                yesterday = today - timedelta(days=1)
                if (isinstance(player.last_daily_reward, datetime) and 
                    player.last_daily_reward.date() == yesterday):
                    player.daily_streak += 1
                else:
                    player.daily_streak = 1
                
                daily_config = ConfigManager.get("daily_rewards") or {}
                base_jijies = daily_config.get("base_jijies", 1000)
                bonus_per_day = daily_config.get("bonus_per_day", 100)
                max_bonus = daily_config.get("max_bonus", 1000)
                
                bonus = min(player.daily_streak * bonus_per_day, max_bonus)
                total_jijies = base_jijies + bonus
                
                player.jijies += total_jijies
                player.total_jijies_earned += total_jijies
                player.last_daily_reward = datetime.utcnow()
                player.update_activity()
                await session.commit()
                
                transaction_logger.log_transaction(player_id, TransactionType.DAILY_REWARD, {
                    "streak": player.daily_streak, "jijies": total_jijies,
                    "base": base_jijies, "bonus": bonus
                })
                
                return {
                    "streak": player.daily_streak, "jijies": total_jijies,
                    "base_reward": base_jijies, "streak_bonus": bonus,
                    "next_claim": today + timedelta(days=1)
                }
        return await cls._safe_execute(_operation, "daily reward claim")