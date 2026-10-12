from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import GameForm
from .library import GameLibrary
from .models import CompletionLog, Game, Platform

User = get_user_model()


class BaseSetup(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("niles", password="pass12345!")
        self.other = User.objects.create_user("someone", password="pass12345!")
        self.pc = Platform.objects.create(name="PC")
        self.switch = Platform.objects.create(name="Nintendo Switch")

    def make(self, title, status=Game.NEW, beaten=0, platform=None, owner=None):
        return Game.objects.create(
            owner=owner or self.user, title=title, platform=platform or self.pc,
            status=status, times_beaten=beaten,
        )


class ModelTests(BaseSetup):
    def test_str(self):
        self.assertEqual(str(self.make("Hades")), "Hades (PC)")

    def test_mark_beaten_counts_and_logs(self):
        game = self.make("Hades", Game.INCOMPLETE)
        game.mark_beaten("first clear")
        game.mark_beaten()
        game.refresh_from_db()
        self.assertEqual(game.times_beaten, 2)
        self.assertEqual(game.status, Game.COMPLETED)
        self.assertEqual(game.completions.count(), 2)

    def test_beating_a_100_game_keeps_100(self):
        game = self.make("Celeste", Game.HUNDRED, beaten=1)
        game.mark_beaten()
        self.assertEqual(game.status, Game.HUNDRED)
        self.assertEqual(game.times_beaten, 2)

    def test_mark_hundred_counts_first_beat(self):
        game = self.make("Hollow Knight")
        game.mark_hundred()
        self.assertEqual(game.status, Game.HUNDRED)
        self.assertEqual(game.times_beaten, 1)
        self.assertEqual(CompletionLog.objects.filter(game=game).count(), 1)

    def test_platform_with_games_cannot_be_deleted(self):
        from django.db.models import ProtectedError
        self.make("Hades")
        with self.assertRaises(ProtectedError):
            self.pc.delete()


class LibraryTests(BaseSetup):
    def setUp(self):
        super().setUp()
        self.make("Hades", Game.COMPLETED, 3)
        self.make("Celeste", Game.HUNDRED, 1, self.switch)
        self.make("Stardew Valley", Game.INCOMPLETE)
        self.make("Zelda", Game.FORGOTTEN, 0, self.switch)
        self.make("Not mine", Game.COMPLETED, 9, owner=self.other)
        self.lib = GameLibrary(self.user)

    def test_only_own_games(self):
        self.assertEqual(self.lib.total(), 4)

    def test_status_counts_dict(self):
        counts = self.lib.status_counts()
        self.assertEqual(counts[Game.COMPLETED], 1)
        self.assertEqual(counts[Game.HUNDRED], 1)
        self.assertEqual(counts[Game.NEW], 0)
        self.assertEqual(sum(counts.values()), 4)

    def test_completion_rate(self):
        self.assertEqual(self.lib.completion_rate(), 50)

    def test_filter_and_search(self):
        self.assertEqual(len(self.lib.filter(platform_id=self.switch.pk)), 2)
        self.assertEqual([g.title for g in self.lib.filter(search="star")], ["Stardew Valley"])
        self.assertEqual(len(self.lib.filter(status=Game.FORGOTTEN)), 1)

    def test_by_platform_and_most_beaten(self):
        self.assertEqual(list(self.lib.by_platform()), ["Nintendo Switch", "PC"])
        self.assertEqual(self.lib.most_beaten()[0].title, "Hades")
        self.assertEqual(len(self.lib.backlog()), 2)

    def test_empty_library(self):
        lib = GameLibrary(User.objects.create_user("empty"))
        self.assertEqual(lib.completion_rate(), 0)
        self.assertEqual(lib.status_summary()[0][2], 0)


class FormTests(BaseSetup):
    def test_requires_platform(self):
        form = GameForm({"title": "Hades", "status": "new", "times_beaten": 0}, owner=self.user)
        self.assertFalse(form.is_valid())

    def test_new_platform_created(self):
        form = GameForm({"title": "Tetris", "new_platform": "Game Boy",
                         "status": "new", "times_beaten": 0}, owner=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        game = form.save()
        self.assertEqual(game.platform.name, "Game Boy")

    def test_duplicate_rejected(self):
        self.make("Hades")
        form = GameForm({"title": "hades", "platform": self.pc.pk,
                         "status": "new", "times_beaten": 0}, owner=self.user)
        self.assertFalse(form.is_valid())

    def test_completed_sets_beaten_to_one(self):
        form = GameForm({"title": "Hades", "platform": self.pc.pk,
                         "status": "completed", "times_beaten": 0}, owner=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.save().times_beaten, 1)


class ViewTests(BaseSetup):
    def setUp(self):
        super().setUp()
        self.client.login(username="niles", password="pass12345!")

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(reverse("game_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_list_page(self):
        self.make("Hades")
        resp = self.client.get(reverse("game_list"))
        self.assertContains(resp, "Hades")

    def test_add_game(self):
        resp = self.client.post(reverse("game_add"), {
            "title": "Elden Ring", "platform": self.pc.pk, "status": "incomplete", "times_beaten": 0,
        })
        self.assertRedirects(resp, reverse("game_list"))
        self.assertTrue(Game.objects.filter(owner=self.user, title="Elden Ring").exists())

    def test_beat_and_hundred_buttons(self):
        game = self.make("Hades")
        self.client.post(reverse("game_beat", args=[game.pk]), {"note": "yay"})
        self.client.post(reverse("game_hundred", args=[game.pk]))
        game.refresh_from_db()
        self.assertEqual(game.times_beaten, 1)
        self.assertEqual(game.status, Game.HUNDRED)

    def test_set_status(self):
        game = self.make("Zelda", Game.INCOMPLETE)
        self.client.post(reverse("game_set_status", args=[game.pk]), {"status": "forgotten"})
        game.refresh_from_db()
        self.assertEqual(game.status, Game.FORGOTTEN)

    def test_invalid_status_ignored(self):
        game = self.make("Zelda", Game.INCOMPLETE)
        self.client.post(reverse("game_set_status", args=[game.pk]), {"status": "bogus"})
        game.refresh_from_db()
        self.assertEqual(game.status, Game.INCOMPLETE)

    def test_cannot_touch_other_members_games(self):
        theirs = self.make("Secret", owner=self.other)
        self.assertEqual(self.client.get(reverse("game_detail", args=[theirs.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("game_delete", args=[theirs.pk])).status_code, 404)

    def test_delete(self):
        game = self.make("Hades")
        self.client.post(reverse("game_delete", args=[game.pk]))
        self.assertFalse(Game.objects.filter(pk=game.pk).exists())

    def test_signup(self):
        self.client.logout()
        resp = self.client.post(reverse("signup"), {
            "username": "newbie", "password1": "Sup3rStrongPass!", "password2": "Sup3rStrongPass!",
        })
        self.assertRedirects(resp, reverse("game_list"))
        self.assertTrue(User.objects.filter(username="newbie").exists())