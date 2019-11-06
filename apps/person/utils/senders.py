import urllib

from django.conf import settings
from django.core.mail import BadHeaderError, send_mail, EmailMultiAlternatives
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import NotFound

SITE_NAME = settings.SITE_NAME


def send_verification_email(data=None):
    """ Send email verification to person """
    if not data:
        raise NotFound()

    user = data.get('user', None)
    request = data.get('request', None)
    new_value = data.get('new_value', None)
    email = data.get('email', None)
    label = data.get('label', _("Verifikasi"))
    username = user.username

    # This secure code append to request before this action
    # And now get back
    secure_code = request.secure_code

    try:
        # Parameter
        subject = _("Otentikasi Aksi %(site_name)s") % {'site_name': SITE_NAME}
        from_email = settings.DEFAULT_FROM_EMAIL
        to = email

        # Message
        text = _("Hi " + username +
                 "JANGAN BERIKAN KODE VERIFIKASI ini kepada siapapun "
                 "TERMASUK PIHAK %(site_name)s. Masukkan otentikasi: " +
                 secure_code)
        html = _("Hi <strong>" + username + "</strong>"
                 "<br /><br />"
                 "JANGAN BERIKAN KODE VERIFIKASI ini kepada siapapun "
                 "TERMASUK PIHAK %(site_name)s.<br />"
                 "Masukkan otentikasi: "
                 "<strong>" + secure_code + "</strong>"
                 "<br /><br />"
                 "Salam, <br /> <strong>%(site_name)s</strong>") % {'site_name': SITE_NAME}

        msg = EmailMultiAlternatives(subject, text, from_email, [to])
        msg.attach_alternative(html, "text/html")
        return msg.send()
    except BadHeaderError:
        raise NotFound(detail=_('Email tidak terkirim.'))


def send_verification_sms(data=None):
    """ Send sms verification to person """
    if not data:
        raise NotFound()

    user = data.get('user', None)
    request = data.get('request', None)
    new_value = data.get('new_value', None)
    username = user.username
    secure_code = request.secure_code

    if new_value[:1] == '0':
        # Replace with 62
        new_value = new_value.replace('0', '62', 1)

    # Number is valid
    country_code = new_value[:2]

    # Number valid country code and min length is 8
    if country_code == '62' and len(new_value) > 8:
        content = urllib.parse.quote(
            'Dari ' + settings.SITE_NAME + '. Kode Otentikasi: ' +
            secure_code + '. JANGAN BERIKAN KESIAPAPUN')
        url = 'http://103.81.246.59:20003/sendsms?account=numb_rahman3&password=123456&numbers=' + new_value + '&content=' + content
        r = urllib.request.Request(url)
        r.add_header('Content-Type', 'application/json')
        r.add_header('Accept', 'application/json')
        r = urllib.request.urlopen(url, data=None)
        return r.read().decode()


def send_password_email(data=None):
    """ Send password reset request """
    if data is None:
        return None

    user = data.get('user', None)
    request = data.get('request', None)
    email = user.email
    username = user.username
    secure_code = request.secure_code

    try:
        # Parameter
        subject = _("Atur Kata Sandi %(site_name)s") % {'site_name': SITE_NAME}
        from_email = settings.DEFAULT_FROM_EMAIL
        to = email

        # Message
        text = _("Hi " + username + ", Atur Ulang Kata Sandi "
                 "JANGAN BERIKAN KODE RAHASIA ini kepada siapapun "
                 "TERMASUK PIHAK %(site_name)s. Masukkan otentikasi: " +
                 secure_code)
        html = _("Hi <strong>" + username + "</strong>"
                 ", Atur Ulang Kata Sandi <br /><br />"
                 "JANGAN BERIKAN KODE RAHASIA ini kepada siapapun "
                 "TERMASUK PIHAK %(site_name)s.<br />"
                 "Masukkan otentikasi: "
                 "<strong>" + secure_code + "</strong>"
                 "<br /><br />"
                 "Salam, <br /> <strong>%(site_name)s</strong>") % {'site_name': SITE_NAME}

        msg = EmailMultiAlternatives(subject, text, from_email, [to])
        msg.attach_alternative(html, "text/html")
        return msg.send()
    except BadHeaderError:
        raise NotFound(detail=_('Email not send.'))


def send_secure_email(data=None):
    """ Send secure action email """
    if data is None:
        return None

    user = data.get('user', None)
    request = data.get('request', None)
    email = data.get('email', None)
    email = user.email if email == user.email else email
    username = user.username
    secure_code = request.secure_code

    try:
        # Parameter
        subject = _("Otentikasi Aksi %(site_name)s") % {'site_name': SITE_NAME}
        from_email = settings.DEFAULT_FROM_EMAIL
        to = email

        # Message
        text = _("Hi " + username + ", Tindakan Penting "
                 "JANGAN BERIKAN KODE RAHASIA ini kepada siapapun "
                 "TERMASUK PIHAK %(site_name)s. Masukkan otentikasi: " +
                 secure_code)
        html = _("Hi <strong>" + username + "</strong>"
                 ", Tindakan Penting <br /><br />"
                 "JANGAN BERIKAN KODE RAHASIA ini kepada siapapun "
                 "TERMASUK PIHAK %(site_name)s.<br />"
                 "Masukkan otentikasi: "
                 "<strong>" + secure_code + "</strong>"
                 "<br /><br />"
                 "Salam, <br /> <strong>%(site_name)s</strong>") % {'site_name': SITE_NAME}

        msg = EmailMultiAlternatives(subject, text, from_email, [to])
        msg.attach_alternative(html, "text/html")
        return msg.send()
    except BadHeaderError:
        raise NotFound(detail=_('Email not send.'))
