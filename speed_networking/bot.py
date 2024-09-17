import time
import datetime
import random
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from threading import Thread


class Match:
    def __init__(self, u1, u2):
        self.start = datetime.datetime.now()
        self.u1 = u1
        self.u2 = u2
        self.room = None

    @property
    def time(self):
        n = datetime.datetime.now()
        diff = (n - self.start)
        return diff.seconds


class Bot(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event("app_mention")(self._mention)
        self.event("member_joined_channel")(self._joined)
        self.event("member_left_channel")(self._left)
        self.command("/networking")(self._start)

        self.middleware(self._log)

        # 10 minutes
        self._timeout = 10 * 60
        self._users = {}
        self._matches = []
        self._channel = None
        self._schedule()

    def _start(self, ack, respond, command):
        self._channel = command["channel_id"]

        output = self.client.conversations_members(channel=self._channel)
        # TODO: handle pagination
        members = output["members"]
        for m in members:
            self._users[m] = None

        ack()
        respond("OK")

    def _log(self, logger, body, next):
        logger.debug(body)
        return next()

    def _mention(self, body, say, logger):
        event = body["event"]
        say("HELO")

    def _joined(self, body, say, logger):
        event = body["event"]
        user = event["user"]
        print(event)
        self._users[user] = None

    def _left(self, body, say, logger):
        event = body["event"]
        user = event["user"]
        if user in self._users:
            del self._users[user]

    def _schedule(self):
        self._t = Thread(target=self._randomize)
        self._t.start()

    def _unmatched(self):
        return [u for u, match in self._users.items() if match is None]

    def _match_users(self, u1, u2):
        self.client.chat_postMessage(text=f"Match: <@{u1}> - <@{u2}>", channel=self._channel)

        m = Match(u1, u2)
        self._users[u1] = m
        self._users[u2] = m
        self._matches.append(m)

        # Custom conversation to use huddle
        output = self.client.conversations_open(users=[u1, u2])
        m.room = output["channel"]["id"]
        self.client.chat_postMessage(text=f"Welcome! you can start a huddle here to start the networking", channel=m.room)

    def _randomize(self):
        if self._channel:
            unmatched = self._unmatched()
            unmatched = random.sample(unmatched, len(unmatched))
            while len(unmatched) >= 2:
                u1 = unmatched.pop()
                u2 = unmatched.pop()
                self._match_users(u1, u2)
            if unmatched:
                self.client.chat_postMessage(text=f"waiting for match: <@{unmatched[0]}>", channel=self._channel)

        matches = []
        for m in self._matches:
            if m.time > self._timeout:
                self._users[m.u1] = None
                self._users[m.u2] = None
                self.client.chat_postMessage(text=f"Meeting ends: <@{m.u1}> - <@{m.u2}>", channel=self._channel)
            else:
                matches.append(m)
        self._matches = matches

        time.sleep(10)
        self._schedule()
