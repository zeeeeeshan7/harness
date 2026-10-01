# Add Telegram steering (pause, resume, abort, status)

## Context
I want to steer a long run from my phone. `TelegramSteer` is a `Hook` (see `harness/hooks.py`) that polls a Telegram bot for commands between steps. The Telegram client is injected so tests need no network. Read `PRD.md`, `DESIGN.md` and `CONTRIBUTING.md` first.

## Files (create exactly these, touch nothing else)
- `harness/steer/__init__.py` (empty)
- `harness/steer/telegram.py`
- `tests/test_telegram.py`

## Interface
```python
class Client(Protocol):
    def get_updates(self, offset: int | None) -> list[dict]: ...   # Telegram getUpdates shape
    def send_message(self, chat_id: int, text: str) -> None: ...

class BotClient:                       # real client, stdlib urllib only
    def __init__(self, token: str, timeout: float = 5.0): ...

class TelegramSteer(Hook):
    def __init__(self, client: Client, chat_id: int): ...
    def on_step(self, state: RunState, step: Step) -> Action | None: ...
    def wait_resume(self, sleep=time.sleep, poll_s: float = 2.0) -> bool: ...
```
Updates look like `{"update_id": 10, "message": {"chat": {"id": 123}, "text": "/pause"}}`.

Behaviour:
- `on_step` calls `client.get_updates(self.offset)` once, handles every update in order, and sets `self.offset = update_id + 1` for each so no update is handled twice.
- **Only messages whose `chat.id == chat_id` are handled.** Others are ignored silently (still advance the offset).
- Commands (case-insensitive, whitespace stripped): `/pause` returns `Action.PAUSE`; `/abort` returns `Action.ABORT`; `/status` replies `step {state.step}, ${state.total_usd:.4f} spent` via `send_message` and does not change the action; unknown text is ignored. If several commands arrive, the first PAUSE or ABORT wins (ABORT over PAUSE if both).
- Commands that return an action also send an acknowledgement (`"pausing"` / `"aborting"`).
- `wait_resume`: loop `get_updates`, handling updates the same way (same chat check, same offset tracking); return `True` on `/resume` (send `"resuming"`), `False` on `/abort`; otherwise `sleep(poll_s)` and repeat. `sleep` is injected so tests do not wait.
- `BotClient` calls `https://api.telegram.org/bot{token}/getUpdates` and `/sendMessage` with `urllib.request` and `json`; `get_updates` passes `offset` and `timeout=0`. **The token must never appear in logs, exceptions or `repr`.** Network errors raise from `get_updates`; `on_step` catches `OSError` there and treats it as "no updates" so a flaky network never crashes a run.

## Acceptance criteria
- [ ] `/pause` returns PAUSE and sends `pausing`; `/abort` returns ABORT.
- [ ] `/status` sends a message containing the step and cost and returns None.
- [ ] Message from a different chat id is ignored and never replied to, even `/abort`.
- [ ] Same update is never handled twice across two `on_step` calls (offset test).
- [ ] ABORT beats PAUSE when both arrive in one batch.
- [ ] `/PAUSE  ` (case and spaces) works; unknown text and updates without `message` are ignored without error.
- [ ] `wait_resume` returns True on `/resume`, False on `/abort`, calls the injected `sleep` between empty polls, and ignores other chats.
- [ ] `get_updates` raising `OSError` inside `on_step` returns None, no crash.
- [ ] `BotClient`: with `urllib.request.urlopen` monkeypatched, assert the request URL and that `repr(client)` and any raised error message do not contain the token.
- [ ] No test uses the network. `pytest` and `ruff check .` pass.

## Do not
- Edit `harness/types.py`, `runner.py`, `hooks.py` or any existing test.
- Add dependencies (no `requests`, no `python-telegram-bot`).
- Use threads, asyncio or webhooks; polling only.
- Read tokens from the environment or files; the caller passes them in.
