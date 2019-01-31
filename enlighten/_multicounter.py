import itertools
import time
from collections import OrderedDict

from enlighten import Counter


class _SubCounter(object):
    def __init__(self, **kwargs):
        self.count = kwargs.get("count", 0)
        self.color = kwargs.get("color", None)


class MultiCounter(Counter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        subcounts = kwargs.get("subcounts", [])
        self._subcounts = OrderedDict(
            [(name, _SubCounter(color=color)) for (name, color) in subcounts]
        )

    @property
    def subcounts(self):
        return OrderedDict(
            itertools.chain(self._subcounts.items(), [(None, self.last_subcount)])
        )

    @property
    def last_subcount(self):
        return _SubCounter(
            count=self.count
            - sum((subcount.count for subcount in self._subcounts.values())),
            color="normal",
        )

    def update(self, incr=1, force=False, subcount=None):
        if subcount:
            self.subcounts[subcount].count += incr
        super().update(incr=incr, force=force)

    def get_bar(self, barWidth):
        bar = ""

        percentages = [
            subcount.count / float(self.total) for subcount in self.subcounts.values()
        ]
        colors = [subcount.color for subcount in self.subcounts.values()]

        for percentage, color in zip(itertools.accumulate(percentages), colors):
            complete = barWidth * percentage
            barLen = int(complete)
            partial = fill = ""
            if barLen < barWidth and (complete - barLen) > 0:
                partial = self.series[
                    int(round((complete - barLen) * (len(self.series) - 1)))
                ]
            sub_bar = "{0}{1}".format(self.series[-1] * barLen, partial)
            sub_bar = sub_bar[self.manager.term.length(bar) :]
            bar += (
                getattr(self.manager.term, color)(sub_bar)
                if color is not "normal"
                else sub_bar
            )
        fill = self.series[0] * (barWidth - self.manager.term.length(bar) - 1)
        return "{0}{1}".format(bar, fill)
