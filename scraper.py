"""
Get all events from API
Move it to sections
Put in Redis
"""
import os
import json
import aiohttp
import asyncio
import aioredis

import datetime as dt


redis_host = os.getenv('redis_host', '0.0.0.0')
redis_port = os.getenv('redis_port', '6379')
redis_key_mask = "scrapper"


def find_sport_type(sports_full_list, sport_id):
    """
    Get all sports list, and find by id in list of dict exactly needed sport
    :param: full list all sports
    :param: id of searchable sport
    :return: dict(sport object)
    """
    for sport in sports_full_list:
        if int(sport.get('id')) == int(sport_id):
            return sport
    else:
        print(f"Can`t find sport with such id - {sport_id}")
    return {'name': '<blank>'}


def find_event(event_full_list, event_id):
    """
    Get all event list, and find by id in list of dict exactly needed event, after delete it`s
    :param: full list all event
    :param: id of searchable event
    :return: dict(event object), event list with deleted event
    """
    for event in event_full_list:
        if int(event.get('id')) == int(event_id):
            event_full_list.remove(event)
            return event, event_full_list
    else:
        print(f"Can`t find event with such id - {event_id}")
    return {}, event_full_list


def formatting_sport_sections(full_data: dict):
    """
    Formatting full data, from server response
    Generator
    :param full_data:
    :return: section with full info about events and sport type.
    """

    sports_full_list = full_data.get('sports')
    sections_full_list = full_data.get('sections')
    events_full_list = full_data.get('events')

    for num_section, section in enumerate(sections_full_list):
        new_section_data = {
            **section,
            "sport": find_sport_type(sports_full_list, section.get('sport')),
            "events": []
        }

        for event_id in section.get('events'):
            event, events_full_list = find_event(events_full_list, event_id)
            new_section_data["events"].append(event)
        yield new_section_data

    else:
        print(f"Was added {num_section} sections")


async def get_events_from_api():
    """
    Func what do request to server and write to redis info about section
    :return:
    """
    redis = await aioredis.create_redis(f'redis://{redis_host}', timeout=5)

    async with aiohttp.ClientSession() as session:
        current_time = dt.datetime.utcnow().timestamp()
        api_url = f'https://clientsapi31.bkfon-resource.ru' \
                  f'/results/results.json.php?locale=en&_={current_time}'

        async with session.post(api_url, verify_ssl=False) as response:
            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])
            if response.status == 200:
                json_data = await response.json()
                for section_obj in formatting_sport_sections(json_data):
                    await redis.set(f"{redis_key_mask}_"
                                    f"{section_obj.get('name').lower().replace(' ', '_')}",
                                    json.dumps(section_obj))

    redis.close()
    await redis.wait_closed()


loop = asyncio.get_event_loop()
loop.run_until_complete(get_events_from_api())
# Zero-sleep to allow underlying connections to close
loop.run_until_complete(asyncio.sleep(0))
loop.close()
