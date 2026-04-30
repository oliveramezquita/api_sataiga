from celery import shared_task
from mail_templated import send_mail


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, template, context, to, cc=None, bcc=None):
    try:
        send_mail(
            template_name=template,
            context=context,
            from_email='Sistema Bellarti <info@bellarti.com.mx>',
            recipient_list=to,
            cc=cc or [],
            bcc=bcc or []
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
