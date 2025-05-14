import asyncio
import contextlib
import logging
import os
import typing

import httpx
from fastapi import FastAPI, Header, Request
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from starlette.middleware import Middleware

from discord_http_bot.middlewares import CustomHeaderMiddleware
from discord_http_bot.types import DiscordInteractionType, DiscordInteractionCallbackType
from discord_http_bot.utils import verify_discord_signature

DISCORD_APPLICATION_PUBLIC_KEY = os.environ["DISCORD_APPLICATION_PUBLIC_KEY"]
DISCORD_APPLICATION_ID = os.environ["DISCORD_APPLICATION_ID"]
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    response = httpx.post(
        f"https://discord.com/api/v10/applications/{DISCORD_APPLICATION_ID}/commands",
        headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
        json={
            "name": "bmsinfo",
            "description": "BMS 정보 저장소 URL을 출력합니다.",
        },
    )
    logger.info(response.text)
    response = httpx.post(
        f"https://discord.com/api/v10/applications/{DISCORD_APPLICATION_ID}/commands",
        headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
        json={
            "name": "카페",
            "description": "카페 접속용 URL을 출력합니다.",
        },
    )
    logger.info(response.text)
    yield


app = FastAPI(
    lifespan=lifespan,
    middleware=[Middleware(CustomHeaderMiddleware, public_key=DISCORD_APPLICATION_PUBLIC_KEY)],
)


class User(BaseModel):
    id: str
    username: str
    global_name: str


class Member(BaseModel):
    user: User


class Data(BaseModel):
    name: typing.Literal["bmsinfo", "카페"]


class DiscordPingRequest(BaseModel):
    type: typing.Literal[DiscordInteractionType.PING]


class DiscordApplicationCommandRequest(BaseModel):
    type: typing.Literal[DiscordInteractionType.APPLICATION_COMMAND]
    user: User | None = None
    member: Member | None = None
    data: Data


DiscordInteractionRequest = DiscordPingRequest | DiscordApplicationCommandRequest


class DiscordInteractionCallbackData(BaseModel):
    tts: bool | None = None
    content: str | None = None


class DiscordInteractionResponseBase(BaseModel):
    type: DiscordInteractionCallbackType
    data: DiscordInteractionCallbackData | None = None


class DiscordPingResponse(DiscordInteractionResponseBase):
    type: typing.Literal[DiscordInteractionCallbackType.PONG]


class DiscordInteractionCallbackResponse(DiscordInteractionResponseBase):
    type: typing.Literal[
        DiscordInteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
    ]


DiscordInteractionResponse = DiscordPingResponse | DiscordInteractionCallbackResponse


@app.post("/")
async def process_interaction_request(
    body: DiscordInteractionRequest,
) -> DiscordInteractionResponse:
    match body.type:
        case DiscordInteractionType.PING:
            return DiscordPingResponse(
                type=DiscordInteractionCallbackType.PONG,
            )
        case _:
            if body.user:
                info_message = f"유저가 DM으로 기능 호출 - {body.user.id} {body.user.username} {body.user.global_name}"
            elif body.member:
                info_message = f"유저가 서버에서 기능 호출 - {body.member.user.id} {body.member.user.username} {body.member.user.global_name}"
            else:
                info_message = "유저가 알 수 없는 경로로 기능 호출"
            logger.info(info_message)
            match body.data:
                case "카페":
                    cafe_info_text = "사좋돌아 https://sadoljoa.co.kr"
                    return DiscordInteractionCallbackResponse(
                        type=DiscordInteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                        data=DiscordInteractionCallbackData(content=cafe_info_text),
                    )
                case _:
                    bms_info_text = "븜스 입문용 정보 저장소입니다! https://sites.google.com/view/remilegi-bms"
                    return DiscordInteractionCallbackResponse(
                        type=DiscordInteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
                        data=DiscordInteractionCallbackData(content=bms_info_text),
                    )


@app.get("/")
async def ping():
    return {"result": "pong"}
