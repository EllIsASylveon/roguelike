from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import tcod

from actions import (
    Action,
    BumpAction,
    EscapeAction,
    PickupAction,
    WaitAction,
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine

MOVE_KEYS = {
    #move keys
    tcod.event.KeySym.UP: (0,-1),
    tcod.event.KeySym.DOWN: (0,1),
    tcod.event.KeySym.LEFT: (-1,0),
    tcod.event.KeySym.RIGHT: (1,0),
    tcod.event.KeySym.HOME: (-1,-1),
    tcod.event.KeySym.END: (-1,1),
    tcod.event.KeySym.PAGEUP: (1,-1),
    tcod.event.KeySym.PAGEDOWN: (1,1),
}

WAIT_KEYS = {
    tcod.event.KeySym.PERIOD,
}

class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> None:
        self.handle_action(self.dispatch(event))

    def handle_action(self, action: Optional[Action]) -> bool:
        # Handle actions returned from event methods. Returns True if action will advance turn
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False # Skip enemy turn of exceptions

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)

class MainGameEventHandler(EventHandler):

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym

        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction(player)
        elif key == tcod.event.KeySym.v:
            self.engine.event_handler = HistoryViewer(self.engine)
        elif key == tcod.event.KeySym.g:
            action = PickupAction(player)

        #no valid key pressed
        return action


class GameOverEventHandler(EventHandler):

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.KeySym.ESCAPE:
            raise SystemExit()


CURSOR_Y_KEYS = {
    tcod.event.KeySym.UP: -1,
    tcod.event.KeySym.DOWN: 1,
    tcod.event.KeySym.PAGEUP: -10,
    tcod.event.KeySym.PAGEDOWN: 10,
}

class HistoryViewer(EventHandler):
    # Print history on a larger window that can be navigated

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)

        log_console = tcod.console.Console(console.width - 6, console.height - 6)

        # Draw fram with custom banner title
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
        )

        # Render the message log using the cursor parameter
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                self.cursor - self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length -1:
                self.cursor = 0
            else:
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.KeySym.HOME:
            self.cursor = 0
        elif event.sym == tcod.event.KeySym.END:
            self.cursor = self.log_length - 1
        else:
            self.engine.event_handler = MainGameEventHandler(self.engine)

class HelpViewer(EventHandler):
    # Print Help window with key bindings

    ...
