from .models import Game


class GameLibrary:
    """Read-only view of one member's game shelf."""

    def __init__(self, user):
        self.user = user
        self.games = list(
            Game.objects.filter(owner=user).select_related("platform")
        )

    # ---------- counting ----------

    def total(self):
        return len(self.games)

    def status_counts(self):
        """dict of {status_code: number_of_games}, including zeros."""
        counts = {code: 0 for code, _label in Game.STATUS_CHOICES}
        for game in self.games:
            counts[game.status] += 1
        return counts

    def status_summary(self):
        """List of (label, count, percent, code) tuples for display."""
        counts = self.status_counts()
        total = self.total()
        rows = []
        for code, label in Game.STATUS_CHOICES:
            count = counts[code]
            percent = round(count * 100 / total) if total else 0
            rows.append((label, count, percent, code))
        return rows

    def completion_rate(self):
        """Percent of games that are Completed or 100% Completed."""
        if not self.games:
            return 0
        finished = sum(1 for g in self.games if g.is_finished)
        return round(finished * 100 / len(self.games))

    def total_beats(self):
        return sum(g.times_beaten for g in self.games)

    # ---------- grouping / filtering ----------

    def by_platform(self):
        """dict of {platform_name: [games]}, sorted by platform name."""
        groups = {}
        for game in self.games:
            groups.setdefault(game.platform.name, []).append(game)
        return dict(sorted(groups.items()))

    def filter(self, status="", platform_id="", search=""):
        """Return a list of games matching all the given filters."""
        results = self.games
        if status:
            results = [g for g in results if g.status == status]
        if platform_id:
            results = [g for g in results if str(g.platform_id) == str(platform_id)]
        if search:
            needle = search.lower().strip()
            results = [g for g in results if needle in g.title.lower()]
        return results

    def most_beaten(self, limit=5):
        """Top games by times beaten (only games beaten at least once)."""
        beaten = [g for g in self.games if g.times_beaten > 0]
        beaten.sort(key=lambda g: (-g.times_beaten, g.title.lower()))
        return beaten[:limit]

    def backlog(self):
        """Games not finished yet: New, Incomplete, or Forgotten."""
        return [g for g in self.games if not g.is_finished]