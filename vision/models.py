from django.db import models
class Event(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    gesture = models.CharField(max_length=120)
    fingers = models.PositiveSmallIntegerField()
    hands = models.PositiveSmallIntegerField()
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.gesture} ({self.fingers})'
