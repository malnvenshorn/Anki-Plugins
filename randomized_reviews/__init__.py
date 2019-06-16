# -*- coding: utf-8 -*-
#
# Copyright: 2019 Sven Lohrmann <malnvenshorn@mailbox.org>
# License: GNU AGPLv3 http://www.gnu.org/licenses/agpl.html
#
# The v2 scheduler only randomizes the review queue which is not enough to prevent cards from
# showing up deck by deck. To mitigate this issue the plugin also randomizes the learning queue
# and mixes learning and review cards.


import random

from anki.consts import NEW_CARDS_FIRST, NEW_CARDS_DISTRIBUTE
from anki.hooks import wrap
from anki.schedv2 import Scheduler


def fillLrnDay(self, _old):
    if not self.lrnCount:
        return False

    if self._lrnDayQueue:
        return True

    self._lrnDayQueue = self.col.db.list(
        "select id from cards where did in %s and queue = 3 and due <= ? order by due limit ?"
        % self._deckLimit(), self.today, self.queueLimit)

    if self._lrnDayQueue:
        rand = random.Random()
        rand.seed(self.today)
        rand.shuffle(self._lrnDayQueue)
        return True


def getCard(self, _old):
    # make sure queues are filled
    self._fillNew()
    self._fillRev()
    self._fillLrnDay()

    # learning card due?
    card = self._getLrnCard()
    if card:
        return card

    # new cards first?
    if self.col.conf['newSpread'] == NEW_CARDS_FIRST:
        card = self._getNewCard()
        if card:
            return card

    if self.col.conf['newSpread'] == NEW_CARDS_DISTRIBUTE:
        newCardCount = len(self._newQueue)
    else:
        newCardCount = 0

    # randomized card from lrnDayQueue, revQueue and newQueue (if the relevant setting is set)
    totalCount = newCardCount + len(self._revQueue) + len(self._lrnDayQueue)
    if totalCount > 0:
        rand = random.randint(1, totalCount)
        if rand <= newCardCount:
            card = self._getNewCard()
        elif rand <= newCardCount + len(self._revQueue):
            card = self._getRevCard()
        else:
            card = self._getLrnDayCard()

        if card:
            return card

    # new cards left?
    card = self._getNewCard()
    if card:
        return card

    # collapse or finish
    return self._getLrnCard(collapse=True)


Scheduler._fillLrnDay = wrap(Scheduler._fillLrnDay, fillLrnDay, 'around')
Scheduler._getCard = wrap(Scheduler._getCard, getCard, 'around')
