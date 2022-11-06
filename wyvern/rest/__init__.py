# MIT License

# Copyright (c) 2022 Sarthak

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import dataclasses
import typing

import aiohttp
import multidict

from wyvern import commands, interactions, models
from wyvern.exceptions import HTTPException, Unauthorized, UserNotFound

from .endpoints import Endpoints

if typing.TYPE_CHECKING:
    from wyvern.clients import GatewayClient
    from wyvern.components.container import ActionRowContainer
    from wyvern.constructors.embeds import EmbedConstructor

__all__: tuple[str, ...] = ("RESTClient",)


@dataclasses.dataclass
class RequestRoute:
    _url: str
    api_version: int = 10
    type: str = "GET"
    json: dict[str, typing.Any] | None = None

    @property
    def url(self) -> str:
        return f"https://discord.com/api/v{self.api_version}/{self._url}"


class RESTClient:
    """The REST Client that deals with disocrd REST Api requests."""

    def __init__(
        self,
        *,
        client: "GatewayClient",
        token: str,
        api_version: int = 10,
        client_session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._client = client
        self._session: aiohttp.ClientSession
        self._token = token
        self._api_version = api_version
        self._headers: typing.Dict[str, multidict.istr] = {"Authorization": multidict.istr(f"Bot {token}")}

        if client_session is not None:
            self._session = client_session

    async def _create_websocket(self) -> aiohttp.ClientWebSocketResponse:
        if getattr(self, "_session", None) is None:
            self._session = aiohttp.ClientSession(headers=self._headers)
        return await self._session.ws_connect(f"wss://gateway.discord.gg/?v={self._api_version}&encoding=json")

    async def request(self, route: RequestRoute) -> typing.Any:
        headers = self._headers.copy()
        headers["Content-Type"] = multidict.istr("application/json")
        res = await self._session.request(route.type, route.url, headers=headers, json=route.json)
        if res.status in (200, 201):
            return await res.json()
        if res.status in (204, 304):
            return
        else:
            raise HTTPException.with_code(res.status, await res.text())

    async def fetch_user(self, user_id: int) -> models.User:
        """Fetchs a user using the REST api.

        Parameters
        ----------

        user_id : int
            ID of the user that is to be fetched.

        Returns
        -------

        wyvern.models.users.User
            The user object that was fetched.

        Raises
        ------

        wyvern.exceptions.UserNotFound
            The targetted user was not found.
        """
        try:
            res = await self.request(RequestRoute(Endpoints.get_user(user_id)))
            return models.converters.payload_to_user(self._client, res)
        except HTTPException as e:
            raise UserNotFound(f"{e.message}\nNotFound : No user with ID {user_id} found.")

    async def fetch_client_user(self) -> "models.BotUser":
        """
        Fetchs the bot's user object.

        Returns
        -------

        wyvern.models.users.BotUser
            BotUser object representating the bot's user.
        """
        try:
            res = await self.request(RequestRoute(Endpoints.fetch_client_user()))
            return models.converters.payload_to_botuser(self._client, res)
        except HTTPException as e:
            if e.code == 401:
                raise Unauthorized("Improper token passed.")
            raise e

    async def edit_client_user(self, username: str | None = None, avatar: bytes | None = None) -> "models.BotUser":
        """Edits the bot's user.

        Parameters
        ----------

        username : str
            The new username.
        avatar : bytes
            The new avatar bytes.

        Returns
        -------

        wyvern.models.users.BotUser
            The updated user of bot.
        """

        payload: dict[str, bytes | str] = {}
        if username is not None:
            payload["username"] = username
        if avatar is not None:
            payload["avatar"] = avatar
        res: dict[str, int | str | bool] = await self.request(
            RequestRoute(Endpoints.fetch_client_user(), type="PATCH", json=payload)
        )
        return models.converters.payload_to_botuser(self._client, res)

    async def create_message(
        self,
        channel_id: int,
        content: str | None = None,
        *,
        embeds: typing.Sequence["EmbedConstructor"] = (),
        components: typing.Sequence[ActionRowContainer] = (),
        reference: int | models.MessageReference | None = None,
        allowed_mentions: models.AllowedMentions | None = None,
    ) -> "models.messages.Message":
        """Create a new message.

        Parameters
        ----------

        channel_id : int
            ID of the channel where the message is to be sent.
        content : str | None
            The text content of the message.
        embeds : typing.Sequence[wyvern.constructors.embeds.EmbedConstructor]
            Sequence of embeds to send.
        components : typing.Sequence[wyvern.components.container.ActionRowContainer]
            Sequence of action rows to send.
        reference : int | wyvern.models.messages.MessageReference | None
            ID or a message reference to which this is a response to.
        allowed_mentions : wyvern.models.messages.AllowedMentions | None
            Allowed mentions configs.

        Returns
        -------

        wyvern.models.messages.Message
            The message object that got created.

        """
        payload: dict[str, typing.Any] = {
            "content": content,
            "embeds": [embed._payload for embed in embeds],
            "components": [comp.to_payload() for comp in components],
            "allowed_mentions": (allowed_mentions or self._client.allowed_mentions).to_payload(),
        }

        if reference is not None:
            if isinstance(reference, models.MessageReference):
                payload["message_reference"] = reference.to_payload()
            else:
                payload["message_reference"] = models.MessageReference(message_id=reference).to_payload()

        res: dict[str, typing.Any] = await self.request(
            RequestRoute(Endpoints.create_message(channel_id), type="POST", json=payload),
        )
        return models.converters.payload_to_message(self._client, res)

    async def create_application_command(
        self,
        *,
        name: str,
        description: str,
        options: typing.Sequence[commands.slash_commands.CommandOption] = (),
        dm_permission: bool = True,
        type: interactions.base.InteractionCommandType,
    ) -> typing.Any:
        payload = {
            "name": name,
            "description": description,
            "options": [option.to_payload() for option in options],
            "dm_permission": dm_permission,
            "type": type,
        }
        return await self.request(
            RequestRoute(Endpoints.interaction_command(self._client._client_id), type="POST", json=payload)
        )

    async def create_interaction_response(
        self,
        interaction: interactions.Interaction,
        interaction_type: interactions.InteractionResponseType,
        *,
        content: str | None = None,
        embeds: typing.Sequence["EmbedConstructor"] = (),
        components: typing.Sequence[ActionRowContainer] = (),
        allowed_mentions: models.AllowedMentions | None = None,
    ) -> None:
        payload: dict[str, typing.Any] = {"type": int(interaction_type), "data": {}}
        if interaction_type is interactions.InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE:
            pass
        elif interaction_type is interactions.InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE:
            payload["data"]["content"] = content
            payload["data"]["embeds"] = [embed._payload for embed in embeds]
            payload["data"]["components"] = [builder.to_payload() for builder in components]
            payload["data"]["allowed_mentions"] = (allowed_mentions or self._client.allowed_mentions).to_payload()
        await self.request(
            RequestRoute(
                Endpoints.interaction_callback(
                    interaction.id,
                    interaction.token,
                ),
                type="POST",
                json=payload,
            )
        )
