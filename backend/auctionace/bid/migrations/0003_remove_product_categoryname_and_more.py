# Generated by Django 5.1 on 2024-08-12 16:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bid', '0002_remove_category_parentcategoryid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='CategoryName',
        ),
        migrations.AddField(
            model_name='category',
            name='ParentCategoryID',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='CategoryID',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bid.category'),
        ),
    ]
