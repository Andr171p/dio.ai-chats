from collections.abc import Buffer
from uuid import UUID

import aiohttp


async def download_file_from_url(url: str) -> Buffer:
    async with aiohttp.ClientSession() as session, session.get(url) as response:
        response.raise_for_status()
        return await response.read()


class MediaClient:

    async def get_download_url(self, attachment_id: UUID) -> ...: ...
