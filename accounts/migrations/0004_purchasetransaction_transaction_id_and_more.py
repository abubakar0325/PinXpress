# Generated by Django 5.0.7 on 2025-05-27 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_purchasetransaction_product_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasetransaction',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=100, unique=True),
        ),
        migrations.AddField(
            model_name='topuptransaction',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='purchasetransaction',
            name='product_id',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='purchasetransaction',
            name='product_type',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='purchasetransaction',
            name='status',
            field=models.CharField(max_length=20),
        ),
    ]
