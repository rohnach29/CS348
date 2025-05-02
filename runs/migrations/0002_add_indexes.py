from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('runs', '0001_initial'),
    ]

    operations = [
        # Index for run_list view - frequently accessed by user_id
        migrations.AddIndex(
            model_name='runner',
            index=models.Index(fields=['user'], name='idx_runner_user'),
        ),
        
        # Index for run filtering and sorting
        migrations.AddIndex(
            model_name='run',
            index=models.Index(fields=['runner', 'date', 'start_time'], name='idx_run_runner_date_time'),
        ),
        
        # Index for route filtering and duplicate checking
        migrations.AddIndex(
            model_name='route',
            index=models.Index(fields=['creator', 'name'], name='idx_route_creator_name'),
        ),
        
        # Index for run report statistics
        migrations.AddIndex(
            model_name='run',
            index=models.Index(fields=['runner', 'date'], name='idx_run_runner_date'),
        ),
        
        # Index for run route statistics
        migrations.AddIndex(
            model_name='run',
            index=models.Index(fields=['route', 'runner'], name='idx_run_route_runner'),
        ),
        
        # Index for comment filtering and spam prevention
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['run', 'commenter', 'created_at'], name='idx_comment_run_commenter_time'),
        ),
        
        # Index for like operations
        migrations.AddIndex(
            model_name='runlike',
            index=models.Index(fields=['run', 'runner'], name='idx_runlike_run_runner'),
        ),
    ] 