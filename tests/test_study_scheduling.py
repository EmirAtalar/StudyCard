"""Study ratings must remain schedulable after repeated or imported reviews."""
from datetime import date, timedelta
from unittest.mock import patch

from duocards import db
from duocards.settings import settings
from duocards.widgets.study_view import StudyView
from test_practice_and_memory import AppFixture


class StudySchedulingTests(AppFixture):
    def set_progress(self, card, reps, interval, ease):
        with db.get_connection() as conn:
            conn.execute('UPDATE cards SET repetition_count=?,interval_days=?,ease_factor=? WHERE id=?',
                         (reps, interval, ease, card['id']))

    def test_first_successful_reviews_keep_the_existing_schedule(self):
        card = self.card()
        for reps, expected in enumerate((1, 3, 8, 22), 1):
            db.record_study_result(card['id'], 3)
            updated = db.get_card(card['id'])
            self.assertEqual(updated['repetition_count'], reps)
            self.assertEqual(updated['interval_days'], expected)
            self.assertEqual(updated['due_date'], (date.today() + timedelta(days=expected)).isoformat())

    def test_existing_large_values_can_be_rated_and_saved(self):
        card = self.card()
        for rating in (2, 3):
            for interval, ease in ((1783431, 4.35), (2**63 - 1, 4.35), (36500, 1e308)):
                with self.subTest(rating=rating, interval=interval, ease=ease):
                    self.set_progress(card, 12, interval, ease)
                    with db.get_connection() as conn:
                        before = conn.execute('SELECT COUNT(*) FROM study_logs').fetchone()[0]
                    db.record_study_result(card['id'], rating)
                    updated = db.get_card(card['id'])
                    self.assertEqual(updated['interval_days'], 36500)
                    self.assertEqual(updated['due_date'], (date.today() + timedelta(days=36500)).isoformat())
                    self.assertEqual(updated['repetition_count'], 13)
                    self.assertEqual(updated['term'], card['term'])
                    self.assertEqual(updated['definition'], card['definition'])
                    with db.get_connection() as conn:
                        self.assertEqual(conn.execute('SELECT COUNT(*) FROM study_logs').fetchone()[0], before + 1)

    def test_repeated_successful_reviews_stay_within_the_date_range(self):
        card = self.card()
        for _ in range(60):
            db.record_study_result(card['id'], 3)
            updated = db.get_card(card['id'])
            self.assertLessEqual(updated['interval_days'], 36500)
            self.assertEqual(date.fromisoformat(updated['due_date']),
                             date.today() + timedelta(days=updated['interval_days']))
        self.assertEqual(updated['repetition_count'], 60)
        with db.get_connection() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM study_logs').fetchone()[0], 60)

    def test_hard_and_forgotten_reviews_keep_the_existing_behavior(self):
        card = self.card()
        for rating, reps, interval, ease, days in ((2, 6, 12, 2.35, 12), (1, 0, 1, 2.5, 0)):
            with self.subTest(rating=rating):
                self.set_progress(card, 5, 10, 2.5)
                db.record_study_result(card['id'], rating)
                updated = db.get_card(card['id'])
                self.assertEqual(updated['repetition_count'], reps)
                self.assertEqual(updated['interval_days'], interval)
                self.assertAlmostEqual(updated['ease_factor'], ease)
                self.assertEqual(updated['status'], 'learning')
                self.assertEqual(updated['due_date'], (date.today() + timedelta(days=days)).isoformat())

    def test_reviews_cannot_exceed_the_last_supported_date(self):
        card = self.card()
        for today in (date(9999, 12, 30), date.max):
            for rating in (2, 3):
                with self.subTest(today=today, rating=rating):
                    self.set_progress(card, 12, 1783431, 4.35)
                    with patch.object(db, 'date') as clock:
                        clock.today.return_value = today
                        clock.max = date.max
                        db.record_study_result(card['id'], rating)
                    updated = db.get_card(card['id'])
                    self.assertEqual(updated['due_date'], date.max.isoformat())
                    self.assertEqual(updated['interval_days'], (date.max - today).days)

    def test_study_shortcut_and_interval_preview_handle_existing_large_values(self):
        card = self.card()
        self.set_progress(card, 12, 1783431, 4.35)
        settings._settings['reduced_motion'] = True
        view = StudyView()
        self.addCleanup(view.deleteLater)
        self.addCleanup(view.close)
        view.reload_session(custom_cards=[db.get_card(card['id'])], allow_autoplay=False)
        self.assertIn('36500', view.btn_easy.text())
        self.assertIn('36500', view.btn_hard.text())
        view.card_widget.flip(animated=False)
        view._on_rating_shortcut(3)
        self.assertEqual(db.get_card(card['id'])['interval_days'], 36500)
        self.assertEqual(view.known_count, 1)
