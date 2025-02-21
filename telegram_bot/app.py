# -*- coding: utf-8 -*-
import sys

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from loguru import logger
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from telegram_bot.controllers import webhook, release, meta
from telegram_bot.cron import jobs, scheduler
from telegram_bot.database import models
from telegram_bot.database.database import engine
from telegram_bot.settings import settings

# 日志格式设置
logger.remove()
FORMAT = "<level>{level: <6}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> <level>{message}</level>"
logger.add(sys.stdout, colorize=True, format=FORMAT, diagnose=False)

app = FastAPI()
app.include_router(meta.router)
app.include_router(webhook.router)
app.include_router(jobs.router)
app.include_router(release.router)


@app.on_event("startup")
async def startup_event():
    # 定时任务
    scheduler.start()
    logger.info("starting cron service..", scheduler)

    # 数据库更新
    logger.info("updating database schema..")
    models.Base.metadata.create_all(bind=engine)


# sentry middleware
if settings.SENTRY_URL:
    sentry_sdk.init(dsn=settings.SENTRY_URL, environment=settings.ENV)
    app = SentryAsgiMiddleware(app)

if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=5000, log_level="info", reload=True)
