# pip install -r requirements.txt && uvicorn main:app

import asyncio
import time
from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator

app = FastAPI(title='Асинхронный расчёт квадратов')

Number = int | float
Delay = Annotated[Number, Field(ge=0, le=60, description='Секунды')]


class CalculateRequest(BaseModel):
    numbers: list[Number] = Field(min_length=1)
    delays: list[Delay] = Field(min_length=1)

    @model_validator(mode='after')
    def check_lengths(self):
        if len(self.numbers) != len(self.delays):
            raise ValueError('numbers и delays должны быть одной длины')
        return self


class SquareResult(BaseModel):
    number: Number
    square: Number
    delay: Number
    time: float = Field(description='Время расчёта в секундах')


class CalculateResponse(BaseModel):
    results: list[SquareResult]
    total_time: float
    parallel_faster_than_sequential: bool


async def square_with_delay(number: Number, delay: Number) -> SquareResult:
    start = time.perf_counter()
    await asyncio.sleep(delay)
    return SquareResult(
        number=number,
        square=number ** 2,
        delay=delay,
        time=round(time.perf_counter() - start, 2),
    )


@app.post('/calculate/')
async def calculate(request: CalculateRequest) -> CalculateResponse:
    start = time.perf_counter()
    results = await asyncio.gather(*(
        square_with_delay(number, delay)
        for number, delay in zip(request.numbers, request.delays)
    ))
    elapsed = time.perf_counter() - start
    return CalculateResponse(
        results=results,
        total_time=round(elapsed, 2),
        parallel_faster_than_sequential=elapsed < sum(request.delays),
    )
