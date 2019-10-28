from django.utils.translation import ugettext_lazy as _

# STATUS
PENDING = 1
REVIEWED = 2
PUBLISHED = 3
RETURNED = 4
REJECTED = 5
DRAFT = 6
STATUS_CHOICES = (
    (PENDING, _("Tertunda")),
    (REVIEWED, _("Ditinjau")),
    (PUBLISHED, _("Terbit")),
    (RETURNED, _("Dikembalikan")),
    (REJECTED, _("Ditolak")),
    (DRAFT, _("Konsep")),
)

# RATINGS
ONE_STAR = 1
TWO_STAR = 2
THREE_STAR = 3
FOUR_STAR = 4
FIVE_STAR = 5
SCORE_CHOICES = (
    (ONE_STAR, _("Terburuk")),
    (TWO_STAR, _("Buruk")),
    (THREE_STAR, _("Sedang")),
    (FOUR_STAR, _("Baik")),
    (FIVE_STAR, _("Sangat Baik")),
)

# PURPOSES
NOT_TRUE = 1
CRITICISM = 2
SUGGESTION = 3
PURPOSE_CHOICES = (
    (NOT_TRUE, _("Tidak Benar")),
    (CRITICISM, _("Kritik dan Saran")),
    (SUGGESTION, _("Diskusi")),
)

# MEDIA CLASSIFICATION
ELECTRONIC = 1
PRINTED = 2
ONLINE = 3

ELECTRONIC_LABEL = _("Elektronik")
PRINTED_LABEL = _("Cetak")
ONLINE_LABEL = _("Online")
CLASSIFICATION_CHOICES = (
    (ELECTRONIC, ELECTRONIC_LABEL),
    (PRINTED, PRINTED_LABEL),
    (ONLINE, ONLINE_LABEL),
)

# PUBLICATION TYPES
TELEVISION = 1
RADIO = 2

YOUTUBE = 3
SOCIAL_MEDIA = 4
BLOG = 5
NEWS_SITE = 6

NEWSPAPER = 7
MAGAZINE = 8
PUBLICATION_CHOICES = [
    (
        (ELECTRONIC, ELECTRONIC_LABEL), (
            (TELEVISION, _("Televisi")),
            (RADIO, _("Radio")),
        )
    ),
    (
        (ONLINE, ONLINE_LABEL), (
            (YOUTUBE, _("YouTube")),
            (SOCIAL_MEDIA, _("Sosial Media")),
            (BLOG, _("Blog")),
            (NEWS_SITE, _("Situs Berita")),
        )
    ),
    (
        (PRINTED, PRINTED_LABEL), (
            (NEWSPAPER, _("Koran")),
            (MAGAZINE, _("Majalah")),
        )
    ),
]
