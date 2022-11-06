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

__all__: tuple[str, ...] = ("Endpoints",)


class Endpoints:
    @classmethod
    def fetch_client_user(cls) -> str:
        return "users/@me"

    @classmethod
    def create_message(cls, channel_id: int) -> str:
        return f"channels/{channel_id}/messages"

    @classmethod
    def get_user(cls, user_id: int) -> str:
        return f"users/{user_id}"

    @classmethod
    def interaction_callback(cls, interaction_id: int, interaction_token: str) -> str:
        return f"interactions/{interaction_id}/{interaction_token}/callback"

    @classmethod
    def interaction_command(cls, app_id: int) -> str:
        return f"applications/{app_id}/commands"
