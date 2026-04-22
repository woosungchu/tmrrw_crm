from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CompanyScopedManager(models.Manager):
    """회사 격리 헬퍼. view 에서 Model.objects.for_company(request.company) 로 사용."""

    def for_company(self, company):
        return self.get_queryset().filter(company=company)


class CompanyScopedModel(TimestampedModel):
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, db_index=True
    )

    objects = CompanyScopedManager()

    class Meta:
        abstract = True
