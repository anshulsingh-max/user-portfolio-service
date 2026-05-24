from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0045_basket_broker'),
    ]

    operations = [
        migrations.AddField(
            model_name='userportfolio',
            name='expected_investment',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='historicaluserportfolio',
            name='expected_investment',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
