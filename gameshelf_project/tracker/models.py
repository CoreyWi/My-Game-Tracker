from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Platform(models.Model):
    """A system games are played on (PC, PS5, Switch...)."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Game(models.Model):
    """A game on one member's shelf."""

    NEW = "new"
    INCOMPLETE = "incomplete"
    COMPLETED = "completed"
    HUNDRED = "100"
    FORGOTTEN = "forgotten"

    STATUS_CHOICES = (
        (NEW, "New (not started)"),
        (INCOMPLETE, "Incomplete (in progress)"),
        (COMPLETED, "Completed"),
        (HUNDRED, "100% Completed"),
        (FORGOTTEN, "Forgotten"),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="games",
    )
    title = models.CharField(max_length=200)
    platform = models.ForeignKey(
        Platform, on_delete=models.PROTECT, related_name="games"
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=NEW)
    times_beaten = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "title", "platform"],
                name="unique_game_per_owner_platform",
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.platform})"

    @property
    def is_finished(self):
        """True if the game has been completed or 100%'d."""
        return self.status in (self.COMPLETED, self.HUNDRED)

    def mark_beaten(self, note=""):
        """Log a completion, bump the counter, and mark the game completed."""
        with transaction.atomic():
            CompletionLog.objects.create(game=self, note=note)
            self.times_beaten += 1
            if self.status != self.HUNDRED:
                self.status = self.COMPLETED
            self.save()

    def mark_hundred(self):
        """Mark the game 100% complete. Counts as a beat if never beaten."""
        with transaction.atomic():
            if self.times_beaten == 0:
                CompletionLog.objects.create(game=self, note="100% completion")
                self.times_beaten = 1
            self.status = self.HUNDRED
            self.save()


class CompletionLog(models.Model):
    """One row per time a game was beaten, so 'times beaten' has history."""

    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="completions"
    )
    date_beaten = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date_beaten", "-id"]

    def __str__(self):
        return f"{self.game.title} beaten on {self.date_beaten}"