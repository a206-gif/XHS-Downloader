from typing import TYPE_CHECKING

from xhshow import Xhshow

from ..module import retry, sleep_time

if TYPE_CHECKING:
    from ..module import Manager

__all__ = ["UserPosted"]


class UserPosted:
    """获取作者主页发布的所有作品 ID。"""

    API = "https://www.xiaohongshu.com/api/sns/web/v1/user_posted"
    PAGE_SIZE = 30

    encipher = Xhshow()

    def __init__(
        self,
        manager: "Manager",
        cookies: str | None = None,
        proxy: str | None = None,
    ):
        self.headers = manager.blank_headers.copy()
        self.client = manager.request_client
        self.cookies = self.get_cookie(cookies)
        self.print = manager.print
        self.avg_delay = manager.avg_delay
        self.proxy = (self.client.proxies.get("all", None) if proxy is None else proxy,)

    def get_cookie(self, cookies: str | None = None) -> dict | str:
        if cookies:
            self.headers["cookie"] = cookies
            return cookies
        return dict(self.client.cookies)

    async def run(
        self,
        user_id: str,
        cookie: str | None = None,
        proxy: str | None = None,
    ) -> list[str]:
        """分页获取作者发布的全部作品 ID。"""

        if cookie:
            self.get_cookie(cookie)
        if proxy is not None:
            self.proxy = (proxy,)
        note_ids: list[str] = []
        cursor = ""
        while True:
            params = {
                "user_id": user_id,
                "cursor": cursor,
                "num": self.PAGE_SIZE,
                "note_index": 0,
            }
            data = await self.get_data(params)
            notes = (data or {}).get("notes", [])
            note_ids.extend(
                note["note_id"] for note in notes if note.get("note_id")
            )
            if not (data or {}).get("has_more") or not notes:
                break
            cursor = data.get("cursor", "")
            if not cursor:
                break
        return note_ids

    @retry
    async def get_data(self, params: dict):
        headers = self.get_headers(params)
        response = await self.client.get(
            self.API,
            params=params,
            headers=headers,
            proxy=self.proxy,
        )
        await sleep_time(self.avg_delay)
        response.raise_for_status()
        return response.json()

    def get_headers(self, params: dict):
        headers = self.encipher.sign_headers_get(
            uri=self.API,
            cookies=self.cookies,
            params=params,
        )
        return headers | self.headers

    def note_link(self, note_id: str) -> str:
        return f"https://www.xiaohongshu.com/explore/{note_id}"
