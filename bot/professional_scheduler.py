"""
Professional Scheduler Implementation
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError:
    # Fallback to simple sleep-based approach
    logging.warning("APScheduler not available, using simple sleep")
    AsyncIOScheduler = None


class ProfessionalScheduler:
    """Professional scheduler with event-driven architecture"""

    def __init__(self, bot):
        self.bot = bot
        self.scheduled_task_running = False
        self.scheduler = None
        self.running = False

    async def start(self):
        """Start professional scheduler"""
        if AsyncIOScheduler is None:
            return

        try:
            self.scheduler = AsyncIOScheduler()
            self.running = True

            # Start scheduled task for debtors
            await self._scheduler.add_job(
                self.qarzdor_check_job,
                trigger='interval',
                minutes=15  # Har 15 daqiqada
                id='qarzdor_check_task'
            )

            logger.info("🕐 Professional scheduler boshlandi")
            self.scheduled_task_running = True

            # Start the polling (blocking)
            # Note: This will block if background task needs to run first

        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}", exc_info=True)
            self.running = False

    async def stop(self):
        """Stop professional scheduler"""
        if self.scheduler:
            await self.scheduler.shutdown()
            self.scheduled_task_running = False
            self.running = False

        logger.info("🛑 Professional scheduler to'xtatildi")

    async def qarzdor_check_job(self):
        """Qarzdorlarni tekshirish"""
        logger.info("🔍 Qarzdorlar tekshiriladi")

        try:
            debtors = await self.bot.db.get_debtors_with_telegram_ids()

            if not debtors:
                logger.info("✅ Qarzdorlar yo'q")
                return

            logger.info(f"📊 {len(debtors)} ta qarzdor topildi")

            success_count = 0
            total_debt = 0

            for debtor in debtors:
                if not debtor['telegram_id']:
                    logger.warning(f"⚠️ {debtor['student_name']} telegram_id yo'q")
                    continue

                status_emoji = "⚠️" if debtor['payment_status'] == 'OVERDUE' else "📋"

                message_text = (
                    f"{status_emoji} *{debtor['student_name']}*\n\n"
                    f"📚 Guruh: {debtor['group_name']}*\n"
                    f"📅 {debtor['month']} {debtor['billing_year']}*\n"
                    f"💰 Qarz: {debtor['debt']:,.0f} / {debtor['amount_due']:,.0f} UZS\n\n"
                    f"💳 To'lov: {debtor['amount_paid']:,.0f} / {debtor['amount_due']:,.0f} UZS\n\n"
                    f"⏰ Deadline: {debtor['due_date'].strftime('%d.%m.%Y') if debtor['due_date'] else '-'}\n\n"
                    f"⚡ *Iltimos, tezroq to'lang!*"
                )

                try:
                    await self.bot.send_message(
                        chat_id=debtor['telegram_id'],
                        text=message_text,
                        parse_mode="Markdown"
                    )
                    success_count += 1
                    total_debt += debtor['debt']
                    logger.info(f"✅ {debtor['student_name']} ga habar yuborildi (Qarz: {debtor['debt']:,.0f} UZS)")

                except Exception as e:
                    logger.warning(f"⚠️ {debtor['student_name']} ga habar yuborilmadi: {e}")

            # Adminlarga habar yuborish
            admin_ids = self.bot.db.get_admin_ids()
            if admin_ids:
                admin_summary = (
                    f"📊 *Qarzdorlar hisobot*\n\n"
                    f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                    f"👥 {len(debtors)} ta qarzdor\n"
                    f"💰 Jami qarz: {total_debt:,.0f} UZS\n\n"
                )

                for admin_id in admin_ids:
                    try:
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=admin_summary,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Admin {admin_id} ga hisobot yuborilmadi: {e}")

            logger.info(f"📢 {success_count}/{len(debtors)} ta qarzdor ga habar yuborildi")
            logger.info(f"💰 Jami qarz: {total_debt:,.0f} UZS")

        except Exception as e:
            logger.error(f"❌ Qarzdorlar tekshirish xatolik: {e}")
            logger.error(f"❌ Qarzdorlarni tekshirish xatolik: {e}", exc_info=True)
            logger.info("🔍 Qarzdorlar tekshirildi")

def qarzdor_check_job():
    """Qarzdor check job for scheduler"""
    return "qarzdor_check_job"