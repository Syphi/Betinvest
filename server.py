import os
import json
import jinja2
import asyncio
import aioredis
import datetime
import aiohttp_jinja2

from aiohttp import web
from pathlib import Path

redis_host = os.getenv('redis_host', '0.0.0.0')
redis_port = os.getenv('redis_port', '6379')
redis_key_mask = "scrapper"
path_template = Path(__file__).resolve().parent


async def get_match_with_filter(section_obj: dict, match_str: str, match_count: int):
    """
    Check for all section, if they have events with name what match /{name}
    """
    new_section_obj = {
        **section_obj,
        "events": [],
    }

    for events in section_obj["events"]:
        if not match_str or events["name"].lower().startswith(match_str.lower()):
            events["startTime"] = datetime.datetime\
                .fromtimestamp(events["startTime"]).strftime('%m/%d/%Y %H:%M:%S')
            new_section_obj["events"].append(events)
            match_count += 1

    if new_section_obj["events"]:
        return new_section_obj, match_count
    return None, match_count


async def match_from_name(redis, match_str: str):
    """
    Get all sections in what matches starts for {name} in url / or full list
    :param redis:
    :param match_str:
    :return:
    """
    all_keys = await redis.keys(f"{redis_key_mask}*", encoding='utf-8')
    result_list = []
    match_count = 0

    while all_keys:
        key = all_keys.pop()
        section_data = await redis.get(key)
        section_data, match_count = await get_match_with_filter(
            json.loads(section_data), match_str, match_count)

        if section_data:
            result_list.append(section_data)

    return result_list, match_count


@aiohttp_jinja2.template('template/index.html')
async def handle(request):
    """
    Handler for request on url / or /{name}
    """
    app = request.app
    match_str = request.match_info.get('name')
    res, match_count = await match_from_name(app['redis'], match_str)
    return {"sections": res, "count": match_count}


async def main(loop_):
    """
    Main loop to write all rules to handle request
    """
    app = web.Application()
    app.router.add_route('GET', '/', handle)
    app.router.add_get('/{name}', handle)
    redis = await aioredis.create_redis_pool(f'redis://{redis_host}', loop=loop_)
    app['redis'] = redis
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(path_template))
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    web.run_app(main(loop))
