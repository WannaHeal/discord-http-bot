import contextlib
import logging
import os
import typing

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from pydantic import BaseModel
from starlette.middleware import Middleware

from .middlewares import CustomHeaderMiddleware
from .types import DiscordInteractionType, DiscordInteractionCallbackType

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


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(
    request: Request, exc: RequestValidationError
) -> Response:
    logger.info(exc)
    return await request_validation_exception_handler(request, exc)


class User(BaseModel):
    id: str
    username: str
    global_name: str


class Member(BaseModel):
    user: User


class InteractionData(BaseModel):
    name: str


class DiscordApplicationCommandRequest(BaseModel):
    type: typing.Literal[
        DiscordInteractionType.APPLICATION_COMMAND,
        DiscordInteractionType.APPLICATION_COMMAND_AUTOCOMPLETE,
        DiscordInteractionType.MESSAGE_COMPONENT,
        DiscordInteractionType.MODAL_SUBMIT,
    ]
    user: User | None = None
    member: Member | None = None
    data: InteractionData


class DiscordPingRequest(BaseModel):
    type: typing.Literal[DiscordInteractionType.PING]


DiscordInteractionRequest = DiscordPingRequest | DiscordApplicationCommandRequest


class DiscordInteractionCallbackData(BaseModel):
    tts: bool | None = None
    content: str | None = None


class DiscordInteractionResponseBase(BaseModel):
    data: DiscordInteractionCallbackData | None = None


class DiscordPingResponse(DiscordInteractionResponseBase):
    type: typing.Literal[DiscordInteractionCallbackType.PONG]


class DiscordInteractionCallbackResponse(DiscordInteractionResponseBase):
    type: typing.Literal[
        DiscordInteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
    ]


DiscordInteractionResponse = DiscordPingResponse | DiscordInteractionCallbackResponse

cafe_info_text = "사좋돌아 https://sadoljoa.co.kr"
bms_info_text = "븜스 입문용 정보 저장소입니다! https://sites.google.com/view/remilegi-bms"


@app.post("/")
async def process_interaction_request(
    body: DiscordInteractionRequest,
) -> DiscordInteractionResponse:
    if isinstance(body, DiscordPingRequest):
        return DiscordPingResponse(
            type=DiscordInteractionCallbackType.PONG,
        )

    if body.user:
        info_message = f"유저가 DM으로 기능 호출 - {body.user.id} {body.user.username} {body.user.global_name}"
    elif body.member:
        info_message = f"유저가 서버에서 기능 호출 - {body.member.user.id} {body.member.user.username} {body.member.user.global_name}"
    else:
        info_message = "유저가 알 수 없는 경로로 기능 호출"
    logger.info(info_message)
    match body.data.name:
        case "카페":
            content = cafe_info_text
        case _:
            content = bms_info_text
    return DiscordInteractionCallbackResponse(
        type=DiscordInteractionCallbackType.CHANNEL_MESSAGE_WITH_SOURCE,
        data=DiscordInteractionCallbackData(content=content),
    )


@app.get("/")
async def ping():
    return {"result": "pong"}
