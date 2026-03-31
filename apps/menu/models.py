from django.db import models


class MainCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']


class SubCategory(models.Model):
    main_category = models.ForeignKey(
        MainCategory,
        on_delete=models.CASCADE,
        related_name='sub_categories'
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.main_category.name} > {self.name}"

    class Meta:
        ordering = ['order', 'name']


class MenuItem(models.Model):
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    photo = models.ImageField(upload_to='menu/', blank=True, null=True)
    is_sold_out = models.BooleanField(default=False)
    is_promo = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']


class MenuPDF(models.Model):
    PDF_TYPE_CHOICES = [
        ('menu', 'Menu'),
        ('promo', 'Promo'),
    ]

    pdf_type = models.CharField(max_length=10, choices=PDF_TYPE_CHOICES, default='menu')
    file = models.FileField(upload_to='menu_pdfs/')
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_pdf_type_display()} PDF - {self.uploaded_at}"